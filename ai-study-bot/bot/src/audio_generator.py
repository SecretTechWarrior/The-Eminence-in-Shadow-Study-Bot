import asyncio
import os
import uuid
import logging
import edge_tts
from config import AUDIO_DIR

logger = logging.getLogger(__name__)

# Available voices
VOICES = {
    "male_us": "en-US-GuyNeural",
    "female_us": "en-US-JennyNeural",
    "male_uk": "en-GB-RyanNeural",
    "female_uk": "en-GB-SoniaNeural",
    "female_in": "en-IN-NeerjaNeural",
    "male_in": "en-IN-PrabhatNeural",
}

DEFAULT_VOICE = VOICES["female_us"]


async def text_to_speech(text: str, voice: str = None, rate: str = "+0%", filename_prefix: str = "audio") -> str:
    """Convert text to speech using Edge TTS, return filepath"""
    if not voice:
        voice = DEFAULT_VOICE

    filepath = os.path.join(AUDIO_DIR, f"{filename_prefix}_{uuid.uuid4().hex[:8]}.mp3")

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(filepath)

    return filepath


async def generate_audio_revision(revision_text: str, length: str = "5min", voice_key: str = "female_us") -> str:
    """Generate audio revision notes"""
    voice = VOICES.get(voice_key, DEFAULT_VOICE)

    # Adjust speech rate based on length preference
    rate = "+10%" if length == "5min" else "+0%"

    filepath = await text_to_speech(revision_text, voice=voice, rate=rate, filename_prefix="revision")
    return filepath


async def list_voices() -> dict:
    return VOICES
