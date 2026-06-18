import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_video_info
from ai_client import ask_ai
from pdf_generator import create_pdf
from database import save_video, save_session, upsert_user
from prompts import notes_prompt, short_notes_prompt, SYSTEM_STUDY

logger = logging.getLogger(__name__)


async def _send_typing(update: Update):
    await update.message.chat.send_action(ChatAction.TYPING)


async def _send_upload_doc(update: Update):
    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)


async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "Usage: `/notes <youtube_link>`\n"
            "Example: `/notes https://youtube.com/watch?v=...`",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    short_mode = len(args) > 1 and args[1].lower() in ("short", "brief", "quick")

    status_msg = await update.message.reply_text(
        "🔍 Processing your video...\n\n"
        "⏳ Step 1/4: Fetching transcript..."
    )

    try:
        await _send_typing(update)
        video_info = await get_video_info(url)

        await status_msg.edit_text(
            f"✅ Transcript fetched!\n"
            f"📹 *{video_info['title']}*\n\n"
            "⏳ Step 2/4: Generating notes with AI...",
            parse_mode="Markdown"
        )

        transcript = video_info["transcript_text"]
        title = video_info["title"]

        # Generate notes
        if short_mode:
            prompt = short_notes_prompt(transcript, title)
            doc_title = "Short Revision Notes"
        else:
            prompt = notes_prompt(transcript, title)
            doc_title = "Complete Study Notes"

        notes_content = await ask_ai(prompt, SYSTEM_STUDY)

        await status_msg.edit_text(
            f"✅ Notes generated!\n\n"
            "⏳ Step 3/4: Creating PDF..."
        )

        await _send_upload_doc(update)
        pdf_path = create_pdf(
            filename="notes",
            title=doc_title,
            subtitle="Detailed Notes from YouTube Lecture",
            content=notes_content,
            video_title=title
        )

        await status_msg.edit_text(
            f"✅ PDF created!\n\n"
            "⏳ Step 4/4: Sending file..."
        )

        # Save to DB
        save_video(user.id, url, video_info["video_id"], title, transcript)
        save_session(user.id, url, video_info["video_id"], transcript, title)

        # Send PDF
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"{'Short_Notes' if short_mode else 'Study_Notes'}_{title[:30]}.pdf",
                caption=(
                    f"📄 *{'Short Notes' if short_mode else 'Study Notes'}*\n"
                    f"📹 {title}\n\n"
                    f"✅ Notes generated successfully!\n\n"
                    f"💡 *Next steps:*\n"
                    f"• `/quiz {url}` — Generate quiz\n"
                    f"• `/revise {url}` — Revision sheet\n"
                    f"• `/ask <question>` — Ask doubts\n"
                    f"• `/audio {url}` — Audio revision"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(pdf_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}\n\nPlease check the URL and try again.")
    except Exception as e:
        logger.error(f"Notes error: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Something went wrong. Please try again.\n\n"
            "If the problem persists, the video may not have captions."
        )


async def shortnotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Short notes — inject 'short' into args"""
    if context.args:
        context.args = [context.args[0], "short"] + context.args[1:]
    await notes_command(update, context)
