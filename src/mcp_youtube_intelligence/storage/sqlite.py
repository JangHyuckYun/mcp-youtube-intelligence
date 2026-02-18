"""SQLite storage implementation using aiosqlite."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from .base import BaseStorage

logger = logging.getLogger(__name__)

INIT_SQL = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    channel_url TEXT,
    enabled INTEGER DEFAULT 1,
    last_checked_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    channel_name TEXT,
    title TEXT,
    description TEXT,
    published_at TEXT,
    duration_seconds INTEGER,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    is_live INTEGER DEFAULT 0,
    was_live INTEGER DEFAULT 0,
    thumbnail_url TEXT,
    transcript_text TEXT,
    transcript_lang TEXT,
    transcript_length INTEGER,
    summary TEXT,
    status TEXT DEFAULT 'pending',
    collected_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    comment_id TEXT UNIQUE,
    author TEXT,
    text TEXT,
    like_count INTEGER DEFAULT 0,
    collected_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_comments_video ON comments(video_id);
"""


class SQLiteStorage(BaseStorage):
    """SQLite-based storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(INIT_SQL)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None, "Storage not initialized"
        return self._db

    # --- Videos ---

    async def get_video(self, video_id: str) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def upsert_video(self, data: dict) -> None:
        vid = data["video_id"]
        existing = await self.get_video(vid)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            # Update only provided fields
            sets = []
            vals = []
            for k, v in data.items():
                if k == "video_id":
                    continue
                sets.append(f"{k} = ?")
                vals.append(v)
            sets.append("updated_at = ?")
            vals.append(now)
            vals.append(vid)
            await self.db.execute(f"UPDATE videos SET {', '.join(sets)} WHERE video_id = ?", vals)
        else:
            data.setdefault("created_at", now)
            data.setdefault("updated_at", now)
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            await self.db.execute(f"INSERT INTO videos ({cols}) VALUES ({placeholders})", list(data.values()))
        await self.db.commit()

    async def search_transcripts(self, query: str, limit: int = 10) -> list[dict]:
        sql = """
            SELECT video_id, title, channel_name, published_at, transcript_text
            FROM videos
            WHERE transcript_text LIKE ?
            ORDER BY published_at DESC
            LIMIT ?
        """
        results = []
        async with self.db.execute(sql, (f"%{query}%", limit)) as cur:
            async for row in cur:
                row_dict = dict(row)
                text = row_dict.pop("transcript_text", "") or ""
                # Find snippet around the match
                snippet = _extract_snippet(text, query)
                row_dict["snippet"] = snippet
                results.append(row_dict)
        return results

    # --- Channels ---

    async def get_channel(self, channel_id: str) -> Optional[dict]:
        async with self.db.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def upsert_channel(self, data: dict) -> None:
        cid = data["channel_id"]
        existing = await self.get_channel(cid)
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            sets = []
            vals = []
            for k, v in data.items():
                if k == "channel_id":
                    continue
                sets.append(f"{k} = ?")
                vals.append(v)
            sets.append("updated_at = ?")
            vals.append(now)
            vals.append(cid)
            await self.db.execute(f"UPDATE channels SET {', '.join(sets)} WHERE channel_id = ?", vals)
        else:
            data.setdefault("created_at", now)
            data.setdefault("updated_at", now)
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            await self.db.execute(f"INSERT INTO channels ({cols}) VALUES ({placeholders})", list(data.values()))
        await self.db.commit()

    async def list_channels(self) -> list[dict]:
        async with self.db.execute("SELECT * FROM channels WHERE enabled = 1 ORDER BY created_at") as cur:
            return [dict(row) async for row in cur]

    async def update_channel_checked(self, channel_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE channels SET last_checked_at = ?, updated_at = ? WHERE channel_id = ?",
            (now, now, channel_id),
        )
        await self.db.commit()

    # --- Comments ---

    async def save_comments(self, video_id: str, comments: list[dict]) -> None:
        for c in comments:
            await self.db.execute(
                "INSERT OR IGNORE INTO comments (video_id, comment_id, author, text, like_count) VALUES (?, ?, ?, ?, ?)",
                (video_id, c.get("comment_id", ""), c.get("author", ""), c.get("text", ""), c.get("like_count", 0)),
            )
        await self.db.commit()

    async def get_comments(self, video_id: str, limit: int = 20) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM comments WHERE video_id = ? ORDER BY like_count DESC LIMIT ?",
            (video_id, limit),
        ) as cur:
            return [dict(row) async for row in cur]


def _extract_snippet(text: str, query: str, context_chars: int = 150) -> str:
    """Extract a snippet around the first occurrence of query in text."""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:300]
    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(query) + context_chars)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
