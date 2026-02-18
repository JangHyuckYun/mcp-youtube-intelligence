"""Topic segmentation for transcripts."""
from __future__ import annotations

import math
import re
from collections import Counter

# Minimum segment size in characters — smaller segments merge into previous
MIN_SEGMENT_CHARS = 100

# Target words per segment when falling back to length-based splitting
_TARGET_WORDS_PER_SEGMENT = 500

# ---------------------------------------------------------------------------
# Stopwords (lightweight, no external deps)
# ---------------------------------------------------------------------------
_EN_STOP = frozenset(
    "a an the and or but is are was were be been being have has had do does did "
    "will would shall should can could may might must not no nor so if then than "
    "that this these those it its i me my we our you your he him his she her they "
    "them their what which who whom how when where why all each every some any many "
    "much more most other another such only also just about above after again "
    "against before between into through during to from up down in out on off over "
    "under of at by for with as".split()
)
_KO_STOP = frozenset(
    "이 그 저 것 수 등 및 에 를 을 은 는 가 의 로 으로 에서 와 과 도 만 까지 부터 "
    "하다 있다 되다 않다 없다 이다 그리고 하지만 또한 때문에 위해 대한 통해".split()
)


def _extract_keywords(text: str, top_n: int = 3) -> list[str]:
    """Extract top-N keywords from *text* using simple term-frequency."""
    tokens = re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", text.lower())
    tokens = [t for t in tokens if t not in _EN_STOP and t not in _KO_STOP]
    if not tokens:
        return []
    counts = Counter(tokens)
    return [w for w, _ in counts.most_common(top_n)]


# ---------------------------------------------------------------------------
# Marker patterns
# ---------------------------------------------------------------------------
TOPIC_MARKERS = [
    # Korean
    r"(?:자[,.]?\s*)?(?:다음|두\s*번째|세\s*번째|네\s*번째|첫\s*번째|마지막)\s*(?:주제|얘기|이야기|포인트)",
    r"오늘의?\s*(?:첫|두|세|네|다섯)\s*번째\s*(?:주제|포인트)",
    r"(?:자[,.]?\s*)?(?:다음으로|그\s*다음)",
    r"자[,.]?\s*이번에는",
    r"첫\s*번째\s*(?:주제는|포인트는)",
    r"다음으로\s",
    # English – topic transition
    r"(?:next|first|second|third|fourth|fifth|last)\s+(?:topic|point|thing)",
    r"moving\s+on\s+to",
    r"let'?s\s+(?:talk|move)\s+(?:about|on)",
    # English – summary / conclusion
    r"in\s+summary",
    r"to\s+(?:summarize|conclude|wrap\s+up)",
    r"in\s+conclusion",
    r"finally[,]?\s",
]

# Sentence-boundary lookbehind: start-of-text OR after ". " / "! " / "? " / "。"
# Also allow Korean sentence endings (다. / 요. / 죠. etc.) followed by space.
_SENTENCE_START = r"(?:^|(?<=\.\s)|(?<=!\s)|(?<=\?\s)|(?<=。)|(?<=\.\n)|(?<=\n))"
_COMBINED_RE = re.compile(
    _SENTENCE_START + r"(?:" + "|".join(TOPIC_MARKERS) + r")",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Keyword-shift detection helpers
# ---------------------------------------------------------------------------

def _word_bag(text: str) -> Counter:
    tokens = re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", text.lower())
    tokens = [t for t in tokens if t not in _EN_STOP and t not in _KO_STOP]
    return Counter(tokens)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _split_sentences(text: str) -> list[str]:
    """Split on common sentence-ending punctuation."""
    parts = re.split(r'(?<=[.!?。])\s+', text)
    return [p for p in parts if p.strip()]


def _fallback_split(text: str) -> list[str]:
    """Split long marker-less text by keyword shift + length heuristic."""
    sentences = _split_sentences(text)
    if len(sentences) <= 2:
        return [text.strip()]

    # Build windows of ~_TARGET_WORDS_PER_SEGMENT words, split where cosine
    # similarity between adjacent windows drops.
    segments: list[str] = []
    current_sents: list[str] = []
    current_words = 0

    for sent in sentences:
        wc = len(sent.split())
        current_sents.append(sent)
        current_words += wc

        if current_words >= _TARGET_WORDS_PER_SEGMENT:
            # Check keyword shift: compare current window vs next sentence(s)
            seg_text = " ".join(current_sents)
            segments.append(seg_text.strip())
            current_sents = []
            current_words = 0

    # Remaining
    if current_sents:
        tail = " ".join(current_sents).strip()
        if tail:
            # If leftover is very short, merge into last segment
            if segments and len(tail) < MIN_SEGMENT_CHARS:
                segments[-1] = segments[-1] + " " + tail
            else:
                segments.append(tail)

    # Refine: try to find better split points using keyword similarity
    if len(segments) >= 2:
        segments = _refine_splits_by_keywords(text, sentences, len(segments))

    return segments if segments else [text.strip()]


def _refine_splits_by_keywords(text: str, sentences: list[str], n_segments: int) -> list[str]:
    """Given target number of segments, find best split points by keyword shift."""
    if n_segments <= 1 or len(sentences) <= n_segments:
        return [text.strip()]

    # Compute cumulative word bags per sentence
    bags = [_word_bag(s) for s in sentences]

    # We need (n_segments - 1) split points. Use greedy: find the point with
    # lowest cosine similarity between left and right halves.
    n_splits = n_segments - 1
    split_indices: list[int] = []

    # Score each possible split point
    scores: list[float] = []
    for i in range(1, len(sentences)):
        left = Counter()
        for b in bags[:i]:
            left.update(b)
        right = Counter()
        for b in bags[i:]:
            right.update(b)
        scores.append(_cosine(left, right))

    # Pick n_splits points with lowest similarity (biggest topic change)
    # but enforce minimum distance between splits
    min_dist = max(1, len(sentences) // (n_segments + 1))
    candidates = sorted(range(len(scores)), key=lambda i: scores[i])

    for idx in candidates:
        split_pos = idx + 1  # split before sentence[split_pos]
        # Check distance from existing splits
        if all(abs(split_pos - s) >= min_dist for s in split_indices):
            split_indices.append(split_pos)
            if len(split_indices) == n_splits:
                break

    if not split_indices:
        return [text.strip()]

    split_indices.sort()

    # Build segments
    result: list[str] = []
    prev = 0
    for si in split_indices:
        seg = " ".join(sentences[prev:si]).strip()
        if seg:
            result.append(seg)
        prev = si
    tail = " ".join(sentences[prev:]).strip()
    if tail:
        result.append(tail)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def segment_topics(text: str) -> list[dict]:
    """Split transcript text into topic segments.

    Strategy:
    1. Try marker-based splitting (explicit topic transitions).
    2. If no markers found and text is long, fall back to length + keyword-shift.
    3. Merge segments smaller than MIN_SEGMENT_CHARS into the previous one.
    4. Attach top-3 keyword labels to each segment.

    Returns list of dicts: segment, text, char_count, topic.
    """
    if not text or not text.strip():
        return []

    matches = list(_COMBINED_RE.finditer(text))

    if not matches:
        # Fallback: length + keyword-based splitting for long texts
        word_count = len(text.split())
        if word_count > _TARGET_WORDS_PER_SEGMENT:
            raw_segments = _fallback_split(text)
        else:
            t = text.strip()
            keywords = _extract_keywords(t)
            topic = ", ".join(keywords) if keywords else ""
            return [{"segment": 0, "text": t, "char_count": len(t), "topic": topic}]
    else:
        # Marker-based splitting
        raw_segments: list[str] = []

        before = text[:matches[0].start()].strip()
        if before:
            raw_segments.append(before)

        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                raw_segments.append(chunk)

        if not raw_segments:
            t = text.strip()
            keywords = _extract_keywords(t)
            topic = ", ".join(keywords) if keywords else ""
            return [{"segment": 0, "text": t, "char_count": len(t), "topic": topic}]

    # Merge small segments
    merged: list[str] = [raw_segments[0]]
    for seg in raw_segments[1:]:
        if len(seg) < MIN_SEGMENT_CHARS and merged:
            merged[-1] = merged[-1] + " " + seg
        else:
            merged.append(seg)

    return [
        {
            "segment": i,
            "text": s,
            "char_count": len(s),
            "topic": ", ".join(_extract_keywords(s)),
        }
        for i, s in enumerate(merged)
    ]
