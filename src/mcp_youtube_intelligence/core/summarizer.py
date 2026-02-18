"""Summarization: extractive (default) with optional LLM-based summarization."""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def extractive_summary(text: str, max_sentences: int = 5, max_chars: int = 1000) -> str:
    """Simple extractive summary picking prominent sentences from the beginning."""
    if not text:
        return ""
    sentences = re.split(r"[.!?。]\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return text[:max_chars]

    # Score: length × position weight (earlier = better)
    scored = []
    for i, s in enumerate(sentences):
        score = len(s) * max(0.1, 1.0 - i * 0.02)
        scored.append((score, i, s))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Take top N, then re-order by original position
    picked = sorted(scored[:max_sentences], key=lambda x: x[1])
    result = ". ".join(s for _, _, s in picked) + "."
    return result[:max_chars]


async def llm_summary(text: str, api_key: str, model: str = "gpt-4o-mini", max_chars: int = 1500) -> Optional[str]:
    """Summarize text using OpenAI API. Returns None on failure."""
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        # Truncate input to avoid excessive token usage
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
