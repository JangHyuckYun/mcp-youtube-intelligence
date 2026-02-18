"""RSS-based channel monitoring with yt-dlp fallback."""
from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)

_RSS_MAX_RETRIES = 2
_RSS_RETRY_DELAY = 1.0  # seconds


def fetch_channel_feed(channel_id: str) -> list[dict]:
    """Fetch recent videos from a YouTube channel RSS feed with retry logic.
    
    Retries once on failure, then falls back to yt-dlp.
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    last_error: Exception | None = None
    for attempt in range(_RSS_MAX_RETRIES):
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                raise RuntimeError(f"RSS parse error: {feed.bozo_exception}")
            videos = []
            for entry in feed.entries:
                vid = entry.get("yt_videoid", "")
                if not vid:
                    continue
                videos.append({
                    "video_id": vid,
                    "title": entry.get("title", ""),
                    "published": entry.get("published", ""),
                    "link": entry.get("link", f"https://www.youtube.com/watch?v={vid}"),
                })
            if videos:
                return videos
            # Empty feed — might be a transient issue, retry
            if attempt < _RSS_MAX_RETRIES - 1:
                import time
                time.sleep(_RSS_RETRY_DELAY)
                continue
            # Still empty after retries — try fallback
            break
        except Exception as e:
            last_error = e
            logger.warning("RSS fetch attempt %d failed for %s: %s", attempt + 1, channel_id, e)
            if attempt < _RSS_MAX_RETRIES - 1:
                import time
                time.sleep(_RSS_RETRY_DELAY)

    # Fallback to yt-dlp
    logger.info("RSS failed for %s, falling back to yt-dlp", channel_id)
    return _fetch_channel_ytdlp(channel_id)


def _fetch_channel_ytdlp(channel_id: str, max_videos: int = 5) -> list[dict]:
    """Fallback: fetch recent videos using yt-dlp flat-playlist."""
    try:
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
        result = subprocess.run(
            [
                "yt-dlp", "--flat-playlist",
                "--print", "id",
                "--print", "title",
                f"--playlist-items", f"1:{max_videos}",
                url,
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            logger.error("yt-dlp fallback failed for %s: %s", channel_id, result.stderr[:200])
            return []

        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        videos = []
        # yt-dlp prints id and title on alternating lines
        for i in range(0, len(lines) - 1, 2):
            vid = lines[i]
            title = lines[i + 1] if i + 1 < len(lines) else ""
            videos.append({
                "video_id": vid,
                "title": title,
                "published": "",
                "link": f"https://www.youtube.com/watch?v={vid}",
            })
        logger.info("yt-dlp fallback fetched %d videos for %s", len(videos), channel_id)
        return videos
    except Exception as e:
        logger.error("yt-dlp fallback error for %s: %s", channel_id, e)
        return []


async def check_channel_new_videos(channel_id: str, storage) -> list[dict]:
    """Check RSS feed for videos not yet in storage. Returns list of new video dicts."""
    feed_videos = fetch_channel_feed(channel_id)
    new_videos = []
    for v in feed_videos:
        existing = await storage.get_video(v["video_id"])
        if existing is None:
            await storage.upsert_video({
                "video_id": v["video_id"],
                "channel_id": channel_id,
                "title": v["title"],
                "published_at": v["published"],
                "status": "pending",
            })
            new_videos.append(v)
    await storage.update_channel_checked(channel_id)
    logger.info("Channel %s: %d new videos", channel_id, len(new_videos))
    return new_videos
