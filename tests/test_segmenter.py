"""Tests for topic segmentation."""
import pytest
from mcp_youtube_intelligence.core.segmenter import segment_topics, MIN_SEGMENT_CHARS


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
        assert len(result) >= 1

    def test_english_marker_splits(self):
        text = ("Introduction to the course and some lengthy initial content that fills space and provides background context for everything we will cover today in this session. "
                "Moving on to the next topic, we discuss AI and its applications in detail across many industries and use cases that are transforming the modern world.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_segment_indices_sequential(self):
        text = "Part one with enough content to be a real segment here. Next topic is here with detailed explanation. Let's talk about something else entirely. Moving on to finale and wrapping up."
        result = segment_topics(text)
        for i, seg in enumerate(result):
            assert seg["segment"] == i

    def test_char_count_matches(self):
        text = "Hello world without any markers at all."
        result = segment_topics(text)
        assert result[0]["char_count"] == len(result[0]["text"])

    def test_multiple_korean_markers(self):
        text = ("오늘의 첫 번째 주제는 경제입니다. 많은 변화가 있었고 여러 분야에서 성장이 이어졌습니다. 특히 글로벌 경제는 큰 변동을 보이고 있으며 각국의 정책이 중요한 역할을 하고 있습니다. "
                "다음 주제는 기술입니다. 기술 발전이 빠르며 AI 분야가 특히 주목받고 있습니다. 반도체 산업도 큰 성장을 보이며 글로벌 공급망이 재편되고 있습니다. "
                "마지막 주제는 문화입니다. 다양한 문화 콘텐츠가 세계적으로 인기를 끌고 있으며 한류의 영향력이 점점 커지고 있습니다.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_lets_talk_about_marker(self):
        text = ("Some intro content here with enough detail to fill a segment properly and give us context about the broader landscape of technology and innovation in this field. "
                "Let's talk about machine learning now. It is fascinating and has many applications across industries including healthcare, finance, and autonomous vehicles.")
        result = segment_topics(text)
        assert len(result) >= 2

    # --- New tests ---

    def test_mid_sentence_no_false_positive(self):
        """'next thing' mid-sentence should NOT trigger segmentation."""
        text = "The next thing in the code is a function call that does processing. We also handle errors gracefully in this module."
        result = segment_topics(text)
        # Should be 1 segment since "next thing" is mid-sentence
        assert len(result) == 1

    def test_sentence_start_marker_matches(self):
        """Marker at sentence start should trigger segmentation."""
        text = ("We covered basics above with plenty of detail for context and background information that helps set the stage for our deeper discussion. "
                "Next topic is advanced patterns that build on the fundamentals we discussed and extend them into practical real-world applications and use cases.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_small_segment_merged(self):
        """Segments smaller than MIN_SEGMENT_CHARS should merge into previous."""
        # Create a scenario where a marker produces a tiny segment
        text = ("A very long introduction segment that has plenty of content to be valid on its own. "
                "다음 주제는 짧다. "  # This segment is tiny (<100 chars)
                "마지막 주제는 이것으로 마무리하며 충분히 긴 내용을 포함하고 있습니다 자세한 설명과 함께.")
        result = segment_topics(text)
        # The tiny middle segment should be merged
        for seg in result:
            # Either merged or standalone, but no tiny segments
            assert seg["char_count"] >= MIN_SEGMENT_CHARS or len(result) == 1

    def test_all_segments_above_minimum(self):
        """All resulting segments should be >= MIN_SEGMENT_CHARS (unless only 1 segment)."""
        text = ("Introduction with substantial content here for the first part of our discussion. "
                "Next topic covers AI and machine learning with detailed explanations and examples. "
                "Moving on to cloud computing infrastructure and deployment strategies in production.")
        result = segment_topics(text)
        if len(result) > 1:
            for seg in result:
                assert seg["char_count"] >= MIN_SEGMENT_CHARS
