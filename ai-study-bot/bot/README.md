# AI Study Assistant Telegram Bot

A full-featured Telegram bot that turns YouTube lectures into comprehensive study materials using AI.

## Features

| Command | Description |
|---------|-------------|
| `/notes <url>` | Detailed study notes PDF |
| `/shortnotes <url>` | Short revision notes PDF |
| `/quiz <url> [type] [difficulty]` | Quiz + Answer Key PDFs |
| `/summary <url> [mode]` | Summary (quick/5min/ultra/detailed) |
| `/chapters <url>` | Chapter-wise breakdown with timestamps |
| `/revise <url>` | One-day revision sheet PDF |
| `/formulas <url>` | Formula extractor PDF |
| `/audio <url> [5min/15min]` | Audio revision MP3 |
| `/explain <topic>` | Explain Like I'm 10 |
| `/ask <question>` | Ask doubts from last processed lecture |
| `/playlist <url>` | Full playlist analyzer |
| `/stats` | Your usage statistics |
| `/history` | Recently processed videos |

## Setup

### Environment Variables
```
TELEGRAM_BOT_TOKEN=your_token
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key
YOUTUBE_API_KEY=your_yt_key (optional, for playlist feature)
```

### Running Locally
```bash
cd bot/src
python main.py
```

### Deploying to Render/Railway
- Set all environment variables in the dashboard
- Set start command: `python bot/src/main.py`
- The bot uses polling mode (no webhook needed)

## AI Stack
- **Primary**: Google Gemini 2.0 Flash
- **Fallback 1**: OpenRouter (Gemma 3 27B free)
- **Fallback 2**: Groq (Llama3 70B)

## Architecture
- `bot/src/main.py` — Entry point, registers all handlers
- `bot/src/handlers/` — Command handlers (notes, quiz, summary, etc.)
- `bot/src/ai_client.py` — AI provider with automatic fallback
- `bot/src/youtube_utils.py` — YouTube transcript extraction
- `bot/src/pdf_generator.py` — PDF creation with ReportLab
- `bot/src/audio_generator.py` — TTS with Edge TTS
- `bot/src/database.py` — SQLite user data & sessions
- `bot/src/prompts.py` — All AI prompts
