"""
ShelterLink - Step 4: Replies in Bangla (Phase 3)

child's sentence -> need + place -> verified service -> short Bangla reply

What this script teaches you:
  - Using an LLM (Claude) safely: it only rewrites facts we already checked
  - A fallback path that works offline (templates)
  - Keeping safety-critical text (emergency numbers) in code, not in the LLM

With an Anthropic API key set (ANTHROPIC_API_KEY), replies come from Claude.
Without one, the offline Bangla templates are used.

Run it from the ShelterLink folder:
    python notebooks/04_bangla_replies.py
    python notebooks/04_bangla_replies.py "khida lagse ami dhanmondi 32 e"
Add --offline to skip Claude (free, no internet needed).
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from shelterlink.bangla import reply_in_bangla
from shelterlink.search import load_landmarks, load_model, load_services

model, services, landmarks = load_model(), load_services(), load_landmarks()
args = [a for a in sys.argv[1:] if a != "--offline"]
use_claude = "--offline" not in sys.argv


def ask(text, when):
    found, reply, source = reply_in_bangla(text, when, model, services, landmarks, use_claude)
    print(f'Child: "{text}"   [{when:%a %I:%M %p}]  need: {found["intent"]}')
    print(f"  ShelterLink ({source}): {reply}\n")


if args:
    ask(" ".join(args), datetime.now())
else:
    friday_11am = datetime(2026, 10, 30, 11, 0)
    friday_8pm = datetime(2026, 10, 30, 20, 0)
    sunday_10am = datetime(2026, 11, 1, 10, 0)

    ask("khida lagse, dhanmondi 32", friday_11am)
    ask("porte chai ami lake er pashe", sunday_10am)
    ask("jor ashche, ami shahbag e", sunday_10am)
    ask("soril ta bala nai", friday_8pm)
    ask("bachao amake martese, science lab", friday_8pm)
    ask("tomar nam ki", sunday_10am)
