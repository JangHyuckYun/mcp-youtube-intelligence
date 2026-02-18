[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)]()
[![PyPI](https://img.shields.io/pypi/v/mcp-youtube-intelligence)](https://pypi.org/project/mcp-youtube-intelligence/)

# MCP YouTube Intelligence

An MCP (Model Context Protocol) server that provides **comprehensive YouTube video intelligence** — transcripts, summaries, entity extraction, topic segmentation, comment analysis, and channel monitoring.

Designed for **token efficiency**: raw transcripts are never returned directly to the LLM. The server processes them server-side and returns summaries, snippets, or file paths instead.

---

## 🤔 Why This Server?

Most YouTube MCP servers (like [mcp-server-youtube-transcript](https://github.com/kimtaeyoon83/mcp-server-youtube-transcript)) are **one-trick ponies** — they dump raw transcripts directly into the LLM context, consuming 5,000–50,000 tokens per video.

**MCP YouTube Intelligence** is different:

| Feature | Other MCP Servers | This Server |
|---------|:-:|:-:|
| Transcript extraction | ✅ | ✅ |
| **Server-side summarization** (token-optimized) | ❌ | ✅ |
| **Channel monitoring** (RSS) | ❌ | ✅ |
| **Comment collection + analysis** | ❌ | ✅ |
| **Topic segmentation** | ❌ | ✅ |
| **Entity extraction** (KR+EN, 70+ entities) | ❌ | ✅ |
| **Transcript search** (keyword, snippets) | ❌ | ✅ |
| SQLite/PostgreSQL storage | ❌ | ✅ |
| Extractive fallback (no API key needed) | ❌ | ✅ |

**Token savings**: ~300 tokens per video (summary) vs. 5,000–50,000 (raw transcript).

---

## 🏗️ Architecture

```
                         ┌─────────────────────────────────────────┐
                         │        MCP YouTube Intelligence         │
                         │                                         │
YouTube ──► yt-dlp/API ──┤  Transcript ──► Clean ──► Summarize ────┤──► MCP Client
                         │      │                                  │    (~300 tokens)
                         │      ├──► Entity Extraction             │
                         │      ├──► Topic Segmentation            │
                         │      └──► Keyword Search                │
                         │                                         │
                         │  Comments ──► Filter ──► Summarize      │
                         │  RSS Feed ──► Monitor ──► New Videos    │
                         │                                         │
                         │      ▼                                  │
                         │  SQLite / PostgreSQL                    │
                         └─────────────────────────────────────────┘
```

**Key insight**: The heavy processing (cleaning, summarization, segmentation) happens **on the server**, so the MCP client only receives compact results. This preserves the LLM's context window for actual reasoning.

---

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install mcp-youtube-intelligence

# Or with pip
pip install mcp-youtube-intelligence

# With optional dependencies
pip install "mcp-youtube-intelligence[llm]"       # OpenAI for server-side summarization
pip install "mcp-youtube-intelligence[postgres]"  # PostgreSQL storage backend
pip install "mcp-youtube-intelligence[dev]"       # Development (pytest, etc.)
```

> **Prerequisite**: `yt-dlp` must be installed and in your PATH.
> ```bash
> pip install yt-dlp
> # or: brew install yt-dlp
> ```

### Run as MCP Server

```bash
mcp-youtube-intelligence
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "MYI_OPENAI_MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

### OpenCode / Cursor Configuration

```json
{
  "youtube": {
    "command": "uvx",
    "args": ["mcp-youtube-intelligence"],
    "env": {
      "OPENAI_API_KEY": "sk-..."
    }
  }
}
```

---

## 📖 Quick Start Scenarios

### Scenario 1: Get a Video Summary

Ask your LLM: *"Summarize this YouTube video: https://youtube.com/watch?v=dQw4w9WgXcQ"*

The LLM calls `get_transcript` with `mode=summary`. Result: ~300 tokens instead of the full transcript.

```json
// Request
{
  "tool": "get_transcript",
  "arguments": {
    "video_id": "dQw4w9WgXcQ",
    "mode": "summary"
  }
}

// Response (~300 tokens)
{
  "video_id": "dQw4w9WgXcQ",
  "mode": "summary",
  "summary": "The video discusses...",
  "char_count": 15420
}
```

### Scenario 2: Monitor a Channel

```json
// Subscribe
{
  "tool": "monitor_channel",
  "arguments": {
    "channel_ref": "@3blue1brown",
    "action": "add"
  }
}

// Check for new videos
{
  "tool": "monitor_channel",
  "arguments": {
    "channel_ref": "UCYO_jab_esuFRV4b17AJtAw",
    "action": "check"
  }
}
```

### Scenario 3: Search Across Transcripts

```json
{
  "tool": "search_transcripts",
  "arguments": {
    "query": "transformer architecture",
    "limit": 5
  }
}
```

---

## 🔧 Tools Reference

### `get_video`

Get video metadata + summary in one call. Caches results for subsequent requests.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID (e.g., `dQw4w9WgXcQ`) |

**Response** (~300 tokens):
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "channel_name": "Channel",
  "published_at": "2024-01-15T00:00:00+00:00",
  "duration_seconds": 612,
  "view_count": 1500000,
  "like_count": 45000,
  "summary": "Concise server-side summary...",
  "transcript_length": 15420,
  "status": "done"
}
```

**Estimated token consumption**: ~300 (summary) or ~500 (with LLM summary)

---

### `get_transcript`

Retrieve transcript in different modes optimized for token usage.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |
| `mode` | string | ❌ | `"summary"` | `summary` · `full` · `chunks` |

**Modes**:
- `summary` — Returns a concise summary (~300 tokens). **Recommended.**
- `full` — Saves transcript to a file, returns the file path (~50 tokens).
- `chunks` — Splits transcript into ~2000-char chunks for sequential processing.

**Response (mode=summary)**:
```json
{
  "video_id": "abc123",
  "mode": "summary",
  "summary": "The video covers three main topics...",
  "char_count": 15420
}
```

**Response (mode=full)**:
```json
{
  "video_id": "abc123",
  "mode": "full",
  "file_path": "/home/user/.mcp-youtube-intelligence/transcripts/abc123.txt",
  "char_count": 15420
}
```

**Response (mode=chunks)**:
```json
{
  "video_id": "abc123",
  "mode": "chunks",
  "chunk_count": 8,
  "chunks": [
    {"index": 0, "text": "First 2000 chars...", "char_count": 2000},
    {"index": 1, "text": "Next 2000 chars...", "char_count": 2000}
  ]
}
```

**Estimated token consumption**: summary ~300 | full ~50 | chunks ~N×500

---

### `get_comments`

Fetch top comments for a video, optionally summarized.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |
| `top_n` | int | ❌ | `10` | Number of top comments to return |
| `summarize` | bool | ❌ | `false` | Return summarized themes instead of raw comments |

**Response**:
```json
{
  "video_id": "abc123",
  "count": 10,
  "comments": [
    {"author": "User1", "text": "Great explanation!", "likes": 245},
    {"author": "User2", "text": "This helped me understand...", "likes": 132}
  ]
}
```

**Estimated token consumption**: ~200–500 depending on `top_n`

---

### `monitor_channel`

RSS-based channel monitoring. Subscribe to channels and detect new uploads.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `channel_ref` | string | ✅ | — | Channel URL, @handle, or channel ID |
| `action` | string | ❌ | `"check"` | `add` · `check` · `list` · `remove` |

**Actions**:
- `add` — Subscribe to a channel
- `check` — Check for new videos since last check
- `list` — List all subscribed channels
- `remove` — Unsubscribe from a channel

**Response (action=check)**:
```json
{
  "channel_id": "UCYO_jab_esuFRV4b17AJtAw",
  "new_videos": [
    {
      "video_id": "abc123",
      "title": "New Video Title",
      "published": "2024-01-20T12:00:00+00:00",
      "link": "https://www.youtube.com/watch?v=abc123"
    }
  ]
}
```

**Estimated token consumption**: ~100–300

---

### `search_transcripts`

Search stored transcripts by keyword. Returns contextual snippets.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `query` | string | ✅ | — | Search keyword or phrase |
| `limit` | int | ❌ | `10` | Maximum results to return |

**Response**:
```json
{
  "query": "transformer",
  "count": 3,
  "results": [
    {
      "video_id": "abc123",
      "title": "Attention Is All You Need Explained",
      "channel_name": "3Blue1Brown",
      "published_at": "2024-01-15",
      "snippet": "...the transformer architecture uses self-attention mechanisms to..."
    }
  ]
}
```

**Estimated token consumption**: ~100–400

---

### `extract_entities`

Extract structured entities from a video's transcript. Supports 70+ Korean and English entities across companies, indices, crypto, countries, sectors, commodities, and people.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |

**Response**:
```json
{
  "video_id": "abc123",
  "entity_count": 5,
  "entities": [
    {"type": "company", "name": "NVIDIA", "keyword": "엔비디아", "count": 12},
    {"type": "sector", "name": "AI", "keyword": "AI", "count": 8},
    {"type": "index", "name": "NASDAQ", "keyword": "나스닥", "count": 5},
    {"type": "person", "name": "Elon Musk", "keyword": "머스크", "count": 3},
    {"type": "crypto", "name": "BTC", "keyword": "비트코인", "count": 2}
  ]
}
```

**Estimated token consumption**: ~150–300

---

### `segment_topics`

Segment a video transcript into topical sections based on transition markers.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |

**Response**:
```json
{
  "video_id": "abc123",
  "segment_count": 4,
  "segments": [
    {"segment": 0, "char_count": 3200, "preview": "First 200 chars of segment..."},
    {"segment": 1, "char_count": 2800, "preview": "First 200 chars of segment..."},
    {"segment": 2, "char_count": 4100, "preview": "First 200 chars of segment..."},
    {"segment": 3, "char_count": 1500, "preview": "First 200 chars of segment..."}
  ]
}
```

**Estimated token consumption**: ~100–250

---

## ⚙️ Configuration

All configuration via environment variables with `MYI_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `MYI_DATA_DIR` | `~/.mcp-youtube-intelligence` | Data directory for SQLite DB and transcripts |
| `MYI_STORAGE` | `sqlite` | Storage backend: `sqlite` or `postgres` |
| `MYI_YT_DLP` | `yt-dlp` | Path to yt-dlp binary |
| `OPENAI_API_KEY` | — | OpenAI API key for LLM summarization |
| `OPENAI_BASE_URL` | — | Custom OpenAI-compatible endpoint |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | Model for LLM summarization |

### LLM Summarization (Optional)

By default, the server uses **extractive summarization** (no API key needed) — it picks prominent sentences from the transcript. For higher-quality summaries, connect an LLM:

**Option 1: OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini
```

**Option 2: Any OpenAI-compatible API** (Ollama, LM Studio, vLLM, etc.)
```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**Token cost comparison:**

| Mode | Client tokens | Server cost |
|------|:------------:|:-----------:|
| No API key (extractive) | ~300 | Free |
| With LLM (gpt-4o-mini) | ~500 | ~$0.001/video |
| Raw transcript (other MCP servers) | 5,000–50,000 | Free but destroys context |

---

## 🔍 Troubleshooting

### `yt-dlp` not found

```
Error: yt-dlp command not found
```

**Solution**: Install yt-dlp:
```bash
pip install yt-dlp
# or
brew install yt-dlp
# or set a custom path:
export MYI_YT_DLP=/usr/local/bin/yt-dlp
```

### No transcript available

Some videos don't have subtitles/captions. The server returns:
```json
{"error": "No transcript available for VIDEO_ID"}
```

**Possible causes**:
- Video has no auto-generated or manual captions
- Video is region-locked or age-restricted
- Video is private or deleted

**Workaround**: Try `get_video` instead — it still returns metadata and can work without a transcript.

### Comments not loading

yt-dlp comment extraction can be slow (30–60s) and may timeout for videos with thousands of comments.

**Solution**: The server limits to 20 comments by default. If it times out, try again or check your network.

### SQLite database locked

If you see `database is locked` errors, ensure only one instance of the server is running.

### OpenAI API errors

If LLM summarization fails, the server automatically falls back to extractive summarization. Check:
- `OPENAI_API_KEY` is set correctly
- Your API key has sufficient credits
- The model name in `MYI_OPENAI_MODEL` is valid

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

```bash
git clone https://github.com/JangHyuckYun/mcp-youtube-intelligence.git
cd mcp-youtube-intelligence
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

- Python 3.10+
- Type hints for all function signatures
- Docstrings for public functions
- Keep tool responses token-efficient

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Ideas for Contribution

- Additional entity dictionaries (Japanese, Chinese, etc.)
- Whisper integration for videos without captions
- Playlist support
- Video comparison tool
- Sentiment analysis for comments
- Export to various formats (CSV, JSON, Markdown)

---

## 📋 Requirements

- Python ≥ 3.10
- `yt-dlp` installed and accessible in PATH
- Internet access for YouTube API calls

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
