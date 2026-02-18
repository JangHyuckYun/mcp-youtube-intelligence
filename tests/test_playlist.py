"""Tests for core.playlist module."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from mcp_youtube_intelligence.core.playlist import get_playlist


def _make_playlist_output(n: int = 3) -> str:
    entries = []
    for i in range(n):
        entries.append(json.dumps({
            "id": f"vid{i}",
            "title": f"Video {i}",
            "duration": 300 + i * 60,
            "playlist_title": "My Playlist",
        }))
    return "\n".join(entries)


@pytest.mark.asyncio
@patch("mcp_youtube_intelligence.core.playlist.subprocess.run")
async def test_get_playlist_basic(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=_make_playlist_output(3),
        stderr="",
    )
    result = await get_playlist("PLtest123")
    assert result["playlist_id"] == "PLtest123"
    assert result["title"] == "My Playlist"
    assert result["video_count"] == 3
    assert result["videos"][0]["video_id"] == "vid0"
    assert result["videos"][1]["duration"] == 360


@pytest.mark.asyncio
@patch("mcp_youtube_intelligence.core.playlist.subprocess.run")
async def test_get_playlist_error(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not found")
    result = await get_playlist("PLbad")
    assert "error" in result


@pytest.mark.asyncio
@patch("mcp_youtube_intelligence.core.playlist.subprocess.run")
async def test_get_playlist_timeout(mock_run):
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 120)
    result = await get_playlist("PLtimeout")
    assert "error" in result
