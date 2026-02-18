"""Tests for comment collection and summarization."""
import pytest
from unittest.mock import patch, MagicMock
from mcp_youtube_intelligence.core.comments import (
    fetch_comments, summarize_comments, _analyze_sentiment, _count_emoji_sentiment,
)


SAMPLE_COMMENTS = [
    {"comment_id": "1", "author": "Alice", "text": "Great video!", "like_count": 100},
    {"comment_id": "2", "author": "Bob", "text": "Very informative content", "like_count": 50},
    {"comment_id": "3", "author": "Charlie", "text": "I disagree with the premise", "like_count": 200},
    {"comment_id": "4", "author": "Diana", "text": "Thanks for sharing", "like_count": 10},
    {"comment_id": "5", "author": "Eve", "text": "First!", "like_count": 5},
]


class TestSentimentAnalysis:
    def test_positive_english(self):
        assert _analyze_sentiment("This is awesome and amazing!") == "positive"

    def test_negative_english(self):
        assert _analyze_sentiment("This is terrible and boring") == "negative"

    def test_neutral(self):
        assert _analyze_sentiment("The video is 10 minutes long") == "neutral"

    def test_positive_korean(self):
        assert _analyze_sentiment("정말 유익한 명강의입니다") == "positive"

    def test_negative_korean(self):
        assert _analyze_sentiment("너무 지루하고 시간낭비") == "negative"

    def test_emoji_positive(self):
        assert _analyze_sentiment("🔥🔥🔥👍") == "positive"

    def test_emoji_negative(self):
        assert _analyze_sentiment("😡👎💩") == "negative"

    def test_mixed_emoji_keywords(self):
        # Positive keyword + negative emoji — should balance
        result = _analyze_sentiment("great video 😡😡😡")
        assert result == "negative"  # 1 pos kw vs 1.5 neg emoji

    def test_expanded_english_positive(self):
        assert _analyze_sentiment("mind-blowing game-changer 10/10") == "positive"

    def test_expanded_english_negative(self):
        assert _analyze_sentiment("clickbait misleading waste of time") == "negative"

    def test_expanded_korean_positive(self):
        assert _analyze_sentiment("갓 레전드 꿀팁") == "positive"

    def test_negation_not_good(self):
        """'not good' should be negative, not positive."""
        assert _analyze_sentiment("This is not good at all") == "negative"

    def test_negation_dont_like(self):
        assert _analyze_sentiment("I don't love this video") == "negative"

    def test_negation_korean(self):
        """Korean negation '안 좋' should be negative."""
        assert _analyze_sentiment("이건 안 좋은 영상이다") == "negative"

    def test_negation_korean_mot(self):
        """Korean '못 하' negation."""
        assert _analyze_sentiment("설명을 못 잘했다") == "negative"

    def test_no_false_negation(self):
        """Pure positive without negation should stay positive."""
        assert _analyze_sentiment("I love this amazing video") == "positive"


class TestEmojiSentiment:
    def test_count_positive(self):
        pos, neg = _count_emoji_sentiment("❤️🔥👍")
        assert pos >= 2
        assert neg == 0

    def test_count_negative(self):
        pos, neg = _count_emoji_sentiment("😡👎")
        assert neg >= 2
        assert pos == 0

    def test_empty(self):
        assert _count_emoji_sentiment("no emoji here") == (0, 0)


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

    def test_sentiment_ratio_not_all_neutral(self):
        """With expanded keywords, 'Great video!' should be positive."""
        comments = [
            {"text": "Great video! awesome! 🔥", "like_count": 10, "author": "A"},
            {"text": "terrible boring garbage", "like_count": 5, "author": "B"},
        ]
        result = summarize_comments(comments)
        assert result["sentiment_ratio"]["positive"] > 0
        assert result["sentiment_ratio"]["negative"] > 0


class TestFetchComments:
    @patch("mcp_youtube_intelligence.core.comments.subprocess.run")
    def test_fetch_returns_list(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = fetch_comments("test_id")
        assert isinstance(result, list)

    @patch("mcp_youtube_intelligence.core.comments.subprocess.run")
    def test_fetch_handles_timeout(self, mock_run):
        mock_run.side_effect = Exception("timeout")
        result = fetch_comments("test_id")
        assert result == []
