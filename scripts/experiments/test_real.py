"""Real-world test of MCP YouTube Intelligence."""
import asyncio
import time
from mcp_youtube_intelligence.core.transcript import fetch_transcript, clean_transcript
from mcp_youtube_intelligence.core.summarizer import extractive_summary, summarize
from mcp_youtube_intelligence.core.segmenter import segment_topics

# Tech talk videos with known captions
TEST_VIDEOS = [
    ("kCc8FmEb1nY", "Andrej Karpathy - Let's build GPT"),
    ("aircAruvnKk", "3Blue1Brown - Neural Networks"),
    ("PyCqQdFxSMY", "CS50 2024 - Lecture 0 - Scratch"),
    ("8jLOx1hD3_o", "CS50 2023 - Lecture 1 - C"),
    ("YQHsXMglC9A", "Fireship - 100 seconds of code"),
    ("pTB0EiLXUC8", "TED - How great leaders inspire action"),
]

def test_fetch_and_summarize():
    results = []
    good_videos = []
    
    print("=" * 60)
    print("1. TRANSCRIPT FETCH & SUMMARIZE TEST")
    print("=" * 60)
    
    for vid, title in TEST_VIDEOS:
        if len(good_videos) >= 3:
            break
        print(f"\nTrying {vid} ({title})...")
        data = fetch_transcript(vid)
        if not data["best"]:
            print(f"  ❌ No transcript available")
            continue
        
        raw = data["best"]
        cleaned = clean_transcript(raw)
        summary = extractive_summary(cleaned)
        
        reduction = (1 - len(summary) / len(cleaned)) * 100 if cleaned else 0
        
        info = {
            "video_id": vid,
            "title": title,
            "lang": data["lang"],
            "raw_len": len(raw),
            "cleaned_len": len(cleaned),
            "summary_len": len(summary),
            "reduction": reduction,
            "segments_count": len(data["timed_segments"]),
            "cleaned_text": cleaned,
            "summary": summary,
        }
        results.append(info)
        good_videos.append(info)
        
        print(f"  ✅ Lang: {data['lang']}, Raw: {len(raw)}, Cleaned: {len(cleaned)}, Summary: {len(summary)}, Reduction: {reduction:.1f}%")
        print(f"  Summary preview: {summary[:150]}...")
    
    return results

def test_segmentation(results):
    print("\n" + "=" * 60)
    print("2. TOPIC SEGMENTATION TEST")
    print("=" * 60)
    
    seg_results = []
    for info in results:
        text = info["cleaned_text"]
        segments = segment_topics(text)
        
        print(f"\n{info['title']} ({info['video_id']})")
        print(f"  Text length: {len(text)} chars")
        print(f"  Segments: {len(segments)}")
        for seg in segments[:10]:
            preview = seg["text"][:80].replace("\n", " ")
            print(f"    [{seg['segment']}] ({seg['char_count']} chars) {preview}...")
        
        seg_results.append({
            "video_id": info["video_id"],
            "title": info["title"],
            "num_segments": len(segments),
            "segments": segments,
        })
    
    return seg_results

def test_batch(results):
    print("\n" + "=" * 60)
    print("3. BATCH PROCESSING TEST")
    print("=" * 60)
    
    video_ids = [r["video_id"] for r in results]
    
    # Sequential
    start = time.time()
    for vid in video_ids:
        data = fetch_transcript(vid)
        if data["best"]:
            cleaned = clean_transcript(data["best"])
            extractive_summary(cleaned)
    seq_time = time.time() - start
    
    # "Parallel" with asyncio (fetch_transcript is sync, so we use executor)
    async def process_one(vid):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_transcript, vid)
        if data["best"]:
            cleaned = clean_transcript(data["best"])
            extractive_summary(cleaned)
        return data
    
    async def parallel():
        tasks = [process_one(vid) for vid in video_ids]
        return await asyncio.gather(*tasks)
    
    start = time.time()
    asyncio.run(parallel())
    par_time = time.time() - start
    
    print(f"\n  Sequential: {seq_time:.2f}s")
    print(f"  Parallel:   {par_time:.2f}s")
    print(f"  Speedup:    {seq_time/par_time:.2f}x")
    
    return {"sequential": seq_time, "parallel": par_time, "speedup": seq_time/par_time}

if __name__ == "__main__":
    results = test_fetch_and_summarize()
    if len(results) < 3:
        print(f"\n⚠️ Only {len(results)} videos had transcripts")
    
    seg_results = test_segmentation(results)
    batch_results = test_batch(results)
    
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    for r in results:
        print(f"\n📹 {r['title']} ({r['video_id']})")
        print(f"   Lang: {r['lang']}, Original: {r['raw_len']} chars, Summary: {r['summary_len']} chars, Reduction: {r['reduction']:.1f}%")
    
    for s in seg_results:
        print(f"\n🔀 {s['title']}: {s['num_segments']} segments")
    
    print(f"\n⏱️ Batch: Sequential {batch_results['sequential']:.2f}s vs Parallel {batch_results['parallel']:.2f}s ({batch_results['speedup']:.2f}x)")
