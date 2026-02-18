"""Video metadata collection via yt-dlp."""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def resolve_channel_url(channel_ref: str) -> str:
    """Normalize a channel reference (URL, @handle, or ID) to a URL."""
    if channel_ref.startswith("http"):
        return channel_ref
    if channel_ref.startswith("@"):
        return f"https://www.youtube.com/{channel_ref}"
    if channel_ref.startswith("UC"):
        return f"https://www.youtube.com/channel/{channel_ref}"
    return f"https://www.youtube.com/@{channel_ref}"


def get_channel_info(channel_ref: str, yt_dlp: str = "yt-dlp") -> dict:
    """Resolve channel ID and name from any reference."""
    url = resolve_channel_url(channel_ref)
    try:
        result = subprocess.run(
            [yt_dlp, "--print", "channel_id", "--print", "channel",
             "--playlist-items", "1", url],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            return {
                "channel_id": lines[0].strip(),
                "channel_name": lines[1].strip(),
                "channel_url": f"https://www.youtube.com/channel/{lines[0].strip()}",
            }
    except Exception as e:
        logger.warning("Failed to resolve channel %s: %s", channel_ref, e)

    cid = channel_ref.split("/")[-1]
    return {"channel_id": cid, "channel_name": cid, "channel_url": f"https://www.youtube.com/channel/{cid}"}


def get_video_metadata(video_id: str, yt_dlp: str = "yt-dlp") -> Optional[dict]:
    """Fetch video metadata via yt-dlp --dump-json."""
    try:
        result = subprocess.run(
            [yt_dlp, "--dump-json", "--skip-download",
             f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.error("yt-dlp failed for %s: %s", video_id, result.stderr[:200])
            return None
        data = json.loads(result.stdout)
        upload_date = data.get("upload_date", "")
        published_at = None
        if upload_date:
            try:
                published_at = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass
        return {
            "video_id": video_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "channel_id": data.get("channel_id", ""),
            "channel_name": data.get("channel", data.get("uploader", "")),
            "published_at": published_at,
            "duration_seconds": data.get("duration"),
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "comment_count": data.get("comment_count"),
            "is_live": data.get("is_live", False),
            "was_live": data.get("was_live", False),
            "thumbnail_url": data.get("thumbnail"),
        }
    except Exception as e:
        logger.error("Metadata error for %s: %s", video_id, e)
        return None
