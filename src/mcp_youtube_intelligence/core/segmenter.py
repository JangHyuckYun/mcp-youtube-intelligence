"""Topic segmentation for transcripts."""
from __future__ import annotations

import re

# Markers that indicate a topic transition (Korean-oriented but extensible)
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

_COMBINED_RE = re.compile("|".join(TOPIC_MARKERS), re.IGNORECASE)


def segment_topics(text: str) -> list[dict]:
    """Split transcript text into topic segments based on marker patterns.

    Returns list of dicts with keys: segment (int), text (str), char_count (int).
    """
    if not text or not text.strip():
        return []

    # Find all marker positions using finditer
    matches = list(_COMBINED_RE.finditer(text))

    if not matches:
        t = text.strip()
        return [{"segment": 0, "text": t, "char_count": len(t)}]

    segments: list[dict] = []
    seg_idx = 0

    # Text before the first marker (if any)
    before = text[:matches[0].start()].strip()
    if before:
        segments.append({"segment": seg_idx, "text": before, "char_count": len(before)})
        seg_idx += 1

    # Each marker starts a new segment that runs until the next marker
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            segments.append({"segment": seg_idx, "text": chunk, "char_count": len(chunk)})
            seg_idx += 1

    return segments if segments else [{"segment": 0, "text": text.strip(), "char_count": len(text.strip())}]
