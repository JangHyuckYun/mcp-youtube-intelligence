"""Data quality verification - Round 2 with working videos."""
import re, sys
sys.path.insert(0, "src")

from mcp_youtube_intelligence.core.transcript import fetch_transcript, clean_transcript, _NOISE_RE
from mcp_youtube_intelligence.core.summarizer import extractive_summary
from mcp_youtube_intelligence.core.segmenter import segment_topics
from mcp_youtube_intelligence.core.entities import extract_entities
from mcp_youtube_intelligence.core.comments import fetch_comments, summarize_comments, _is_noise, _analyze_sentiment

VIDEOS = {
    "A": {"id": "PkZNo7MFNFg", "name": "Learn Python (영어 긴 영상 ~4.5h)", "lang": "en"},
    "B": {"id": "aircAruvnKk", "name": "한국어 영상 (ko manual)", "lang": "ko"},
    "C": {"id": "dQw4w9WgXcQ", "name": "Rick Astley - 짧은 영상", "lang": "en"},
}

for label, info in VIDEOS.items():
    vid = info["id"]
    print(f"\n{'='*70}")
    print(f"영상 {label}: {info['name']} (ID: {vid})")
    print(f"{'='*70}")
    
    tr = fetch_transcript(vid)
    raw = tr.get("best", "") or ""
    lang = tr.get("lang", "unknown")
    print(f"언어: {lang}, 원본: {len(raw)} chars")
    if not raw:
        print("❌ 자막 없음"); continue
    
    # === 1. Transcript Cleaning ===
    cleaned = clean_transcript(raw)
    removed = len(raw) - len(cleaned)
    rate = removed / len(raw) * 100
    noise_matches = _NOISE_RE.findall(raw)
    
    print(f"\n--- 1. 자막 정제 ---")
    print(f"제거율: {rate:.1f}% ({removed} chars)")
    print(f"노이즈 매치: {len(noise_matches)}")
    if noise_matches:
        print(f"노이즈 샘플: {list(set(noise_matches))[:10]}")
    print(f"원본 처음 150자: {raw[:150]}")
    print(f"정제 후 150자: {cleaned[:150]}")
    
    # === 2. Extractive Summary ===
    summary = extractive_summary(cleaned, max_sentences=5, max_chars=1000)
    s_ratio = len(summary) / len(cleaned) * 100
    sents = [s.strip() for s in re.split(r'[.!?。]\s+', summary) if s.strip()]
    incomplete = [s for s in sents if len(s) < 10]
    
    print(f"\n--- 2. 추출식 요약 ---")
    print(f"요약: {len(summary)} chars ({s_ratio:.1f}% of cleaned)")
    print(f"문장 수: {len(sents)}, 불완전: {len(incomplete)}")
    print(f"요약 내용: {summary[:300]}")
    
    # === 3. Topic Segmentation ===
    segments = segment_topics(cleaned)
    print(f"\n--- 3. 토픽 세그멘테이션 ---")
    print(f"세그먼트: {len(segments)}")
    for seg in segments[:8]:
        print(f"  [{seg['segment']}] {seg['char_count']}ch: {seg['text'][:70]}...")
    
    # === 4. Entity Extraction ===
    entities = extract_entities(cleaned)
    print(f"\n--- 4. 엔티티 추출 ---")
    print(f"추출: {len(entities)}")
    for e in entities[:10]:
        print(f"  {e['type']:10} {e['name']:20} kw='{e['keyword']}' cnt={e['count']}")
    
    # === 5. Comments ===
    print(f"\n--- 5. 댓글 ---")
    comments = fetch_comments(vid, max_comments=15)
    print(f"댓글: {len(comments)}")
    if comments:
        cs = summarize_comments(comments)
        print(f"감성: {cs['sentiment_ratio']}")
        for i, c in enumerate(comments[:10]):
            print(f"  {i+1}. [{c['sentiment']:8}] {c['text'][:60]}")

# === Edge Case Tests ===
print(f"\n{'='*70}")
print("엣지 케이스 + 단위 테스트")
print(f"{'='*70}")

# Noise cleaning preserves meaning
tests = [
    ("[음악] 음악 산업은 성장합니다", "음악 산업"),
    ("[Music] The music industry grows", "music industry"),
    ("1:23 시간에 2:34 이야기", "시간에 이야기"),
    ("아 어 음 그래서 결론", "그래서 결론"),
    ("[박수] 박수를 보냅니다", "박수를 보냅니다"),
]
print("\n[노이즈 제거 의미 보존 테스트]")
for raw_t, must in tests:
    c = clean_transcript(raw_t)
    ok = must in c
    print(f"  {'✅' if ok else '❌'} '{raw_t}' → '{c}' (must: '{must}')")

# Longest match
print("\n[Longest-match 테스트]")
t1 = "삼성전자가 좋다. 삼성의 미래."
e1 = extract_entities(t1)
for e in e1:
    print(f"  {e['keyword']}: count={e['count']}")
# 삼성전자 should match first, then 삼성 in second sentence
has_samsung = any(e['keyword'] == '삼성전자' for e in e1)
has_samsung2 = any(e['keyword'] == '삼성' for e in e1)
print(f"  삼성전자 매치: {has_samsung}, 삼성(별도) 매치: {has_samsung2}")

# English segmenter
print("\n[영어 세그멘테이션]")
en = "Welcome. First topic is AI. It changes everything. Moving on to cloud computing. It's growing fast. Let's talk about security."
segs = segment_topics(en)
print(f"  세그먼트: {len(segs)}")
for s in segs:
    print(f"    [{s['segment']}] {s['text'][:60]}")

# Korean segmenter
print("\n[한국어 세그멘테이션]")
ko = "안녕하세요. 첫 번째 주제는 경제입니다. 성장률이 낮습니다. 자 다음으로 부동산 얘기를 하겠습니다. 집값이 올랐습니다. 자 마지막 주제는 AI입니다."
segs_ko = segment_topics(ko)
print(f"  세그먼트: {len(segs_ko)}")
for s in segs_ko:
    print(f"    [{s['segment']}] {s['text'][:60]}")

# Sentiment
print("\n[감성 분석 테스트]")
sent_tests = [
    ("정말 최고예요! 감사합니다", "positive"),
    ("최악이다 실망", "negative"),
    ("오늘 날씨가 좋다", "neutral"),
    ("This is amazing and wonderful", "positive"),
    ("terrible and boring", "negative"),
]
correct = 0
for text, expected in sent_tests:
    got = _analyze_sentiment(text)
    ok = got == expected
    correct += ok
    print(f"  {'✅' if ok else '❌'} '{text}' → {got} (expected {expected})")
print(f"  감성 정확도: {correct}/{len(sent_tests)} = {correct/len(sent_tests)*100:.0f}%")

# Noise filter
print("\n[노이즈 필터 테스트]")
noise_tests = [
    ("ㅋㅋ", True), ("😂😂😂", True), ("구독 좋아요 눌러주세요", True),
    ("sub 4 sub check my channel", True), ("이 영상 정말 유익해요 경제에 대해 많이 배웠습니다", False),
    ("hi", True), ("Great video explaining complex topics clearly", False),
]
nc = 0
for text, expected in noise_tests:
    got = _is_noise(text)
    ok = got == expected
    nc += ok
    print(f"  {'✅' if ok else '❌'} '{text[:40]}' noise={got} (expected {expected})")
print(f"  노이즈 필터 정확도: {nc}/{len(noise_tests)} = {nc/len(noise_tests)*100:.0f}%")

print("\n✅ 검증 완료")
