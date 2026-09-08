"""TextRank vs TF-IDF extractive summary 비교 테스트"""
import re
import math
from collections import Counter

# ── 공통 유틸 ──

_MUSIC_RE = re.compile(r"\[?[♪♫♬]+\]?")
_STOPWORDS = frozenset(
    "the a an is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between and but or nor not so yet "
    "this that these those it its he she they we you i me him her us them my "
    "his our your their what which who whom how when where why all each every "
    "both few more most other some such no any if than too very just about also "
    "then only still even because since while although though after before until "
    "은 는 이 가 을 를 에 에서 의 와 과 도 로 으로 한 된 하는 있는 없는 그 이 저 것 수 등 "
    "좀 잘 더 또 안 못 제 너 나 요 네 거 건 게 데 때 곳 중 다 해 줘 줄 걸 뭐 왜".split()
)

_IMPORTANCE_RE = re.compile(
    r"\b(결론|핵심|요약하면|정리하면|요점|중요한|"
    r"in summary|to summarize|the key point|importantly|in conclusion|"
    r"takeaway|bottom line|to recap|the main|crucial|essential)\b",
    re.IGNORECASE,
)

def clean(text):
    text = _MUSIC_RE.sub("", text)
    return re.sub(r"\s{2,}", " ", text).strip()

def split_sentences(text):
    # 마침표/느낌표/물음표 + 공백, 또는 줄바꿈
    parts = re.split(r"(?<=[.!?。])\s+|\n+", text)
    return [p.strip() for p in parts if p and len(p.strip()) > 15]

def tokenize(text):
    return [w.lower() for w in re.findall(r"[a-zA-Z가-힣\d]+", text) if len(w) > 1]

def adaptive_max_chars(text_len):
    if text_len < 1000: return max(200, int(text_len * 0.50))
    if text_len < 5000: return max(200, int(text_len * 0.20))
    if text_len < 20000: return max(200, int(text_len * 0.10))
    return max(200, int(text_len * 0.05))


# ── TextRank 구현 ──

def _cosine_similarity(a_tokens, b_tokens):
    """두 문장의 토큰 간 코사인 유사도"""
    a_filtered = [t for t in a_tokens if t not in _STOPWORDS]
    b_filtered = [t for t in b_tokens if t not in _STOPWORDS]
    if not a_filtered or not b_filtered:
        return 0.0
    a_counter = Counter(a_filtered)
    b_counter = Counter(b_filtered)
    all_words = set(a_counter) | set(b_counter)
    dot = sum(a_counter.get(w, 0) * b_counter.get(w, 0) for w in all_words)
    mag_a = math.sqrt(sum(v**2 for v in a_counter.values()))
    mag_b = math.sqrt(sum(v**2 for v in b_counter.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def textrank_summary(text, max_sentences=7, max_chars=0):
    """TextRank 기반 요약: 문장 간 유사도 그래프 → PageRank → 상위 문장 선택"""
    text = clean(text)
    if not text:
        return ""
    if max_chars <= 0:
        max_chars = adaptive_max_chars(len(text))
    
    sentences = split_sentences(text)
    sentences = [s for s in sentences if len(s.strip()) > 20]
    if len(sentences) <= max_sentences:
        result = ". ".join(sentences)
        return result[:max_chars]
    
    n = len(sentences)
    
    # 1. 토큰화
    sent_tokens = [tokenize(s) for s in sentences]
    
    # 2. 유사도 행렬 구축
    similarity_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim = _cosine_similarity(sent_tokens[i], sent_tokens[j])
            similarity_matrix[i][j] = sim
            similarity_matrix[j][i] = sim
    
    # 3. PageRank 반복 (damping=0.85, 30회)
    damping = 0.85
    scores = [1.0 / n] * n
    for _ in range(30):
        new_scores = [0.0] * n
        for i in range(n):
            rank_sum = 0.0
            for j in range(n):
                if i == j:
                    continue
                # j에서 나가는 링크의 합
                out_sum = sum(similarity_matrix[j][k] for k in range(n) if k != j)
                if out_sum > 0:
                    rank_sum += similarity_matrix[j][i] * scores[j] / out_sum
            new_scores[i] = (1 - damping) / n + damping * rank_sum
        scores = new_scores
    
    # 4. 위치 + 키워드 보너스
    for i in range(n):
        if i == 0:
            scores[i] *= 1.3
        elif i == n - 1:
            scores[i] *= 1.2
        if _IMPORTANCE_RE.search(sentences[i]):
            scores[i] *= 1.5
    
    # 5. 상위 문장 선택 (중복 제거)
    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)
    selected_indices = []
    for idx in ranked:
        if len(selected_indices) >= max_sentences:
            break
        # 중복 체크 (Jaccard > 0.5)
        is_dup = False
        for sel_idx in selected_indices:
            ta = set(sent_tokens[idx]) - _STOPWORDS
            tb = set(sent_tokens[sel_idx]) - _STOPWORDS
            if ta and tb and len(ta & tb) / len(ta | tb) > 0.5:
                is_dup = True
                break
        if not is_dup:
            selected_indices.append(idx)
    
    # 6. 원래 순서로 정렬
    selected_indices.sort()
    
    # 7. max_chars 내에서 조합
    parts = []
    total = 0
    for idx in selected_indices:
        s = sentences[idx]
        addition = len(s) + (2 if parts else 0)
        if total + addition > max_chars and parts:
            break
        parts.append(s)
        total += addition
    
    result = ". ".join(parts)
    if result and not result.endswith((".", "!", "?")):
        result += "."
    return result


# ── 기존 TF-IDF (현재 코드 그대로) ──

def tfidf_summary(text, max_sentences=7, max_chars=0):
    """현재 extractive_summary와 동일한 로직"""
    from mcp_youtube_intelligence.core.summarizer import extractive_summary
    return extractive_summary(text, max_sentences=max_sentences, max_chars=max_chars)


# ── 비교 테스트 실행 ──

if __name__ == "__main__":
    from mcp_youtube_intelligence.core.transcript import fetch_transcript
    
    videos = [
        ("kCc8FmEb1nY", "Let's build GPT (Karpathy, 영어 긴 영상)"),
        ("pBy1zgt0XPc", "한국어 짧은 영상"),
        ("aircAruvnKk", "한국어 중간 영상"),
    ]
    
    for vid, desc in videos:
        print(f"\n{'='*80}")
        print(f"📹 {desc} ({vid})")
        print(f"{'='*80}")
        
        result = fetch_transcript(vid)
        raw = result['best']
        if not raw:
            print("  ❌ 자막 없음, 스킵")
            continue
        
        print(f"  📝 원본: {len(raw):,} chars | 언어: {result['lang']}")
        print(f"  📏 목표 요약 길이: {adaptive_max_chars(len(raw))} chars")
        
        # TF-IDF 요약
        tfidf = tfidf_summary(raw)
        print(f"\n  ── TF-IDF (현재) ──")
        print(f"  길이: {len(tfidf)} chars ({len(tfidf)*100//len(raw)}% of original)")
        print(f"  내용: {tfidf[:400]}")
        
        # TextRank 요약  
        tr = textrank_summary(raw)
        print(f"\n  ── TextRank (신규) ──")
        print(f"  길이: {len(tr)} chars ({len(tr)*100//len(raw)}% of original)")
        print(f"  내용: {tr[:400]}")
        
        # 비교 분석
        print(f"\n  ── 비교 ──")
        # 겹치는 문장 확인
        tfidf_sents = set(tfidf.split(". "))
        tr_sents = set(tr.split(". "))
        overlap = tfidf_sents & tr_sents
        print(f"  겹치는 문장: {len(overlap)}/{max(len(tfidf_sents), len(tr_sents))}")
        print(f"  TF-IDF 고유 문장 수: {len(tfidf_sents - tr_sents)}")
        print(f"  TextRank 고유 문장 수: {len(tr_sents - tfidf_sents)}")
