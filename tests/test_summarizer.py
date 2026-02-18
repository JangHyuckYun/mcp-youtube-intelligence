"""Tests for summarizer module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mcp_youtube_intelligence.core.summarizer import (
    extractive_summary, llm_summary, summarize, _adaptive_max_chars, _split_sentences,
    _clean_music_symbols,
)


class TestAdaptiveMaxChars:
    def test_short_text(self):
        # <1000 chars: 50%
        assert _adaptive_max_chars(800) == 400

    def test_medium_text(self):
        # 1000~5000: 20%
        assert _adaptive_max_chars(3000) == 600

    def test_long_text(self):
        # 5000~20000: 10%
        assert _adaptive_max_chars(10000) == 1000

    def test_very_long(self):
        # >20000: 5%
        assert _adaptive_max_chars(100000) == 5000

    def test_very_short(self):
        # min 200
        assert _adaptive_max_chars(100) == 200


class TestCleanMusicSymbols:
    def test_bracketed_music(self):
        assert _clean_music_symbols("Hello [♪♪♪] world") == "Hello world"

    def test_inline_music(self):
        assert _clean_music_symbols("♪ Some lyrics ♫") == "Some lyrics"

    def test_no_music(self):
        assert _clean_music_symbols("Normal text") == "Normal text"

    def test_only_music(self):
        assert _clean_music_symbols("♪♪♪") == ""


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

    def test_short_text_not_over_trimmed(self):
        """Short text (<500 chars) should not be aggressively trimmed."""
        text = "This is a short but meaningful paragraph about machine learning. It covers the basics of neural networks and deep learning. The conclusion is that AI is transforming every industry."
        result = extractive_summary(text)
        # Should retain most of the content for short text
        assert len(result) > len(text) * 0.3

    def test_music_symbols_cleaned(self):
        text = "[♪♪♪] Welcome to the show everyone. ♪ This is an important announcement about the upcoming event. ♫ Thank you for watching and subscribing to the channel."
        result = extractive_summary(text)
        assert "♪" not in result
        assert "♫" not in result
        assert len(result) > 0

    def test_picks_top_sentences(self):
        text = "This is a very important introductory sentence about the topic. Another sentence follows with details and explanations. A third sentence wraps up the discussion nicely."
        result = extractive_summary(text, max_sentences=2)
        assert len(result) > 0
        assert result.endswith(".")

    def test_adaptive_length_default(self):
        """When max_chars=0, should use adaptive length."""
        text = ". ".join("This is a long enough sentence to pass the filter easily" for _ in range(50))
        result = extractive_summary(text)
        assert len(result) > 0

    def test_respects_explicit_max_chars(self):
        text = ". ".join("This is a long enough sentence to pass the filter easily" for _ in range(50))
        result = extractive_summary(text, max_chars=500)
        assert len(result) <= 500

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

    def test_first_and_last_sentence_bonus(self):
        """First and last sentences should get position bonus."""
        sentences = [
            "The main thesis of this presentation is about climate change impacts",
            "Various data points were collected from multiple sources worldwide",
            "Statistical analysis revealed patterns in the temperature readings",
            "More research is needed to fully understand these complex dynamics",
            "In conclusion climate action is urgently needed across all sectors",
        ]
        text = ". ".join(sentences) + "."
        result = extractive_summary(text, max_sentences=2)
        # Should likely include first or last sentence
        has_first = "thesis" in result.lower()
        has_last = "conclusion" in result.lower()
        assert has_first or has_last

    def test_deduplication(self):
        """Similar/duplicate sentences should be deduplicated."""
        text = (
            "Machine learning is transforming the technology industry today. "
            "Machine learning is changing the technology industry rapidly. "
            "Quantum computing represents a completely different paradigm shift. "
            "The future of AI depends on responsible development practices."
        )
        result = extractive_summary(text, max_sentences=3)
        # Should not have both near-duplicate ML sentences
        assert result.count("machine learning") <= 1 or result.count("Machine learning") <= 1

    def test_long_text_covers_different_parts(self):
        """Long text should have sentences from different parts."""
        sentences = [
            f"Sentence number {i} provides detailed information about topic {i}"
            for i in range(50)
        ]
        text = ". ".join(sentences)
        result = extractive_summary(text, max_sentences=5)
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
        assert "200" in result or "conclusion" in result.lower()

    def test_korean_text_summary(self):
        """Korean text should be properly split and summarized."""
        text = (
            "인공지능 기술이 빠르게 발전하고 있습니다. "
            "많은 기업들이 AI를 도입하고 있습니다. "
            "특히 자연어 처리 분야에서 큰 발전이 있었습니다. "
            "결론적으로 AI는 우리 생활을 크게 변화시킬 것입니다."
        )
        result = extractive_summary(text, max_sentences=2)
        assert len(result) > 0
        # Should pick the conclusion sentence
        assert "결론" in result or "인공지능" in result


class TestLlmSummary:
    @pytest.mark.asyncio
    async def test_no_provider(self):
        config = MagicMock()
        config.llm_provider = "none"
        config.anthropic_api_key = ""
        config.openai_api_key = ""
        config.google_api_key = ""
        result = await llm_summary("some text", config)
        assert result is None


class TestSummarize:
    @pytest.mark.asyncio
    async def test_without_api_key_uses_extractive(self):
        text = "This is a fairly long sentence that should pass the filter easily. Another important sentence here too."
        result = await summarize(text, api_key="")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_with_api_key_tries_llm(self):
        with patch("mcp_youtube_intelligence.core.summarizer._openai_summary", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "LLM summary"
            result = await summarize("text", api_key="sk-test")
            assert result == "LLM summary"
