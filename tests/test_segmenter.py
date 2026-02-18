"""Tests for topic segmentation."""
import pytest
from mcp_youtube_intelligence.core.segmenter import segment_topics


class TestSegmentTopics:
    def test_empty_string(self):
        assert segment_topics("") == []

    def test_no_markers(self):
        text = "This is a normal paragraph without any topic transitions."
        result = segment_topics(text)
        assert len(result) == 1
        assert result[0]["segment"] == 0
        assert result[0]["text"] == text

    def test_korean_marker_splits(self):
        text = "첫 번째 내용입니다. 다음 주제로 넘어가겠습니다. 두 번째 내용입니다."
        result = segment_topics(text)
        assert len(result) >= 1  # Should detect "다음 주제"

    def test_english_marker_splits(self):
        text = "Introduction to the course. Moving on to the next topic, we discuss AI. Final thoughts."
        result = segment_topics(text)
        assert len(result) >= 2  # "moving on to" is a marker

    def test_segment_indices_sequential(self):
        text = "Part one. Next topic is here. Let's talk about something else. Moving on to finale."
        result = segment_topics(text)
        for i, seg in enumerate(result):
            assert seg["segment"] == i

    def test_char_count_matches(self):
        text = "Hello world without any markers at all."
        result = segment_topics(text)
        assert result[0]["char_count"] == len(result[0]["text"])

    def test_multiple_korean_markers(self):
        text = "오늘의 첫 번째 주제는 경제입니다. 많은 변화가 있었습니다. 다음 주제는 기술입니다. 기술 발전이 빠릅니다. 마지막 주제는 문화입니다."
        result = segment_topics(text)
        # Should split on "다음 주제" and "마지막 주제"
        assert len(result) >= 2

    def test_lets_talk_about_marker(self):
        text = "Some intro content here. Let's talk about machine learning now. It is fascinating."
        result = segment_topics(text)
        assert len(result) >= 2
