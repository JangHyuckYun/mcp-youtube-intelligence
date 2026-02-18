"""Tests for comments.py noise filtering, sentiment, and summarization."""
from mcp_youtube_intelligence.core.comments import _is_noise, _analyze_sentiment, summarize_comments


def test_noise_short():
    assert _is_noise("ㅋㅋ") is True
    assert _is_noise("좋아") is True  # < 5 chars


def test_noise_repeated_chars():
    assert _is_noise("ㅋㅋㅋㅋㅋㅋㅋ") is True


def test_noise_subscribe_spam():
    assert _is_noise("제 채널도 구독 부탁드립니다!") is True


def test_not_noise():
    assert _is_noise("이 영상 정말 유익했습니다 감사합니다") is False


def test_sentiment_positive():
    assert _analyze_sentiment("정말 최고입니다 감사합니다") == "positive"
    assert _analyze_sentiment("This is amazing and great") == "positive"


def test_sentiment_negative():
    assert _analyze_sentiment("최악이다 실망했다") == "negative"
    assert _analyze_sentiment("This is terrible and horrible") == "negative"


def test_sentiment_neutral():
    assert _analyze_sentiment("오늘 날씨가 어떤가요") == "neutral"


def test_summarize_empty():
    result = summarize_comments([])
    assert result["count"] == 0


def test_summarize_with_comments():
    comments = [
        {"author": "A", "text": "정말 좋은 영상입니다 감사합니다", "like_count": 10, "sentiment": "positive"},
        {"author": "B", "text": "별로였어요 실망입니다", "like_count": 2, "sentiment": "negative"},
        {"author": "C", "text": "그냥 그렇습니다", "like_count": 0, "sentiment": "neutral"},
    ]
    result = summarize_comments(comments, top_n=2)
    assert result["count"] == 3
    assert "sentiment_ratio" in result
    assert len(result["top_comments"]) == 2
    assert result["top_comments"][0]["likes"] == 10
    assert "top_keywords" in result
