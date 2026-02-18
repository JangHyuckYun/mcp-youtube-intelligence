"""Tests for core.search module."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_youtube_intelligence.core.search import search_youtube, _search_ytdlp


# ---- yt-dlp fallback tests ----

def _make_ytdlp_output(n: int = 2) -> str:
    entries = []
    for i in range(n):
        entries.append(json.dumps({
            "id": f"vid{i}",
            "title": f"Title {i}",
            "channel": f"Channel {i}",
            "upload_date": "20240101",
            "description": "desc",
            "thumbnail": "https://img.youtube.com/vi/vid0/default.jpg",
        }))
    return "\n".join(entries)


@patch("mcp_youtube_intelligence.core.search.subprocess.run")
def test_search_ytdlp_basic(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=_make_ytdlp_output(3),
        stderr="",
    )
    results = _search_ytdlp("test query", max_results=3, yt_dlp="yt-dlp")
    assert len(results) == 3
    assert results[0]["video_id"] == "vid0"
    assert results[0]["title"] == "Title 0"
    mock_run.assert_called_once()


@patch("mcp_youtube_intelligence.core.search.subprocess.run")
def test_search_ytdlp_error(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
    results = _search_ytdlp("fail", max_results=5, yt_dlp="yt-dlp")
    assert len(results) == 1
    assert "error" in results[0]


# ---- search_youtube dispatcher tests ----

@pytest.mark.asyncio
@patch("mcp_youtube_intelligence.core.search._search_ytdlp")
async def test_search_youtube_no_api_key(mock_fallback):
    mock_fallback.return_value = [{"video_id": "abc", "title": "Test"}]
    results = await search_youtube("test", api_key="")
    mock_fallback.assert_called_once()
    assert results[0]["video_id"] == "abc"


@pytest.mark.asyncio
@patch("mcp_youtube_intelligence.core.search._search_api")
async def test_search_youtube_with_api_key(mock_api):
    mock_api.return_value = [{"video_id": "xyz", "title": "API Result"}]
    results = await search_youtube("test", api_key="fake-key")
    mock_api.assert_called_once()
    assert results[0]["video_id"] == "xyz"
