# AI Study Assistant Telegram Bot

A full-featured Telegram bot that transforms any YouTube lecture into comprehensive study materials using AI.

## Run & Operate

- **Start bot:** Workflow `Telegram Study Bot` runs `cd bot/src && python main.py`
- **Bot entry point:** `bot/src/main.py`
- **Database:** SQLite at `bot/data/studybot.db` (auto-created)
- **Generated files:** PDFs → `bot/pdfs/`, Audio → `bot/audio/`, Temp → `bot/temp/`

## Stack

- Python 3.11 + python-telegram-bot 22.x
- AI: Google Gemini 2.0 Flash (primary) → OpenRouter Gemma 3 (fallback) → Groq Llama3-70B (fallback)
- YouTube: youtube-transcript-api (transcript extraction)
- PDF: ReportLab (styled A4 PDFs)
- TTS: Edge TTS (high-quality voices)
- DB: SQLite (user data, sessions, history)

## Where things live

```
bot/
├── src/
│   ├── main.py              # Entry point, registers all handlers
│   ├── config.py            # All env vars and settings
│   ├── ai_client.py         # Multi-provider AI with fallback
│   ├── youtube_utils.py     # Transcript extraction, playlist parsing
│   ├── pdf_generator.py     # Styled PDF creation (ReportLab)
│   ├── audio_generator.py   # TTS audio (Edge TTS)
│   ├── database.py          # SQLite: users, sessions, history
│   ├── prompts.py           # All AI prompts
│   └── handlers/
│       ├── start.py         # /start, /help, /stats, /history
│       ├── notes.py         # /notes, /shortnotes
│       ├── quiz.py          # /quiz
│       ├── summary.py       # /summary, /chapters
│       ├── revision.py      # /revise, /formulas
│       ├── audio.py         # /audio
│       ├── explain.py       # /explain, /ask
│       └── playlist.py      # /playlist
├── data/                    # SQLite DB (auto-created)
├── pdfs/                    # Generated PDFs (temp)
├── audio/                   # Generated MP3s (temp)
└── requirements.txt
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/notes <url>` | Detailed study notes PDF |
| `/shortnotes <url>` | Short revision notes PDF |
| `/quiz <url> [mcq/subjective/mixed] [easy/medium/hard/exam]` | Quiz + Answer Key PDFs |
| `/summary <url> [quick/5min/ultra/detailed]` | Summary modes |
| `/chapters <url>` | Chapter-wise breakdown with timestamps |
| `/revise <url>` | One-day revision sheet PDF |
| `/formulas <url>` | Formula extractor PDF |
| `/audio <url> [5min/15min]` | Audio revision MP3 |
| `/explain <topic>` | Explain Like I'm 10 |
| `/ask <question>` | Ask doubts from last processed lecture |
| `/playlist <url>` | Full playlist analyzer |
| `/stats` | Usage statistics |
| `/history` | Recently processed videos |

## Architecture decisions

- **AI fallback chain**: Gemini → OpenRouter → Groq. If Gemini quota is hit, auto-falls back silently.
- **Session storage**: Each user's last processed video is stored in SQLite. `/ask` uses this context.
- **PDF cleanup**: PDFs are deleted from disk after sending to Telegram to avoid storage bloat.
- **Polling mode**: Bot uses long-polling (not webhooks) — works perfectly on Render/Railway free tier.
- **Concurrent updates**: `concurrent_updates=True` so multiple users can process videos simultaneously.

## Product

Students send a YouTube lecture URL and get:
- Detailed or short study notes (PDF)
- Quiz with answer key (PDF)
- Multiple summary modes
- Chapter breakdown with timestamps
- One-day revision sheet
- Formula extractor
- Audio revision (MP3)
- "Explain Like I'm 10" on any topic
- Doubt-answering from lecture content
- Full playlist analysis

## Required Secrets (already configured)

- `TELEGRAM_BOT_TOKEN` — Telegram Bot API token
- `GEMINI_API_KEY` — Google Gemini API key
- `OPENROUTER_API_KEY` — OpenRouter API key
- `GROQ_API_KEY` — GroqCloud API key
- `YOUTUBE_API_KEY` — (Optional) YouTube Data API v3, needed for /playlist

## User preferences

- Host on Render or Railway (polling mode, no webhook needed)
- All AI providers configured with automatic fallback
- Free-tier friendly stack throughout

## Gotchas

- Bot can't connect to Telegram from Replit's dev environment (network restrictions). It must be deployed to Render/Railway.
- Run `pip install -r bot/requirements.txt` if deploying manually.
- Start command for deployment: `python bot/src/main.py`
- YouTube videos without captions will fail transcript extraction.
- `/playlist` requires `YOUTUBE_API_KEY` env var.

## Deployment (Render / Railway)

1. Push this repo to GitHub
2. Create a new Web Service (or Worker) on Render/Railway
3. Set start command: `python bot/src/main.py`
4. Add all secrets as environment variables
5. Deploy — the bot will start polling automatically

## Pointers

- See `bot/README.md` for detailed deployment guide
- See `bot/src/prompts.py` to customize AI behavior
- See `bot/src/config.py` for all configurable settings
