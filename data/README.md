# Data guide

## services.csv: one row per service

The first 3 rows are **EXAMPLES**. Replace them with real services you have checked yourself.

| Column | What to write | Example |
|---|---|---|
| id | A number, counting up | 4 |
| category | `food`, `health` or `education` | food |
| type | Kind of service (see list below) | meal_point |
| name | Name of the place or program | Gurudwara langar |
| landmark | How a child would describe the place | near the bus park, blue gate |
| latitude, longitude | From Google Maps (right-click the place) | 27.7172, 85.3240 |
| days | Days open, separated by `;` | Mon;Wed;Fri |
| time | Opening hours | 12:00-14:00 |
| start_date, end_date | **Only for camps or events** (YYYY-MM-DD). Leave empty for permanent places | 2026-11-15 |
| age_range | Who can come | 6-14 or all |
| cost | Price, if any | free, or OPD ticket 10 taka |
| free_items | What is given for free, separated by `;` | lunch;books |
| language | Language spoken there | Nepali |
| organizer | Who runs it | XYZ Foundation |
| contact | **Organization's** phone number (never a child's) | 98XXXXXXXX |
| verified_by | Your name, once you have visited or called | (your name) |
| verified_date | Date you checked it | 2026-10-25 |
| notes | Anything useful | Children must come before 1pm |

### Types
- **food:** `meal_point`, `community_kitchen`, `food_drive`, `school_meal`, `food_bank`, `mobile_meal`
- **health:** `health_camp`, `clinic`, `hospital`, `medicine_distribution`, `vaccination`, `first_aid`, `counselling`
- **education:** `edu_camp`, `street_class`, `night_school`, `school_admission`, `skill_training`, `library`, `free_materials`

## Rules
- Never add a service you have not **verified** yourself or through a trusted NGO.
- Never store children's names, photos or phone numbers in this folder.
- Re-check services every month, and every week for camps.
