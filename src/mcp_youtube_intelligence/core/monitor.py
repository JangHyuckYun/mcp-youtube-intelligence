"""RSS-based channel monitoring."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)


def fetch_channel_feed(channel_id: str) -> list[dict]:
    """Fetch recent videos from a YouTube channel RSS feed."""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)
    videos = []
    for entry in feed.entries:
        vid = entry.get("yt_videoid", "")
        if not vid:
            continue
        published = entry.get("published", "")
        videos.append({
            "video_id": vid,
            "title": entry.get("title", ""),
            "published": published,
            "link": entry.get("link", f"https://www.youtube.com/watch?v={vid}"),
        })
    return videos


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
    # Update channel last_checked
    await storage.update_channel_checked(channel_id)
    logger.info("Channel %s: %d new videos", channel_id, len(new_videos))
    return new_videos
