"""
ShelterLink voice (Phase 4): many street children cannot read or write,
so they speak to the bot and the bot speaks back.

  hear()  -> a child's voice message becomes Bangla text (Whisper, runs on this computer)
  speak() -> the Bangla reply becomes a voice message (edge-tts, Bangladeshi voice)

Safety:
  - The child's voice never leaves this computer: Whisper runs locally,
    and the recording is deleted right after it becomes text.
  - Only the bot's reply (place names, times) goes to the speech service.
"""

import asyncio
import re
import unicodedata
from pathlib import Path

import edge_tts

VOICE = "bn-BD-NabanitaNeural"  # Bangladeshi Bangla, female. Male: bn-BD-PradeepNeural
WHISPER_SIZE = "small"  # bigger ("medium") understands Bangla better but is slower
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

_whisper = None


# ---------------------------------------------------------------
# 1. Hearing: voice message -> text
# ---------------------------------------------------------------
def load_whisper():
    """The first run downloads the model (about 500 MB), then it works offline."""
    global _whisper
    if _whisper is None:
        import numpy as np
        from faster_whisper import WhisperModel
        _whisper = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8")
        # Warm up on one second of silence, so the first child doesn't wait for the start-up work
        # (temperature 0 and a few tokens: on silence Whisper would otherwise keep "hearing" things)
        list(_whisper.transcribe(np.zeros(16000, dtype=np.float32), language="bn",
                                 temperature=0, max_new_tokens=3)[0])
    return _whisper


# Whisper sometimes writes Bangla sounds in Hindi letters (आमार instead of আমার).
# The two alphabets sit side by side in Unicode, 0x80 apart, so most letters
# convert by moving them along. A few Hindi letters have no Bangla twin.
DEVANAGARI_TO_BANGLA = {"व": "ব", "ऑ": "অ", "ॉ": "", "ऍ": "এ", "ॅ": "", "ळ": "ল", "ऱ": "র", "ऩ": "ন", "ऴ": "ল"}


def to_bangla_letters(text):
    out = []
    for ch in text:
        if "ऀ" <= ch <= "ॿ":
            twin = chr(ord(ch) + 0x80)
            ch = DEVANAGARI_TO_BANGLA.get(ch, twin if unicodedata.name(twin, "") else ch)
        out.append(ch)
    return "".join(out)


def hear(audio_path):
    """Bangla text from a recording. The recording is deleted afterwards, whatever happens."""
    try:
        # condition_on_previous_text=False stops Whisper from repeating itself on short clips
        segments, _ = load_whisper().transcribe(
            str(audio_path), language="bn", vad_filter=True, condition_on_previous_text=False)
        return to_bangla_letters(" ".join(segment.text.strip() for segment in segments).strip())
    finally:
        Path(audio_path).unlink(missing_ok=True)


# ---------------------------------------------------------------
# 2. Speaking: reply text -> voice message
#    Written replies have emoji, "12:00-14:00" and "কিমি". Said aloud,
#    a child should hear "দুপুর ১২টা থেকে ২টা" and "কিলোমিটার".
# ---------------------------------------------------------------
def time_bn(hour):
    if hour < 5 or hour >= 20:
        part = "রাত"
    elif hour < 12:
        part = "সকাল"
    elif hour < 15:
        part = "দুপুর"
    elif hour < 18:
        part = "বিকেল"
    else:
        part = "সন্ধ্যা"
    return f"{part} {str(hour % 12 or 12).translate(BN_DIGITS)}টা"


def hours_aloud(match):
    start, end = int(match.group(1)), int(match.group(3))
    if start == 0 and end == 24:
        return "২৪ ঘণ্টা"
    return f"{time_bn(start)} থেকে {time_bn(end % 24)}"


def spoken_text(text):
    text = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️]", "", text)  # emoji
    text = re.sub(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", hours_aloud, text)
    text = text.replace("কিমি", "কিলোমিটার")
    text = text.replace("(", ", ").replace(")", ",")
    return re.sub(r"\s+", " ", text).strip()


async def speak(text, out_path, tries=3):
    """Save the reply as an MP3 voice message. Needs internet; the service sometimes
    sends nothing back, so we try again a couple of times."""
    for attempt in range(tries):
        try:
            await edge_tts.Communicate(spoken_text(text), VOICE).save(str(out_path))
            return out_path
        except edge_tts.exceptions.NoAudioReceived:
            if attempt == tries - 1:
                raise
            await asyncio.sleep(1 + attempt)
