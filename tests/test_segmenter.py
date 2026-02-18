"""Tests for segmenter.py topic segmentation."""
from mcp_youtube_intelligence.core.segmenter import segment_topics


def test_empty_string():
    assert segment_topics("") == []


def test_whitespace_only():
    assert segment_topics("   ") == []


def test_no_markers():
    result = segment_topics("그냥 일반적인 텍스트입니다.")
    assert len(result) == 1
    assert result[0]["segment"] == 0


def test_multiple_markers():
    text = "자 다음 주제는 반도체입니다. 반도체 시장이 성장하고 있습니다. 자 마지막 주제는 금리입니다. 금리가 오르고 있습니다."
    result = segment_topics(text)
    assert len(result) >= 2  # At least 2 marker-based segments
    # Verify segments have proper structure
    for seg in result:
        assert "segment" in seg
        assert "text" in seg
        assert "char_count" in seg
        assert seg["char_count"] == len(seg["text"])


def test_three_segments_with_preamble():
    text = "오늘 이야기를 시작하겠습니다. 자 다음 주제는 반도체입니다. 반도체 시장이... 자 마지막 주제는 금리입니다. 금리 이야기."
    result = segment_topics(text)
    assert len(result) == 3  # preamble + 2 marker segments


def test_english_markers():
    text = "Let's begin. Next topic is AI. AI is growing. Moving on to crypto. Bitcoin rises."
    result = segment_topics(text)
    assert len(result) >= 2


def test_segment_indices_sequential():
    text = "자 다음 주제는 A. 내용A. 자 다음 주제는 B. 내용B."
    result = segment_topics(text)
    for i, seg in enumerate(result):
        assert seg["segment"] == i
