import re
import asyncio
import logging
import requests

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
)

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
# TRANSCRIPT (FIXED FOR NEW API)
# ---------------------------
async def get_transcript(video_id: str) -> tuple[list, str]:

    def _fetch():
        try:
            api = YouTubeTranscriptApi()

            # NEW API (v1.2+)
            try:
                fetched = api.fetch(video_id)

                return [
                    {
                        "text": s.text,
                        "start": s.start,
                        "duration": s.duration,
                    }
                    for s in fetched
                ]

            except Exception as e:
                logger.warning(f"New API failed, fallback used: {e}")

            # FALLBACK (older behavior)
            return YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["en", "en-US", "en-GB"]
            )

        except TranscriptsDisabled:
            raise ValueError("Transcripts are disabled for this video.")

        except NoTranscriptFound:
            raise ValueError("No transcript found for this video.")

        except Exception as e:
            raise ValueError(f"Could not get transcript: {e}")

    transcript_list = await asyncio.to_thread(_fetch)

    # normalize safely
    full_text = " ".join(
        str(entry.get("text", "") if isinstance(entry, dict) else getattr(entry, "text", ""))
        for entry in transcript_list
    ).strip()

    return transcript_list, full_text


# ---------------------------
# VIDEO TITLE
# ---------------------------
async def get_video_title(video_id: str) -> str:
    try:
        url = (
            "https://www.youtube.com/oembed"
            f"?url=https://youtube.com/watch?v={video_id}&format=json"
        )

        response = await asyncio.to_thread(
            requests.get,
            url,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("title", f"Video {video_id}")

    except Exception as e:
        logger.warning(f"Title fetch failed: {e}")

    return f"YouTube Video ({video_id})"


# ---------------------------
# MAIN VIDEO INFO
# ---------------------------
async def get_video_info(url: str) -> dict:
    video_id = extract_video_id(url)

    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    title = await get_video_title(video_id)
    transcript_list, full_text = await get_transcript(video_id)

    if not full_text:
        raise ValueError("Transcript empty.")

    return {
        "video_id": video_id,
        "url": url,
        "title": title,
        "transcript_list": transcript_list,
        "transcript_text": full_text,
        "duration_estimate": transcript_list[-1].get("start", 0) if transcript_list else 0,
    }


# ---------------------------
# TIMESTAMP FORMATTER
# ---------------------------
def format_timestamp(seconds: float) -> str:
    return f"{int(seconds//60):02d}:{int(seconds%60):02d}"


# ---------------------------
# PLAYLIST FETCH
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
