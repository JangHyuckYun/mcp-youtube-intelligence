"""Test with synthetic data since YouTube blocks cloud IPs."""
import asyncio
import time
from mcp_youtube_intelligence.core.transcript import clean_transcript
from mcp_youtube_intelligence.core.summarizer import extractive_summary, summarize
from mcp_youtube_intelligence.core.segmenter import segment_topics

# Synthetic transcripts mimicking real tech talks
SYNTHETIC = [
    {
        "video_id": "synth_gpt",
        "title": "Building GPT from Scratch (synthetic)",
        "lang": "en_manual",
        "text": """Today we're going to build a GPT language model from scratch. The key insight behind transformer models is the self-attention mechanism. Self-attention allows each token in the sequence to attend to every other token. This is fundamentally different from recurrent neural networks which process tokens sequentially. The architecture consists of multiple layers of self-attention followed by feed-forward neural networks. Each attention head learns different patterns in the data. For example, one head might learn syntactic relationships while another learns semantic ones. The training process involves predicting the next token given all previous tokens. This is called autoregressive language modeling. We use cross-entropy loss to measure how well our predictions match the actual next tokens. The key hyperparameters are the number of layers, the number of attention heads, and the embedding dimension. Scaling laws tell us that larger models trained on more data generally perform better. However, there are diminishing returns as we scale up. The implementation starts with tokenization, converting raw text into integer sequences. We then create embedding layers that map these integers to dense vectors. Position encodings are added to give the model information about token positions. The multi-head attention mechanism computes queries, keys, and values from the input. The attention weights are computed as the softmax of the scaled dot product of queries and keys. These weights are then used to compute a weighted sum of the values. Layer normalization is applied before each sub-layer for training stability. Residual connections allow gradients to flow directly through the network. The feed-forward network consists of two linear transformations with a GELU activation in between. During training, we use the Adam optimizer with a learning rate warmup followed by cosine decay. Dropout is applied for regularization. The final output layer projects the hidden states back to vocabulary size and we apply softmax to get probability distributions over the vocabulary. In conclusion, transformer models are remarkably simple in their architecture but incredibly powerful when scaled up with sufficient data and compute.""",
    },
    {
        "video_id": "synth_nn",
        "title": "Neural Networks Deep Dive (synthetic)",
        "lang": "en_auto",
        "text": """Let's talk about neural networks from the ground up. A neural network is essentially a function approximator composed of layers of connected neurons. Each neuron computes a weighted sum of its inputs plus a bias term and passes the result through an activation function. The most common activation functions are ReLU, sigmoid, and tanh. ReLU is defined as max of zero and x, which introduces non-linearity while being computationally efficient. The universal approximation theorem tells us that a neural network with a single hidden layer can approximate any continuous function given enough neurons. However, in practice, deeper networks with fewer neurons per layer tend to work better than shallow wide networks. This is because deep networks can learn hierarchical representations of the data. The first layers learn low-level features like edges and textures while deeper layers combine these into high-level concepts. Training a neural network involves minimizing a loss function using gradient descent. The backpropagation algorithm efficiently computes gradients by applying the chain rule of calculus layer by layer from the output back to the input. Stochastic gradient descent processes data in mini-batches rather than the entire dataset at once which introduces beneficial noise that helps escape local minima. Batch normalization normalizes the activations within each mini-batch which stabilizes training and allows higher learning rates. Weight initialization is crucial for training deep networks. Xavier initialization and He initialization are designed to maintain the variance of activations across layers. Convolutional neural networks use local connectivity and weight sharing to efficiently process spatial data like images. Recurrent neural networks maintain a hidden state that captures temporal information making them suitable for sequential data. The vanishing gradient problem occurs when gradients become exponentially small as they propagate through many layers making it difficult to train very deep networks. Residual connections solve this by adding skip connections that allow gradients to flow directly through the network. In summary, neural networks are powerful function approximators that learn hierarchical representations through gradient-based optimization.""",
    },
    {
        "video_id": "synth_cs",
        "title": "Introduction to Computer Science (synthetic)",
        "lang": "en_manual",
        "text": """Welcome to the introduction to computer science. First topic we'll cover is computational thinking. Computational thinking involves breaking down complex problems into smaller manageable pieces. This process is called decomposition. Pattern recognition involves identifying similarities across different problems. Abstraction means focusing on the important information while ignoring irrelevant details. Algorithms are step-by-step instructions for solving problems. Next topic is binary representation. Computers store all information as sequences of zeros and ones called bits. Eight bits make a byte which can represent 256 different values. ASCII uses one byte per character to represent text. Unicode extends this to support characters from all writing systems around the world. Moving on to algorithms and data structures. An array is a contiguous block of memory that stores elements of the same type. A linked list consists of nodes where each node contains data and a pointer to the next node. Binary search trees allow efficient searching sorting and insertion operations. Hash tables provide average case constant time lookups by mapping keys to array indices using a hash function. Let's talk about programming paradigms. Imperative programming describes computation as a sequence of statements that change program state. Object-oriented programming organizes code into objects that encapsulate data and behavior. Functional programming treats computation as evaluation of mathematical functions and avoids mutable state. Each paradigm has its strengths and is suited to different types of problems. Last topic for today is computational complexity. Big O notation describes the upper bound of an algorithm's time or space requirements as a function of input size. An algorithm with O of n complexity scales linearly with input size. An algorithm with O of n squared complexity becomes much slower as input grows. Understanding complexity helps us choose the right algorithm and data structure for each problem. To summarize, computer science is fundamentally about problem solving using computational thinking algorithms and efficient data representations.""",
    },
]

def main():
    print("=" * 60)
    print("1. TRANSCRIPT CLEANING & SUMMARIZATION TEST")
    print("=" * 60)
    
    results = []
    for item in SYNTHETIC:
        raw = item["text"]
        cleaned = clean_transcript(raw)
        summary = extractive_summary(cleaned)
        reduction = (1 - len(summary) / len(cleaned)) * 100
        
        results.append({**item, "raw_len": len(raw), "cleaned_len": len(cleaned),
                        "summary_len": len(summary), "reduction": reduction,
                        "cleaned": cleaned, "summary": summary})
        
        print(f"\n📹 {item['title']} ({item['video_id']})")
        print(f"   Lang: {item['lang']}")
        print(f"   Raw: {len(raw)} → Cleaned: {len(cleaned)} → Summary: {len(summary)} chars")
        print(f"   Reduction: {reduction:.1f}%")
        print(f"   Summary: {summary[:200]}...")

    # Test async summarize (extractive fallback since no API key)
    print("\n\n--- Async summarize() fallback test ---")
    for item in results[:1]:
        s = asyncio.run(summarize(item["cleaned"]))
        print(f"   async summarize() len={len(s)}, same as extractive: {s == item['summary']}")

    print("\n" + "=" * 60)
    print("2. TOPIC SEGMENTATION TEST")
    print("=" * 60)
    
    seg_results = []
    for item in results:
        segments = segment_topics(item["cleaned"])
        quality = _evaluate_segmentation(segments, item["cleaned"])
        
        print(f"\n🔀 {item['title']}")
        print(f"   Segments: {len(segments)}, Quality: {quality}/10")
        for seg in segments:
            label = seg["text"][:60].replace("\n", " ")
            print(f"     [{seg['segment']}] ({seg['char_count']} chars) {label}...")
        
        seg_results.append({"title": item["title"], "num_segments": len(segments),
                           "quality": quality, "segments": segments})

    print("\n" + "=" * 60)
    print("3. BATCH PROCESSING TEST")
    print("=" * 60)
    
    texts = [r["cleaned"] for r in results]
    
    # Sequential
    start = time.time()
    for _ in range(10):
        for t in texts:
            clean_transcript(t)
            extractive_summary(t)
            segment_topics(t)
    seq_time = time.time() - start
    
    # Parallel with asyncio executor
    async def process_one(t):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, clean_transcript, t)
        await loop.run_in_executor(None, extractive_summary, t)
        await loop.run_in_executor(None, segment_topics, t)
    
    async def parallel():
        for _ in range(10):
            await asyncio.gather(*[process_one(t) for t in texts])
    
    start = time.time()
    asyncio.run(parallel())
    par_time = time.time() - start
    
    print(f"\n  Sequential (10 rounds × 3 videos): {seq_time:.4f}s")
    print(f"  Parallel   (10 rounds × 3 videos): {par_time:.4f}s")
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"  Speedup: {speedup:.2f}x")

    # Test edge cases
    print("\n" + "=" * 60)
    print("4. EDGE CASES & BUGS")
    print("=" * 60)
    
    # Empty input
    assert clean_transcript("") == ""
    assert extractive_summary("") == ""
    assert segment_topics("") == []
    print("  ✅ Empty input handled")
    
    # Noise-only input
    noisy = "[Music] [Applause] ♪♪♪ [음악] um uh"
    cleaned = clean_transcript(noisy)
    print(f"  ✅ Noise-only: '{noisy}' → '{cleaned}' (len={len(cleaned)})")
    
    # Very short text
    short = "Hello world."
    segs = segment_topics(short)
    summ = extractive_summary(short)
    print(f"  ✅ Short text: segments={len(segs)}, summary='{summ}'")
    
    # Korean markers
    korean = "첫 번째 주제는 AI입니다. 인공지능은 컴퓨터가 학습하는 기술입니다. 다음 주제는 ML입니다. 머신러닝은 데이터로부터 패턴을 학습합니다. 마지막 주제는 DL입니다. 딥러닝은 신경망을 사용합니다."
    segs = segment_topics(korean)
    print(f"  ✅ Korean markers: {len(segs)} segments")
    for s in segs:
        print(f"      [{s['segment']}] {s['text'][:50]}...")
    
    # Division by zero in batch
    assert segment_topics("   ") == []
    print("  ✅ Whitespace-only input handled")

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    for r in results:
        print(f"\n📹 {r['video_id']} | {r['title']}")
        print(f"   Original: {r['raw_len']} chars → Summary: {r['summary_len']} chars | Reduction: {r['reduction']:.1f}%")
    for s in seg_results:
        print(f"\n🔀 {s['title']}: {s['num_segments']} segments, Quality: {s['quality']}/10")
    print(f"\n⏱️ Sequential: {seq_time:.4f}s | Parallel: {par_time:.4f}s | Speedup: {speedup:.2f}x")


def _evaluate_segmentation(segments, full_text):
    """Heuristic quality score 1-10."""
    n = len(segments)
    text_len = len(full_text)
    
    if n <= 1:
        # Single segment = no segmentation happened
        # Check if text has topic markers that should have been caught
        from mcp_youtube_intelligence.core.segmenter import _COMBINED_RE
        expected = len(list(_COMBINED_RE.finditer(full_text)))
        if expected > 0:
            return 3  # missed markers
        return 5  # no markers to find, acceptable
    
    # Good: multiple segments, reasonable sizes
    sizes = [s["char_count"] for s in segments]
    avg_size = sum(sizes) / len(sizes)
    size_variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
    
    score = 7
    if n >= 3:
        score += 1
    if all(s > 100 for s in sizes):
        score += 1
    if size_variance < avg_size ** 2:
        score += 1
    
    return min(10, score)


if __name__ == "__main__":
    main()
