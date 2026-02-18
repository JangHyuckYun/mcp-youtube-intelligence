"""Transcript extraction, cleaning, and management."""
from __future__ import annotations

import glob
import logging
import re
import subprocess
import tempfile
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


# Language fallback priority order
LANG_FALLBACK_ORDER = ["ko", "en", "ja", "zh", "de", "fr", "es", "pt"]


def _parse_vtt(text: str) -> list[dict]:
    """Parse VTT subtitle text into segments."""
    segments: list[dict] = []
    lines = text.strip().split("\n")
    timestamp_re = re.compile(r"(\d+:)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d+:)?(\d{2}):(\d{2})[.,](\d{3})")
    i = 0
    while i < len(lines):
        m = timestamp_re.match(lines[i])
        if m:
            h1 = int(m.group(1).rstrip(":")) if m.group(1) else 0
            start = h1 * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
            h2 = int(m.group(5).rstrip(":")) if m.group(5) else 0
            end = h2 * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 1000
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() and not timestamp_re.match(lines[i]):
                # Strip VTT tags like <c>, </c>, <00:01:02.345>
                clean = re.sub(r"<[^>]+>", "", lines[i]).strip()
                if clean:
                    text_lines.append(clean)
                i += 1
            if text_lines:
                seg_text = " ".join(text_lines)
                segments.append({"start": start, "duration": round(end - start, 3), "text": seg_text})
        else:
            i += 1
    # Deduplicate consecutive identical texts (common in auto-subs)
    deduped: list[dict] = []
    for seg in segments:
        if not deduped or deduped[-1]["text"] != seg["text"]:
            deduped.append(seg)
    return deduped


def _parse_srt(text: str) -> list[dict]:
    """Parse SRT subtitle text into segments."""
    segments: list[dict] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    ts_re = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")
    for block in blocks:
        lines = block.strip().split("\n")
        for j, line in enumerate(lines):
            m = ts_re.match(line)
            if m:
                start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
                end = int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 1000
                seg_text = " ".join(l.strip() for l in lines[j + 1:] if l.strip())
                if seg_text:
                    segments.append({"start": start, "duration": round(end - start, 3), "text": seg_text})
                break
    return segments


def _fetch_via_ytdlp(video_id: str) -> dict:
    """Fallback: fetch transcript via yt-dlp subprocess."""
    result: dict = {
        "auto_ko": None, "auto_en": None, "manual": None,
        "best": None, "lang": None, "timed_segments": [],
    }
    tmpdir = tempfile.mkdtemp(prefix="myi_ytdlp_")
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--write-sub", "--write-auto-sub",
        "--sub-langs", "ko,en,ja,zh,de,fr,es,pt,*",
        "--skip-download",
        "-o", f"{tmpdir}/%(id)s",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            logger.warning("yt-dlp failed for %s: %s", video_id, proc.stderr[:500])
            return result
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("yt-dlp unavailable or timed out for %s: %s", video_id, e)
        return result

    # Find subtitle files
    sub_files = glob.glob(f"{tmpdir}/{video_id}*.vtt") + glob.glob(f"{tmpdir}/{video_id}*.srt")
    if not sub_files:
        logger.warning("yt-dlp produced no subtitle files for %s in %s", video_id, tmpdir)
        return result

    # Parse all found subtitle files, keyed by lang code
    parsed: dict[str, list[dict]] = {}
    for fpath in sub_files:
        # Extract lang from filename like VIDEO_ID.ko.vtt or VIDEO_ID.en.srt
        fname = Path(fpath).name
        parts = fname.split(".")
        if len(parts) >= 3:
            lang = parts[-2]  # e.g. "ko", "en", "ja"
        else:
            lang = "unknown"
        content = Path(fpath).read_text(encoding="utf-8", errors="replace")
        if fpath.endswith(".vtt"):
            segs = _parse_vtt(content)
        else:
            segs = _parse_srt(content)
        if segs and (lang not in parsed or len(segs) > len(parsed[lang])):
            parsed[lang] = segs

    # Fill result using fallback order
    for lang_code, segs in parsed.items():
        text = " ".join(s["text"] for s in segs)
        if lang_code.startswith("ko"):
            result["auto_ko"] = result["auto_ko"] or text
        elif lang_code.startswith("en"):
            result["auto_en"] = result["auto_en"] or text

    # Pick best by fallback order
    for pref in LANG_FALLBACK_ORDER:
        for lang_code, segs in parsed.items():
            if lang_code.startswith(pref):
                text = " ".join(s["text"] for s in segs)
                result["best"] = text
                result["lang"] = f"{lang_code}_ytdlp"
                result["timed_segments"] = segs
                return result

    # If none matched priority, take first available
    if parsed:
        lang_code, segs = next(iter(parsed.items()))
        text = " ".join(s["text"] for s in segs)
        result["best"] = text
        result["lang"] = f"{lang_code}_ytdlp"
        result["timed_segments"] = segs

    return result


def _select_best_from_list(transcript_list) -> dict:
    """Given a youtube-transcript-api transcript list, pick best using multilingual fallback."""
    result: dict = {
        "auto_ko": None, "auto_en": None, "manual": None,
        "best": None, "lang": None, "timed_segments": [],
    }

    best_segments = None

    # Index transcripts by language prefix for fallback
    by_lang: dict[str, list] = {}
    for tr in transcript_list:
        prefix = tr.language_code[:2]
        by_lang.setdefault(prefix, []).append(tr)

    # Manual Korean
    for tr in by_lang.get("ko", []):
        if not tr.is_generated:
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
    for tr in by_lang.get("ko", []):
        if tr.is_generated:
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
    for tr in by_lang.get("en", []):
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

    # Multilingual fallback: if still no best, try ja → zh → ... → any
    if not best_segments:
        for pref in LANG_FALLBACK_ORDER[2:]:  # skip ko, en already tried
            for tr in by_lang.get(pref, []):
                fetched = tr.fetch()
                text = " ".join(s.text for s in fetched)
                segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in fetched]
                best_segments = segments
                result["best"] = text
                result["lang"] = f"{tr.language_code}_{'auto' if tr.is_generated else 'manual'}"
                break
            if best_segments:
                break

    # Last resort: any available transcript
    if not best_segments:
        for tr in transcript_list:
            fetched = tr.fetch()
            text = " ".join(s.text for s in fetched)
            segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in fetched]
            best_segments = segments
            result["best"] = text
            result["lang"] = f"{tr.language_code}_{'auto' if tr.is_generated else 'manual'}"
            break

    result["timed_segments"] = best_segments or []
    return result


def fetch_transcript(video_id: str) -> dict:
    """Fetch transcript with multilingual fallback + yt-dlp fallback.

    Strategy:
    1. Try youtube-transcript-api (fast, structured)
    2. On failure (IP blocked, etc.) → fallback to yt-dlp subprocess
    3. Language priority: ko → en → ja → zh → de → fr → es → pt → any

    Returns dict with keys:
    auto_ko, auto_en, manual, best, lang, timed_segments, error.
    """
    result: dict = {
        "auto_ko": None, "auto_en": None, "manual": None,
        "best": None, "lang": None, "timed_segments": [], "error": None,
    }

    # --- Attempt 1: youtube-transcript-api ---
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        result = _select_best_from_list(transcript_list)
        result.setdefault("error", None)
        if result.get("best"):
            return result
        # Had transcripts list but none fetched successfully — still try yt-dlp
        logger.info("youtube-transcript-api returned no usable transcript for %s, trying yt-dlp", video_id)
    except Exception as e:
        err_type = type(e).__name__
        logger.warning("youtube-transcript-api failed for %s (%s: %s), trying yt-dlp fallback", video_id, err_type, e)
        result["error"] = f"youtube-transcript-api: {err_type}: {e}"

    # --- Attempt 2: yt-dlp fallback ---
    try:
        ytdlp_result = _fetch_via_ytdlp(video_id)
        if ytdlp_result.get("best"):
            ytdlp_result["error"] = result.get("error")  # preserve original error info
            return ytdlp_result
        logger.warning("yt-dlp also returned no transcript for %s", video_id)
        if not result.get("error"):
            result["error"] = "No transcript found via youtube-transcript-api or yt-dlp"
    except Exception as e2:
        logger.warning("yt-dlp fallback also failed for %s: %s", video_id, e2)
        prev = result.get("error", "")
        result["error"] = f"{prev} | yt-dlp: {type(e2).__name__}: {e2}"

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
