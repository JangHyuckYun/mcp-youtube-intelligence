"""Data quality verification for MCP YouTube Intelligence pipeline."""
import json, re, sys
sys.path.insert(0, "src")

from mcp_youtube_intelligence.core.transcript import fetch_transcript, clean_transcript
from mcp_youtube_intelligence.core.summarizer import extractive_summary
from mcp_youtube_intelligence.core.segmenter import segment_topics
from mcp_youtube_intelligence.core.entities import extract_entities
from mcp_youtube_intelligence.core.comments import fetch_comments, summarize_comments, _is_noise, _analyze_sentiment

# Test videos
VIDEOS = {
    "A": {"id": "4ZkicMOOo3o", "name": "슈카월드 - 경제 이야기 (한국어 긴 영상)", "lang": "ko"},  # 슈카월드
    "B": {"id": "r-oZFd3SOz8", "name": "Fireship - 영어 기술 영상", "lang": "en"},  # Fireship
    "C": {"id": "dQw4w9WgXcQ", "name": "짧은 영상 (뉴스/음악)", "lang": "en"},  # short/popular
}

results = {}

print("=" * 80)
print("MCP YouTube Intelligence - 데이터 품질 검증")
print("=" * 80)

for label, info in VIDEOS.items():
    vid = info["id"]
    print(f"\n{'='*60}")
    print(f"영상 {label}: {info['name']} (ID: {vid})")
    print(f"{'='*60}")
    
    # 1. Transcript fetch
    print("\n[1] 자막 가져오기...")
    tr = fetch_transcript(vid)
    raw = tr.get("best", "") or ""
    lang = tr.get("lang", "unknown")
    print(f"  언어: {lang}, 원본 길이: {len(raw)} chars")
    if not raw:
        print(f"  ❌ 자막 없음 - 스킵")
        continue
    print(f"  원본 처음 200자: {raw[:200]}")
    
    # 2. Clean transcript
    print("\n[2] 자막 정제...")
    cleaned = clean_transcript(raw)
    removed_chars = len(raw) - len(cleaned)
    removal_rate = removed_chars / len(raw) * 100 if raw else 0
    print(f"  정제 후 길이: {len(cleaned)} chars")
    print(f"  제거율: {removal_rate:.1f}% ({removed_chars} chars removed)")
    print(f"  정제 후 처음 200자: {cleaned[:200]}")
    
    # Check for meaning loss - find removed content
    # Find what noise patterns matched
    from mcp_youtube_intelligence.core.transcript import _NOISE_RE
    noise_matches = _NOISE_RE.findall(raw)
    print(f"  노이즈 매칭 수: {len(noise_matches)}")
    if noise_matches:
        unique_noise = set(noise_matches[:20])
        print(f"  노이즈 샘플: {unique_noise}")
    
    # Check dangerous pattern: "음악 산업" should not lose "음악"
    if "음악" in raw and "음악" not in "[음악]":
        # Check if meaningful "음악" in context was preserved
        meaningful_music = re.findall(r'[가-힣]+음악[가-힣]*', raw)
        if meaningful_music:
            preserved = [m for m in meaningful_music if m in cleaned]
            print(f"  '음악' 포함 복합어 원본: {meaningful_music[:5]}")
            print(f"  정제 후 보존: {preserved[:5]}")
    
    # 3. Extractive Summary
    print("\n[3] 추출식 요약...")
    summary = extractive_summary(cleaned, max_sentences=5, max_chars=1000)
    summary_ratio = len(summary) / len(cleaned) * 100 if cleaned else 0
    print(f"  요약 길이: {len(summary)} chars ({summary_ratio:.1f}% of cleaned)")
    print(f"  요약 내용:\n    {summary[:500]}")
    
    # Check sentence completeness
    summary_sentences = re.split(r'[.!?。]\s+', summary)
    incomplete = [s for s in summary_sentences if len(s.strip()) < 10 and s.strip()]
    print(f"  문장 수: {len(summary_sentences)}, 불완전 문장: {len(incomplete)}")
    if incomplete:
        print(f"  불완전 문장 사례: {incomplete[:3]}")
    
    # 4. Topic Segmentation
    print("\n[4] 토픽 세그멘테이션...")
    segments = segment_topics(cleaned)
    print(f"  세그먼트 수: {len(segments)}")
    for seg in segments[:5]:
        preview = seg['text'][:80]
        print(f"    세그먼트 {seg['segment']}: {seg['char_count']} chars - {preview}...")
    
    if len(segments) <= 1:
        print(f"  ⚠️ 세그먼트가 1개 이하 - 마커가 없거나 짧은 영상")
    
    # 5. Entity Extraction
    print("\n[5] 엔티티 추출...")
    entities = extract_entities(cleaned)
    print(f"  추출된 엔티티 수: {len(entities)}")
    for e in entities[:10]:
        print(f"    {e['type']:10} | {e['name']:25} | keyword='{e['keyword']}' | count={e['count']}")
    
    # Longest-match test
    if "삼성전자" in cleaned:
        samsung_entities = [e for e in entities if "Samsung" in e['name']]
        print(f"  삼성전자 longest-match 테스트: {samsung_entities}")
    
    # 6. Comments
    print("\n[6] 댓글 분석...")
    comments = fetch_comments(vid, max_comments=20)
    print(f"  가져온 댓글 수: {len(comments)}")
    if comments:
        summary_c = summarize_comments(comments)
        print(f"  감성 비율: {summary_c['sentiment_ratio']}")
        print(f"  상위 키워드: {[k['word'] for k in summary_c['top_keywords'][:5]]}")
        
        # Manual sentiment check on first 10
        print("\n  [감성 분석 수동 검증 - 처음 10개]")
        for i, c in enumerate(comments[:10]):
            text_preview = c['text'][:60]
            auto_sent = c['sentiment']
            print(f"    {i+1}. [{auto_sent:8}] {text_preview}")
    
    # Store results
    results[label] = {
        "raw_len": len(raw),
        "cleaned_len": len(cleaned),
        "removal_rate": removal_rate,
        "summary_len": len(summary),
        "summary_ratio": summary_ratio,
        "segment_count": len(segments),
        "entity_count": len(entities),
        "comment_count": len(comments),
    }

# ==============================
# 6. Pipeline Information Loss Analysis (Video A)
# ==============================
print("\n" + "=" * 80)
print("전체 파이프라인 정보 손실 분석 (영상 A)")
print("=" * 80)

if "A" in results:
    r = results["A"]
    print(f"  원본 → 정제: {r['removal_rate']:.1f}% 손실")
    info_in_summary = r['summary_ratio']
    print(f"  정제 → 요약: {100 - info_in_summary:.1f}% 압축 (요약이 원문의 {info_in_summary:.1f}%)")
    overall = r['summary_len'] / r['raw_len'] * 100
    print(f"  원본 → 최종 요약: {overall:.1f}% 보존")
    print(f"  엔티티 수: {r['entity_count']}, 세그먼트 수: {r['segment_count']}")

# Unit tests for edge cases
print("\n" + "=" * 80)
print("엣지 케이스 단위 테스트")
print("=" * 80)

# Test: noise removal doesn't kill meaningful content
test_cases = [
    ("[음악] 오늘의 주제는 음악 산업입니다", "음악 산업"),
    ("[Music] The music industry is growing", "music industry"),
    ("1:23 타임스탬프 테스트 2:34", "타임스탬프 테스트"),
    ("아 어 음 그래서 결론은", "그래서 결론은"),
]

for raw_t, must_contain in test_cases:
    cleaned_t = clean_transcript(raw_t)
    ok = must_contain in cleaned_t
    status = "✅" if ok else "❌"
    print(f"  {status} '{raw_t[:40]}' → '{cleaned_t[:40]}' (must contain '{must_contain}')")

# Test: longest match
test_text = "삼성전자의 주가가 올랐다. 삼성의 전략은"
ents = extract_entities(test_text)
samsung_ents = [e for e in ents if "Samsung" in e['name']]
# Should have count for 삼성전자 and 삼성 but no overlap
print(f"\n  Longest-match 테스트: '{test_text}'")
for e in samsung_ents:
    print(f"    {e['keyword']}: count={e['count']}")

# English segmenter test
en_text = "First topic is about AI. AI is changing everything. Moving on to the next point. Blockchain is also important. Let's talk about quantum computing."
en_segs = segment_topics(en_text)
print(f"\n  영어 세그멘테이션 테스트: {len(en_segs)} segments")
for s in en_segs:
    print(f"    seg {s['segment']}: {s['text'][:60]}")

print("\n" + "=" * 80)
print("검증 완료")
print("=" * 80)
