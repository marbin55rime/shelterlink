"""
ShelterLink - Step 5: Telegram test bot (Phase 1)

Try ShelterLink from a phone: type or SAY what you need in Telegram,
and get the Bangla reply as a voice message and as text.

What this script teaches you:
  - Connecting your code to a real chat app (python-telegram-bot)
  - Keeping a secret (the bot token) out of your code and out of git
  - Running slow work (Claude, Whisper) without freezing the bot (asyncio.to_thread)
  - Voice in and out for children who cannot read (shelterlink/voice.py)
  - Keeping only anonymous data, as the safeguarding policy says

Setup (once):
  1. In Telegram, open @BotFather, send /newbot and follow the steps.
  2. BotFather gives you a token. Never share it and never paste it in a chat.
  3. Save it in a file called telegram_token.txt in the ShelterLink folder
     (git ignores this file), or set the TELEGRAM_BOT_TOKEN environment variable.

Run it from the ShelterLink folder:
    python notebooks/05_telegram_bot.py
    python notebooks/05_telegram_bot.py --offline    (no Claude, templates only)
The bot answers while this script runs. Press Ctrl+C to stop it.

The first run downloads the speech model (about 500 MB), so it takes a few minutes.

Safety:
  - We never save message text, names, phone numbers, chat ids or GPS points.
  - Voice messages become text on this computer and are deleted right away.
  - A shared location is kept in memory only, so the next question can use it.
  - Each question is logged anonymously to outputs/telegram_log.csv:
    the date, the need (intent), the general area, and 👍 / 👎 feedback.
"""

import asyncio
import csv
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import NetworkError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from shelterlink.bangla import EMERGENCY_LINE, reply_in_bangla
from shelterlink.search import load_landmarks, load_model, load_services
from shelterlink.voice import hear, load_whisper, speak

PROJECT = Path(__file__).resolve().parent.parent
TOKEN_FILE = PROJECT / "telegram_token.txt"
LOG_FILE = PROJECT / "outputs" / "telegram_log.csv"
TEMP = Path(tempfile.gettempdir())  # voice files live here for a few seconds only

model, services, landmarks = load_model(), load_services(), load_landmarks()
use_claude = "--offline" not in sys.argv

WELCOME = (
    "হ্যালো! আমি ShelterLink। আমি ফ্রি খাবার, ডাক্তার, ক্লাস আর থাকার জায়গা খুঁজে দিতে পারি।\n\n"
    "🎤 মাইকের বোতাম চেপে ধরে মুখে বলো তোমার কী লাগবে আর তুমি কোথায় আছো। "
    "যেমন: \"ভুখ লাগছে, আমি ধানমন্ডি বত্রিশে\"। লিখেও বলতে পারো।\n"
    "📍 নিচের বোতাম চাপলে তোমার কাছের জায়গা খুঁজে দেবো।\n\n"
    f"{EMERGENCY_LINE}"
)
LOCATION_BUTTON = ReplyKeyboardMarkup(
    [[KeyboardButton("📍 আমার লোকেশন পাঠাও", request_location=True)]], resize_keyboard=True
)


# ---------------------------------------------------------------
# 1. Getting the token (a secret: never in the code, never in git)
# ---------------------------------------------------------------
def get_token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token and TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8-sig").strip()  # utf-8-sig: Notepad may add a BOM
    if not token:
        sys.exit("No bot token. Save it in telegram_token.txt (see the top of this file).")
    # A token looks like 1234567890:ABC... (numbers, a colon, then letters). We never print it.
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{30,}", token):
        sys.exit("The token doesn't look right. It must be numbers, then ':', then letters, "
                 "for example 1234567890:ABC... Copy it again from @BotFather.")
    return token


# ---------------------------------------------------------------
# 2. Anonymous log: date, need, general area, feedback. Nothing else.
# ---------------------------------------------------------------
def log_event(event, intent, place="", source="", helpful=""):
    LOG_FILE.parent.mkdir(exist_ok=True)
    new_file = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["date", "event", "intent", "place", "source", "helpful"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d"), event, intent, place, source, helpful])


def area_name(found):
    """The general area only: a landmark name, or just 'gps' (never the GPS point)."""
    place = found["place"]
    if place is None:
        return ""
    return "gps" if place["name"] == "your location" else place["name"]


def feedback_buttons(intent):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("👍 কাজে লেগেছে", callback_data=f"fb:{intent}:yes"),
        InlineKeyboardButton("👎 লাগেনি", callback_data=f"fb:{intent}:no"),
    ]])


def answer_child(text, location=None):
    """The same steps as notebook 04: need + place -> checked service -> Bangla reply."""
    found, reply, source = reply_in_bangla(text, None, model, services, landmarks, use_claude, location)
    log_event("question", found["intent"], area_name(found), source)
    return found, reply


VOICE_CACHE = {}  # reply text -> voice; the same reply (e.g. the welcome) is spoken only once


async def reply_voice_bytes(text, update_id):
    if text not in VOICE_CACHE:
        voice_file = TEMP / f"shelterlink_reply_{update_id}.mp3"
        try:
            await speak(text, voice_file)
            if len(VOICE_CACHE) >= 200:
                VOICE_CACHE.pop(next(iter(VOICE_CACHE)))  # forget the oldest
            VOICE_CACHE[text] = voice_file.read_bytes()
        finally:
            voice_file.unlink(missing_ok=True)
    return VOICE_CACHE[text]


async def show_working(update):
    """'typing…' at the top of the chat, so the child knows the bot is busy."""
    try:
        await update.effective_chat.send_action(ChatAction.TYPING)
    except Exception:
        pass  # only a nicety


async def send_reply(update, text, reply_markup=None, heard=None):
    """Every reply twice: as text (straight away) and as a voice message (for children who can't read)."""
    voice = asyncio.create_task(reply_voice_bytes(text, update.update_id))  # starts now, in the background
    shown = f"🎤 শুনলাম: \"{heard}\"\n\n{text}" if heard else text
    await update.message.reply_text(shown, reply_markup=reply_markup)
    try:
        await update.message.reply_voice(await voice)
    except Exception as error:  # no internet for the speech service: the text already went out
        print(f"Voice reply failed ({type(error).__name__}), sent text only")


# ---------------------------------------------------------------
# 3. What the bot does with each kind of message
# ---------------------------------------------------------------
async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update, WELCOME, reply_markup=LOCATION_BUTTON)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_working(update)
    location = context.chat_data.get("location")
    # Claude can take a few seconds; to_thread keeps the bot answering other children meanwhile
    found, reply = await asyncio.to_thread(answer_child, update.message.text, location)
    await send_reply(update, reply, feedback_buttons(found["intent"]))


async def on_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # In memory only, for this chat's next questions. Never saved to a file.
    context.chat_data["location"] = (update.message.location.latitude, update.message.location.longitude)
    await send_reply(update, "ধন্যবাদ! এখন মুখে বা লিখে বলো তোমার কী লাগবে: খাবার, ডাক্তার, ক্লাস, না থাকার জায়গা?")


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_working(update)
    recording = update.message.voice or update.message.audio
    audio_file = TEMP / f"shelterlink_voice_{update.update_id}.oga"
    try:
        await (await recording.get_file()).download_to_drive(audio_file)
        # Whisper takes a few seconds; hear() deletes the recording when it is done
        text = await asyncio.to_thread(hear, audio_file)
    finally:
        audio_file.unlink(missing_ok=True)

    if not text:
        await send_reply(update, f"দুঃখিত, বুঝতে পারিনি। আবার একটু জোরে বলো।\n\n{EMERGENCY_LINE}")
        return
    location = context.chat_data.get("location")
    found, reply = await asyncio.to_thread(answer_child, text, location)
    await send_reply(update, reply, feedback_buttons(found["intent"]), heard=text)


async def on_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, intent, helpful = query.data.split(":")
    log_event("feedback", intent, helpful=helpful)
    await query.answer("ধন্যবাদ!")
    await query.edit_message_reply_markup(reply_markup=None)  # one vote per reply


def build_app(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_feedback, pattern=r"^fb:"))
    return app


def main():
    token = get_token()
    print("Loading the speech model (the first time, this downloads about 500 MB)...")
    load_whisper()
    # If the internet drops, start again instead of stopping for good
    while True:
        print(f"ShelterLink bot is running ({'Claude' if use_claude else 'offline templates'}). Ctrl+C to stop.")
        try:
            build_app(token).run_polling(close_loop=False)
            break  # stopped with Ctrl+C
        except NetworkError as error:
            print(f"No internet ({error}). Trying again in 30 seconds...")
            time.sleep(30)


if __name__ == "__main__":
    main()
