"""YouTube playlist extraction via yt-dlp."""
from __future__ import annotations

import json
import logging
import subprocess

logger = logging.getLogger(__name__)


async def get_playlist(
    playlist_id: str,
    max_videos: int = 50,
    yt_dlp: str = "yt-dlp",
) -> dict:
    """Extract playlist metadata and video list using yt-dlp.

    Returns a dict with keys:
        playlist_id, title, video_count, videos
    where *videos* is a list of ``{video_id, title, duration}``.
    """
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    logger.info("Fetching playlist %s (max %d)", playlist_id, max_videos)

    try:
        proc = subprocess.run(
            [
                yt_dlp,
                "--flat-playlist",
                "--dump-json",
                "--playlist-end", str(max_videos),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.error("yt-dlp playlist failed: %s", exc)
        return {"error": str(exc)}

    if proc.returncode != 0:
        logger.error("yt-dlp playlist stderr: %s", proc.stderr[:500])
        return {"error": f"yt-dlp exited with {proc.returncode}"}

    videos: list[dict] = []
    playlist_title = ""
    for line in proc.stdout.strip().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not playlist_title:
            playlist_title = entry.get("playlist_title", "")
        videos.append({
            "video_id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "duration": entry.get("duration"),
        })

    return {
        "playlist_id": playlist_id,
        "title": playlist_title,
        "video_count": len(videos),
        "videos": videos,
    }
