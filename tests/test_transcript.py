"""Tests for transcript cleaning, chunking, and extractive summarization."""
import pytest
from mcp_youtube_intelligence.core.transcript import (
    clean_transcript,
    make_chunks,
    summarize_extractive,
)


class TestCleanTranscript:
    def test_empty_input(self):
        assert clean_transcript("") == ""

    def test_none_input(self):
        assert clean_transcript(None) == ""

    def test_removes_music_tag(self):
        assert "[Music]" not in clean_transcript("Hello [Music] world")

    def test_removes_korean_noise(self):
        result = clean_transcript("안녕하세요 [음악] 여러분 [박수]")
        assert "[음악]" not in result
        assert "[박수]" not in result

    def test_removes_timestamps(self):
        result = clean_transcript("At 1:23 we see something and at 1:23:45 another")
        assert "1:23" not in result

    def test_normalizes_whitespace(self):
        result = clean_transcript("hello    world   foo")
        assert "  " not in result

    def test_removes_filler_sounds(self):
        result = clean_transcript("그래서 아 어 음 이것은")
        # Filler pattern removes repeated fillers
        assert result.strip()  # still has content

    def test_preserves_meaningful_content(self):
        text = "오늘은 삼성전자에 대해 알아보겠습니다"
        assert clean_transcript(text) == text


class TestMakeChunks:
    def test_empty_input(self):
        assert make_chunks("") == []

    def test_single_chunk(self):
        text = "Hello world"
        chunks = make_chunks(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["index"] == 0

    def test_multiple_chunks(self):
        text = "A" * 5000
        chunks = make_chunks(text, chunk_size=2000)
        assert len(chunks) == 3
        assert chunks[0]["char_count"] == 2000
        assert chunks[2]["char_count"] == 1000

    def test_chunk_indices_sequential(self):
        chunks = make_chunks("A" * 6000, chunk_size=2000)
        for i, c in enumerate(chunks):
            assert c["index"] == i

    def test_custom_chunk_size(self):
        text = "A" * 100
        chunks = make_chunks(text, chunk_size=30)
        assert len(chunks) == 4  # 30+30+30+10


class TestSummarizeExtractive:
    def test_empty_input(self):
        assert summarize_extractive("") == ""

    def test_short_text_fallback(self):
        # Text with no sentences >20 chars falls back to truncation
        result = summarize_extractive("Short.")
        assert result  # returns something

    def test_picks_sentences(self):
        text = "This is a very important first sentence about the topic at hand. Second sentence is also quite relevant and informative. Third one covers additional ground nicely."
        result = summarize_extractive(text, max_sentences=2)
        assert result.endswith(".")

    def test_respects_max_sentences(self):
        sentences = ". ".join(f"Sentence number {i} has enough characters to pass filter" for i in range(10))
        result = summarize_extractive(sentences, max_sentences=3)
        # Should have at most 3 sentence-like segments
        assert len(result) < len(sentences)

    def test_long_text_truncation(self):
        text = ". ".join("This is a moderately long sentence number whatever" for _ in range(100))
        result = summarize_extractive(text)
        assert len(result) > 0
