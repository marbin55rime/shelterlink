"""
ShelterLink Bangla replies (Phase 3).

Two ways to write the reply:
  1. Claude (an LLM) rewrites the checked facts into short, kind Bangla.
     It is only given facts from our verified data, so it cannot invent places.
  2. Offline templates: ready-made Bangla sentences, used when there is
     no internet or no API key, or if Claude fails.

Safety rule: for emergencies, the helpline line is ALWAYS added by this code,
never left to the LLM.
"""

import os
from pathlib import Path

import anthropic

from shelterlink.search import PROJECT, answer_details

MODEL = "claude-opus-5-5"
HOSPITAL_GUIDE = (PROJECT / "docs" / "hospital_guide.md").read_text(encoding="utf-8")

EMERGENCY_LINE = "🚨 এখনই ১০৯৮ (শিশু হেল্পলাইন) বা ৯৯৯ নম্বরে ফোন করো। দুইটাই ফ্রি।"

SYSTEM_PROMPT = """You are ShelterLink, a kind helper for street children in Dhaka, Bangladesh.
Children aged 5-14 ask you where to find free food, a doctor, or a class.

How to reply:
- Write in simple, spoken Bangla (Bengali script). Use "তুমি", like a caring older sibling.
- At most 3 short sentences. Many children cannot read well; the reply may be read aloud.
- Use ONLY the facts given to you. Never add a place, time, price or phone number that is not in the facts.
  Place and organization names may stay in English.
- Never diagnose an illness and never name a medicine.
- If the facts say nothing was found, say so kindly and give the advice in the facts.
- Reply with the message only: no headings, no lists, no notes to me."""

DAYS_BN = {"Sat": "শনি", "Sun": "রবি", "Mon": "সোম", "Tue": "মঙ্গল",
           "Wed": "বুধ", "Thu": "বৃহস্পতি", "Fri": "শুক্র"}

_client = None


def has_credentials():
    """True if an API key, token, or `ant auth login` profile is set up."""
    env = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE")
    return any(os.environ.get(name) for name in env) or (Path.home() / ".config" / "anthropic").exists()


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# ---------------------------------------------------------------
# 1. Claude: rewrite the checked facts in Bangla
# ---------------------------------------------------------------
def claude_reply(child_text, found):
    context = f"Child said: {child_text}\nNeed detected: {found['intent']}\nChecked facts: {found['facts']}"
    if found["intent"] in ("HEALTH", "EMERGENCY"):
        context += f"\n\nHospital guide (background only):\n{HOSPITAL_GUIDE}"

    response = get_client().beta.messages.create(
        model=MODEL,
        max_tokens=2000,
        output_config={"effort": "low"},  # short chat replies don't need deep thinking
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the request is declined, the API retries on a fallback model
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    if response.stop_reason == "refusal":
        return None
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or None


# ---------------------------------------------------------------
# 2. Offline templates
# ---------------------------------------------------------------
def hours_bn(service):
    if service["type"] == "hospital":
        return "বহির্বিভাগ শনি থেকে বৃহস্পতি সকাল ৮টা থেকে দুপুর ২:৩০ (টিকিট ২টা পর্যন্ত, ১০ টাকা), শুক্রবার বন্ধ।"
    if isinstance(service["days"], str):
        days = ", ".join(DAYS_BN.get(d, d) + "বার" for d in service["days"].split(";"))
        return f"খোলা থাকে {days}, {service['time']}।"
    return ""


def where_bn(service):
    line = f"{service['name']} ({service['landmark']})"
    km = service.get("km")
    if km == km and km is not None:  # km != km only when it is NaN (unknown)
        line += ", একদম কাছে" if km < 0.2 else f", প্রায় {km:.1f} কিমি দূরে"
    return line


def template_reply(found):
    intent, best = found["intent"], found["best"]
    if intent == "OTHER":
        return "আমি তোমাকে ফ্রি খাবার, ডাক্তার আর ক্লাস খুঁজে দিতে পারি। তোমার কী লাগবে?"
    if intent == "EMERGENCY":
        if found["emergency"] is not None:
            return f"কাছের জরুরি বিভাগ (২৪ ঘণ্টা খোলা): {where_bn(found['emergency'])}।"
        return ""
    if best is None:
        return "এখনো যাচাই করা কোনো জায়গা নেই। তোমার আলোর স্কুলের শিক্ষককে জিজ্ঞেস করো, অথবা ১০৯৮ নম্বরে ফোন করো।"

    if found["is_open"]:
        reply = f"এখন খোলা আছে: {where_bn(best)}। {hours_bn(best)}"
    else:
        reply = f"এখন কিছু খোলা নেই। এখানে যেতে পারো: {where_bn(best)}। {hours_bn(best)}"
        if found["emergency"] is not None:
            reply += " খুব খারাপ লাগলে এখনই জরুরি বিভাগে যাও, ২৪ ঘণ্টা খোলা।"
    if found["place"] is None:
        reply += " তুমি কোথায় আছো বললে কাছের জায়গা খুঁজে দিতে পারবো।"
    return reply


# ---------------------------------------------------------------
# Put it together
# ---------------------------------------------------------------
def reply_in_bangla(child_text, when=None, model=None, services=None, landmarks=None, use_claude=True):
    """Returns (found, reply, source) where source is 'claude' or 'offline'."""
    found = answer_details(child_text, when, model, services, landmarks)

    reply, source = None, "offline"
    if use_claude and has_credentials():
        try:
            reply = claude_reply(child_text, found)
            source = "claude"
        except anthropic.AuthenticationError:
            pass  # no API key yet: use the offline templates
        except anthropic.APIConnectionError:
            pass  # no internet
        except anthropic.APIStatusError:
            pass  # API problem: rate limit, server error, ...
        except anthropic.AnthropicError:
            pass  # anything else from the SDK, e.g. no credentials configured
    if not reply:
        reply, source = template_reply(found), "offline"

    if found["intent"] == "EMERGENCY":
        reply = f"{EMERGENCY_LINE} {reply}".strip()
    return found, reply, source
