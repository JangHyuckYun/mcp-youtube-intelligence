[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)]()
[![PyPI](https://img.shields.io/pypi/v/mcp-youtube-intelligence)](https://pypi.org/project/mcp-youtube-intelligence/)

# MCP YouTube Intelligence

> **An MCP server that intelligently analyzes YouTube videos** — transcript extraction, summarization, entity extraction, comment analysis, topic segmentation, and channel monitoring.

🎯 **Core value**: Raw transcripts (5,000–50,000 tokens) are **processed server-side**, delivering only **~300 tokens** to the LLM. No more wasting your context window.

[한국어](README.md)

---

## 🤔 Why This Server?

Most YouTube MCP servers dump raw transcripts directly into the LLM context — consuming tens of thousands of tokens per video.

| Feature | Other MCP Servers | MCP YouTube Intelligence |
|---------|:---:|:---:|
| Transcript extraction | ✅ | ✅ |
| **Server-side summarization** (token-optimized) | ❌ | ✅ |
| **Channel monitoring** (RSS) | ❌ | ✅ |
| **Comment collection + sentiment analysis** | ❌ | ✅ |
| **Topic segmentation** | ❌ | ✅ |
| **Entity extraction** (KR+EN, 200+ entities) | ❌ | ✅ |
| **Transcript search** (keyword → snippets) | ❌ | ✅ |
| **YouTube search** | ❌ | ✅ |
| **Playlist analysis** | ❌ | ✅ |
| **Batch processing** | ❌ | ✅ |
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
                         │  Comments ──► Filter + Sentiment ──► Summary │
                         │  RSS Feed ──► Monitor ──► New Videos    │
                         │                                         │
                         │      ▼                                  │
                         │  SQLite / PostgreSQL                    │
                         └─────────────────────────────────────────┘
```

Heavy processing (cleaning, summarization, analysis) happens **on the server**. The MCP client receives only **compact results**.

---

## 🚀 Quick Start

### Installation

```bash
# uv (recommended)
uv pip install mcp-youtube-intelligence

# pip
pip install mcp-youtube-intelligence

# Optional dependencies
pip install "mcp-youtube-intelligence[llm]"       # OpenAI LLM summarization
pip install "mcp-youtube-intelligence[postgres]"  # PostgreSQL backend
pip install "mcp-youtube-intelligence[dev]"       # Development (pytest, etc.)
```

> **Prerequisite**: `yt-dlp` must be installed and in your PATH.
> ```bash
> pip install yt-dlp
> ```

### CLI Usage

After installation, the `mcp-yt` command is available.

#### Transcript Extraction

```bash
# Summary (default, ~300 tokens)
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ

# Full transcript (saved to file)
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ --mode full

# Split into chunks
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ --mode chunks

# JSON output
mcp-yt --json transcript https://youtube.com/watch?v=dQw4w9WgXcQ

# Save to file
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ -o summary.txt
```

#### YouTube Search

```bash
mcp-yt search "transformer explained"
mcp-yt search "python tutorial" --max 5 --order date
mcp-yt search "AI news" --channel UCxxxx
```

#### Video Metadata + Summary

```bash
mcp-yt video https://youtube.com/watch?v=dQw4w9WgXcQ
```

Sample output:
```
video_id: dQw4w9WgXcQ
title: Video Title
channel_name: Channel Name
duration_seconds: 612
view_count: 1500000
summary: This video covers three main topics...
```

#### Comment Collection

```bash
# Top 10 comments
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ

# Newest 20 comments
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --max 20 --sort newest

# Positive comments only
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --sentiment positive

# Negative comments only
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --sentiment negative
```

#### Channel Monitoring

```bash
# Subscribe
mcp-yt monitor subscribe @3blue1brown

# Check for new videos
mcp-yt monitor check --channel UCYO_jab_esuFRV4b17AJtAw

# List subscriptions
mcp-yt monitor list
```

#### Entity Extraction

```bash
mcp-yt entities https://youtube.com/watch?v=dQw4w9WgXcQ
```

Sample output:
```
entity_count: 5
entities: (5 items)
  [1] type: company, name: NVIDIA, keyword: NVIDIA, count: 12
  [2] type: technology, name: AI, keyword: AI, count: 8
  [3] type: index, name: NASDAQ, keyword: NASDAQ, count: 5
```

#### Topic Segmentation

```bash
mcp-yt segments https://youtube.com/watch?v=dQw4w9WgXcQ
```

#### Playlist

```bash
mcp-yt playlist https://youtube.com/playlist?list=PLrAXtmErZgOe...
mcp-yt playlist PLrAXtmErZgOe... --max 10
```

#### Batch Processing

```bash
mcp-yt batch dQw4w9WgXcQ abc123def45 xyz789ghi01
mcp-yt batch dQw4w9WgXcQ abc123def45 --mode full
```

#### Search Stored Transcripts

```bash
mcp-yt search-transcripts "transformer architecture"
```

> 💡 Add `--json` to any command for JSON output.

---

## 🔌 MCP Server Connection Guide

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add youtube -- uvx mcp-youtube-intelligence
```

### OpenCode

Add to your `mcp.json` or project config:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Cursor

Create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Claude Code Skills

Since a CLI is provided, you can register it as a skill in Claude Code:

```
skills/
  youtube/
    SKILL.md
```

Sample `SKILL.md`:

```markdown
# YouTube Analysis Skill

Use the `mcp-yt` CLI for YouTube video analysis.

## Available Commands

- `mcp-yt transcript <URL>` — Extract/summarize transcript
- `mcp-yt video <URL>` — Video metadata
- `mcp-yt comments <URL>` — Comment analysis
- `mcp-yt entities <URL>` — Entity extraction
- `mcp-yt segments <URL>` — Topic segmentation
- `mcp-yt search "query"` — YouTube search
- `mcp-yt search-transcripts "query"` — Search stored transcripts
- `mcp-yt monitor subscribe <URL>` — Channel monitoring
- `mcp-yt playlist <URL>` — Playlist info
- `mcp-yt batch <id1> <id2>` — Batch processing

## Rules

- Always use `--json` for structured output
- Both video URLs and 11-character IDs are accepted
- Transcript summaries are ~300 tokens by default
```

---

## 🔧 MCP Tools Reference (9 tools)

### 1. `get_video`

Get video metadata + summary in one call. Results are cached.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `video_id` | string | ✅ | YouTube video ID |

```json
// Request
{"tool": "get_video", "arguments": {"video_id": "dQw4w9WgXcQ"}}

// Response (~300 tokens)
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "channel_name": "Channel",
  "duration_seconds": 612,
  "view_count": 1500000,
  "like_count": 45000,
  "summary": "This video covers...",
  "transcript_length": 15420,
  "status": "done"
}
```

**Estimated tokens**: ~300

---

### 2. `get_transcript`

Retrieve transcript in 3 modes.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |
| `mode` | string | ❌ | `"summary"` | `summary` · `full` · `chunks` |

**Modes**:

- **`summary`** — Returns a concise summary (~300 tokens, **recommended**)
- **`full`** — Saves transcript to file, returns path (~50 tokens)
- **`chunks`** — Splits into ~2000-char chunks for sequential processing

```json
// summary mode
{"video_id": "abc123", "mode": "summary", "summary": "...", "char_count": 15420}

// full mode
{"video_id": "abc123", "mode": "full", "file_path": "~/.mcp-youtube-intelligence/transcripts/abc123.txt", "char_count": 15420}

// chunks mode
{"video_id": "abc123", "mode": "chunks", "chunk_count": 8, "chunks": [{"index": 0, "text": "...", "char_count": 2000}]}
```

**Estimated tokens**: summary ~300 | full ~50 | chunks ~N×500

---

### 3. `get_comments`

Fetch comments with automatic spam/noise filtering and sentiment analysis.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `video_id` | string | ✅ | — | YouTube video ID |
| `top_n` | int | ❌ | `10` | Number of comments to return |
| `summarize` | bool | ❌ | `false` | Return summarized view |

```json
{
  "video_id": "abc123",
  "count": 10,
  "comments": [
    {"author": "User1", "text": "Great explanation!", "likes": 245, "sentiment": "positive"},
    {"author": "User2", "text": "Very helpful", "likes": 132, "sentiment": "positive"}
  ]
}
```

**Estimated tokens**: ~200–500

---

### 4. `monitor_channel`

RSS-based channel monitoring. Subscribe and detect new uploads.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `channel_ref` | string | ✅ | — | Channel URL, @handle, or channel ID |
| `action` | string | ❌ | `"check"` | `add` · `check` · `list` · `remove` |

```json
// Subscribe
{"tool": "monitor_channel", "arguments": {"channel_ref": "@3blue1brown", "action": "add"}}

// Check for new videos
{"tool": "monitor_channel", "arguments": {"channel_ref": "UCYO_jab...", "action": "check"}}
// → {"channel_id": "...", "new_videos": [{"video_id": "abc123", "title": "New Video", "published": "..."}]}
```

**Estimated tokens**: ~100–300

---

### 5. `search_transcripts`

Search stored transcripts by keyword. Returns contextual snippets.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `query` | string | ✅ | — | Search keyword or phrase |
| `limit` | int | ❌ | `10` | Maximum results |

```json
{
  "query": "transformer",
  "count": 3,
  "results": [
    {"video_id": "abc123", "title": "Attention Is All You Need", "snippet": "...transformer architecture uses..."}
  ]
}
```

**Estimated tokens**: ~100–400

---

### 6. `extract_entities`

Extract structured entities from a video transcript. Covers companies, indices, crypto, technologies, people, and more — 200+ entities with Korean and English support.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `video_id` | string | ✅ | YouTube video ID |

```json
{
  "video_id": "abc123",
  "entity_count": 5,
  "entities": [
    {"type": "company", "name": "NVIDIA", "keyword": "NVIDIA", "count": 12},
    {"type": "technology", "name": "GPT-4", "keyword": "GPT-4", "count": 8},
    {"type": "person", "name": "Sam Altman", "keyword": "Sam Altman", "count": 3}
  ]
}
```

**Estimated tokens**: ~150–300

---

### 7. `segment_topics`

Segment a video transcript into topical sections based on transition markers.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `video_id` | string | ✅ | YouTube video ID |

```json
{
  "video_id": "abc123",
  "segment_count": 4,
  "segments": [
    {"segment": 0, "char_count": 3200, "preview": "First 200 chars preview..."},
    {"segment": 1, "char_count": 2800, "preview": "Next segment preview..."}
  ]
}
```

**Estimated tokens**: ~100–250

---

### 8. `search_youtube`

Search YouTube videos by keyword.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `query` | string | ✅ | — | Search keyword or phrase |
| `max_results` | int | ❌ | `10` | Max results (1–50) |
| `channel_id` | string | ❌ | — | Limit to specific channel |
| `published_after` | string | ❌ | — | Filter by publish date (ISO 8601) |
| `order` | string | ❌ | `"relevance"` | `relevance` · `date` · `rating` · `viewCount` |

**Estimated tokens**: ~200

---

### 9. `get_playlist`

Get playlist metadata and video list.

| Parameter | Type | Required | Default | Description |
|-----------|------|:--------:|---------|-------------|
| `playlist_id` | string | ✅ | — | YouTube playlist ID |
| `max_videos` | int | ❌ | `50` | Max videos to retrieve |

**Estimated tokens**: ~200–500

---

## ⚙️ Configuration

All settings are managed via environment variables (`MYI_` prefix):

| Variable | Default | Description |
|----------|---------|-------------|
| `MYI_DATA_DIR` | `~/.mcp-youtube-intelligence` | Data directory (DB, transcript files) |
| `MYI_STORAGE` | `sqlite` | Storage backend: `sqlite` · `postgres` |
| `MYI_SQLITE_PATH` | `{DATA_DIR}/data.db` | SQLite DB path |
| `MYI_POSTGRES_DSN` | — | PostgreSQL connection string |
| `MYI_TRANSCRIPT_DIR` | `{DATA_DIR}/transcripts` | Transcript file directory |
| `MYI_YT_DLP` | `yt-dlp` | yt-dlp binary path |
| `MYI_YOUTUBE_API_KEY` | — | YouTube Data API key |
| `MYI_MAX_COMMENTS` | `20` | Max comments to fetch |
| `MYI_MAX_TRANSCRIPT_CHARS` | `500000` | Max transcript length |
| `OPENAI_API_KEY` | — | OpenAI API key (for LLM summarization) |
| `OPENAI_BASE_URL` | — | OpenAI-compatible endpoint |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | LLM model name |

### LLM Integration

By default, **extractive summarization** (no API key needed) is used. Connect an LLM for higher-quality summaries.

**OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini
```

**Ollama (local)**
```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**LM Studio (local)**
```bash
export OPENAI_API_KEY=lm-studio
export OPENAI_BASE_URL=http://localhost:1234/v1
export MYI_OPENAI_MODEL=your-model-name
```

**Token cost comparison**:

| Mode | Client Tokens | Server Cost |
|------|:-:|:-:|
| No API key (extractive) | ~300 | Free |
| LLM (gpt-4o-mini) | ~500 | ~$0.001/video |
| Raw transcript (other MCP servers) | 5,000–50,000 | Free but destroys context |

---

## 📐 Extractive Summarization Pipeline

Effective summarization without an LLM. Here's how it works:

```
Raw Transcript
  │
  ▼
① Sentence splitting (Korean endings + English punctuation)
  │
  ▼
② Even chunking (split into N equal chunks)
  │  → Ensures coverage across beginning/middle/end
  │
  ▼
③ Sentence scoring
  │  • Length weight (longer = more informative)
  │  • Position weight (earlier sentences slightly preferred)
  │  • Keyword bonus ("in conclusion", "key point", etc. → ×1.6)
  │  • Number bonus (statistics/data → ×1.4)
  │
  ▼
④ Adaptive length (proportional to source, 500–2000 chars)
  │
  ▼
⑤ Reassemble in original order → Summary complete
```

---

## 🔍 Troubleshooting

### `yt-dlp` not found

```bash
pip install yt-dlp
# Or specify path:
export MYI_YT_DLP=/usr/local/bin/yt-dlp
```

### No transcript available

Some videos lack auto-generated or manual captions. Use `get_video` instead — it still returns metadata without a transcript.

### Slow comment loading

yt-dlp comment extraction can take 30–60s. Limited to 20 comments by default.

### SQLite database locked

Ensure only one server instance is running.

### OpenAI API errors

If LLM summarization fails, it automatically falls back to extractive summarization. Check your `OPENAI_API_KEY` and `MYI_OPENAI_MODEL`.

---

## 🤝 Contributing

### Development Setup

```bash
git clone https://github.com/JangHyuckYun/mcp-youtube-intelligence.git
cd mcp-youtube-intelligence
pip install -e ".[dev]"
```

### Tests

```bash
pytest tests/ -v
```

### Ideas for Contribution

- Additional entity dictionaries (Japanese, Chinese, etc.)
- Whisper integration for videos without captions
- Advanced comment sentiment analysis
- Export formats (CSV, Markdown)

---

## 📋 Requirements

- Python ≥ 3.10
- `yt-dlp` installed and in PATH
- Internet connection

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
