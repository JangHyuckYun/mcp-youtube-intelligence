"""Tests for channel monitor with RSS fallback."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from mcp_youtube_intelligence.core.monitor import fetch_channel_feed, _fetch_channel_ytdlp


class TestFetchChannelFeed:
    @patch("mcp_youtube_intelligence.core.monitor.feedparser.parse")
    def test_successful_rss(self, mock_parse):
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                {"yt_videoid": "abc123", "title": "Test Video", "published": "2024-01-01", "link": "https://youtube.com/watch?v=abc123"},
            ],
        )
        result = fetch_channel_feed("UCtest")
        assert len(result) == 1
        assert result[0]["video_id"] == "abc123"

    @patch("mcp_youtube_intelligence.core.monitor._fetch_channel_ytdlp")
    @patch("mcp_youtube_intelligence.core.monitor.feedparser.parse")
    def test_rss_failure_falls_back_to_ytdlp(self, mock_parse, mock_ytdlp):
        mock_parse.side_effect = Exception("Network error")
        mock_ytdlp.return_value = [{"video_id": "fallback1", "title": "Fallback", "published": "", "link": ""}]
        result = fetch_channel_feed("UCtest")
        assert len(result) == 1
        assert result[0]["video_id"] == "fallback1"
        mock_ytdlp.assert_called_once()

    @patch("mcp_youtube_intelligence.core.monitor._fetch_channel_ytdlp")
    @patch("mcp_youtube_intelligence.core.monitor.feedparser.parse")
    def test_empty_rss_falls_back(self, mock_parse, mock_ytdlp):
        """Empty RSS feed should trigger yt-dlp fallback."""
        mock_parse.return_value = MagicMock(bozo=False, entries=[])
        mock_ytdlp.return_value = []
        result = fetch_channel_feed("UCtest")
        assert isinstance(result, list)
        mock_ytdlp.assert_called_once()


class TestFetchChannelYtdlp:
    @patch("mcp_youtube_intelligence.core.monitor.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="vid1\nTitle 1\nvid2\nTitle 2\n",
        )
        result = _fetch_channel_ytdlp("UCtest", max_videos=5)
        assert len(result) == 2
        assert result[0]["video_id"] == "vid1"
        assert result[0]["title"] == "Title 1"

    @patch("mcp_youtube_intelligence.core.monitor.subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = _fetch_channel_ytdlp("UCtest")
        assert result == []

    @patch("mcp_youtube_intelligence.core.monitor.subprocess.run")
    def test_exception(self, mock_run):
        mock_run.side_effect = Exception("timeout")
        result = _fetch_channel_ytdlp("UCtest")
        assert result == []
