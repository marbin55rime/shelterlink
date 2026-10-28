"""
ShelterLink search: find the right service for a child's need, place and time.

The steps for one question:
  1. predict_intent()  -> what does the child need? (the Phase 1 model)
  2. find_landmark()   -> where is the child? (matches place names, even misspelled)
  3. search()          -> which verified services are nearest and open now?
  4. answer()          -> a short reply the child can understand
"""

import math
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import joblib
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
MODEL_PATH = PROJECT / "models" / "intent_model.joblib"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HELPLINES = "Child Helpline 1098 or Emergency 999 (both free)"
EMERGENCY_THRESHOLD = 0.30  # same safety rule as the training script
LANDMARK_MATCH = 0.80  # how similar a word must be to a place name (0 to 1)


# ---------------------------------------------------------------
# Loading data
# ---------------------------------------------------------------
def load_services():
    return pd.read_csv(DATA / "services.csv")


def load_landmarks():
    return pd.read_csv(DATA / "landmarks.csv")


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("No model yet. Run notebooks/02_train_intent_classifier.py first.")
    return joblib.load(MODEL_PATH)


# ---------------------------------------------------------------
# 1. What does the child need?
# ---------------------------------------------------------------
def predict_intent(model, text):
    probs = model.predict_proba([text.lower()])[0]
    classes = list(model.classes_)
    if probs[classes.index("EMERGENCY")] >= EMERGENCY_THRESHOLD:
        return "EMERGENCY"
    return classes[probs.argmax()]


# ---------------------------------------------------------------
# 2. Where is the child?
#    Children say "dhanmondi 32", "batrish number", "lake er pashe".
#    We compare the text with every alias. SequenceMatcher gives a
#    similarity score, so small spelling mistakes still match.
# ---------------------------------------------------------------
def find_landmark(text, landmarks):
    words = text.lower().split()
    best, best_score = None, 0.0
    for _, row in landmarks.iterrows():
        for alias in row["aliases"].split(";"):
            alias = alias.strip().lower()
            size = len(alias.split())
            pieces = [" ".join(words[i:i + size]) for i in range(len(words) - size + 1)]
            score = max((SequenceMatcher(None, alias, p).ratio() for p in pieces), default=0)
            if score > best_score:
                best, best_score = row, score
    return best if best_score >= LANDMARK_MATCH else None


def distance_km(lat1, lon1, lat2, lon2):
    """Straight-line distance between two map points (haversine formula)."""
    r = 6371  # Earth's radius in km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------------------------------------------------------------
# 3. Is it open right now?
#    Returns True / False, or None when we don't know the hours yet.
# ---------------------------------------------------------------
def is_open(service, when):
    # Camps only run between their start and end dates
    if pd.notna(service["start_date"]):
        start = pd.Timestamp(service["start_date"])
        end = pd.Timestamp(service["end_date"]) if pd.notna(service["end_date"]) else start
        if not start.date() <= when.date() <= end.date():
            return False

    if pd.isna(service["days"]) or pd.isna(service["time"]):
        return None
    days = DAY_NAMES if service["days"] == "Every day" else service["days"].split(";")
    if DAY_NAMES[when.weekday()] not in days:
        return False

    hours = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", service["time"])
    if not hours:
        return None
    h1, m1, h2, m2 = map(int, hours.groups())
    now = when.hour * 60 + when.minute
    return h1 * 60 + m1 <= now < h2 * 60 + m2


def has_24h_emergency(service):
    return pd.notna(service["time"]) and "24/7" in service["time"]


def search(category, landmark, when, services, include_unverified=False):
    """Services in a category, open ones first, then nearest first."""
    in_category = services["category"] == category
    if category == "food":
        # Schools and other places that hand out meals count as food too (e.g. Alor School)
        in_category |= services["free_items"].str.contains("meal|lunch|tiffin|snack", case=False, na=False)
    found = services[in_category].copy()
    if not include_unverified:
        # Safety: never send a child to a place nobody has checked
        found = found[found["verified_by"].notna() & (found["verified_by"] != "NOT VERIFIED")]

    found["open_now"] = [is_open(s, when) for _, s in found.iterrows()]
    if landmark is not None:
        found["km"] = [
            distance_km(landmark["latitude"], landmark["longitude"], s["latitude"], s["longitude"])
            if pd.notna(s["latitude"]) else math.nan
            for _, s in found.iterrows()
        ]
    else:
        found["km"] = math.nan

    # Sort: open now (0), unknown (1), closed (2); then by distance
    found["rank"] = found["open_now"].map({True: 0, None: 1, False: 2}).fillna(1)
    return found.sort_values(["rank", "km"], na_position="last")


# ---------------------------------------------------------------
# 4. Put it together into a short reply
# ---------------------------------------------------------------
def describe(service):
    line = f"{service['name']} ({service['landmark']})"
    if pd.notna(service["km"]):
        line += f", about {service['km']:.1f} km away"
    if pd.notna(service["days"]):
        line += f". {service['days'].replace(';', ', ')}, {service['time']}"
    return line


def nearest_emergency(results):
    er = results[[has_24h_emergency(s) for _, s in results.iterrows()]]
    return er.iloc[0] if len(er) else None


def answer_details(text, when=None, model=None, services=None, landmarks=None):
    """
    Everything ShelterLink found for one question, as a dictionary:
      intent, place, best (the service to suggest, or None), is_open,
      emergency (nearest 24-hour emergency hospital, or None),
      facts (a plain-English summary - the ONLY facts a reply may use)
    """
    when = when or datetime.now()
    model = model or load_model()
    services = load_services() if services is None else services
    landmarks = load_landmarks() if landmarks is None else landmarks

    intent = predict_intent(model, text)
    place = find_landmark(text, landmarks)
    where = f" near {place['name']}" if place is not None else ""
    found = {"intent": intent, "place": place, "best": None, "is_open": False, "emergency": None}

    if intent == "EMERGENCY":
        found["emergency"] = nearest_emergency(search("health", place, when, services))
        facts = f"Call {HELPLINES} now."
        if found["emergency"] is not None:
            facts += f" Nearest emergency (open 24 hours): {describe(found['emergency'])}."
        return {**found, "facts": facts}

    if intent == "OTHER":
        return {**found, "facts": "I can help you find free food, a doctor, or a class. What do you need?"}

    results = search(intent.lower(), place, when, services)
    open_now = results[results["open_now"] == True]  # noqa: E712 (open_now can be None)

    if len(open_now):
        found["best"], found["is_open"] = open_now.iloc[0], True
        facts = f"Open now{where}: {describe(found['best'])}."
    elif len(results):
        found["best"] = results.iloc[0]
        facts = f"Nothing is open right now{where}. Next option: {describe(found['best'])}."
        if intent == "HEALTH":
            found["emergency"] = nearest_emergency(results)
            if found["emergency"] is not None:
                facts += f" If it is serious, go to the Emergency gate at {found['emergency']['name']} (open 24 hours)."
    else:
        facts = f"I don't have a checked place for this yet. Ask your Alor School teacher, or call {HELPLINES}."
    if place is None and len(results):
        facts += " Tell me where you are, and I can find the nearest one."
    return {**found, "facts": facts}


def answer(text, when=None, model=None, services=None, landmarks=None):
    """Short English reply: (intent, place, reply)."""
    found = answer_details(text, when, model, services, landmarks)
    return found["intent"], found["place"], found["facts"]
