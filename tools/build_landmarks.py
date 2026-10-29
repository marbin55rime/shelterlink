"""
Build data/landmarks.csv for the whole of Dhaka city.

For each area below, we ask OpenStreetMap (Nominatim, a free public map service)
for its map location, once, and save the result. After that ShelterLink works
offline. Only area names are sent - never anything a child says.

Run it from the ShelterLink folder (needs internet, takes about 2 minutes):
    python tools/build_landmarks.py

To add a place: add a line to AREAS and run the script again.
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "landmarks.csv"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ShelterLink/0.1 (https://github.com/marbin55rime/shelterlink)"
DHAKA_BOX = "90.30,23.92,90.52,23.66"  # left, top, right, bottom of Dhaka city

# (name, aliases children use, OpenStreetMap search text, manual lat/lon or None)
# Manual locations are used where we know the exact spot (e.g. Alor School's bridge).
AREAS = [
    ("Dhanmondi 32", "dhanmondi 32;dhanmondi 32 number;32 number;batrish number;ধানমন্ডি ৩২;৩২ নম্বর;dhanmondi bridge", None, (23.7517, 90.3780)),
    ("Dhanmondi Lake", "dhanmondi lake;lake er pashe;ধানমন্ডি লেক", None, (23.7465, 90.3760)),
    ("Dhanmondi 27", "dhanmondi 27;27 number;ধানমন্ডি ২৭", "Dhanmondi 27", None),
    ("Dhanmondi 15", "dhanmondi 15;15 number;ধানমন্ডি ১৫", "Dhanmondi 15", None),
    ("Science Lab", "science lab;science lab mor;সায়েন্সল্যাব;সাইন্সল্যাব", "Science Laboratory, Dhaka", None),
    ("Kalabagan", "kalabagan;কলাবাগান", "Kalabagan", None),
    ("Jigatola", "jigatola;জিগাতলা", "Jigatola", None),
    ("Hazaribagh", "hazaribagh;hazaribag;হাজারীবাগ", "Hazaribagh", None),
    ("Rayer Bazar", "rayer bazar;rayerbazar;রায়ের বাজার", "Rayer Bazar", None),
    ("Bosila", "bosila;basila;বসিলা", "Basila", None),
    ("Mohammadpur", "mohammadpur;mohammodpur;মোহাম্মদপুর", "Mohammadpur", None),
    ("Mohammadpur Town Hall", "town hall;mohammadpur town hall;টাউন হল", "Mohammadpur Town Hall", None),
    ("Adabor", "adabor;adabar;আদাবর", "Adabor", None),
    ("Shyamoli", "shyamoli;shamoli;শ্যামলী", "Shyamoli", None),
    ("Asad Gate", "asad gate;asadgate;আসাদগেট", "Asad Gate", None),
    ("Kallyanpur", "kallyanpur;kalyanpur;কল্যাণপুর", "Kallyanpur", None),
    ("Gabtoli", "gabtoli;gabtali;gabtoli bus stand;গাবতলী", "Gabtali", None),
    ("Technical", "technical;technical mor;টেকনিক্যাল", "Technical Mor, Dhaka", None),
    ("Mirpur 1", "mirpur 1;mirpur ek;মিরপুর ১", "Mirpur 1", None),
    ("Mirpur 2", "mirpur 2;mirpur dui;মিরপুর ২", "Mirpur 2", None),
    ("Mirpur 10", "mirpur 10;mirpur dosh;মিরপুর ১০", "Mirpur 10", None),
    ("Mirpur 11", "mirpur 11;মিরপুর ১১", "Mirpur 11", None),
    ("Mirpur 12", "mirpur 12;মিরপুর ১২", "Mirpur 12", None),
    ("Pallabi", "pallabi;পল্লবী", "Pallabi", None),
    ("Kazipara", "kazipara;কাজীপাড়া", "Kazipara", None),
    ("Shewrapara", "shewrapara;sheorapara;শেওড়াপাড়া", "Shewrapara", None),
    ("Agargaon", "agargaon;আগারগাঁও", "Agargaon", None),
    ("Bijoy Sarani", "bijoy sarani;bijoy shoroni;বিজয় সরণি", "Bijoy Sarani", None),
    ("Kafrul", "kafrul;কাফরুল", "Kafrul", None),
    ("Ibrahimpur", "ibrahimpur;ইব্রাহিমপুর", "Ibrahimpur", None),
    ("Cantonment", "cantonment;ক্যান্টনমেন্ট", "Dhaka Cantonment", None),
    ("Farmgate", "farmgate;farm gate;farmget;ফার্মগেট", "Farmgate", None),
    ("Tejgaon", "tejgaon;তেজগাঁও", "Tejgaon", None),
    ("Karwan Bazar", "karwan bazar;kawran bazar;karwanbazar;কারওয়ান বাজার", "Karwan Bazar", None),
    ("Panthapath", "panthapath;pantha path;পান্থপথ", "Panthapath", None),
    ("Green Road", "green road;গ্রিন রোড", "Green Road, Dhaka", None),
    ("Bangla Motor", "bangla motor;banglamotor;বাংলামোটর", "Bangla Motor", None),
    ("Moghbazar", "moghbazar;mogbazar;মগবাজার", "Moghbazar", None),
    ("Hatirjheel", "hatirjheel;hatirjhil;হাতিরঝিল", "Hatirjheel", None),
    ("Mouchak", "mouchak;মৌচাক", "Mouchak Market", None),
    ("Malibagh", "malibagh;malibag;মালিবাগ", "Malibagh", None),
    ("Shantinagar", "shantinagar;শান্তিনগর", "Shantinagar", None),
    ("Kakrail", "kakrail;কাকরাইল", "Kakrail", None),
    ("Ramna", "ramna;ramna park;রমনা", "Ramna Park", None),
    ("Segunbagicha", "segunbagicha;সেগুনবাগিচা", "Segunbagicha", None),
    ("Shahbag", "shahbag;shahbagh;শাহবাগ", "Shahbag", None),
    ("Dhaka University", "dhaka university;tsc;dhabi;ঢাকা বিশ্ববিদ্যালয়;ঢাবি;টিএসসি", "University of Dhaka", None),
    ("Nilkhet", "nilkhet;নীলক্ষেত", "Nilkhet", None),
    ("New Market", "new market;newmarket;নিউমার্কেট;নিউ মার্কেট", "New Market, Dhaka", None),
    ("Azimpur", "azimpur;আজিমপুর", "Azimpur", None),
    ("Lalbagh", "lalbagh;lalbag;lalbagh kella;লালবাগ", "Lalbagh Fort", None),
    ("Shaheed Minar", "shaheed minar;bakshibazar;dhaka medical;শহীদ মিনার;বকশীবাজার;ঢাকা মেডিকেল", "Central Shaheed Minar", None),
    ("Chankharpul", "chankharpul;চানখারপুল", "Chankharpul", None),
    ("Chawkbazar", "chawkbazar;chokbazar;চকবাজার", "Chawkbazar, Dhaka", None),
    ("Bangshal", "bangshal;বংশাল", "Bangshal", None),
    ("Sadarghat", "sadarghat;launch ghat;সদরঘাট", "Sadarghat", None),
    ("Gulistan", "gulistan;golap shah mazar;গুলিস্তান", "Gulistan, Dhaka", None),
    ("Paltan", "paltan;polton;পল্টন", "Paltan", None),
    ("Motijheel", "motijheel;motijhil;মতিঝিল", "Motijheel", None),
    ("Kamalapur", "kamalapur;kamalapur station;railway station;কমলাপুর", "Kamalapur Railway Station", None),
    ("Wari", "wari;ওয়ারী", "Wari Thana", None),
    ("Gendaria", "gendaria;গেন্ডারিয়া", "Gendaria", None),
    ("Sayedabad", "sayedabad;saidabad;সায়েদাবাদ", "Sayedabad Bus Terminal", None),
    ("Jatrabari", "jatrabari;যাত্রাবাড়ী", "Jatrabari", None),
    ("Postogola", "postogola;পোস্তগোলা", "Postogola", None),
    ("Demra", "demra;ডেমরা", "Demra", None),
    ("Kamrangirchar", "kamrangirchar;কামরাঙ্গীরচর", "Kamrangirchar", None),
    ("Basabo", "basabo;bashabo;বাসাবো", "Basabo", None),
    ("Mugda", "mugda;মুগদা", "Mugda", None),
    ("Khilgaon", "khilgaon;খিলগাঁও", "Khilgaon", None),
    ("Rampura", "rampura;রামপুরা", "Rampura", None),
    ("Banasree", "banasree;banasri;বনশ্রী", "Banasree", None),
    ("Aftabnagar", "aftabnagar;আফতাবনগর", "Aftabnagar", None),
    ("Badda", "badda;বাড্ডা", "Badda", None),
    ("Mohakhali", "mohakhali;mohakhali bus stand;মহাখালী", "Mohakhali", None),
    ("Banani", "banani;বনানী", "Banani", None),
    ("Gulshan 1", "gulshan 1;gulshan ek;গুলশান ১", "Gulshan 1", None),
    ("Gulshan 2", "gulshan 2;gulshan dui;গুলশান ২", "Gulshan 2", None),
    ("Nadda", "nadda;নদ্দা", "Nadda", None),
    ("Bashundhara", "bashundhara;bosundhora;বসুন্ধরা", "Bashundhara Residential Area", None),
    ("Kuril", "kuril;kuril bishwa road;কুড়িল", "Kuril", None),
    ("Khilkhet", "khilkhet;খিলক্ষেত", "Khilkhet", None),
    ("Airport", "airport;biman bondor;এয়ারপোর্ট;বিমানবন্দর", "Hazrat Shahjalal International Airport", None),
    ("Kawla", "kawla;কাওলা", "Kawla", None),
    ("Uttara", "uttara;uttora;উত্তরা", "Uttara", None),
    ("Abdullahpur", "abdullahpur;আব্দুল্লাহপুর", "Abdullahpur", None),
    ("Dakshinkhan", "dakshinkhan;dokkhinkhan;দক্ষিণখান", "Dakshinkhan", None),
    ("Uttarkhan", "uttarkhan;উত্তরখান", "Uttarkhan", None),
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
    return round(float(results[0]["lat"]), 5), round(float(results[0]["lon"]), 5)


rows, missing = [], []
for name, aliases, query, manual in AREAS:
    if manual:
        lat, lon = manual
        source = "manual"
    else:
        found = geocode(query)
        if found is None:
            missing.append(name)
            continue
        lat, lon = found
        source = "openstreetmap"
    rows.append({"name": name, "latitude": lat, "longitude": lon, "aliases": aliases, "source": source})
    print(f"  {name:22} {lat:.4f}, {lon:.4f}  ({source})")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "latitude", "longitude", "aliases", "source"])
    writer.writeheader()
    writer.writerows(rows)

print(f"\nSaved {len(rows)} places to {OUT}")
if missing:
    print(f"Not found on OpenStreetMap ({len(missing)}): {', '.join(missing)}")
    print("Fix the search text for these in AREAS, or add a manual location.")
