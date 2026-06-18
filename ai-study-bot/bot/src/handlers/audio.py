import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_video_info
from ai_client import ask_ai
from audio_generator import generate_audio_revision, VOICES
from database import save_session, upsert_user
from prompts import audio_revision_prompt, SYSTEM_STUDY

logger = logging.getLogger(__name__)


async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "*Usage:*\n"
            "`/audio <url>` — 5-minute audio revision\n"
            "`/audio <url> 15min` — 15-minute audio revision\n\n"
            "Output: MP3 file ready to download and listen!",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    length = "5min"
    for arg in args[1:]:
        if arg.lower() in ("15min", "15", "long"):
            length = "15min"
        elif arg.lower() in ("5min", "5", "short"):
            length = "5min"

    status_msg = await update.message.reply_text(
        f"🔍 Fetching transcript...\n"
        f"Audio length: *{length}*",
        parse_mode="Markdown"
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Got transcript!\n📹 *{title}*\n\n"
            "⏳ Writing audio script with AI...",
            parse_mode="Markdown"
        )

        prompt = audio_revision_prompt(transcript, title, length)
        script = await ask_ai(prompt, SYSTEM_STUDY)

        await status_msg.edit_text(
            "✅ Script ready!\n\n"
            "⏳ Converting to speech... (this may take a moment)"
        )

        await update.message.chat.send_action(ChatAction.RECORD_VOICE)
        audio_path = await generate_audio_revision(script, length=length, voice_key="female_us")

        await status_msg.edit_text("✅ Audio generated!\n\n⏳ Sending audio file...")

        save_session(user.id, url, video_info["video_id"], transcript, title)

        await update.message.chat.send_action(ChatAction.UPLOAD_VOICE)

        file_size = os.path.getsize(audio_path)
        if file_size > 50 * 1024 * 1024:  # 50MB Telegram limit
            await update.message.reply_text(
                "⚠️ Audio file is too large for Telegram (>50MB).\n"
                "Try `/audio <url> 5min` for a shorter audio."
            )
        else:
            with open(audio_path, "rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    filename=f"Revision_{length}_{title[:30]}.mp3",
                    title=f"Revision: {title[:50]}",
                    performer="AI Study Assistant",
                    caption=(
                        f"🎧 *{length} Audio Revision*\n"
                        f"📹 {title}\n\n"
                        "Listen while commuting, walking, or before sleep!\n\n"
                        "💡 Tip: Use `/audio <url> 15min` for a longer session"
                    ),
                    parse_mode="Markdown"
                )

        await status_msg.delete()
        os.remove(audio_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Audio error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong generating audio. Please try again.")
