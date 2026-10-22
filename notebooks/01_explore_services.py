"""
ShelterLink - Step 1: Explore the data

What this script teaches you:
  - Loading a CSV file with pandas
  - Counting, filtering and checking data
  - Working with dates (for camps)
  - Making a simple chart with matplotlib

Run it from the ShelterLink folder:
    python notebooks/01_explore_services.py
"""

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save charts to files instead of opening a window
import matplotlib.pyplot as plt
import pandas as pd

# Paths are built from this file's location, so the script works from any folder
PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUTPUT = PROJECT / "outputs"
OUTPUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------
# 1. Load the services
# ---------------------------------------------------------------
services = pd.read_csv(DATA / "services.csv")
print("=== SERVICES ===")
print(f"Total services: {len(services)}\n")

# ---------------------------------------------------------------
# 2. How many services in each category?
# ---------------------------------------------------------------
print("Services per category:")
print(services["category"].value_counts().to_string(), "\n")

# ---------------------------------------------------------------
# 3. Safety check: which services are NOT verified yet?
# ---------------------------------------------------------------
not_verified = services[
    services["verified_by"].isna() | (services["verified_by"] == "NOT VERIFIED")
]
print(f"Not verified yet: {len(not_verified)}")
for _, row in not_verified.iterrows():
    print(f"  - #{row['id']} {row['name']}")
print()

# ---------------------------------------------------------------
# 4. Camps and events: which are upcoming, which are over?
# ---------------------------------------------------------------
services["start_date"] = pd.to_datetime(services["start_date"], errors="coerce")
services["end_date"] = pd.to_datetime(services["end_date"], errors="coerce")
today = pd.Timestamp(date.today())

events = services[services["start_date"].notna()]
upcoming = events[events["end_date"] >= today]
finished = events[events["end_date"] < today]
print(f"Camps/events: {len(events)}  (upcoming: {len(upcoming)}, finished: {len(finished)})")
for _, row in upcoming.iterrows():
    print(f"  - {row['name']} on {row['start_date'].date()} at {row['landmark']}")
print()

# ---------------------------------------------------------------
# 5. Load the chatbot training sentences
# ---------------------------------------------------------------
intents = pd.read_csv(DATA / "intent_examples.csv")
print("=== CHATBOT TRAINING SENTENCES ===")
print(f"Total sentences: {len(intents)}")
counts = intents["intent"].value_counts()
print(counts.to_string())
print("Goal for Phase 1: at least 150 sentences per intent.\n")

# ---------------------------------------------------------------
# 6. Chart: services per category
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 4))
services["category"].value_counts().plot(kind="bar", ax=ax, color="#4a7bd0")
ax.set_title("ShelterLink: services per category")
ax.set_xlabel("")
ax.set_ylabel("Number of services")
plt.xticks(rotation=0)
plt.tight_layout()
chart_path = OUTPUT / "services_per_category.png"
plt.savefig(chart_path)
print(f"Chart saved to: {chart_path}")
