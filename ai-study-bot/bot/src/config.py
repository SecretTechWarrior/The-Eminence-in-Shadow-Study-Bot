import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Dirs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
PDFS_DIR = os.path.join(BASE_DIR, "pdfs")
DATA_DIR = os.path.join(BASE_DIR, "data")

for d in [TEMP_DIR, AUDIO_DIR, PDFS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# AI Settings
MAX_TOKENS = 8192
GEMINI_MODEL = "gemini-2.0-flash"
OPENROUTER_MODEL = "google/gemma-3-27b-it:free"
GROQ_MODEL = "llama3-70b-8192"

# Feature flags
USE_GEMINI_PRIMARY = True
FALLBACK_TO_OPENROUTER = True
