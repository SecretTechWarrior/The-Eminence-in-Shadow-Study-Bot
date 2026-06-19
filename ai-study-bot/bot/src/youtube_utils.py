import re
import asyncio
import logging
import requests
import os
import tempfile

import yt_dlp
from faster_whisper import WhisperModel

from config import YOUTUBE_API_KEY

logger = logging.getLogger(__name__)

# ---------------------------
# VIDEO ID EXTRACTION
# ---------------------------
def extract_video_id(url: str) -> str | None:
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


# ---------------------------
# PLAYLIST ID
# ---------------------------
def extract_playlist_id(url: str) -> str | None:
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


# ---------------------------
# METHOD 1: YT-DLP CAPTIONS
# ---------------------------
def _yt_dlp_captions(video_url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    subs = info.get("subtitles") or info.get("automatic_captions") or {}

    if "en" not in subs:
        return None

    lines = subs["en"]
    text = " ".join([x.get("text", "") for x in lines if isinstance(x, dict)])

    return text.strip() or None


# ---------------------------
# METHOD 2: WHISPER TRANSCRIPTION
# ---------------------------
def _whisper_transcribe(video_url: str):
    model = WhisperModel("base", device="cpu", compute_type="int8")

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = os.path.join(tmp, "audio.mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        segments, _ = model.transcribe(audio_path)

        text = " ".join(seg.text for seg in segments)

        return text.strip() or None


# ---------------------------
# MAIN TRANSCRIPT FUNCTION
# ---------------------------
async def get_transcript(video_id: str) -> tuple[list, str]:
    url = f"https://www.youtube.com/watch?v={video_id}"

    def _fetch():
        # 1. Try yt-dlp captions
        try:
            text = _yt_dlp_captions(url)
            if text:
                return [{"text": text, "start": 0}], text
        except Exception as e:
            logger.warning(f"yt-dlp captions failed: {e}")

        # 2. Whisper fallback
        try:
            text = _whisper_transcribe(url)
            if text:
                return [{"text": text, "start": 0}], text
        except Exception as e:
            logger.error(f"Whisper failed: {e}")

        raise ValueError("No transcript available for this video.")

    return await asyncio.to_thread(_fetch)


# ---------------------------
# VIDEO TITLE
# ---------------------------
async def get_video_title(video_id: str) -> str:
    try:
        url = (
            "https://www.youtube.com/oembed"
            f"?url=https://youtube.com/watch?v={video_id}&format=json"
        )

        response = await asyncio.to_thread(requests.get, url, timeout=10)

        if response.status_code == 200:
            return response.json().get("title", f"Video {video_id}")

    except Exception as e:
        logger.warning(f"Title fetch failed: {e}")

    return f"YouTube Video ({video_id})"


# ---------------------------
# MAIN INFO
# ---------------------------
async def get_video_info(url: str) -> dict:
    video_id = extract_video_id(url)

    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    title = await get_video_title(video_id)
    transcript_list, full_text = await get_transcript(video_id)

    return {
        "video_id": video_id,
        "url": url,
        "title": title,
        "transcript_list": transcript_list,
        "transcript_text": full_text,
        "duration_estimate": 0,
    }


# ---------------------------
# TIMESTAMP
# ---------------------------
def format_timestamp(seconds: float) -> str:
    return f"{int(seconds//60):02d}:{int(seconds%60):02d}"


# ---------------------------
# PLAYLIST (UNCHANGED SAFE)
# ---------------------------
async def get_playlist_videos(playlist_url: str) -> list[dict]:
    playlist_id = extract_playlist_id(playlist_url)

    if not playlist_id:
        raise ValueError("Invalid playlist URL.")

    if not YOUTUBE_API_KEY:
        raise ValueError("Missing YouTube API key.")

    videos = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY,
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        response = await asyncio.to_thread(
            requests.get,
            "https://www.googleapis.com/youtube/v3/playlistItems",
            params=params,
            timeout=15,
        )

        data = response.json()

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            vid = snippet.get("resourceId", {}).get("videoId")
            title = snippet.get("title", "Unknown")

            if vid:
                videos.append({"video_id": vid, "title": title})

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return videos


# ---------------------------
# CHUNKING
# ---------------------------
def chunk_transcript(transcript_text: str, max_chars: int = 12000) -> list[str]:
    words = transcript_text.split()
    chunks, current, length = [], [], 0

    for w in words:
        length += len(w) + 1
        current.append(w)

        if length >= max_chars:
            chunks.append(" ".join(current))
            current, length = [], 0

    if current:
        chunks.append(" ".join(current))

    return chunks
