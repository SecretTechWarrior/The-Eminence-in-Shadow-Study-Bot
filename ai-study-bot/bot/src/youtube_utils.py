import re
import asyncio
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import requests
from config import YOUTUBE_API_KEY

logger = logging.getLogger(__name__)


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


def extract_playlist_id(url: str) -> str | None:
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


async def get_transcript(video_id: str) -> tuple[list, str]:
    """Returns (transcript_list, full_text)"""
    def _fetch():
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
            return transcript_list
        except NoTranscriptFound:
            # Try auto-generated
            try:
                transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                for t in transcripts:
                    try:
                        return t.fetch()
                    except:
                        pass
                raise
            except Exception:
                raise
        except TranscriptsDisabled:
            raise ValueError("Transcripts are disabled for this video.")
        except Exception as e:
            raise ValueError(f"Could not get transcript: {e}")

    transcript_list = await asyncio.to_thread(_fetch)
    full_text = " ".join([entry['text'] for entry in transcript_list])
    return transcript_list, full_text


async def get_video_title(video_id: str) -> str:
    """Get video title via oEmbed (no API key needed)"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json"
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("title", f"Video {video_id}")
    except Exception as e:
        logger.warning(f"Could not get video title: {e}")
    return f"YouTube Video ({video_id})"


async def get_video_info(url: str) -> dict:
    """Main function to get video info from URL"""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video link.")

    title = await get_video_title(video_id)
    transcript_list, full_text = await get_transcript(video_id)

    if not full_text.strip():
        raise ValueError("Transcript is empty for this video.")

    return {
        "video_id": video_id,
        "url": url,
        "title": title,
        "transcript_list": transcript_list,
        "transcript_text": full_text,
        "duration_estimate": len(transcript_list) > 0 and transcript_list[-1].get('start', 0) or 0
    }


def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


async def get_playlist_videos(playlist_url: str) -> list[dict]:
    """Get all video IDs and titles from a playlist using YouTube Data API"""
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid playlist URL.")

    if not YOUTUBE_API_KEY:
        raise ValueError("YouTube Data API key not configured. Use /setapikey to configure it, or contact the bot admin.")

    videos = []
    next_page_token = None
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"

    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = await asyncio.to_thread(requests.get, base_url, params=params, timeout=15)
        if response.status_code != 200:
            raise ValueError(f"YouTube API error: {response.status_code}")

        data = response.json()
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            title = snippet.get("title", "Unknown")
            if video_id:
                videos.append({"video_id": video_id, "title": title})

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def chunk_transcript(transcript_text: str, max_chars: int = 12000) -> list[str]:
    """Split long transcripts into chunks for processing"""
    words = transcript_text.split()
    chunks = []
    current_chunk = []
    current_len = 0

    for word in words:
        current_len += len(word) + 1
        current_chunk.append(word)
        if current_len >= max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
