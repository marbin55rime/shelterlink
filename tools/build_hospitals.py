"""
Add Dhaka's government hospitals to data/services.csv.

For each hospital below, we ask OpenStreetMap (Nominatim, a free public map service)
for its map location, once. Only hospital names are sent - never anything a child says.
Hospitals already in services.csv (same name) are left as they are.

Two kinds:
  - general:    any illness or injury. OPD 10 taka ticket + Emergency open 24 hours.
                The chatbot suggests the nearest one.
  - specialist: one kind of problem only (eyes, burns, teeth...). Saved for later;
                the chatbot does not suggest them for a normal "I'm sick" yet.

Run it from the ShelterLink folder (needs internet, takes about 1 minute):
    python tools/build_hospitals.py

To add a hospital: add a line to HOSPITALS and run the script again.
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SERVICES = Path(__file__).resolve().parent.parent / "data" / "services.csv"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ShelterLink/0.1 (https://github.com/marbin55rime/shelterlink)"
DHAKA_BOX = "90.30,23.92,90.52,23.66"  # left, top, right, bottom of Dhaka city

GENERAL_TIME = "OPD 08:00-14:30 (ticket counter closes 14:00); Emergency 24/7 every day"
SPECIALIST_TIME = "OPD 08:00-14:30 (ticket counter closes 14:00)"

# (name, landmark a child would know, OpenStreetMap search text, kind, what it is for)
HOSPITALS = [
    ("Sir Salimullah Medical College Mitford Hospital", "Babubazar - near Sadarghat",
     "Sir Salimullah Medical College Mitford Hospital", "general", "Big general hospital in Old Dhaka."),
    ("Mugda Medical College Hospital", "Mugda", "Mugda Medical College Hospital", "general",
     "General hospital, near Basabo, Khilgaon and Kamalapur."),
    ("Kurmitola General Hospital", "Kurmitola - Airport Road", "Kurmitola General Hospital", "general",
     "General hospital, near Banani, Khilkhet and the airport."),
    ("Kuwait Bangladesh Friendship Government Hospital", "Uttara", "Kuwait Bangladesh Friendship Government Hospital",
     "general", "General hospital in Uttara."),
    ("Mohanagar General Hospital", "Nayabazar - Babubazar, Old Dhaka", "Mohanagar General Hospital", "general",
     "City Corporation general hospital in Old Dhaka."),
    ("National Institute of Traumatology and Orthopaedic Rehabilitation (Pongu Hospital)", "Sher-e-Bangla Nagar - Shyamoli",
     "National Institute of Traumatology and Orthopaedic Rehabilitation", "specialist",
     "For broken bones and road accidents. Has a 24-hour emergency."),
    ("National Institute of Burn and Plastic Surgery", "Next to Dhaka Medical College Hospital",
     "Burn Institute", "specialist", "For burns. Has a 24-hour emergency."),
    ("Infectious Diseases Hospital", "Mohakhali", "Infectious Disease Hospital", "specialist",
     "For infections such as diarrhoea, measles and chickenpox."),
    ("National Institute of Diseases of the Chest and Hospital", "Mohakhali",
     "National Institute of Diseases of the Chest and Hospital", "specialist", "For long cough, TB and breathing problems."),
    ("National Institute of Ophthalmology and Hospital", "Sher-e-Bangla Nagar - Agargaon",
     "National Institute of Ophthalmology", "specialist", "For eyes."),
    ("National Institute of ENT", "Tejgaon", "ENT Institute Tejgaon", "specialist", "For ear, nose and throat."),
    ("Dhaka Dental College Hospital", "Mirpur 14", "Dhaka Dental College", "specialist", "For teeth."),
    ("National Institute of Mental Health", "Sher-e-Bangla Nagar - Agargaon", "National Institute of Mental Health and Hospital",
     "specialist", "For mental health: very sad, scared or troubled."),
    ("National Institute of Neurosciences and Hospital", "Agargaon", "National Institute of Neurosciences & Hospital",
     "specialist", "For the brain and nerves (head injury, fits). Has a 24-hour emergency."),
    ("National Institute of Cardiovascular Diseases (NICVD)", "Sher-e-Bangla Nagar",
     "জাতীয় হৃদরোগ ইনস্টিটিউট", "specialist", "For the heart. Has a 24-hour emergency."),
    ("National Institute of Kidney Diseases and Urology", "Sher-e-Bangla Nagar",
     "National Institute of Kidney Diseases & Urology", "specialist", "For the kidneys."),
    ("Maternal and Child Health Training Institute (Azimpur Matrisadan)", "Azimpur",
     "Azimpur Maternity Hospital", "specialist", "For pregnant girls, mothers and babies."),
]


def geocode(query):
    params = urllib.parse.urlencode({
        "q": f"{query}, Dhaka, Bangladesh", "format": "json", "limit": 1,
        "countrycodes": "bd", "viewbox": DHAKA_BOX, "bounded": 1,
    })
    request = urllib.request.Request(f"{NOMINATIM}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        results = json.load(response)
    time.sleep(1.1)  # OpenStreetMap's rule: at most 1 request per second
    if not results:
        return None
    return round(float(results[0]["lat"]), 5), round(float(results[0]["lon"]), 5), results[0]["display_name"]


with open(SERVICES, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields, rows = reader.fieldnames, list(reader)
known = {row["name"] for row in rows}
next_id = max(int(row["id"]) for row in rows) + 1

added, missing = 0, []
for name, landmark, query, kind, what_for in HOSPITALS:
    if name in known:
        continue
    found = geocode(query)
    if found is None:
        missing.append(name)
        continue
    lat, lon, osm_name = found
    rows.append({
        "id": next_id, "category": "health",
        "type": "hospital" if kind == "general" else "specialist_hospital",
        "name": name, "landmark": landmark, "latitude": lat, "longitude": lon,
        "days": "Sat;Sun;Mon;Tue;Wed;Thu",
        "time": GENERAL_TIME if kind == "general" else SPECIALIST_TIME,
        "start_date": "", "end_date": "", "age_range": "all", "cost": "OPD ticket 10 taka",
        "free_items": "basic medicine (limited stock)", "language": "Bangla", "organizer": "Government",
        "contact": "", "verified_by": "public government hospital information",
        "verified_date": date.today().isoformat(),
        "notes": f"{what_for} OPD closed Friday. Child should go with a trusted adult. "
                 "See docs/hospital_guide.md. Map location from OpenStreetMap - confirm on Google Maps.",
    })
    next_id += 1
    added += 1
    print(f"  {name[:60]:60} {lat:.4f}, {lon:.4f}\n      OpenStreetMap: {osm_name[:100]}")

with open(SERVICES, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nAdded {added} hospitals to {SERVICES}")
if missing:
    print(f"Not found on OpenStreetMap ({len(missing)}): {', '.join(missing)}")
    print("Fix the search text for these in HOSPITALS.")
