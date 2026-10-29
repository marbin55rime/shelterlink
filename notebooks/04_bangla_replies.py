"""
ShelterLink - Step 4: Replies in Bangla (Phase 3)

child's sentence -> need + place -> verified service -> short Bangla reply

What this script teaches you:
  - Using an LLM (Claude) safely: it only rewrites facts we already checked
  - A fallback path that works offline (templates)
  - Keeping safety-critical text (emergency numbers) in code, not in the LLM
  - Two ways to know where a child is: a place name, or GPS

With an Anthropic API key set (ANTHROPIC_API_KEY), replies come from Claude.
Without one, the offline Bangla templates are used.

Run it from the ShelterLink folder:
    python notebooks/04_bangla_replies.py
    python notebooks/04_bangla_replies.py "khida lagse ami mirpur 10 e"
    python notebooks/04_bangla_replies.py "jor ashche" --at 23.8103,90.4125
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
use_claude = "--offline" not in sys.argv

# --at LAT,LON gives a GPS location instead of a place name
gps = None
args = [a for a in sys.argv[1:] if a != "--offline"]
if "--at" in args:
    i = args.index("--at")
    gps = tuple(float(x) for x in args[i + 1].split(","))
    del args[i:i + 2]


def ask(text, when, location=None):
    found, reply, source = reply_in_bangla(text, when, model, services, landmarks, use_claude, location)
    place = found["place"]["name"] if found["place"] is not None else "unknown"
    print(f'Child: "{text}"   [{when:%a %I:%M %p}]  need: {found["intent"]}  place: {place}')
    print(f"  ShelterLink ({source}): {reply}\n")


if args:
    ask(" ".join(args), datetime.now(), gps)
else:
    friday_11am = datetime(2026, 10, 30, 11, 0)
    friday_8pm = datetime(2026, 10, 30, 20, 0)
    sunday_10am = datetime(2026, 11, 1, 10, 0)

    print("--- Different parts of Dhaka ---\n")
    ask("khida lagse, dhanmondi 32", friday_11am)
    ask("jor ashche, ami shahbag e", sunday_10am)
    ask("dacter dhekhan lagbo ami mirpur 10 e", sunday_10am)
    ask("pet betha korche, jatrabari", sunday_10am)
    ask("soril ta bala nai ami uttara", sunday_10am)
    ask("porte chai ami kamalapur station e", sunday_10am)
    ask("bachao amake martese, sadarghat", friday_8pm)

    print("--- With GPS (e.g. a kiosk at Farmgate) ---\n")
    ask("oshudh kothay pabo", sunday_10am, location=(23.7590, 90.3871))

    print("--- No place given ---\n")
    ask("soril ta bala nai", friday_8pm)
