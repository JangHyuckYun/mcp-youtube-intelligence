"""Comment collection via yt-dlp with noise filtering and sentiment analysis."""
from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# --- Sentiment keyword lists ---
_POSITIVE_KW = {
    # Korean
    "좋아요", "감사", "최고", "대박", "잘했", "응원", "축하", "멋지", "훌륭", "사랑",
    "기대", "재밌", "유익", "도움", "감동", "행복", "좋다", "좋은", "좋아",
    # English
    "love", "great", "amazing", "thanks", "thank", "awesome", "excellent",
    "wonderful", "fantastic", "good", "best", "perfect", "helpful", "brilliant",
}
_NEGATIVE_KW = {
    # Korean
    "별로", "싫어", "최악", "실망", "짜증", "화나", "나쁜", "나쁘", "못했", "안됨",
    "쓰레기", "거짓", "사기", "불만", "지루", "재미없", "별로",
    # English
    "hate", "terrible", "worst", "disappointed", "boring", "bad", "awful",
    "horrible", "trash", "garbage", "waste", "dislike", "annoying", "stupid",
}

# Spam / noise patterns
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_REPEAT_CHAR_RE = re.compile(r"(.)\1{4,}")
_EMOJI_ONLY_RE = re.compile(
    r"^[\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
    r"\U0000200D\U00002640-\U00002642\U00002600-\U000026FF\U0000231A-\U0000231B"
    r"\U00002934-\U00002935\U000025AA-\U000025FE\U000023E9-\U000023F3]+$"
)
_SUB_SPAM_RE = re.compile(
    r"(구독|좋아요\s*눌러|subscribe|sub\s*4\s*sub|check\s*my\s*channel)", re.IGNORECASE
)


def _is_noise(text: str) -> bool:
    """Return True if comment is noise (too short, emoji-only, spam)."""
    stripped = text.strip()
    if len(stripped) < 5:
        return True
    if _EMOJI_ONLY_RE.match(stripped):
        return True
    if _REPEAT_CHAR_RE.search(stripped):
        return True
    # URL-heavy spam: more than 2 URLs
    if len(_URL_RE.findall(stripped)) > 2:
        return True
    if _SUB_SPAM_RE.search(stripped):
        return True
    return False


def _analyze_sentiment(text: str) -> str:
    """Lightweight keyword-based sentiment analysis.

    Returns "positive", "negative", or "neutral".
    """
    lower = text.lower()
    pos = sum(1 for kw in _POSITIVE_KW if kw in lower)
    neg = sum(1 for kw in _NEGATIVE_KW if kw in lower)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def fetch_comments(
    video_id: str,
    max_comments: int = 30,
    sort: str = "top",
    sentiment: str = "all",
    filter_noise: bool = True,
    yt_dlp: str = "yt-dlp",
) -> list[dict]:
    """Fetch comments for a video using yt-dlp.

    Args:
        video_id: YouTube video ID.
        max_comments: Maximum number of comments to fetch.
        sort: "top" (like-sorted, default) or "newest".
        sentiment: Filter by sentiment — "all", "positive", "negative".
        filter_noise: If True, remove short/spam/emoji-only comments.
        yt_dlp: Path to yt-dlp binary.

    Returns:
        List of comment dicts with keys: comment_id, author, text, like_count, sentiment.
    """
    sort_arg = "new" if sort == "newest" else "top"
    # Fetch extra to compensate for noise filtering
    fetch_count = max_comments * 3 if filter_noise else max_comments

    comments: list[dict] = []
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                [yt_dlp, "--write-comments",
                 "--extractor-args", f"youtube:comment_sort={sort_arg};max_comments={fetch_count}",
                 "--skip-download", "--write-info-json",
                 "-o", f"{tmpdir}/%(id)s.%(ext)s",
                 f"https://www.youtube.com/watch?v={video_id}"],
                capture_output=True, text=True, timeout=90,
            )
            info_files = list(Path(tmpdir).glob("*.info.json"))
            if info_files:
                data = json.loads(info_files[0].read_text())
                for c in data.get("comments") or []:
                    text = c.get("text", "")
                    if filter_noise and _is_noise(text):
                        continue
                    sent = _analyze_sentiment(text)
                    if sentiment != "all" and sent != sentiment:
                        continue
                    comments.append({
                        "comment_id": c.get("id", ""),
                        "author": c.get("author", ""),
                        "text": text,
                        "like_count": c.get("like_count", 0),
                        "sentiment": sent,
                    })
                    if len(comments) >= max_comments:
                        break
    except Exception as e:
        logger.debug("Comment fetch error for %s: %s", video_id, e)
    return comments


def summarize_comments(comments: list[dict], top_n: int = 5) -> dict:
    """Return a compact summary of comments with sentiment stats and keywords."""
    if not comments:
        return {"count": 0, "top_comments": [], "sentiment_ratio": {}, "top_keywords": []}

    # Sentiment ratio
    sentiments = [c.get("sentiment", _analyze_sentiment(c.get("text", ""))) for c in comments]
    total = len(sentiments)
    ratio = {
        "positive": round(sentiments.count("positive") / total, 3),
        "negative": round(sentiments.count("negative") / total, 3),
        "neutral": round(sentiments.count("neutral") / total, 3),
    }

    # Top comments by likes
    sorted_c = sorted(comments, key=lambda c: c.get("like_count", 0), reverse=True)
    top = sorted_c[:top_n]

    # Keyword extraction (simple Counter on words >= 2 chars)
    word_counter: Counter[str] = Counter()
    for c in comments:
        words = re.findall(r"[\w가-힣]{2,}", c.get("text", ""))
        word_counter.update(w.lower() for w in words)
    # Remove very common stop-like words
    for stop in ("the", "is", "it", "to", "and", "of", "in", "that", "this", "for", "are", "was"):
        word_counter.pop(stop, None)
    top_keywords = [{"word": w, "count": cnt} for w, cnt in word_counter.most_common(15)]

    return {
        "count": total,
        "sentiment_ratio": ratio,
        "top_comments": [
            {"author": c.get("author", ""), "text": c.get("text", "")[:200],
             "likes": c.get("like_count", 0), "sentiment": c.get("sentiment", "neutral")}
            for c in top
        ],
        "top_keywords": top_keywords,
    }
