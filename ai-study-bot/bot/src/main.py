import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

from config import TELEGRAM_BOT_TOKEN
from database import init_db

# Import handlers
from handlers.start import (
    start_command, help_command, stats_command,
    history_command, button_callback
)
from handlers.notes import notes_command, shortnotes_command
from handlers.quiz import quiz_command
from handlers.summary import summary_command, chapters_command
from handlers.revision import revise_command, formulas_command
from handlers.audio import audio_command
from handlers.explain import explain_command, ask_command
from handlers.playlist import playlist_command

# Logging
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred. Please try again.\n"
                "If this keeps happening, try /start to reset."
            )
        except Exception:
            pass


async def unknown_command(update: Update, context) -> None:
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see all available commands.",
        parse_mode="Markdown"
    )


async def handle_url_message(update: Update, context) -> None:
    """Handle messages that look like YouTube URLs sent without a command"""
    text = update.message.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        await update.message.reply_text(
            "🎬 I see you sent a YouTube link!\n\n"
            "What do you want to do with it?\n\n"
            f"• `/notes {text}` — Detailed notes PDF\n"
            f"• `/quiz {text}` — Generate quiz\n"
            f"• `/summary {text}` — Quick summary\n"
            f"• `/revise {text}` — Revision sheet\n"
            f"• `/audio {text}` — Audio revision\n"
            f"• `/formulas {text}` — Formula sheet\n"
            f"• `/chapters {text}` — Chapter breakdown",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "💬 I only understand commands. Use /help to see what I can do!\n\n"
            "Quick start: `/notes <youtube_link>`",
            parse_mode="Markdown"
        )


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    logger.info("Initializing database...")
    init_db()

    logger.info("Starting AI Study Assistant Bot...")

    # Build with longer timeouts for stability on Render/Railway
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=30,
        pool_timeout=30,
    )

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .concurrent_updates(True)
        .build()
    )

    # Core commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("history", history_command))

    # Video commands
    app.add_handler(CommandHandler("notes", notes_command))
    app.add_handler(CommandHandler("shortnotes", shortnotes_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("chapters", chapters_command))
    app.add_handler(CommandHandler("revise", revise_command))
    app.add_handler(CommandHandler("formulas", formulas_command))
    app.add_handler(CommandHandler("audio", audio_command))

    # AI interaction commands
    app.add_handler(CommandHandler("explain", explain_command))
    app.add_handler(CommandHandler("ask", ask_command))

    # Playlist
    app.add_handler(CommandHandler("playlist", playlist_command))

    # Button callbacks
    app.add_handler(CallbackQueryHandler(button_callback))

    # Handle plain messages (YouTube URLs, unknown text)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))

    # Unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30,
    )


if __name__ == "__main__":
    main()
