"""Transcript extraction, cleaning, and management."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Noise patterns to strip from transcripts
NOISE_PATTERNS = [
    # Korean tags
    r"\[음악\]", r"\[박수\]", r"\[웃음\]", r"\[박수와 환호\]",
    # English tags
    r"\[Music\]", r"\[Applause\]", r"\[Laughter\]", r"\[inaudible\]",
    r"\[Inaudible\]", r"\[INAUDIBLE\]",
    # Generic bracket tags (e.g. [__], [ __ ], [♪], [♪♪♪])
    r"\[\s*[_♪♫]+\s*\]",
    r"\[\s*\]",  # empty brackets
    # Standalone music symbols (not inside brackets)
    r"[♪♫]+",
    # Timestamps like 1:23 or 1:23:45
    r"\d{1,2}:\d{2}(:\d{2})?",
    # Korean filler sounds
    r"(?:아|어|음|으|에)\s*(?:아|어|음|으|에)\s*",
    # English filler words (standalone, word-boundary)
    r"\b[Uu]mm?\b",   # um, umm
    r"\b[Uu]hh?\b",   # uh, uhh
    r"\b[Yy]ou know\b",
    r"\b[Ss]ort of\b",
    r"\b[Kk]ind of\b",
]
_NOISE_RE = re.compile("|".join(NOISE_PATTERNS))

# Detect duplicate consecutive sentences (auto-generated subtitle artifacts)
_DUPLICATE_SENTENCE_RE = re.compile(r"(.{20,}?)\s+\1")


def clean_transcript(text: str) -> str:
    """Remove noise patterns, duplicates, and normalize whitespace."""
    if not text:
        return ""
    text = _NOISE_RE.sub(" ", text)
    # Remove duplicate consecutive sentences
    text = _DUPLICATE_SENTENCE_RE.sub(r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_transcript(video_id: str) -> dict:
    """Fetch transcript using youtube-transcript-api. Returns dict with keys:
    auto_ko, auto_en, manual, best, lang, timed_segments.
    """
    result: dict = {
        "auto_ko": None, "auto_en": None, "manual": None,
        "best": None, "lang": None, "timed_segments": [],
    }
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        best_segments = None

        # Manual Korean
        for tr in transcript_list:
            if not tr.is_generated and tr.language_code.startswith("ko"):
                fetched = tr.fetch()
                segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in fetched]
                text = " ".join(s.text for s in fetched)
                result["manual"] = text
                if not best_segments:
                    best_segments = segments
                    result["best"] = text
                    result["lang"] = "ko_manual"
                break

        # Auto Korean
        for tr in transcript_list:
            if tr.is_generated and tr.language_code.startswith("ko"):
                fetched = tr.fetch()
                text = " ".join(s.text for s in fetched)
                segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in fetched]
                result["auto_ko"] = text
                if not best_segments:
                    best_segments = segments
                    result["best"] = text
                    result["lang"] = "ko_auto"
                break

        # English
        for tr in transcript_list:
            if tr.language_code.startswith("en"):
                fetched = tr.fetch()
                text = " ".join(s.text for s in fetched)
                segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in fetched]
                if tr.is_generated:
                    result["auto_en"] = text
                else:
                    result["manual"] = result["manual"] or text
                if not best_segments:
                    best_segments = segments
                    result["best"] = text
                    result["lang"] = f"en_{'auto' if tr.is_generated else 'manual'}"
                break

        result["timed_segments"] = best_segments or []

    except Exception as e:
        logger.debug("Transcript fetch error for %s: %s", video_id, e)

    return result


def save_transcript_file(video_id: str, text: str, transcript_dir: str) -> str:
    """Save full transcript to a file and return the path."""
    path = Path(transcript_dir) / f"{video_id}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def summarize_extractive(text: str, max_sentences: int = 5) -> str:
    """Simple extractive summary: pick longest sentences from the start."""
    if not text:
        return ""
    sentences = re.split(r"[.!?。]\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return text[:500]
    scored = []
    for i, s in enumerate(sentences):
        score = len(s) * (1.0 - i * 0.02)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = scored[:max_sentences]
    picked_texts = [s for _, s in picked]
    return ". ".join(picked_texts) + "."


def make_chunks(text: str, chunk_size: int = 2000) -> list[dict]:
    """Split text into chunks of approximately chunk_size characters."""
    if not text:
        return []
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        chunks.append({"index": len(chunks), "text": chunk, "char_count": len(chunk)})
    return chunks
