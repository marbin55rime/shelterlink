# ShelterLink

**An AI voice helpline that connects street children to free food, health care and education, in their own language, from any phone or a kiosk.**

Built by a volunteer teacher at **Alor School**, a free street school for children aged 5–14 in Dhanmondi, Dhaka, Bangladesh. First language: **Bangla**.

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
│   └── landmarks.csv          # 88 Dhaka areas with map locations and the spellings children use
├── notebooks/
│   ├── 01_explore_services.py        # look at the data
│   ├── 02_train_intent_classifier.py # Phase 1: train the "what do you need?" model
│   ├── 03_smart_search.py            # Phase 2: need + place + time -> nearest open service
│   └── 04_bangla_replies.py          # Phase 3: short, kind replies in Bangla
├── shelterlink/
│   ├── search.py              # reusable search code (landmarks, distance, open now)
│   └── bangla.py              # Bangla replies: Claude (LLM) or offline templates
├── tools/
│   └── build_landmarks.py     # gets map locations for Dhaka areas from OpenStreetMap
├── LEARNING_LOG.md            # what I learn every week
└── requirements.txt
```

## Roadmap
- [ ] **Phase 0: Field work and foundations** (weeks 1–4): map 30+ verified services, talk to children, learn Python and Pandas
- [ ] **Phase 1: Intent classifier** (weeks 5–8): FOOD / HEALTH / EDUCATION / EMERGENCY / OTHER, plus a Telegram test bot. *In progress: v0.1 model at 58%, collecting real student sentences*
- [ ] **Phase 2: Smart search** (weeks 9–11): landmarks, "open now", dates for camps, age filter. *In progress: landmark matching, distance, open-now and safety filters working*
- [ ] **Phase 3: LLM answers** (weeks 12–15): tool calling over verified data, health safety rules. *In progress: Bangla replies from checked facts only (Claude, or offline templates); emergency numbers always added by code*
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
