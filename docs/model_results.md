# Model results

Every time the intent model is retrained, add a row here. This shows progress over time, which is good evidence for a scholarship application.

| Version | Date | Sentences | Accuracy | EMERGENCY caught (recall) | Notes |
|---|---|---|---|---|---|
| v0 baseline | 2026-10-29 | 164 (English, Bangla, Banglish) | 52% | 54% (19 of 35) | TF-IDF char n-grams + logistic regression, 5-fold cross-validation. Too little data: ~12 sentences per intent per language. |
| v0.1 | 2026-10-29 | 171 (+7 real student sentences) | 58% | 54% (19 of 35) | First real Alor School sentences (food, health). Now handles spelling variants like *bhuk lagse* and *shorir bhalo nai*. |

## What we learned from v0
- **The model is weak because the data is tiny.** Each intent has only about 12 examples per language (English, Bangla script, Banglish).
- **HEALTH and EMERGENCY get mixed up** (14 health sentences were predicted as emergency). This makes sense: "pain", "blood" and "fever" sit close together. A mix-up toward EMERGENCY is the safer kind of mistake.
- **The safety rule (EMERGENCY at 30% or more) made no difference yet**, because with this little data the model is unsure about everything.
- **Missed emergencies** include *bachao*, *rokto porche*, *রক্ত পড়তেছে* and *আমাকে মারছে*. These must never be missed.

## Next steps
1. Collect **real sentences** from Alor School students. Target: 150 per intent.
2. Add more ways of saying each emergency (different spellings, short words like *bachao*).
3. Consider a **keyword safety net** (a list of danger words that always trigger EMERGENCY) alongside the model.
4. Retrain and add the v1 row above.
