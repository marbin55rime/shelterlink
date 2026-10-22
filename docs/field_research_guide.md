# Field research guide (Phase 0)

## Part A: Talking with children

**Before you start**
- Talk only with children who already know and trust you (for example, your own students).
- Tell them what it's for: "I'm making a phone helper so kids can find free food, doctors and classes."
- Children can say no or stop at any time. Never pressure them.
- **Don't write down names, photos or exact sleeping places.** Use codes like C01, C02.
- If a child tells you they are in danger, stop the interview and follow the emergency steps in `child_safeguarding_policy.md`.

**Questions** (ask casually, like a conversation)

*Food*
1. When you're hungry, where do you go?
2. Is there a time of day when it's hardest to find food?
3. Do you know a place that gives free food? How did you find out?

*Health*
4. When you or a friend gets sick or hurt, what do you do?
5. Have you ever been to a free clinic or health camp? Was it easy to go?
6. What stops you from going to a doctor? (fear, distance, papers, money, no one to go with)

*Education*
7. What would you like to learn? (reading, math, English, computer, a job skill)
8. Have you ever been to school? Would you like to go?
9. Have you heard about free classes or camps? How?

*Phones and access*
10. Can you use any phone? Yours, a friend's, a shop's?
11. Can you make a call? Send an SMS? Use WhatsApp?
12. Would you rather **talk** to a helper or **press pictures**?
13. What language do you speak with friends?

**Record answers** in `data/research_notes.csv` with these columns:
`code, age_group, question_no, answer, date`

## Part B: Verifying a service

Before adding any place to `services.csv`, check:

- [ ] Visited in person, or called the organizer directly
- [ ] It is really **free** for children
- [ ] It accepts street children (no ID card or parent needed?)
- [ ] Days and time are correct
- [ ] An easy landmark a child would know
- [ ] An organizer contact person and phone number
- [ ] Safe: a registered NGO, a religious place, a government service, or someone you personally trust

Then fill in `verified_by` and `verified_date`.

## Week 1–2 targets
- [ ] 10 food services
- [ ] 10 health services
- [ ] 10 education services (your own class is #1)
- [ ] 5–10 children interviewed
- [ ] Translate `data/intent_examples.csv` sentences into your local language
