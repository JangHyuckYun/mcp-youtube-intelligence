"""Tests for comment collection and summarization."""
import pytest
from unittest.mock import patch, MagicMock
from mcp_youtube_intelligence.core.comments import fetch_comments, summarize_comments


SAMPLE_COMMENTS = [
    {"comment_id": "1", "author": "Alice", "text": "Great video!", "like_count": 100},
    {"comment_id": "2", "author": "Bob", "text": "Very informative content", "like_count": 50},
    {"comment_id": "3", "author": "Charlie", "text": "I disagree with the premise", "like_count": 200},
    {"comment_id": "4", "author": "Diana", "text": "Thanks for sharing", "like_count": 10},
    {"comment_id": "5", "author": "Eve", "text": "First!", "like_count": 5},
]


class TestSummarizeComments:
    def test_empty_comments(self):
        result = summarize_comments([])
        assert result["count"] == 0

    def test_sorts_by_likes(self):
        result = summarize_comments(SAMPLE_COMMENTS, top_n=3)
        likes = [c["likes"] for c in result["top_comments"]]
        assert likes == sorted(likes, reverse=True)

    def test_respects_top_n(self):
        result = summarize_comments(SAMPLE_COMMENTS, top_n=2)
        assert len(result["top_comments"]) == 2

    def test_truncates_long_text(self):
        long_comment = [{"comment_id": "x", "author": "X", "text": "A" * 500, "like_count": 1}]
        result = summarize_comments(long_comment, top_n=1)
        assert len(result["top_comments"][0]["text"]) <= 200

    def test_count_reflects_total(self):
        result = summarize_comments(SAMPLE_COMMENTS, top_n=2)
        assert result["count"] == 5

    def test_top_comment_is_highest_likes(self):
        result = summarize_comments(SAMPLE_COMMENTS, top_n=1)
        assert result["top_comments"][0]["author"] == "Charlie"


class TestFetchComments:
    @patch("mcp_youtube_intelligence.core.comments.subprocess.run")
    def test_fetch_returns_list(self, mock_run):
        # Mock subprocess to return empty (no info.json found)
        mock_run.return_value = MagicMock(returncode=0)
        result = fetch_comments("test_id")
        assert isinstance(result, list)

    @patch("mcp_youtube_intelligence.core.comments.subprocess.run")
    def test_fetch_handles_timeout(self, mock_run):
        mock_run.side_effect = Exception("timeout")
        result = fetch_comments("test_id")
        assert result == []
