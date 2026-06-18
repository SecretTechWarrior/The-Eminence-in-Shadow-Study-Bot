import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_video_info
from ai_client import ask_ai
from pdf_generator import create_pdf
from database import save_session, upsert_user
from prompts import summary_prompt, chapters_prompt, SYSTEM_STUDY

logger = logging.getLogger(__name__)

VALID_MODES = {"quick", "5min", "ultra", "detailed"}


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "*Usage:*\n"
            "`/summary <url>` — Detailed summary\n"
            "`/summary <url> quick` — 10 bullet points\n"
            "`/summary <url> 5min` — 1-page revision summary\n"
            "`/summary <url> ultra` — 100-word summary",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    mode = "detailed"
    for arg in args[1:]:
        if arg.lower() in VALID_MODES:
            mode = arg.lower()

    mode_labels = {
        "quick": "Quick Summary (10 Points)",
        "5min": "5-Minute Revision",
        "ultra": "Ultra Short (100 Words)",
        "detailed": "Detailed Summary",
    }

    status_msg = await update.message.reply_text(
        f"🔍 Fetching transcript...\n"
        f"Mode: *{mode_labels[mode]}*",
        parse_mode="Markdown"
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Transcript ready!\n📹 *{title}*\n\n"
            f"⏳ Generating {mode_labels[mode]}...",
            parse_mode="Markdown"
        )

        prompt = summary_prompt(transcript, title, mode)
        content = await ask_ai(prompt, SYSTEM_STUDY)

        if mode == "ultra":
            # For ultra short, just send as text message
            await update.message.reply_text(
                f"📄 *Ultra Short Summary*\n📹 _{title}_\n\n{content}\n\n"
                f"💡 Use `/summary {url} detailed` for full summary",
                parse_mode="Markdown"
            )
            await status_msg.delete()
            save_session(user.id, url, video_info["video_id"], transcript, title)
            return

        # Create PDF for other modes
        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        pdf_path = create_pdf(
            filename="summary",
            title=mode_labels[mode],
            subtitle=f"Mode: {mode.upper()}",
            content=content,
            video_title=title
        )

        save_session(user.id, url, video_info["video_id"], transcript, title)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Summary_{mode}_{title[:30]}.pdf",
                caption=(
                    f"📋 *{mode_labels[mode]}*\n"
                    f"📹 {title}\n\n"
                    f"💡 Other options:\n"
                    f"• `/quiz {url}` — Create quiz\n"
                    f"• `/revise {url}` — Revision sheet\n"
                    f"• `/ask <question>` — Ask doubts"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(pdf_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Summary error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")


async def chapters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "Usage: `/chapters <youtube_link>`",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    status_msg = await update.message.reply_text("🔍 Fetching transcript for chapter analysis...")

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript_list = video_info["transcript_list"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Transcript ready!\n📹 *{title}*\n\n"
            "⏳ Analyzing chapters...",
            parse_mode="Markdown"
        )

        prompt = chapters_prompt(transcript_list, title)
        content = await ask_ai(prompt, SYSTEM_STUDY)

        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        pdf_path = create_pdf(
            filename="chapters",
            title="Chapter-wise Breakdown",
            subtitle="AI-detected chapters with timestamps",
            content=content,
            video_title=title
        )

        save_session(user.id, url, video_info["video_id"], transcript, title)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Chapters_{title[:30]}.pdf",
                caption=(
                    f"📑 *Chapter Breakdown*\n"
                    f"📹 {title}\n\n"
                    "Navigate to specific chapters and study section by section!\n\n"
                    f"💡 Now try: `/notes {url}` for full notes"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(pdf_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Chapters error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")
