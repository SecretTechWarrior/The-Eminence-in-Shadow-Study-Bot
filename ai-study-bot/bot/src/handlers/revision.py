import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_video_info
from ai_client import ask_ai
from pdf_generator import create_pdf
from database import save_session, upsert_user
from prompts import revision_prompt, formulas_prompt, SYSTEM_STUDY

logger = logging.getLogger(__name__)


async def revise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "Usage: `/revise <youtube_link>`\n\n"
            "Creates a one-day revision sheet you can read in 15 minutes!",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    status_msg = await update.message.reply_text(
        "🔍 Fetching transcript...\n"
        "Creating your revision sheet!"
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Got transcript!\n📹 *{title}*\n\n"
            "⏳ Generating revision sheet...",
            parse_mode="Markdown"
        )

        prompt = revision_prompt(transcript, title)
        content = await ask_ai(prompt, SYSTEM_STUDY)

        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        pdf_path = create_pdf(
            filename="revision",
            title="One-Day Revision Sheet",
            subtitle="Read in 15 minutes. Master in 1 day.",
            content=content,
            video_title=title
        )

        save_session(user.id, url, video_info["video_id"], transcript, title)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Revision_{title[:30]}.pdf",
                caption=(
                    f"📅 *One-Day Revision Sheet*\n"
                    f"📹 {title}\n\n"
                    "📌 Contains:\n"
                    "• Top 20 concepts\n"
                    "• Key formulas\n"
                    "• Common mistakes\n"
                    "• FAQs\n"
                    "• Revision checklist\n\n"
                    "Read it the night before your exam! 💪"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(pdf_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Revision error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")


async def formulas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "Usage: `/formulas <youtube_link>`\n\n"
            "Extracts all formulas, equations, and variables from the lecture!",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    status_msg = await update.message.reply_text("🔍 Fetching transcript for formula extraction...")

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Got transcript!\n📹 *{title}*\n\n"
            "⏳ Extracting formulas...",
            parse_mode="Markdown"
        )

        prompt = formulas_prompt(transcript, title)
        content = await ask_ai(prompt, SYSTEM_STUDY)

        # Check if no formulas found
        if "No mathematical formulas found" in content:
            await status_msg.edit_text(
                f"ℹ️ *No formulas found in this lecture*\n\n"
                f"📹 {title}\n\n"
                "This appears to be a conceptual/theoretical topic without mathematical formulas.\n\n"
                f"Try `/notes {url}` for detailed notes instead.",
                parse_mode="Markdown"
            )
            return

        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        pdf_path = create_pdf(
            filename="formulas",
            title="Formula Sheet",
            subtitle="All formulas with explanations and conditions",
            content=content,
            video_title=title
        )

        save_session(user.id, url, video_info["video_id"], transcript, title)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Formulas_{title[:30]}.pdf",
                caption=(
                    f"🔢 *Formula Sheet*\n"
                    f"📹 {title}\n\n"
                    "Contains all formulas with:\n"
                    "• Variables & units\n"
                    "• Conditions of use\n"
                    "• Common mistakes\n"
                    "• Importance rating ⭐\n\n"
                    "Perfect for quick formula revision! 📐"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(pdf_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Formulas error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")
