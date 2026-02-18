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
    if not text:
        return []

    splits = _COMBINED_RE.split(text)

    if len(splits) <= 1:
        return [{"segment": 0, "text": text.strip(), "char_count": len(text.strip())}]

    segments = []
    current = ""
    seg_idx = 0
    for part in splits:
        if _COMBINED_RE.match(part):
            if current.strip():
                t = current.strip()
                segments.append({"segment": seg_idx, "text": t, "char_count": len(t)})
                seg_idx += 1
            current = part
        else:
            current += part
    if current.strip():
        t = current.strip()
        segments.append({"segment": seg_idx, "text": t, "char_count": len(t)})

    return segments if segments else [{"segment": 0, "text": text.strip(), "char_count": len(text.strip())}]
