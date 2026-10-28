"""
ShelterLink - Step 3: Smart search (Phase 2)

Connects your Phase 1 model to the services list:
    child's sentence -> need + place -> nearest verified service open now

What this script teaches you:
  - Splitting a program into a reusable module (shelterlink/search.py)
  - Fuzzy matching (finding place names even when misspelled)
  - Map distance with the haversine formula
  - Working with days and times ("open now?")

Run it from the ShelterLink folder:
    python notebooks/03_smart_search.py
Or ask your own question:
    python notebooks/03_smart_search.py "khida lagse ami dhanmondi 32 e"
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so Python finds shelterlink/
sys.stdout.reconfigure(encoding="utf-8")

from shelterlink.search import answer, load_landmarks, load_model, load_services

model, services, landmarks = load_model(), load_services(), load_landmarks()


def ask(text, when):
    intent, place, reply = answer(text, when, model, services, landmarks)
    place_name = place["name"] if place is not None else "unknown"
    print(f'Child: "{text}"   [{when:%a %d %b, %I:%M %p}]')
    print(f"  need: {intent} | place: {place_name}")
    print(f"  ShelterLink: {reply}\n")


if len(sys.argv) > 1:
    ask(" ".join(sys.argv[1:]), datetime.now())
else:
    # Test questions at different times, to check the "open now" logic
    friday_11am = datetime(2026, 10, 30, 11, 0)
    friday_8pm = datetime(2026, 10, 30, 20, 0)
    sunday_10am = datetime(2026, 11, 1, 10, 0)
    sunday_4pm = datetime(2026, 11, 1, 16, 0)

    ask("porte chai ami dhanmondi 32 e", friday_11am)
    ask("aj class ache? ami lake er pashe", sunday_10am)
    ask("jor ashche, ami shahbag e", sunday_10am)
    ask("dacter dhekhan lagbo, ami agargaon", sunday_4pm)
    ask("soril ta bala nai", friday_8pm)
    ask("khida lagse, dhanmondi 32", friday_11am)
    ask("bachao amake martese, science lab", friday_8pm)
    ask("tomar nam ki", sunday_10am)
