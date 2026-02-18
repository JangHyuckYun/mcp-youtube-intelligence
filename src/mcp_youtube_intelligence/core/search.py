"""YouTube video search via Data API v3 with yt-dlp fallback."""
from __future__ import annotations

import json
import logging
import subprocess
from typing import Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


async def search_youtube(
    query: str,
    max_results: int = 10,
    channel_id: Optional[str] = None,
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    order: str = "relevance",
    api_key: str = "",
    yt_dlp: str = "yt-dlp",
) -> list[dict]:
    """Search YouTube videos by keyword.

    Uses YouTube Data API v3 when *api_key* is provided, otherwise falls
    back to ``yt-dlp ytsearch`` (lower quality but no API key needed).

    Returns a list of dicts with keys:
        video_id, title, channel, published_at, description, thumbnail
    """
    if api_key:
        return await _search_api(
            query,
            max_results=max_results,
            channel_id=channel_id,
            published_after=published_after,
            published_before=published_before,
            order=order,
            api_key=api_key,
        )
    return _search_ytdlp(query, max_results=max_results, yt_dlp=yt_dlp)


# ------------------------------------------------------------------
# YouTube Data API v3
# ------------------------------------------------------------------

async def _search_api(
    query: str,
    *,
    max_results: int,
    channel_id: Optional[str],
    published_after: Optional[str],
    published_before: Optional[str],
    order: str,
    api_key: str,
) -> list[dict]:
    """Call YouTube Data API v3 ``search.list`` endpoint."""
    import aiohttp  # local import to keep dependency optional

    params: dict = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": order,
        "key": api_key,
    }
    if channel_id:
        params["channelId"] = channel_id
    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before

    url = "https://www.googleapis.com/youtube/v3/search?" + urlencode(params)
    logger.info("YouTube API search: %s", query)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error("YouTube API error %s: %s", resp.status, body)
                return [{"error": f"YouTube API returned {resp.status}"}]
            data = await resp.json()

    results: list[dict] = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        results.append({
            "video_id": item.get("id", {}).get("videoId", ""),
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", "")[:200],
            "thumbnail": (snippet.get("thumbnails") or {}).get("default", {}).get("url", ""),
        })
    return results


# ------------------------------------------------------------------
# yt-dlp fallback
# ------------------------------------------------------------------

def _search_ytdlp(query: str, *, max_results: int, yt_dlp: str) -> list[dict]:
    """Fallback search using ``yt-dlp ytsearch``."""
    search_url = f"ytsearch{max_results}:{query}"
    logger.info("yt-dlp fallback search: %s", search_url)

    try:
        proc = subprocess.run(
            [yt_dlp, "--flat-playlist", "--dump-json", search_url],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.error("yt-dlp search failed: %s", exc)
        return [{"error": str(exc)}]

    if proc.returncode != 0:
        logger.error("yt-dlp search stderr: %s", proc.stderr[:500])
        return [{"error": f"yt-dlp exited with {proc.returncode}"}]

    results: list[dict] = []
    for line in proc.stdout.strip().splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        results.append({
            "video_id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "channel": entry.get("channel", entry.get("uploader", "")),
            "published_at": entry.get("upload_date", ""),
            "description": (entry.get("description") or "")[:200],
            "thumbnail": entry.get("thumbnail", ""),
        })
    return results
