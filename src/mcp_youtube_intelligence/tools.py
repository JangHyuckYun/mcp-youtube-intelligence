"""MCP tool definitions — 7 tools for YouTube intelligence."""
from __future__ import annotations

import json
import logging
from typing import Any

from .config import Config
from .core import collector, comments, transcript, monitor, segmenter, entities, summarizer, search, playlist
from .storage.base import BaseStorage

logger = logging.getLogger(__name__)


async def get_video(video_id: str, *, config: Config, storage: BaseStorage) -> dict:
    """Get video metadata + summary (~300 tokens). Collects if not cached."""
    # Check cache first
    cached = await storage.get_video(video_id)
    if cached and cached.get("status") == "done":
        return _compact_video(cached)

    # Fetch metadata
    meta = collector.get_video_metadata(video_id, yt_dlp=config.yt_dlp_path)
    if not meta:
        return {"error": f"Could not fetch metadata for {video_id}"}

    # Fetch transcript
    tr = transcript.fetch_transcript(video_id)
    cleaned = transcript.clean_transcript(tr.get("best", ""))

    # Summarize
    summary = await summarizer.summarize(cleaned, api_key=config.openai_api_key, model=config.openai_model)

    # Save to storage
    await storage.upsert_video({
        "video_id": video_id,
        **meta,
        "transcript_text": cleaned,
        "transcript_lang": tr.get("lang"),
        "transcript_length": len(cleaned),
        "summary": summary,
        "status": "done",
    })

    result = {**meta, "summary": summary, "transcript_length": len(cleaned)}
    # Strip heavy fields
    result.pop("description", None)
    return result


async def get_transcript(
    video_id: str, mode: str = "summary", *, config: Config, storage: BaseStorage
) -> dict:
    """Get transcript. mode: summary (default), full (file path), chunks (segmented)."""
    cached = await storage.get_video(video_id)
    text = None
    if cached:
        text = cached.get("transcript_text")

    if not text:
        tr = transcript.fetch_transcript(video_id)
        text = transcript.clean_transcript(tr.get("best", ""))
        if text:
            await storage.upsert_video({
                "video_id": video_id,
                "transcript_text": text,
                "transcript_lang": tr.get("lang"),
                "transcript_length": len(text),
            })

    if not text:
        return {"error": f"No transcript available for {video_id}"}

    if mode == "full":
        path = transcript.save_transcript_file(video_id, text, config.transcript_dir)
        return {"video_id": video_id, "mode": "full", "file_path": path, "char_count": len(text)}
    elif mode == "chunks":
        chunks = transcript.make_chunks(text)
        return {"video_id": video_id, "mode": "chunks", "chunk_count": len(chunks), "chunks": chunks}
    else:  # summary
        summary = await summarizer.summarize(text, api_key=config.openai_api_key, model=config.openai_model)
        return {"video_id": video_id, "mode": "summary", "summary": summary, "char_count": len(text)}


async def get_comments(
    video_id: str, top_n: int = 10, summarize: bool = False,
    sort: str = "top", sentiment: str = "all", filter_noise: bool = True,
    *, config: Config, storage: BaseStorage
) -> dict:
    """Get top N comments, optionally summarized.

    Args:
        sort: "top" (likes) or "newest".
        sentiment: "all", "positive", or "negative".
        filter_noise: Remove spam/short/emoji-only comments.
    """
    raw = comments.fetch_comments(
        video_id,
        max_comments=config.max_comments,
        sort=sort,
        sentiment=sentiment,
        filter_noise=filter_noise,
        yt_dlp=config.yt_dlp_path,
    )
    if raw:
        await storage.save_comments(video_id, raw)

    result_comments = raw[:top_n]

    if summarize:
        return comments.summarize_comments(result_comments, top_n=top_n)

    comment_list = [
        {"author": c.get("author", ""), "text": c.get("text", ""),
         "likes": c.get("like_count", 0), "sentiment": c.get("sentiment", "neutral")}
        for c in result_comments
    ]
    return {"video_id": video_id, "count": len(comment_list), "comments": comment_list}


async def monitor_channel(
    channel_ref: str, action: str = "check",
    *, config: Config, storage: BaseStorage
) -> dict:
    """Monitor a YouTube channel. action: add, check, list, remove."""
    if action == "add":
        info = collector.get_channel_info(channel_ref, yt_dlp=config.yt_dlp_path)
        await storage.upsert_channel({
            "channel_id": info["channel_id"],
            "channel_name": info["channel_name"],
            "channel_url": info["channel_url"],
            "enabled": 1,
        })
        return {"action": "added", **info}

    elif action == "check":
        # Resolve channel_id
        ch = await storage.get_channel(channel_ref)
        if not ch:
            # Try to resolve
            info = collector.get_channel_info(channel_ref, yt_dlp=config.yt_dlp_path)
            channel_id = info["channel_id"]
        else:
            channel_id = ch["channel_id"]
        new_videos = await monitor.check_channel_new_videos(channel_id, storage)
        return {"channel_id": channel_id, "new_videos": new_videos}

    elif action == "list":
        channels = await storage.list_channels()
        return {"channels": channels}

    elif action == "remove":
        ch = await storage.get_channel(channel_ref)
        if ch:
            await storage.upsert_channel({"channel_id": ch["channel_id"], "enabled": 0})
            return {"action": "removed", "channel_id": ch["channel_id"]}
        return {"error": f"Channel {channel_ref} not found"}

    return {"error": f"Unknown action: {action}"}


async def search_transcripts(
    query: str, limit: int = 10, *, config: Config, storage: BaseStorage
) -> dict:
    """Search stored transcripts by keyword. Returns snippets."""
    results = await storage.search_transcripts(query, limit=limit)
    return {"query": query, "count": len(results), "results": results}


async def extract_entities_tool(
    video_id: str, *, config: Config, storage: BaseStorage
) -> dict:
    """Extract entities from a video's transcript."""
    cached = await storage.get_video(video_id)
    text = cached.get("transcript_text") if cached else None

    if not text:
        tr = transcript.fetch_transcript(video_id)
        text = transcript.clean_transcript(tr.get("best", ""))

    if not text:
        return {"error": f"No transcript available for {video_id}"}

    found = entities.extract_entities(text)
    return {"video_id": video_id, "entity_count": len(found), "entities": found}


async def segment_topics(
    video_id: str, *, config: Config, storage: BaseStorage
) -> dict:
    """Segment a video transcript into topics."""
    cached = await storage.get_video(video_id)
    text = cached.get("transcript_text") if cached else None

    if not text:
        tr = transcript.fetch_transcript(video_id)
        text = transcript.clean_transcript(tr.get("best", ""))

    if not text:
        return {"error": f"No transcript available for {video_id}"}

    segments = segmenter.segment_topics(text)
    # Return without full text for token efficiency
    compact = [{"segment": s["segment"], "char_count": s["char_count"], "preview": s["text"][:200]} for s in segments]
    return {"video_id": video_id, "segment_count": len(compact), "segments": compact}


async def search_youtube_tool(
    query: str,
    max_results: int = 10,
    channel_id: str | None = None,
    published_after: str | None = None,
    order: str = "relevance",
    *,
    config: Config,
    storage: BaseStorage,
) -> dict:
    """Search YouTube videos by keyword. Returns metadata list (~200 tokens)."""
    results = await search.search_youtube(
        query,
        max_results=max_results,
        channel_id=channel_id,
        published_after=published_after,
        order=order,
        api_key=config.youtube_api_key,
        yt_dlp=config.yt_dlp_path,
    )
    return {"query": query, "count": len(results), "results": results}


async def get_playlist_tool(
    playlist_id: str,
    max_videos: int = 50,
    *,
    config: Config,
    storage: BaseStorage,
) -> dict:
    """Get playlist metadata and video list."""
    return await playlist.get_playlist(
        playlist_id,
        max_videos=max_videos,
        yt_dlp=config.yt_dlp_path,
    )


async def batch_get_videos(
    video_ids: list[str], *, config: Config, storage: BaseStorage
) -> dict:
    """Process multiple videos in batch. Returns list of results."""
    results = []
    for vid in video_ids:
        try:
            r = await get_video(vid, config=config, storage=storage)
            results.append(r)
        except Exception as e:
            results.append({"video_id": vid, "error": str(e)})
    return {"count": len(results), "results": results}


async def batch_get_transcripts(
    video_ids: list[str], mode: str = "summary", *, config: Config, storage: BaseStorage
) -> dict:
    """Get transcripts for multiple videos in batch."""
    results = []
    for vid in video_ids:
        try:
            r = await get_transcript(vid, mode=mode, config=config, storage=storage)
            results.append(r)
        except Exception as e:
            results.append({"video_id": vid, "error": str(e)})
    return {"count": len(results), "results": results}


def _compact_video(data: dict) -> dict:
    """Strip heavy fields from a video record for token efficiency."""
    exclude = {"transcript_text", "description"}
    return {k: v for k, v in data.items() if k not in exclude and v is not None}
