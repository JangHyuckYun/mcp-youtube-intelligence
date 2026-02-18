"""Summarization: extractive (default) with optional multi-provider LLM summarization."""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
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

# Music symbols cleanup
_MUSIC_RE = re.compile(r"\[?[♪♫♬]+\]?")

# Sentence splitting: Korean endings (다/요/까/죠/지 + punctuation) and general punctuation
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[다요까죠지니고])[.?!]\s+"
    r"|(?<=[.!?。])\s+"
)

_SYSTEM_PROMPT = (
    "Summarize the following transcript concisely. "
    "Focus on key points, arguments, and conclusions. Keep it under 300 words."
)
_USER_PROMPT_PREFIX = "Summarize concisely in the same language:\n\n"
_MAX_INPUT_CHARS = 30_000

# Stopwords for TF-IDF (common words to ignore)
_STOPWORDS = frozenset(
    "the a an is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between and but or nor not so yet "
    "this that these those it its he she they we you i me him her us them my "
    "his our your their what which who whom how when where why all each every "
    "both few more most other some such no any if than too very just about also "
    "then only still even because since while although though after before until "
    "은 는 이 가 을 를 에 에서 의 와 과 도 로 으로 한 된 하는 있는 없는 그 이 저 것 수 등".split()
)


def _clean_music_symbols(text: str) -> str:
    """Remove music symbols from subtitle text."""
    text = _MUSIC_RE.sub("", text)
    # Clean up extra whitespace left behind
    return re.sub(r"\s{2,}", " ", text).strip()


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return [w.lower() for w in re.findall(r"[a-zA-Z가-힣\d]+", text) if len(w) > 1]


def _compute_tfidf_scores(sentences: list[str]) -> list[float]:
    """Compute TF-IDF-like score for each sentence."""
    n = len(sentences)
    if n == 0:
        return []

    # Document frequency: how many sentences contain each word
    doc_freq: Counter = Counter()
    sent_tokens = []
    for s in sentences:
        tokens = _tokenize(s)
        unique = set(tokens) - _STOPWORDS
        sent_tokens.append(tokens)
        for w in unique:
            doc_freq[w] += 1

    scores = []
    for tokens in sent_tokens:
        filtered = [t for t in tokens if t not in _STOPWORDS]
        if not filtered:
            scores.append(0.0)
            continue
        tf = Counter(filtered)
        score = 0.0
        for word, count in tf.items():
            df = doc_freq.get(word, 1)
            idf = math.log(n / df + 1)
            score += (count / len(filtered)) * idf
        scores.append(score)
    return scores


def _similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity between two sentences."""
    ta = set(_tokenize(a)) - _STOPWORDS
    tb = set(_tokenize(b)) - _STOPWORDS
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _adaptive_max_chars(text_len: int) -> int:
    """Adaptive summary length based on original text length."""
    if text_len < 1000:
        ratio = 0.50
    elif text_len < 5000:
        ratio = 0.20
    elif text_len < 20000:
        ratio = 0.10
    else:
        ratio = 0.05
    return max(200, int(text_len * ratio))


def extractive_summary(text: str, max_sentences: int = 7, max_chars: int = 0) -> str:
    if not text:
        return ""
    # Clean music symbols first
    text = _clean_music_symbols(text)
    if not text:
        return ""
    if max_chars <= 0:
        max_chars = _adaptive_max_chars(len(text))
    sentences = _split_sentences(text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return text[:max_chars]
    return _ranked_summary(sentences, max_sentences, max_chars)


def _ranked_summary(sentences: list[str], max_sentences: int, max_chars: int) -> str:
    """Score sentences by TF-IDF + position + keyword bonuses, deduplicate, and select top ones."""
    n = len(sentences)
    tfidf_scores = _compute_tfidf_scores(sentences)

    scored: list[tuple[float, int, str]] = []
    for i, s in enumerate(sentences):
        score = tfidf_scores[i] if i < len(tfidf_scores) else 0.0

        # Position bonus: first and last sentences get a boost
        if i == 0:
            score *= 1.5
        elif i == n - 1:
            score *= 1.3
        elif i == 1 or i == n - 2:
            score *= 1.1

        # Keyword bonus
        if _IMPORTANCE_KEYWORDS_RE.search(s):
            score *= 1.6
        if _HAS_NUMBER_RE.search(s):
            score *= 1.4

        # Length bonus (prefer substantive sentences, but not too long)
        slen = len(s)
        if 30 < slen < 200:
            score *= 1.2
        elif slen >= 200:
            score *= 1.0

        scored.append((score, i, s))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Select top sentences with deduplication
    selected: list[tuple[float, int, str]] = []
    for score, idx, sent in scored:
        if len(selected) >= max_sentences:
            break
        # Check similarity with already selected
        is_dup = False
        for _, _, existing in selected:
            if _similarity(sent, existing) > 0.5:
                is_dup = True
                break
        if not is_dup:
            selected.append((score, idx, sent))

    # Sort by original position for coherent output
    selected.sort(key=lambda x: x[1])

    # Build result respecting max_chars
    parts = []
    total = 0
    for _, _, s in selected:
        addition = s if not parts else ". " + s
        if total + len(addition) > max_chars and parts:
            break
        parts.append(s)
        total += len(addition)

    result = ". ".join(parts)
    if result and not result.endswith((".", "!", "?")):
        result += "."
    return result


# ── Provider resolution ──

def _check_ollama_available(base_url: str) -> bool:
    """Check if Ollama server is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        return False


def resolve_provider(config: Config) -> Optional[str]:
    """Resolve which LLM provider to use based on config."""
    provider = config.llm_provider.lower().strip()
    valid = ("openai", "anthropic", "google", "ollama", "vllm", "lmstudio")
    if provider != "auto":
        return provider if provider in valid else None
    # auto: anthropic > openai > google > ollama > vllm > lmstudio
    if config.anthropic_api_key:
        return "anthropic"
    if config.openai_api_key:
        return "openai"
    if config.google_api_key:
        return "google"
    if _check_ollama_available(config.ollama_base_url):
        return "ollama"
    # vllm and lmstudio require explicit config
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


async def _ollama_summary(text: str, base_url: str, model: str) -> Optional[str]:
    try:
        import httpx
    except ImportError:
        raise ImportError(
            "httpx package not installed. Run: pip install httpx"
        )
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text[:_MAX_INPUT_CHARS]},
                ],
                "stream": False,
                "keep_alive": "30m",
            },
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


async def _vllm_summary(text: str, base_url: str, model: str) -> Optional[str]:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. Run: pip install openai"
        )
    client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
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


async def _lmstudio_summary(text: str, base_url: str, model: str) -> Optional[str]:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package not installed. Run: pip install openai"
        )
    client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
    response = await client.chat.completions.create(
        model=model or "local-model",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text[:_MAX_INPUT_CHARS]},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


# ── Main entry points ──

_PROVIDER_MAP = {
    "openai": lambda text, cfg: _openai_summary(text, cfg.openai_api_key, cfg.openai_model),
    "anthropic": lambda text, cfg: _anthropic_summary(text, cfg.anthropic_api_key, cfg.anthropic_model),
    "google": lambda text, cfg: _google_summary(text, cfg.google_api_key, cfg.google_model),
    "ollama": lambda text, cfg: _ollama_summary(text, cfg.ollama_base_url, cfg.ollama_model),
    "vllm": lambda text, cfg: _vllm_summary(text, cfg.vllm_base_url, cfg.vllm_model),
    "lmstudio": lambda text, cfg: _lmstudio_summary(text, cfg.lmstudio_base_url, cfg.lmstudio_model),
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
