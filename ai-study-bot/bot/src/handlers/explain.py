import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from ai_client import ask_ai
from database import get_session, upsert_user
from prompts import explain_eli10_prompt, doubts_prompt, SYSTEM_ELI10, SYSTEM_STUDY

logger = logging.getLogger(__name__)


async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a topic to explain!\n\n"
            "Usage: `/explain <topic>`\n\n"
            "Examples:\n"
            "• `/explain Electric Potential`\n"
            "• `/explain Newton's Laws of Motion`\n"
            "• `/explain Photosynthesis`\n"
            "• `/explain Integration by Parts`",
            parse_mode="Markdown"
        )
        return

    topic = " ".join(context.args)
    status_msg = await update.message.reply_text(
        f"🔍 Explaining *{topic}* in simple terms...",
        parse_mode="Markdown"
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        # Get transcript context if available
        session = get_session(user.id)
        transcript_context = ""
        if session and session.get("last_transcript"):
            transcript_context = session["last_transcript"][:3000]

        prompt = explain_eli10_prompt(topic, transcript_context)
        explanation = await ask_ai(prompt, SYSTEM_ELI10)

        # Split into chunks if too long for Telegram (4096 char limit)
        if len(explanation) > 4000:
            parts = [explanation[i:i+4000] for i in range(0, len(explanation), 4000)]
            await status_msg.delete()
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(
                        f"🌟 *Explain Like I'm 10: {topic}*\n\n{part}",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(part, parse_mode="Markdown")
        else:
            await status_msg.edit_text(
                f"🌟 *Explain Like I'm 10: {topic}*\n\n{explanation}",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Explain error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask doubts from the last processed lecture"""
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    if not context.args:
        await update.message.reply_text(
            "❌ Please ask a question!\n\n"
            "Usage: `/ask <your question>`\n\n"
            "Examples:\n"
            "• `/ask Why is current same in series?`\n"
            "• `/ask What is the formula for electric field?`\n"
            "• `/ask Explain Gauss Law`\n\n"
            "💡 *First* process a video with `/notes <url>`, then ask doubts!",
            parse_mode="Markdown"
        )
        return

    question = " ".join(context.args)
    session = get_session(user.id)

    if not session or not session.get("last_transcript"):
        await update.message.reply_text(
            "⚠️ *No lecture loaded yet!*\n\n"
            "Process a video first:\n"
            "`/notes <youtube_link>`\n\n"
            "Then ask your doubts with `/ask <question>`\n\n"
            "💡 I'll answer from that specific lecture's content.",
            parse_mode="Markdown"
        )
        return

    title = session.get("last_title", "the lecture")
    transcript = session.get("last_transcript", "")

    status_msg = await update.message.reply_text(
        f"💬 Searching lecture for: *{question[:50]}*...",
        parse_mode="Markdown"
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        prompt = doubts_prompt(question, transcript, title)
        answer = await ask_ai(prompt, SYSTEM_STUDY)

        if len(answer) > 4000:
            parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
            await status_msg.delete()
            for i, part in enumerate(parts):
                header = f"❓ *Doubt: {question[:50]}*\n📹 From: _{title[:40]}_\n\n" if i == 0 else ""
                await update.message.reply_text(
                    f"{header}{part}",
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(
                f"❓ *Doubt: {question[:50]}*\n"
                f"📹 From: _{title[:40]}_\n\n"
                f"{answer}",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Ask error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")
