# Hospital guide (government hospitals, Dhaka)

This is the knowledge the chatbot uses to explain **how** to get help at a government hospital. In Phase 3 it is loaded into the bot (RAG). The bot must explain it in short, simple Bangla.

Applies to: Dhaka Shishu Hospital, Shaheed Suhrawardy Medical College Hospital, Dhaka Medical College Hospital, Bangladesh Medical University Hospital. See `data/services.csv`.

## Opening times
| Service | Days | Time |
|---|---|---|
| Outdoor (OPD), for normal illness | Saturday to Thursday (**closed Friday**) | 8:00 am to 2:30 pm |
| OPD ticket counter | Saturday to Thursday | 8:00 am to **2:00 pm** (come before 2!) |
| Emergency | **Every day, 24 hours** | Always open |

## Cost
- OPD ticket: **10 taka** (same for children and adults)
- Basic medicines are **free**, but stock is limited. Sometimes medicine must be bought from a pharmacy.

## 1. Normal illness (daytime)
For mild fever, cough, skin rash, stomach pain, or a check-up:
1. Go to the **ticket counter (OPD registration)** before 2:00 pm and buy a 10 taka ticket.
2. Say the ticket is **for a child**, so they send you to the right room.
3. Go to the **Child Health / Pediatrics outdoor** room and wait for your turn.
4. Ask the doctor or the hospital pharmacy for the **free medicine**.

## 🚨 2. Emergency (any time, day or night)
If someone is badly hurt, bleeding a lot, can't breathe, has fainted or won't wake up:
1. **Don't wait in the normal line.** Go straight to the **Emergency gate**. It's open 24 hours.
2. Tell the counter: **"This is a child emergency."**
3. Doctors check the child right away and may send them to the children's emergency ward.
4. Call **999** for an ambulance or police, and **1098** (Child Helpline) for help. Both are free.

## 💉 3. Vaccines
For a baby's or child's routine vaccines, look for the **EPI room / vaccine corner**. It is kept separate from sick children.

## ⚠️ Going without an adult
A child should go with a **trusted adult**. Many street children have no one, so the bot should say:
- "If you can, go with your **Alor School teacher** or another trusted volunteer."
- "If you have no one, call **1098**. They can help you."
- In an emergency: **never wait for an adult.** Go to the Emergency gate, or call 999.

## Rules for the chatbot
- Never diagnose an illness or name a medicine to take.
- If it sounds serious, treat it as an emergency.
- On Friday, or after 2:00 pm, tell the child the OPD is closed and send them to Emergency if they need help now.
