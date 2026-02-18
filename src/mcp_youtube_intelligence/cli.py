"""CLI interface for mcp-youtube-intelligence.

Usage: mcp-yt <command> [options]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from typing import Any


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from a YouTube URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, url_or_id)
        if m:
            return m.group(1)
    # If it looks like a bare ID (11 chars, valid chars)
    if re.fullmatch(r'[a-zA-Z0-9_-]{11}', url_or_id):
        return url_or_id
    return url_or_id


def extract_playlist_id(url_or_id: str) -> str:
    """Extract playlist ID from URL or return as-is."""
    m = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url_or_id)
    if m:
        return m.group(1)
    return url_or_id


async def _get_storage_and_config():
    """Create config and storage for CLI use."""
    from .config import Config
    from .storage.sqlite import SQLiteStorage as SqliteStorage

    config = Config.from_env()
    storage = SqliteStorage(config.sqlite_path)
    await storage.initialize()
    return config, storage


def _print_result(data: Any, as_json: bool = False, output_file: str | None = None):
    """Print result in human-readable or JSON format."""
    if as_json:
        text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    else:
        text = _format_human(data)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Output saved to {output_file}")
    else:
        print(text)


def _format_human(data: Any, indent: int = 0) -> str:
    """Format data for human reading."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        if "error" in data:
            return f"Error: {data['error']}"
        lines = []
        for k, v in data.items():
            prefix = "  " * indent
            if isinstance(v, list):
                lines.append(f"{prefix}{k}: ({len(v)} items)")
                for i, item in enumerate(v):
                    lines.append(f"{prefix}  [{i+1}] {_format_human(item, indent+2)}")
            elif isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(_format_human(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
    if isinstance(data, list):
        return "\n".join(f"[{i+1}] {_format_human(item, indent+1)}" for i, item in enumerate(data))
    return str(data)


# ── Command handlers ──

async def cmd_transcript(args):
    from .tools import get_transcript
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        provider = getattr(args, 'provider', None)
        result = await get_transcript(video_id, mode=args.mode, llm_provider=provider, config=config, storage=storage)
        _print_result(result, as_json=args.json, output_file=args.output)
    finally:
        await storage.close()


async def cmd_search(args):
    from .tools import search_youtube_tool
    config, storage = await _get_storage_and_config()
    try:
        result = await search_youtube_tool(
            args.query,
            max_results=args.max,
            channel_id=args.channel,
            order=args.order,
            config=config,
            storage=storage,
        )
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_video(args):
    from .tools import get_video
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        result = await get_video(video_id, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_comments(args):
    from .tools import get_comments
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        result = await get_comments(
            video_id,
            top_n=args.max,
            sort=args.sort,
            sentiment=args.sentiment,
            filter_noise=not args.no_filter,
            config=config,
            storage=storage,
        )
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_monitor(args):
    from .tools import monitor_channel
    config, storage = await _get_storage_and_config()
    try:
        if args.monitor_action == "subscribe":
            result = await monitor_channel(args.url_or_handle, action="add", config=config, storage=storage)
        elif args.monitor_action == "check":
            if not args.channel:
                print("Error: --channel is required for 'check' action", file=sys.stderr)
                sys.exit(1)
            result = await monitor_channel(args.channel, action="check", config=config, storage=storage)
        elif args.monitor_action == "list":
            result = await monitor_channel("", action="list", config=config, storage=storage)
        else:
            print(f"Error: Unknown monitor action '{args.monitor_action}'", file=sys.stderr)
            sys.exit(1)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_entities(args):
    from .tools import extract_entities_tool
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        result = await extract_entities_tool(video_id, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_segments(args):
    from .tools import segment_topics
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        result = await segment_topics(video_id, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_search_transcripts(args):
    from .tools import search_transcripts
    config, storage = await _get_storage_and_config()
    try:
        result = await search_transcripts(args.query, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_playlist(args):
    from .tools import get_playlist_tool
    config, storage = await _get_storage_and_config()
    try:
        playlist_id = extract_playlist_id(args.playlist_id_or_url)
        result = await get_playlist_tool(playlist_id, max_videos=args.max, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


async def cmd_report(args):
    from .tools import generate_report
    config, storage = await _get_storage_and_config()
    try:
        video_id = extract_video_id(args.url_or_id)
        provider = getattr(args, 'provider', None)
        include_comments = not getattr(args, 'no_comments', False)
        result = await generate_report(
            video_id,
            include_comments=include_comments,
            llm_provider=provider,
            config=config,
            storage=storage,
        )
        md = result.get("report", "")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Report saved to {args.output}")
        else:
            print(md)
    finally:
        await storage.close()


async def cmd_batch(args):
    from .tools import batch_get_transcripts
    config, storage = await _get_storage_and_config()
    try:
        video_ids = [extract_video_id(v) for v in args.ids]
        result = await batch_get_transcripts(video_ids, mode=args.mode, config=config, storage=storage)
        _print_result(result, as_json=args.json)
    finally:
        await storage.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="mcp-yt",
        description="YouTube Intelligence CLI — transcripts, search, comments, and more.",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # transcript
    p = subparsers.add_parser("transcript", help="Extract video transcript")
    p.add_argument("url_or_id", help="YouTube URL or video ID")
    p.add_argument("--mode", choices=["summary", "full", "chunks"], default="summary")
    p.add_argument("--chunk", type=int, help="Specific chunk number (with --mode chunks)")
    p.add_argument("--output", "-o", help="Save output to file")
    p.add_argument("--provider", choices=["auto", "openai", "anthropic", "google", "ollama", "vllm", "lmstudio"], default=None,
                   help="LLM provider for summary mode (default: auto)")

    # search
    p = subparsers.add_parser("search", help="Search YouTube videos")
    p.add_argument("query", help="Search query")
    p.add_argument("--max", type=int, default=10, help="Max results (default: 10)")
    p.add_argument("--channel", help="Filter by channel ID")
    p.add_argument("--order", choices=["relevance", "date", "rating", "viewCount"], default="relevance")

    # video
    p = subparsers.add_parser("video", help="Get video metadata and summary")
    p.add_argument("url_or_id", help="YouTube URL or video ID")

    # comments
    p = subparsers.add_parser("comments", help="Get video comments")
    p.add_argument("url_or_id", help="YouTube URL or video ID")
    p.add_argument("--max", type=int, default=10, help="Max comments (default: 10)")
    p.add_argument("--sort", choices=["top", "newest"], default="top")
    p.add_argument("--sentiment", choices=["all", "positive", "negative"], default="all")
    p.add_argument("--no-filter", action="store_true", help="Don't filter spam/noise")

    # monitor
    p = subparsers.add_parser("monitor", help="Monitor YouTube channels")
    monitor_sub = p.add_subparsers(dest="monitor_action")
    ps = monitor_sub.add_parser("subscribe", help="Subscribe to a channel")
    ps.add_argument("url_or_handle", help="Channel URL, @handle, or ID")
    ps = monitor_sub.add_parser("check", help="Check for new videos")
    ps.add_argument("--channel", help="Channel ID to check")
    monitor_sub.add_parser("list", help="List monitored channels")

    # entities
    p = subparsers.add_parser("entities", help="Extract entities from transcript")
    p.add_argument("url_or_id", help="YouTube URL or video ID")

    # segments
    p = subparsers.add_parser("segments", help="Segment transcript into topics")
    p.add_argument("url_or_id", help="YouTube URL or video ID")

    # search-transcripts
    p = subparsers.add_parser("search-transcripts", help="Search stored transcripts")
    p.add_argument("query", help="Search query")
    p.add_argument("--channel", help="Filter by channel ID")

    # playlist
    p = subparsers.add_parser("playlist", help="Get playlist info and videos")
    p.add_argument("playlist_id_or_url", help="Playlist ID or URL")
    p.add_argument("--max", type=int, default=50, help="Max videos (default: 50)")

    # report
    p = subparsers.add_parser("report", help="Generate structured analysis report")
    p.add_argument("url_or_id", help="YouTube URL or video ID")
    p.add_argument("--no-comments", action="store_true", help="Exclude comment analysis")
    p.add_argument("--output", "-o", help="Save report to file")
    p.add_argument("--provider", choices=["auto", "openai", "anthropic", "google", "ollama", "vllm", "lmstudio"], default=None,
                   help="LLM provider for summary")

    # batch
    p = subparsers.add_parser("batch", help="Process multiple videos")
    p.add_argument("ids", nargs="+", help="Video IDs or URLs")
    p.add_argument("--mode", choices=["summary", "full"], default="summary")

    return parser


_COMMAND_MAP = {
    "transcript": cmd_transcript,
    "search": cmd_search,
    "video": cmd_video,
    "comments": cmd_comments,
    "monitor": cmd_monitor,
    "entities": cmd_entities,
    "segments": cmd_segments,
    "search-transcripts": cmd_search_transcripts,
    "playlist": cmd_playlist,
    "report": cmd_report,
    "batch": cmd_batch,
}


def main():
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _COMMAND_MAP.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    try:
        asyncio.run(handler(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
