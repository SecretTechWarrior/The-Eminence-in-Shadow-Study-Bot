import sys
import os
import logging
import re

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
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def is_youtube_link(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"(youtube\.com|youtu\.be)", text))


async def error_handler(update: object, context) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)

    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Try again or use /start."
            )
    except Exception:
        pass


async def unknown_command(update: Update, context) -> None:
    if update.message:
        await update.message.reply_text(
            "❓ Unknown command. Use /help to see available commands."
        )


async def handle_url_message(update: Update, context) -> None:
    text = update.message.text if update.message else ""

    if not text:
        return

    text = text.strip()

    if is_youtube_link(text):
        await update.message.reply_text(
            "🎬 YouTube link detected!\n\n"
            "Choose what you want:\n\n"
            f"• /notes {text}\n"
            f"• /quiz {text}\n"
            f"• /summary {text}\n"
            f"• /revise {text}\n"
            f"• /audio {text}\n"
            f"• /formulas {text}\n"
            f"• /chapters {text}"
        )
    else:
        await update.message.reply_text(
            "💬 Send a YouTube link or use /help to see commands."
        )


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    logger.info("Initializing database...")
    init_db()

    logger.info("Starting bot...")

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

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("history", history_command))

    app.add_handler(CommandHandler("notes", notes_command))
    app.add_handler(CommandHandler("shortnotes", shortnotes_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("chapters", chapters_command))
    app.add_handler(CommandHandler("revise", revise_command))
    app.add_handler(CommandHandler("formulas", formulas_command))
    app.add_handler(CommandHandler("audio", audio_command))

    app.add_handler(CommandHandler("explain", explain_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("playlist", playlist_command))

    # Callback buttons
    app.add_handler(CallbackQueryHandler(button_callback))

    # Messages
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message)
    )

    app.add_handler(
        MessageHandler(filters.COMMAND, unknown_command)
    )

    # Error handler
    app.add_error_handler(error_handler)

    logger.info("✅ Bot running!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30,
    )


if __name__ == "__main__":
    main()
