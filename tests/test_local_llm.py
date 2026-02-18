"""Tests for local LLM providers (Ollama, vLLM, LM Studio)."""
from __future__ import annotations

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_youtube_intelligence.config import Config
from mcp_youtube_intelligence.core.summarizer import (
    resolve_provider,
    llm_summary,
    _ollama_summary,
    _vllm_summary,
    _lmstudio_summary,
)


def _make_config(**overrides) -> Config:
    return Config(**overrides)


class TestLocalLLMConfig:
    def test_default_ollama_config(self):
        cfg = Config()
        assert cfg.ollama_base_url == "http://localhost:11434"
        assert cfg.ollama_model == "llama3.1:8b"

    def test_default_vllm_config(self):
        cfg = Config()
        assert cfg.vllm_base_url == "http://localhost:8000"
        assert cfg.vllm_model == ""

    def test_default_lmstudio_config(self):
        cfg = Config()
        assert cfg.lmstudio_base_url == "http://localhost:1234"
        assert cfg.lmstudio_model == ""

    def test_from_env_ollama(self):
        with patch.dict(os.environ, {
            "MYI_LLM_PROVIDER": "ollama",
            "MYI_OLLAMA_BASE_URL": "http://myhost:11434",
            "MYI_OLLAMA_MODEL": "qwen2.5:7b",
        }):
            cfg = Config.from_env()
            assert cfg.llm_provider == "ollama"
            assert cfg.ollama_base_url == "http://myhost:11434"
            assert cfg.ollama_model == "qwen2.5:7b"

    def test_from_env_vllm(self):
        with patch.dict(os.environ, {
            "MYI_LLM_PROVIDER": "vllm",
            "MYI_VLLM_BASE_URL": "http://gpu-server:8000",
            "MYI_VLLM_MODEL": "Qwen/Qwen2.5-7B-Instruct",
        }):
            cfg = Config.from_env()
            assert cfg.llm_provider == "vllm"
            assert cfg.vllm_base_url == "http://gpu-server:8000"
            assert cfg.vllm_model == "Qwen/Qwen2.5-7B-Instruct"

    def test_from_env_lmstudio(self):
        with patch.dict(os.environ, {
            "MYI_LLM_PROVIDER": "lmstudio",
            "MYI_LMSTUDIO_BASE_URL": "http://localhost:1234",
            "MYI_LMSTUDIO_MODEL": "my-model",
        }):
            cfg = Config.from_env()
            assert cfg.llm_provider == "lmstudio"
            assert cfg.lmstudio_model == "my-model"


class TestResolveProviderLocal:
    def test_explicit_ollama(self):
        cfg = _make_config(llm_provider="ollama")
        assert resolve_provider(cfg) == "ollama"

    def test_explicit_vllm(self):
        cfg = _make_config(llm_provider="vllm")
        assert resolve_provider(cfg) == "vllm"

    def test_explicit_lmstudio(self):
        cfg = _make_config(llm_provider="lmstudio")
        assert resolve_provider(cfg) == "lmstudio"

    @patch("mcp_youtube_intelligence.core.summarizer._check_ollama_available", return_value=True)
    def test_auto_falls_to_ollama(self, mock_check):
        cfg = _make_config(llm_provider="auto")
        assert resolve_provider(cfg) == "ollama"

    @patch("mcp_youtube_intelligence.core.summarizer._check_ollama_available", return_value=False)
    def test_auto_no_ollama_returns_none(self, mock_check):
        cfg = _make_config(llm_provider="auto")
        assert resolve_provider(cfg) is None

    def test_auto_cloud_before_local(self):
        """Cloud providers should be preferred over local in auto mode."""
        cfg = _make_config(llm_provider="auto", openai_api_key="sk-test")
        assert resolve_provider(cfg) == "openai"

    @patch("mcp_youtube_intelligence.core.summarizer._check_ollama_available", return_value=True)
    def test_auto_priority_anthropic_over_ollama(self, mock_check):
        cfg = _make_config(llm_provider="auto", anthropic_api_key="sk-ant")
        assert resolve_provider(cfg) == "anthropic"


@pytest.mark.asyncio
class TestOllamaSummary:
    async def test_ollama_summary_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Ollama summary result"}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await _ollama_summary("test text", "http://localhost:11434", "llama3.1:8b")
            assert result == "Ollama summary result"

    async def test_ollama_via_llm_summary(self):
        cfg = _make_config(llm_provider="ollama", ollama_base_url="http://localhost:11434", ollama_model="test")
        with patch("mcp_youtube_intelligence.core.summarizer._ollama_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "Ollama result"
            result = await llm_summary("test text", cfg)
            assert result == "Ollama result"


@pytest.mark.asyncio
class TestVllmSummary:
    async def test_vllm_via_llm_summary(self):
        cfg = _make_config(llm_provider="vllm", vllm_base_url="http://localhost:8000", vllm_model="test-model")
        with patch("mcp_youtube_intelligence.core.summarizer._vllm_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "vLLM result"
            result = await llm_summary("test text", cfg)
            assert result == "vLLM result"


@pytest.mark.asyncio
class TestLmstudioSummary:
    async def test_lmstudio_via_llm_summary(self):
        cfg = _make_config(llm_provider="lmstudio", lmstudio_base_url="http://localhost:1234", lmstudio_model="test")
        with patch("mcp_youtube_intelligence.core.summarizer._lmstudio_summary", new_callable=AsyncMock) as mock:
            mock.return_value = "LM Studio result"
            result = await llm_summary("test text", cfg)
            assert result == "LM Studio result"

    async def test_lmstudio_failure_returns_none(self):
        cfg = _make_config(llm_provider="lmstudio")
        with patch("mcp_youtube_intelligence.core.summarizer._lmstudio_summary", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Connection refused")
            result = await llm_summary("test text", cfg)
            assert result is None
