# Experiment scripts

Ad-hoc scripts used while tuning summarization, segmentation, and comment
analysis quality. They are **not** part of the package or the test suite and
may hit the real YouTube API.

Run from the repository root:

```bash
uv run python scripts/experiments/quality_test.py
```

| Script | Purpose |
| ------ | ------- |
| `quality_test.py`, `quality_test2.py` | End-to-end quality check on real videos (transcript → summary → topics → entities → comments) |
| `test_real.py` | Timing and output comparison for extractive vs. LLM summaries on real videos |
| `test_synthetic.py` | Same pipeline on synthetic transcripts (offline) |
| `test_textrank_compare.py` | TextRank variant comparison for extractive summarization |
