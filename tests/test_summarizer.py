"""Tests for summarizer module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mcp_youtube_intelligence.core.summarizer import (
    extractive_summary, llm_summary, summarize, _adaptive_max_chars, _split_sentences,
)


class TestAdaptiveMaxChars:
    def test_short_text(self):
        assert _adaptive_max_chars(5000) == 500

    def test_medium_text(self):
        assert _adaptive_max_chars(20000) == 1000

    def test_long_text(self):
        assert _adaptive_max_chars(100000) == 2000

    def test_very_short(self):
        assert _adaptive_max_chars(100) == 500  # min clamp

    def test_very_long(self):
        assert _adaptive_max_chars(1000000) == 2000  # max clamp


class TestSplitSentences:
    def test_english_splitting(self):
        text = "First sentence. Second sentence! Third sentence?"
        result = _split_sentences(text)
        assert len(result) == 3

    def test_korean_ending_da(self):
        text = "이것은 첫 번째입니다. 두 번째 문장이 이어집니다. 세 번째도 있습니다."
        result = _split_sentences(text)
        assert len(result) >= 3

    def test_korean_ending_yo(self):
        text = "좋은 내용이에요. 감사합니다. 다음에 또 봐요."
        result = _split_sentences(text)
        assert len(result) >= 3

    def test_korean_ending_kka(self):
        text = "이게 맞을까? 확인해 봅시다. 결론은 이렇습니다."
        result = _split_sentences(text)
        assert len(result) >= 3


class TestExtractiveSummary:
    def test_empty_input(self):
        assert extractive_summary("") == ""

    def test_short_text_no_sentences(self):
        result = extractive_summary("Short text here.")
        assert result

    def test_picks_top_sentences(self):
        text = "This is a very important introductory sentence about the topic. Another sentence follows with details and explanations. A third sentence wraps up the discussion nicely."
        result = extractive_summary(text, max_sentences=2)
        assert len(result) > 0
        assert result.endswith(".")

    def test_adaptive_length_default(self):
        """When max_chars=0, should use adaptive length."""
        text = ". ".join("This is a long enough sentence to pass the filter easily" for _ in range(50))
        result = extractive_summary(text)  # max_chars=0 → adaptive
        assert len(result) <= 2000

    def test_respects_explicit_max_chars(self):
        text = ". ".join("This is a long enough sentence to pass the filter easily" for _ in range(50))
        result = extractive_summary(text, max_chars=500)
        assert len(result) <= 500

    def test_favors_earlier_sentences(self):
        sentences = [f"Sentence {i} has enough content to pass the twenty char filter" for i in range(20)]
        text = ". ".join(sentences)
        result = extractive_summary(text, max_sentences=3)
        assert len(result) > 0

    def test_boosts_sentences_with_numbers(self):
        """Sentences with numbers/stats should be favored."""
        text = (
            "This is a generic introduction to the topic at hand. "
            "Revenue grew by 45% year over year to $2.5 billion. "
            "The company is based in California and has many employees."
        )
        result = extractive_summary(text, max_sentences=1)
        assert "45%" in result or "$2.5" in result

    def test_boosts_importance_keywords(self):
        """Sentences with 'in summary', 'the key point' etc should be boosted."""
        text = (
            "There are many factors to consider in this analysis. "
            "Various stakeholders have different perspectives on this. "
            "In summary the most important finding is the growth trajectory."
        )
        result = extractive_summary(text, max_sentences=1)
        assert "summary" in result.lower() or "important" in result.lower()

    def test_chunked_summary_long_text(self):
        """Long text (>30 sentences) should use chunked approach."""
        sentences = [
            f"Sentence number {i} provides detailed information about topic {i}"
            for i in range(50)
        ]
        text = ". ".join(sentences)
        result = extractive_summary(text, max_sentences=5)
        assert len(result) > 0
        # Should cover different parts of the text, not just beginning
        assert any(str(i) in result for i in range(25, 50))

    def test_even_sampling_short_text(self):
        """Even short texts should use chunked/even sampling now."""
        sentences = [f"Topic {i} is an important discussion point here" for i in range(10)]
        text = ". ".join(sentences)
        result = extractive_summary(text, max_sentences=3)
        assert len(result) > 0

    def test_no_intro_bias(self):
        """Summary should not only pick from the first few sentences."""
        sentences = [
            "Generic introduction to the video content and overview. " * 2,
            "More introductory remarks about the topic at hand. " * 2,
            "Background context for what we will discuss today. " * 2,
            "The key finding is that revenue increased by 200 percent year over year. ",
            "This represents a significant milestone for the company growth. ",
            "In conclusion the results exceeded all analyst expectations dramatically. ",
        ]
        text = " ".join(sentences)
        result = extractive_summary(text, max_sentences=2)
        # Should pick the sentences with numbers and conclusion keywords
        assert "200" in result or "conclusion" in result.lower()


class TestLlmSummary:
    @pytest.mark.asyncio
    async def test_no_api_key(self):
        result = await llm_summary("some text", api_key="")
        assert result is None

    @pytest.mark.asyncio
    async def test_api_call_failure_returns_none(self):
        result = await llm_summary("text", api_key="sk-test")
        assert result is None


class TestSummarize:
    @pytest.mark.asyncio
    async def test_without_api_key_uses_extractive(self):
        text = "This is a fairly long sentence that should pass the filter easily. Another important sentence here too."
        result = await summarize(text, api_key="")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_with_api_key_tries_llm(self):
        with patch("mcp_youtube_intelligence.core.summarizer.llm_summary", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "LLM summary"
            result = await summarize("text", api_key="sk-test")
            assert result == "LLM summary"
            mock_llm.assert_called_once()
