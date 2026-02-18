"""Tests for multi-provider LLM summarization."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_youtube_intelligence.config import Config
from mcp_youtube_intelligence.core.summarizer import (
    resolve_provider,
    llm_summary,
    summarize,
    extractive_summary,
)


def _make_config(**overrides) -> Config:
    return Config(**overrides)


class TestResolveProvider:
    def test_explicit_openai(self):
        cfg = _make_config(llm_provider="openai", openai_api_key="sk-test")
        assert resolve_provider(cfg) == "openai"

    def test_explicit_anthropic(self):
        cfg = _make_config(llm_provider="anthropic", anthropic_api_key="sk-ant-test")
        assert resolve_provider(cfg) == "anthropic"

    def test_explicit_google(self):
        cfg = _make_config(llm_provider="google", google_api_key="goog-test")
        assert resolve_provider(cfg) == "google"

    def test_auto_prefers_anthropic(self):
        cfg = _make_config(
            llm_provider="auto",
            anthropic_api_key="sk-ant",
            openai_api_key="sk-oai",
            google_api_key="goog",
        )
        assert resolve_provider(cfg) == "anthropic"

    def test_auto_falls_to_openai(self):
        cfg = _make_config(llm_provider="auto", openai_api_key="sk-oai", google_api_key="goog")
        assert resolve_provider(cfg) == "openai"

    def test_auto_falls_to_google(self):
        cfg = _make_config(llm_provider="auto", google_api_key="goog")
        assert resolve_provider(cfg) == "google"

    def test_auto_no_keys(self):
        cfg = _make_config(llm_provider="auto")
        assert resolve_provider(cfg) is None

    def test_invalid_provider(self):
        cfg = _make_config(llm_provider="invalid")
        assert resolve_provider(cfg) is None


@pytest.mark.asyncio
class TestLlmSummary:
    async def test_openai_summary(self):
        cfg = _make_config(llm_provider="openai", openai_api_key="sk-test")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="OpenAI summary"))]

        with patch("mcp_youtube_intelligence.core.summarizer._openai_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "OpenAI summary"
            result = await llm_summary("test text", cfg)
            assert result == "OpenAI summary"

    async def test_anthropic_summary(self):
        cfg = _make_config(llm_provider="anthropic", anthropic_api_key="sk-ant")
        with patch("mcp_youtube_intelligence.core.summarizer._anthropic_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "Anthropic summary"
            result = await llm_summary("test text", cfg)
            assert result == "Anthropic summary"

    async def test_google_summary(self):
        cfg = _make_config(llm_provider="google", google_api_key="goog")
        with patch("mcp_youtube_intelligence.core.summarizer._google_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "Google summary"
            result = await llm_summary("test text", cfg)
            assert result == "Google summary"

    async def test_provider_override(self):
        cfg = _make_config(llm_provider="openai", openai_api_key="sk", anthropic_api_key="sk-ant")
        with patch("mcp_youtube_intelligence.core.summarizer._anthropic_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "Anthropic override"
            result = await llm_summary("test text", cfg, provider_override="anthropic")
            assert result == "Anthropic override"

    async def test_no_provider_returns_none(self):
        cfg = _make_config(llm_provider="auto")
        result = await llm_summary("test text", cfg)
        assert result is None

    async def test_failure_falls_back_to_none(self):
        cfg = _make_config(llm_provider="openai", openai_api_key="sk-test")
        with patch("mcp_youtube_intelligence.core.summarizer._openai_summary", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API error")
            result = await llm_summary("test text", cfg)
            assert result is None

    async def test_import_error_returns_none(self):
        cfg = _make_config(llm_provider="anthropic", anthropic_api_key="sk-ant")
        with patch("mcp_youtube_intelligence.core.summarizer._anthropic_summary", new_callable=AsyncMock) as mock:
            mock.side_effect = ImportError("no anthropic")
            result = await llm_summary("test text", cfg)
            assert result is None


@pytest.mark.asyncio
class TestSummarize:
    async def test_falls_back_to_extractive(self):
        cfg = _make_config(llm_provider="auto")
        result = await summarize("This is a long enough text for testing purposes. " * 10, config=cfg)
        assert result  # extractive fallback should produce something

    async def test_legacy_api_key_path(self):
        with patch("mcp_youtube_intelligence.core.summarizer._openai_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "legacy result"
            result = await summarize("text", api_key="sk-test", model="gpt-4o-mini")
            assert result == "legacy result"


class TestExtractiveSummary:
    def test_empty(self):
        assert extractive_summary("") == ""

    def test_short_text(self):
        result = extractive_summary("Short text that is not very long at all")
        assert result  # returns something


class TestConfigFromEnv:
    def test_llm_provider_env(self):
        import os
        with patch.dict(os.environ, {"MYI_LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant"}):
            cfg = Config.from_env()
            assert cfg.llm_provider == "anthropic"
            assert cfg.anthropic_api_key == "sk-ant"
