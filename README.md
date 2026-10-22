# ShelterLink

**An AI voice helpline that connects street children to free food, health care and education, in their own language, from any phone or a kiosk.**

Built by a volunteer street-class teacher, for the children they teach.

## Scope (v1)
🍲 Food · ⚕️ Health care · 📚 Education, plus emergency routing to the child helpline, which is always on.

## Project structure
```
ShelterLink/
├── data/
│   ├── services.csv           # verified food, health, education services
│   ├── intent_examples.csv    # training sentences for the chatbot
│   └── README.md              # how to fill in the data
├── docs/
│   ├── field_research_guide.md      # interview questions + verification checklist
│   └── child_safeguarding_policy.md # safety rules (draft)
├── notebooks/
│   └── 01_explore_services.py # first Python script: look at the data
├── LEARNING_LOG.md            # what I learn every week
└── requirements.txt
```

## Roadmap
- [ ] **Phase 0: Field work and foundations** (weeks 1–4): map 30+ verified services, talk to children, learn Python and Pandas
- [ ] **Phase 1: Intent classifier** (weeks 5–8): FOOD / HEALTH / EDUCATION / EMERGENCY / OTHER, plus a Telegram test bot
- [ ] **Phase 2: Smart search** (weeks 9–11): landmarks, "open now", dates for camps, age filter
- [ ] **Phase 3: LLM answers** (weeks 12–15): tool calling over verified data, health safety rules
- [ ] **Phase 4: Voice** (weeks 16–19): speech-to-text and text-to-speech in the local language
- [ ] **Phase 5: Access channels** (weeks 20–23): missed-call line, SMS, kiosk, picture posters, camp alerts
- [ ] **Phase 6: Pilot and impact** (weeks 24–30): real use with partner NGOs, impact report

## How to run
```bash
pip install -r requirements.txt
python notebooks/01_explore_services.py
```

## Safety
Read [docs/child_safeguarding_policy.md](docs/child_safeguarding_policy.md). No personal data about children is ever stored in this repository.
