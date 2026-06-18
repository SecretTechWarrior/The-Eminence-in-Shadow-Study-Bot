import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from youtube_utils import get_playlist_videos, get_transcript, get_video_title, extract_playlist_id
from ai_client import ask_ai
from pdf_generator import create_pdf
from database import upsert_user
from prompts import playlist_master_notes_prompt, notes_prompt, SYSTEM_STUDY

logger = logging.getLogger(__name__)

MAX_PLAYLIST_VIDEOS = 15  # Limit to avoid abuse


async def playlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.first_name or "")

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Please provide a YouTube playlist link!\n\n"
            "Usage: `/playlist <playlist_url>`\n\n"
            "Example:\n"
            "`/playlist https://youtube.com/playlist?list=PLxxxx`\n\n"
            "⚠️ Note: Processes up to 15 videos. Large playlists may take a few minutes.",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    playlist_id = extract_playlist_id(url)

    if not playlist_id:
        await update.message.reply_text(
            "❌ Invalid playlist URL!\n\n"
            "Make sure the URL contains `list=` parameter.\n"
            "Example: `https://youtube.com/playlist?list=PLxxxx`",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text(
        "🎵 *Playlist Analyzer Started!*\n\n"
        "⏳ Step 1: Fetching playlist videos...",
        parse_mode="Markdown"
    )

    try:
        videos = await get_playlist_videos(url)

        if not videos:
            await status_msg.edit_text("❌ No videos found in this playlist.")
            return

        total = len(videos)
        process_count = min(total, MAX_PLAYLIST_VIDEOS)

        await status_msg.edit_text(
            f"✅ Found *{total} videos* in playlist!\n\n"
            f"⏳ Processing first {process_count} videos...\n"
            "(This will take a few minutes)",
            parse_mode="Markdown"
        )

        # Process videos one by one
        processed_videos = []
        failed = []
        combined_transcript = ""
        video_titles = []

        for i, video in enumerate(videos[:process_count]):
            vid_id = video["video_id"]
            vid_title = video["title"]

            await status_msg.edit_text(
                f"📹 Processing video {i+1}/{process_count}:\n"
                f"_{vid_title[:50]}_\n\n"
                f"Progress: {'▓' * (i+1)}{'░' * (process_count-i-1)} {i+1}/{process_count}",
                parse_mode="Markdown"
            )

            try:
                transcript_list, transcript_text = await get_transcript(vid_id)
                processed_videos.append({
                    "video_id": vid_id,
                    "title": vid_title,
                    "transcript": transcript_text
                })
                video_titles.append(vid_title)
                combined_transcript += f"\n\n=== {vid_title} ===\n{transcript_text[:2000]}"
            except Exception as e:
                logger.warning(f"Skipping video {vid_id}: {e}")
                failed.append(vid_title)

            await asyncio.sleep(0.5)

        if not processed_videos:
            await status_msg.edit_text(
                "❌ Could not process any videos from this playlist.\n"
                "Most videos may not have captions."
            )
            return

        await status_msg.edit_text(
            f"✅ Processed {len(processed_videos)}/{process_count} videos!\n"
            f"{'⚠️ Skipped: ' + str(len(failed)) + ' (no captions)' if failed else ''}\n\n"
            "⏳ Generating Master Notes...",
            parse_mode="Markdown"
        )

        playlist_title = f"Playlist — {process_count} Videos"

        # Generate master notes
        master_prompt = playlist_master_notes_prompt(
            combined_transcript,
            playlist_title,
            video_titles
        )
        master_content = await ask_ai(master_prompt, SYSTEM_STUDY)

        # Create master PDF
        await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        master_pdf = create_pdf(
            filename="playlist_master",
            title="Playlist Master Notes",
            subtitle=f"Combined notes from {len(processed_videos)} videos",
            content=master_content,
            video_title=playlist_title
        )

        # Send master PDF
        with open(master_pdf, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"Master_Notes_Playlist.pdf",
                caption=(
                    f"📚 *Playlist Master Notes*\n\n"
                    f"✅ Processed: {len(processed_videos)} videos\n"
                    f"{'⚠️ Skipped: ' + str(len(failed)) + ' (no captions)' if failed else ''}\n\n"
                    "Contains:\n"
                    "• Overview of all topics\n"
                    "• Combined key concepts\n"
                    "• Master formula sheet\n"
                    "• Top revision points"
                ),
                parse_mode="Markdown"
            )

        os.remove(master_pdf)

        # Send summary of what was processed
        summary_lines = [f"✅ *Playlist Processing Complete!*\n"]
        summary_lines.append(f"📹 Processed: {len(processed_videos)}/{total} videos\n")
        if failed:
            summary_lines.append(f"⚠️ Skipped (no captions): {len(failed)} videos\n")
        summary_lines.append("\n*Videos processed:*\n")
        for i, t in enumerate(video_titles[:10], 1):
            summary_lines.append(f"{i}. {t[:60]}\n")
        if len(video_titles) > 10:
            summary_lines.append(f"... and {len(video_titles)-10} more\n")

        await status_msg.edit_text(
            "".join(summary_lines),
            parse_mode="Markdown"
        )

    except ValueError as e:
        await status_msg.edit_text(
            f"❌ Error: {e}\n\n"
            "💡 Note: Playlist analysis requires a YouTube Data API key.\n"
            "Contact the bot admin to enable this feature."
        )
    except Exception as e:
        logger.error(f"Playlist error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Something went wrong. Please try again.")
