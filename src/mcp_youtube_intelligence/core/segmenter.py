"""Topic segmentation for transcripts."""
from __future__ import annotations

import re

# Minimum segment size in characters — smaller segments merge into previous
MIN_SEGMENT_CHARS = 50

# Markers that indicate a topic transition
# Each pattern is anchored to sentence start: after sentence-ending punctuation
# or at the very beginning of text.
TOPIC_MARKERS = [
    r"(?:자[,.]?\s*)?(?:다음|두\s*번째|세\s*번째|네\s*번째|첫\s*번째|마지막)\s*(?:주제|얘기|이야기)",
    r"오늘의?\s*(?:첫|두|세|네|다섯)\s*번째\s*주제",
    r"(?:자[,.]?\s*)?(?:다음으로|그\s*다음)",
    r"자[,.]?\s*이번에는",
    # English markers
    r"(?:next|first|second|third|fourth|fifth|last)\s+(?:topic|point|thing)",
    r"moving\s+on\s+to",
    r"let'?s\s+talk\s+about",
]

# Combined pattern: marker must appear at sentence boundary
# (start of text, or after ". " / "! " / "? " — i.e., not mid-sentence)
_SENTENCE_START = r"(?:^|(?<=\.\s)|(?<=!\s)|(?<=\?\s)|(?<=。\s))"
_COMBINED_RE = re.compile(
    _SENTENCE_START + r"(?:" + "|".join(TOPIC_MARKERS) + r")",
    re.IGNORECASE | re.MULTILINE,
)


def segment_topics(text: str) -> list[dict]:
    """Split transcript text into topic segments based on marker patterns.

    Markers only match at sentence boundaries to prevent false positives
    (e.g. "the next thing in the code" mid-sentence won't trigger a split).
    Segments smaller than MIN_SEGMENT_CHARS are merged into the previous segment.

    Returns list of dicts with keys: segment (int), text (str), char_count (int).
    """
    if not text or not text.strip():
        return []

    matches = list(_COMBINED_RE.finditer(text))

    if not matches:
        t = text.strip()
        return [{"segment": 0, "text": t, "char_count": len(t)}]

    raw_segments: list[str] = []

    # Text before the first marker
    before = text[:matches[0].start()].strip()
    if before:
        raw_segments.append(before)

    # Each marker starts a new segment
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            raw_segments.append(chunk)

    if not raw_segments:
        t = text.strip()
        return [{"segment": 0, "text": t, "char_count": len(t)}]

    # Merge small segments into previous
    merged: list[str] = [raw_segments[0]]
    for seg in raw_segments[1:]:
        if len(seg) < MIN_SEGMENT_CHARS and merged:
            merged[-1] = merged[-1] + " " + seg
        else:
            merged.append(seg)

    return [
        {"segment": i, "text": s, "char_count": len(s)}
        for i, s in enumerate(merged)
    ]
