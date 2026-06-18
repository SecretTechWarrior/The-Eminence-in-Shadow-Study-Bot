from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import upsert_user, get_user_stats, get_recent_videos

HELP_TEXT = """
📚 *AI Study Assistant Bot*

I can turn any YouTube lecture into study material!

*📹 Video Commands:*
`/notes <youtube_link>` — Detailed notes PDF
`/shortnotes <youtube_link>` — Short revision notes
`/quiz <youtube_link>` — Quiz with answer key
`/summary <youtube_link>` — Quick summary
`/chapters <youtube_link>` — Chapter breakdown
`/revise <youtube_link>` — One-day revision sheet
`/formulas <youtube_link>` — Formula extractor
`/audio <youtube_link>` — Audio revision (MP3)
`/explain <topic>` — Explain like I'm 10

*🎵 Playlist Commands:*
`/playlist <playlist_url>` — Analyze full playlist

*💬 Doubt Solving:*
`/ask <question>` — Ask doubt from last processed lecture

*📊 Account:*
`/stats` — Your usage statistics
`/history` — Recently processed videos
`/help` — Show this help message

*💡 Tips:*
• Process a video first with `/notes`, then use `/ask` to ask doubts
• Use `/quiz hard` or `/quiz easy` for difficulty levels
• Use `/summary quick` for 10 bullet points
• Use `/audio 15min` for longer audio

*Supported YouTube URLs:*
• `youtube.com/watch?v=...`
• `youtu.be/...`
• `youtube.com/shorts/...`
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    keyboard = [
        [
            InlineKeyboardButton("📝 Generate Notes", callback_data="help_notes"),
            InlineKeyboardButton("🧪 Create Quiz", callback_data="help_quiz"),
        ],
        [
            InlineKeyboardButton("📖 Summary", callback_data="help_summary"),
            InlineKeyboardButton("🎧 Audio", callback_data="help_audio"),
        ],
        [
            InlineKeyboardButton("❓ Ask Doubts", callback_data="help_ask"),
            InlineKeyboardButton("📋 All Commands", callback_data="help_all"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = (
        f"👋 Hello *{user.first_name}*! Welcome to *AI Study Assistant Bot*!\n\n"
        "I can transform any YouTube lecture into:\n"
        "• 📄 Detailed/Short Notes PDF\n"
        "• 🧪 Quiz with Answer Key PDF\n"
        "• 📋 Chapter-wise Breakdown\n"
        "• 📅 One-Day Revision Sheet\n"
        "• 🔢 Formula Extractor\n"
        "• 🎧 Audio Revision MP3\n"
        "• 🔍 Explain Like I'm 10\n"
        "• 💬 Ask Doubts from Lecture\n"
        "• 📚 Full Playlist Analyzer\n\n"
        "Just send me a YouTube link with the right command!\n\n"
        "*Quick Start:* `/notes https://youtube.com/watch?v=...`"
    )

    await update.message.reply_text(
        welcome_msg,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = get_user_stats(user.id)

    if not stats:
        await update.message.reply_text("No stats yet! Process a video to get started.")
        return

    msg = (
        f"📊 *Your Study Statistics*\n\n"
        f"👤 Name: {stats.get('first_name', 'Unknown')}\n"
        f"📹 Videos Processed: {stats.get('video_count', 0)}\n"
        f"📝 Notes Generated: {stats.get('total_notes', 0)}\n"
        f"🧪 Quizzes Generated: {stats.get('total_quizzes', 0)}\n\n"
        f"Keep studying! 💪"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    videos = get_recent_videos(user.id, limit=5)

    if not videos:
        await update.message.reply_text(
            "No history yet! Use `/notes <youtube_link>` to get started.",
            parse_mode="Markdown"
        )
        return

    msg = "📜 *Recently Processed Videos:*\n\n"
    for i, v in enumerate(videos, 1):
        title = v.get("title", "Unknown")[:50]
        date = v.get("created_at", "")[:10]
        url = v.get("video_url", "")
        msg += f"{i}. [{title}]({url})\n   📅 {date}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    help_texts = {
        "help_notes": (
            "📝 *Notes Commands*\n\n"
            "`/notes <url>` — Full detailed notes PDF\n"
            "`/shortnotes <url>` — Short revision notes PDF\n\n"
            "*Example:*\n`/notes https://youtube.com/watch?v=dQw4w9WgXcQ`"
        ),
        "help_quiz": (
            "🧪 *Quiz Commands*\n\n"
            "`/quiz <url>` — Mixed quiz (medium difficulty)\n"
            "`/quiz <url> mcq` — MCQ only\n"
            "`/quiz <url> subjective` — Subjective only\n"
            "`/quiz <url> mixed hard` — Mixed hard quiz\n\n"
            "*Difficulty options:* easy, medium, hard, exam"
        ),
        "help_summary": (
            "📖 *Summary Commands*\n\n"
            "`/summary <url>` — Detailed summary\n"
            "`/summary <url> quick` — 10 bullet points\n"
            "`/summary <url> 5min` — 1-page revision\n"
            "`/summary <url> ultra` — 100 words only\n"
            "`/chapters <url>` — Chapter-wise breakdown"
        ),
        "help_audio": (
            "🎧 *Audio Commands*\n\n"
            "`/audio <url>` — 5-minute audio revision\n"
            "`/audio <url> 15min` — 15-minute audio\n\n"
            "Voices available: US, UK, Indian (male/female)\n"
            "Output: MP3 file ready to download"
        ),
        "help_ask": (
            "❓ *Doubt Solving*\n\n"
            "First process a video:\n"
            "`/notes <url>`\n\n"
            "Then ask your doubt:\n"
            "`/ask Why is current same in series?`\n"
            "`/ask What is the formula for electric field?`\n\n"
            "The bot answers from the lecture content!"
        ),
        "help_all": HELP_TEXT,
    }

    text = help_texts.get(query.data, "Unknown command")
    await query.edit_message_text(text, parse_mode="Markdown")
