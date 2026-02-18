"""MCP server entrypoint for YouTube Intelligence."""
from __future__ import annotations

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from . import tools
from .config import Config
from .storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)

# Global state
_config: Config | None = None
_storage: SQLiteStorage | None = None


def _get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


async def _get_storage() -> SQLiteStorage:
    global _storage
    if _storage is None:
        cfg = _get_config()
        _storage = SQLiteStorage(cfg.sqlite_path)
        await _storage.initialize()
    return _storage


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("mcp-youtube-intelligence")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_video",
                description="Get video metadata + summary (~300 tokens). Provide a YouTube video ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "string", "description": "YouTube video ID (e.g. dQw4w9WgXcQ)"},
                    },
                    "required": ["video_id"],
                },
            ),
            Tool(
                name="get_transcript",
                description="Get video transcript. mode: 'summary' (default, ~300 tokens), 'full' (saves to file, returns path), 'chunks' (split into segments).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "string", "description": "YouTube video ID"},
                        "mode": {"type": "string", "enum": ["summary", "full", "chunks"], "default": "summary"},
                    },
                    "required": ["video_id"],
                },
            ),
            Tool(
                name="get_comments",
                description="Get top comments for a video. Optionally summarize them.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "string", "description": "YouTube video ID"},
                        "top_n": {"type": "integer", "default": 10, "description": "Number of top comments"},
                        "summarize": {"type": "boolean", "default": False, "description": "Return summarized view"},
                    },
                    "required": ["video_id"],
                },
            ),
            Tool(
                name="monitor_channel",
                description="Monitor a YouTube channel via RSS. action: 'add' (subscribe), 'check' (poll for new videos), 'list' (show subscriptions), 'remove' (unsubscribe).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_ref": {"type": "string", "description": "Channel URL, @handle, or ID"},
                        "action": {"type": "string", "enum": ["add", "check", "list", "remove"], "default": "check"},
                    },
                    "required": ["channel_ref"],
                },
            ),
            Tool(
                name="search_transcripts",
                description="Search stored transcripts by keyword. Returns matching snippets.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword or phrase"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="extract_entities",
                description="Extract structured entities (companies, indices, people, sectors, etc.) from a video transcript.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "string", "description": "YouTube video ID"},
                    },
                    "required": ["video_id"],
                },
            ),
            Tool(
                name="segment_topics",
                description="Segment a video transcript into topics based on transition markers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "string", "description": "YouTube video ID"},
                    },
                    "required": ["video_id"],
                },
            ),
            Tool(
                name="search_youtube",
                description="Search YouTube videos by keyword. Returns metadata list (~200 tokens).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword or phrase"},
                        "max_results": {"type": "integer", "default": 10, "description": "Max results (1-50)"},
                        "channel_id": {"type": "string", "description": "Limit search to a specific channel ID"},
                        "published_after": {"type": "string", "description": "Filter: published after (ISO 8601)"},
                        "order": {
                            "type": "string",
                            "enum": ["relevance", "date", "rating", "viewCount"],
                            "default": "relevance",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_playlist",
                description="Get playlist metadata and video list from a YouTube playlist.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {"type": "string", "description": "YouTube playlist ID (e.g. PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf)"},
                        "max_videos": {"type": "integer", "default": 50, "description": "Max videos to retrieve"},
                    },
                    "required": ["playlist_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        import json

        cfg = _get_config()
        storage = await _get_storage()
        kwargs = {"config": cfg, "storage": storage}

        handlers = {
            "get_video": lambda args: tools.get_video(args["video_id"], **kwargs),
            "get_transcript": lambda args: tools.get_transcript(
                args["video_id"], args.get("mode", "summary"), **kwargs
            ),
            "get_comments": lambda args: tools.get_comments(
                args["video_id"], args.get("top_n", 10), args.get("summarize", False), **kwargs
            ),
            "monitor_channel": lambda args: tools.monitor_channel(
                args["channel_ref"], args.get("action", "check"), **kwargs
            ),
            "search_transcripts": lambda args: tools.search_transcripts(
                args["query"], args.get("limit", 10), **kwargs
            ),
            "extract_entities": lambda args: tools.extract_entities_tool(args["video_id"], **kwargs),
            "segment_topics": lambda args: tools.segment_topics(args["video_id"], **kwargs),
            "search_youtube": lambda args: tools.search_youtube_tool(
                args["query"],
                args.get("max_results", 10),
                args.get("channel_id"),
                args.get("published_after"),
                args.get("order", "relevance"),
                **kwargs,
            ),
            "get_playlist": lambda args: tools.get_playlist_tool(
                args["playlist_id"], args.get("max_videos", 50), **kwargs
            ),
        }

        handler = handlers.get(name)
        if not handler:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        try:
            result = await handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


def main():
    """Entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    server = create_server()
    asyncio.run(_run(server))


async def _run(server: Server):
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
