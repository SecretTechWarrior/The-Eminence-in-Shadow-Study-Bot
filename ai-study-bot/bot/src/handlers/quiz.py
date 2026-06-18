import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_video_info
from ai_client import ask_ai
from pdf_generator import create_quiz_pdf
from database import save_session, upsert_user
from prompts import quiz_prompt, SYSTEM_QUIZ

logger = logging.getLogger(__name__)

VALID_TYPES = {"mcq", "subjective", "mixed"}
VALID_DIFFICULTY = {"easy", "medium", "hard", "exam"}


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube link!\n\n"
            "*Usage:*\n"
            "`/quiz <url>` — Mixed medium quiz\n"
            "`/quiz <url> mcq` — MCQ only\n"
            "`/quiz <url> subjective hard` — Hard subjective\n"
            "`/quiz <url> mixed exam` — Exam-level quiz\n\n"
            "*Types:* mcq, subjective, mixed\n"
            "*Difficulty:* easy, medium, hard, exam",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    quiz_type = "mixed"
    difficulty = "medium"

    for arg in args[1:]:
        arg_lower = arg.lower()
        if arg_lower in VALID_TYPES:
            quiz_type = arg_lower
        elif arg_lower in VALID_DIFFICULTY:
            difficulty = arg_lower

    status_msg = await update.message.reply_text(
        "🔍 Processing your video...\n\n"
        "⏳ Step 1/4: Fetching transcript..."
    )

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        video_info = await get_video_info(url)
        title = video_info["title"]
        transcript = video_info["transcript_text"]

        await status_msg.edit_text(
            f"✅ Transcript fetched!\n"
            f"📹 *{title}*\n\n"
            f"⏳ Step 2/4: Generating {difficulty} {quiz_type} quiz...",
            parse_mode="Markdown"
        )

        prompt = quiz_prompt(transcript, title, quiz_type, difficulty)
        raw_response = await ask_ai(prompt, SYSTEM_QUIZ)

        await status_msg.edit_text("✅ Quiz generated!\n\n⏳ Step 3/4: Creating PDFs...")

        # Split response into quiz and answers
        if "---" in raw_response:
            parts = raw_response.split("---", 1)
            quiz_content = parts[0].strip()
            answer_content = parts[1].strip() if len(parts) > 1 else "Answer key not generated."
        else:
            quiz_content = raw_response
            answer_content = "Answer key not available. Please regenerate."

        quiz_lines = quiz_content.split("\n")
        answer_lines = answer_content.split("\n")

        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        quiz_path, ans_path = create_quiz_pdf(
            filename="quiz",
            title=f"{difficulty.title()} {quiz_type.upper()} Quiz",
            questions=quiz_lines,
            answers=answer_lines,
            video_title=title
        )

        await status_msg.edit_text("✅ PDFs created!\n\n⏳ Step 4/4: Sending files...")

        save_session(user.id, url, video_info["video_id"], transcript, title)

        # Send quiz PDF
        with open(quiz_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Quiz_{difficulty}_{title[:30]}.pdf",
                caption=(
                    f"🧪 *{difficulty.title()} {quiz_type.upper()} Quiz*\n"
                    f"📹 {title}\n\n"
                    "Attempt all questions before checking answers!"
                ),
                parse_mode="Markdown"
            )

        # Send answer key PDF
        with open(ans_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Answer_Key_{difficulty}_{title[:30]}.pdf",
                caption=(
                    f"✅ *Answer Key*\n"
                    f"Check your answers here!\n\n"
                    f"💡 Also try: `/revise {url}` for revision sheet"
                ),
                parse_mode="Markdown"
            )

        await status_msg.delete()
        os.remove(quiz_path)
        os.remove(ans_path)

    except ValueError as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Quiz error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")
