"""Summarization: extractive (default) with optional multi-provider LLM summarization."""
from __future__ import annotations

import logging
import re
from typing import Optional

from ..config import Config

logger = logging.getLogger(__name__)

# Keywords that signal important/summary sentences
_IMPORTANCE_KEYWORDS_RE = re.compile(
    r"\b(결론|핵심|요약하면|정리하면|요점|중요한|"
    r"in summary|to summarize|the key point|importantly|in conclusion|"
    r"takeaway|bottom line|to recap|the main|crucial|essential)\b",
    re.IGNORECASE,
)
_HAS_NUMBER_RE = re.compile(r"\d+[\d.,]*[%$€£₩]?")

# Korean sentence-ending patterns
_KOREAN_SENTENCE_RE = re.compile(
    r"(?<=[다요까죠지])[.?!]\s+"
    r"|[.!?。]\s+"
)

_SYSTEM_PROMPT = (
    "Summarize the following transcript concisely. "
    "Focus on key points, arguments, and conclusions. Keep it under 300 words."
)
_USER_PROMPT_PREFIX = "Summarize concisely in the same language:\n\n"
_MAX_INPUT_CHARS = 30_000


def _split_sentences(text: str) -> list[str]:
    parts = _KOREAN_SENTENCE_RE.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def _adaptive_max_chars(text_len: int) -> int:
    return min(2000, max(500, text_len // 20))


def extractive_summary(text: str, max_sentences: int = 7, max_chars: int = 0) -> str:
    if not text:
        return ""
    if max_chars <= 0:
        max_chars = _adaptive_max_chars(len(text))
    sentences = _split_sentences(text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return text[:max_chars]
    return _chunked_summary(sentences, max_sentences, max_chars)


def _chunked_summary(sentences: list[str], max_sentences: int, max_chars: int) -> str:
    n = len(sentences)
    num_chunks = min(max_sentences, max(1, min(n, n // 10 + 1)))
    chunk_size = max(1, n // num_chunks)
    picks_per_chunk = max(1, max_sentences // num_chunks)

    all_picks: list[tuple[float, int, str]] = []
    for ci in range(num_chunks):
        start = ci * chunk_size
        end = start + chunk_size if ci < num_chunks - 1 else n
        chunk = sentences[start:end]
        scored = []
        for j, s in enumerate(chunk):
            global_idx = start + j
            score = len(s) * max(0.3, 1.0 - j * 0.02)
            if _HAS_NUMBER_RE.search(s):
                score *= 1.4
            if _IMPORTANCE_KEYWORDS_RE.search(s):
                score *= 1.6
            scored.append((score, global_idx, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        all_picks.extend(scored[:picks_per_chunk])

    all_picks.sort(key=lambda x: x[1])
    result = ". ".join(s for _, _, s in all_picks) + "."
    return result[:max_chars]


# ── Provider resolution ──

def resolve_provider(config: Config) -> Optional[str]:
    """Resolve which LLM provider to use based on config."""
    provider = config.llm_provider.lower().strip()
    if provider != "auto":
        return provider if provider in ("openai", "anthropic", "google") else None
    # auto: anthropic > openai > google
    if config.anthropic_api_key:
        return "anthropic"
    if config.openai_api_key:
        return "openai"
    if config.google_api_key:
        return "google"
    return None


# ── Provider implementations ──

async def _openai_summary(text: str, api_key: str, model: str) -> Optional[str]:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. Run: pip install 'mcp-youtube-intelligence[llm]'"
        )
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text[:_MAX_INPUT_CHARS]},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


async def _anthropic_summary(text: str, api_key: str, model: str) -> Optional[str]:
    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        raise ImportError(
            "Anthropic package not installed. Run: pip install 'mcp-youtube-intelligence[anthropic-llm]'"
        )
    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=500,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"{_USER_PROMPT_PREFIX}{text[:_MAX_INPUT_CHARS]}"},
        ],
    )
    return response.content[0].text


async def _google_summary(text: str, api_key: str, model: str) -> Optional[str]:
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "Google GenAI package not installed. Run: pip install 'mcp-youtube-intelligence[google-llm]'"
        )
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    prompt = (
        "Summarize the following transcript concisely in the same language. "
        "Focus on key points. Keep under 300 words.\n\n"
        + text[:_MAX_INPUT_CHARS]
    )
    response = await model_obj.generate_content_async(prompt)
    return response.text


# ── Main entry points ──

_PROVIDER_MAP = {
    "openai": lambda text, cfg: _openai_summary(text, cfg.openai_api_key, cfg.openai_model),
    "anthropic": lambda text, cfg: _anthropic_summary(text, cfg.anthropic_api_key, cfg.anthropic_model),
    "google": lambda text, cfg: _google_summary(text, cfg.google_api_key, cfg.google_model),
}


async def llm_summary(text: str, config: Config, provider_override: Optional[str] = None) -> Optional[str]:
    """Summarize text using the configured LLM provider. Returns None on failure."""
    if provider_override and provider_override != "auto":
        provider = provider_override
    else:
        provider = resolve_provider(config)
    if not provider:
        return None

    handler = _PROVIDER_MAP.get(provider)
    if not handler:
        logger.warning("Unknown LLM provider: %s", provider)
        return None

    try:
        return await handler(text, config)
    except ImportError as e:
        logger.warning("LLM provider unavailable: %s", e)
        return None
    except Exception as e:
        logger.warning("LLM summary failed (%s): %s", provider, e)
        return None


# Legacy compatible signature
async def summarize(
    text: str,
    api_key: str = "",
    model: str = "gpt-4o-mini",
    *,
    config: Optional[Config] = None,
    provider: Optional[str] = None,
) -> str:
    """Summarize text. Uses LLM if available, otherwise extractive.

    Supports both legacy (api_key, model) and new (config) calling conventions.
    """
    if config:
        result = await llm_summary(text, config, provider_override=provider)
        if result:
            return result
    elif api_key:
        # Legacy path
        try:
            return await _openai_summary(text, api_key, model) or extractive_summary(text)
        except Exception as e:
            logger.warning("LLM summary failed: %s", e)
    return extractive_summary(text)
