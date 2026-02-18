"""Summarization: extractive (default) with optional LLM-based summarization."""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Keywords that signal important/summary sentences
_IMPORTANCE_KEYWORDS_RE = re.compile(
    r"\b(결론|핵심|요약하면|정리하면|요점|중요한|"
    r"in summary|to summarize|the key point|importantly|in conclusion|"
    r"takeaway|bottom line|to recap|the main|crucial|essential)\b",
    re.IGNORECASE,
)
_HAS_NUMBER_RE = re.compile(r"\d+[\d.,]*[%$€£₩]?")


def _adaptive_max_chars(text_len: int) -> int:
    """Calculate adaptive max chars based on source text length."""
    return min(2000, max(500, text_len // 20))


def extractive_summary(text: str, max_sentences: int = 7, max_chars: int = 0) -> str:
    """Extractive summary with adaptive length, position + keyword + stats scoring.
    
    Uses chunked extraction for long texts to ensure full coverage.
    """
    if not text:
        return ""

    if max_chars <= 0:
        max_chars = _adaptive_max_chars(len(text))

    sentences = re.split(r"[.!?。]\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return text[:max_chars]

    n = len(sentences)

    # For long texts, use chunked approach
    if n > 30:
        return _chunked_summary(sentences, max_sentences, max_chars)

    scored = []
    for i, s in enumerate(sentences):
        # Base: position weight (earlier = better, but not too steep)
        position_weight = max(0.3, 1.0 - i * 0.015)
        score = len(s) * position_weight

        # Boost: contains numbers/statistics
        if _HAS_NUMBER_RE.search(s):
            score *= 1.4

        # Boost: contains importance keywords
        if _IMPORTANCE_KEYWORDS_RE.search(s):
            score *= 1.6

        scored.append((score, i, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = sorted(scored[:max_sentences], key=lambda x: x[1])
    result = ". ".join(s for _, _, s in picked) + "."
    return result[:max_chars]


def _chunked_summary(sentences: list[str], max_sentences: int, max_chars: int) -> str:
    """Split sentences into chunks and pick top from each for full coverage."""
    n = len(sentences)
    # Number of chunks: proportional but capped
    num_chunks = min(max_sentences, max(3, n // 15))
    chunk_size = n // num_chunks
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

    # Re-order by original position
    all_picks.sort(key=lambda x: x[1])
    result = ". ".join(s for _, _, s in all_picks) + "."
    return result[:max_chars]


async def llm_summary(text: str, api_key: str, model: str = "gpt-4o-mini", max_chars: int = 1500) -> Optional[str]:
    """Summarize text using OpenAI API. Returns None on failure."""
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        truncated = text[:30000]
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Summarize the following transcript concisely in the same language. Focus on key points, arguments, and conclusions. Keep it under 300 words."},
                {"role": "user", "content": truncated},
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning("LLM summary failed: %s", e)
        return None


async def summarize(text: str, api_key: str = "", model: str = "gpt-4o-mini") -> str:
    """Summarize text. Uses LLM if API key is available, otherwise extractive."""
    if api_key:
        result = await llm_summary(text, api_key, model)
        if result:
            return result
    return extractive_summary(text)
