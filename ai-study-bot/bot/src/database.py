import sqlite3
import json
import os
from config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "studybot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_videos INTEGER DEFAULT 0,
            total_quizzes INTEGER DEFAULT 0,
            total_notes INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS processed_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            video_url TEXT,
            video_id TEXT,
            title TEXT,
            transcript TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            last_video_url TEXT,
            last_video_id TEXT,
            last_transcript TEXT,
            last_title TEXT,
            context_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            playlist_url TEXT,
            playlist_title TEXT,
            video_count INTEGER,
            processed_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def upsert_user(user_id: int, username: str, first_name: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name
    """, (user_id, username, first_name))
    conn.commit()
    conn.close()


def save_video(user_id: int, video_url: str, video_id: str, title: str, transcript: str, summary: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO processed_videos (user_id, video_url, video_id, title, transcript, summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, video_url, video_id, title, transcript, summary))
    c.execute("UPDATE users SET total_videos = total_videos + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_session(user_id: int, video_url: str, video_id: str, transcript: str, title: str, context: dict = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_sessions (user_id, last_video_url, last_video_id, last_transcript, last_title, context_data, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            last_video_url=excluded.last_video_url,
            last_video_id=excluded.last_video_id,
            last_transcript=excluded.last_transcript,
            last_title=excluded.last_title,
            context_data=excluded.context_data,
            updated_at=CURRENT_TIMESTAMP
    """, (user_id, video_url, video_id, transcript, title, json.dumps(context or {})))
    conn.commit()
    conn.close()


def get_session(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM user_sessions WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_user_stats(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    c.execute("SELECT COUNT(*) as cnt FROM processed_videos WHERE user_id = ?", (user_id,))
    vid_count = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["video_count"] = vid_count["cnt"] if vid_count else 0
        return d
    return None


def get_recent_videos(user_id: int, limit: int = 5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT video_url, title, created_at FROM processed_videos
        WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
