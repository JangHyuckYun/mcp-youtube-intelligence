"""Structured report generation from video analysis."""
from __future__ import annotations

import logging
from typing import Optional

from ..config import Config
from . import collector, comments, entities, segmenter, summarizer, transcript

logger = logging.getLogger(__name__)


def _format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "N/A"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _estimate_segment_times(
    segments: list[dict], timed_segments: list[dict], total_duration: Optional[int]
) -> list[tuple[str, str]]:
    """Estimate start~end time for each topic segment."""
    n = len(segments)
    if not n:
        return []

    # If we have timed transcript segments, use char offsets to estimate
    if timed_segments and total_duration:
        total_chars = sum(s.get("char_count", len(s.get("text", ""))) for s in segments)
        if total_chars == 0:
            total_chars = 1
        cumulative = 0
        times = []
        for seg in segments:
            start_frac = cumulative / total_chars
            cumulative += seg.get("char_count", len(seg.get("text", "")))
            end_frac = cumulative / total_chars
            start_sec = start_frac * total_duration
            end_sec = end_frac * total_duration
            times.append((_format_timestamp(start_sec), _format_timestamp(end_sec)))
        return times

    # Fallback: evenly distribute
    if total_duration:
        chunk = total_duration / n
        return [
            (_format_timestamp(i * chunk), _format_timestamp((i + 1) * chunk))
            for i in range(n)
        ]

    return [("", "") for _ in range(n)]


def _group_entities(entity_list: list[dict]) -> dict[str, list[str]]:
    """Group entities by type."""
    groups: dict[str, list[str]] = {}
    for e in entity_list:
        t = e.get("type", "other")
        name = e.get("name", e.get("keyword", ""))
        if name and name not in groups.get(t, []):
            groups.setdefault(t, []).append(name)
    return groups


_TYPE_LABELS = {
    "person": "Person",
    "company": "Company",
    "technology": "Technology",
    "index": "Index",
    "sector": "Sector",
    "crypto": "Cryptocurrency",
    "language": "Programming Language",
    "framework": "Framework",
    "tool": "Tool",
    "platform": "Platform",
    "concept": "Concept",
}


async def generate_report(
    video_id: str,
    config: Optional[Config] = None,
    include_comments: bool = True,
    llm_provider: Optional[str] = None,
) -> str:
    """Generate a structured markdown report for a YouTube video.

    Args:
        video_id: YouTube video ID.
        config: Config for LLM access. If None, uses extractive summarization.
        include_comments: Whether to include comment analysis.
        llm_provider: LLM provider override for summarization.

    Returns:
        Markdown report string.
    """
    yt_dlp = config.yt_dlp_path if config else "yt-dlp"

    # 1. Metadata
    meta = collector.get_video_metadata(video_id, yt_dlp=yt_dlp)
    title = meta.get("title", video_id) if meta else video_id
    channel = meta.get("channel_name", "N/A") if meta else "N/A"
    duration_sec = meta.get("duration_seconds") if meta else None
    duration_str = _format_duration(duration_sec)

    # 2. Transcript
    tr = transcript.fetch_transcript(video_id)
    text = transcript.clean_transcript(tr.get("best", ""))
    lang = tr.get("lang", "N/A") or "N/A"
    timed_segs = tr.get("timed_segments", [])

    if not text:
        return f"# ⚠️ Report Generation Failed: {title}\n\nCould not retrieve transcript."

    # 3. Summary (async)
    if config:
        summary = await summarizer.summarize(text, config=config, provider=llm_provider)
    else:
        summary = transcript.summarize_extractive(text)

    # 4. Topic segments
    segments = segmenter.segment_topics(text)
    times = _estimate_segment_times(segments, timed_segs, duration_sec)

    # 5. Entities
    entity_list = entities.extract_entities(text)
    grouped = _group_entities(entity_list)

    # 6. Comments (optional, failure-tolerant)
    comment_section = ""
    if include_comments:
        try:
            max_c = config.max_comments if config else 30
            raw_comments = comments.fetch_comments(video_id, max_comments=max_c, yt_dlp=yt_dlp)
            if raw_comments:
                cs = comments.summarize_comments(raw_comments)
                ratio = cs.get("sentiment_ratio", {})
                pos = int(ratio.get("positive", 0) * 100)
                neg = int(ratio.get("negative", 0) * 100)
                neu = int(ratio.get("neutral", 0) * 100)
                top_c = cs.get("top_comments", [])
                top_opinions = "\n".join(
                    f"  - **{c.get('author', '?')}** ({c.get('sentiment', '?')}, 👍{c.get('likes', 0)}): {c.get('text', '')}"
                    for c in top_c[:5]
                )
                comment_section = (
                    f"## 5. Viewer Reactions\n\n"
                    f"- Total comments: {cs.get('count', 0)}\n"
                    f"- Sentiment: Positive {pos}% / Negative {neg}% / Neutral {neu}%\n"
                    f"- Top opinions:\n{top_opinions}\n"
                )
            else:
                comment_section = "## 5. Viewer Reactions\n\n- No comments\n"
        except Exception as e:
            logger.warning("Comment fetch failed: %s", e)
            comment_section = "## 5. Viewer Reactions\n\n- Comments unavailable\n"

    # Build report
    lines = [
        f"# 📹 Video Analysis Report: {title}\n",
        f"> Channel: {channel} | Duration: {duration_str} | Language: {lang}\n",
        "## 📑 Table of Contents\n",
        "1. [Summary](#summary)",
        "2. [Key Topics](#key-topics)",
        "3. [Detailed Analysis](#detailed-analysis)",
        "4. [Keywords & Entities](#keywords--entities)",
        "5. [Viewer Reactions](#viewer-reactions)\n",
        "---\n",
        f"## 1. Summary\n\n{summary}\n",
    ]

    # Topics table
    lines.append("## 2. Key Topics\n")
    lines.append("| # | Topic | Keywords | Timespan |")
    lines.append("|---|-------|----------|----------|")
    for i, seg in enumerate(segments):
        topic = seg.get("topic", "")
        start, end = times[i] if i < len(times) else ("", "")
        time_range = f"{start}~{end}" if start else ""
        lines.append(f"| {i+1} | {topic} | {topic} | {time_range} |")
    lines.append("")

    # Detailed analysis
    lines.append("## 3. Detailed Analysis\n")
    for i, seg in enumerate(segments):
        topic = seg.get("topic", f"Segment {i+1}")
        preview = seg.get("text", "")[:500]
        lines.append(f"### Topic {i+1}: {topic}\n")
        lines.append(f"{preview}\n")

    # Entities
    lines.append("## 4. Keywords & Entities\n")
    if grouped:
        for etype, names in grouped.items():
            label = _TYPE_LABELS.get(etype, etype)
            lines.append(f"- **{label}**: {', '.join(names[:10])}")
    else:
        lines.append("- (No entities extracted)")
    lines.append("")

    # Comments
    if include_comments:
        lines.append(comment_section)
    else:
        lines.append("## 5. Viewer Reactions\n\n- (Comment analysis excluded)\n")

    return "\n".join(lines)
