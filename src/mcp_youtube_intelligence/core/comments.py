"""Comment collection via yt-dlp."""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def fetch_comments(video_id: str, max_comments: int = 20, yt_dlp: str = "yt-dlp") -> list[dict]:
    """Fetch top comments for a video using yt-dlp."""
    comments = []
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                [yt_dlp, "--write-comments",
                 "--extractor-args", f"youtube:comment_sort=top;max_comments={max_comments}",
                 "--skip-download", "--write-info-json",
                 "-o", f"{tmpdir}/%(id)s.%(ext)s",
                 f"https://www.youtube.com/watch?v={video_id}"],
                capture_output=True, text=True, timeout=60,
            )
            info_files = list(Path(tmpdir).glob("*.info.json"))
            if info_files:
                data = json.loads(info_files[0].read_text())
                for c in (data.get("comments") or [])[:max_comments]:
                    comments.append({
                        "comment_id": c.get("id", ""),
                        "author": c.get("author", ""),
                        "text": c.get("text", ""),
                        "like_count": c.get("like_count", 0),
                    })
    except Exception as e:
        logger.debug("Comment fetch error for %s: %s", video_id, e)
    return comments


def summarize_comments(comments: list[dict], top_n: int = 5) -> dict:
    """Return a compact summary of comments."""
    if not comments:
        return {"count": 0, "top_comments": [], "themes": "No comments available."}
    sorted_c = sorted(comments, key=lambda c: c.get("like_count", 0), reverse=True)
    top = sorted_c[:top_n]
    return {
        "count": len(comments),
        "top_comments": [
            {"author": c["author"], "text": c["text"][:200], "likes": c.get("like_count", 0)}
            for c in top
        ],
    }
