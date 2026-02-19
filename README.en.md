[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
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
| Basic summary (preview-level, no API/model needed) | ❌ | ✅ |

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

## 💡 Use Cases

### 🔬 Research & Learning

| Scenario | Traditional | With MYI | Improvement |
|----------|------------|---------|-------------|
| Summarize 1-hour lecture | Watch entire video (60 min) | Read summary (2 min) | ⏱️ **97% time saved** |
| Analyze paper review videos | Manual notes + timestamp hunting | Auto topic segmentation | 📑 Instant navigation |
| Track tech trends | Watch 10 videos individually | Batch process all at once | 🚀 **10x throughput** |

**Example**: "Anthropic Agent SDK" tutorial (20 min)
```
Raw transcript: 15,000+ tokens
→ MYI summary: ~300 tokens (98% reduction)
→ Extracted entities: [Anthropic, Agent SDK, Claude, Tool Use, MCP, Python]
→ Topic segments: [Installation, Architecture, Tool Integration, Agent Run, Deployment]
```

### 📊 Market & Trend Monitoring

| Scenario | How | Impact |
|----------|-----|--------|
| Track crypto YouTubers | `monitor_channel` detects new videos → auto-summarize | 📡 Real-time market insights |
| Competitor product analysis | Entity extraction + comment sentiment from launch videos | 🎯 Instant market reaction |
| Investment research | Batch summarize analyst videos → save to Notion DB | 📚 Systematic knowledge base |

**Example**: Channel monitoring → AI agent automation
```bash
# 1. Register channel
mcp-yt monitor UC_x5XG1OV2P6uZZ5FSM9Ttw --interval 3600

# 2. Auto-summarize new videos (cron/script integration)
mcp-yt transcript <new_video_id> --summarize
# → Send summary to Slack/Discord webhook
```

### 🤖 AI Agent Integration

| Agent | Integration | Use Case |
|-------|------------|----------|
| Claude Code | Direct MCP connection | "Summarize this video" — done in one prompt |
| OpenClaw | Register as Skill | Build automated research pipelines |
| Cursor | MCP config | Instantly analyze coding tutorials |
| Custom bots | CLI pipeline | `mcp-yt transcript ID \| jq .summary` |

**Measured token cost savings**:
```
1 video (20 min) raw transcript to LLM:    ~15,000 tokens ($0.015)
After MYI summarization:                   ~300 tokens ($0.0003)
──────────────────────────────────────────────────────────
Savings: 98%, 50x cost efficiency (100 videos: $1.50 → $0.03)
```

### 🎓 Education & Content Creation

- **Auto lecture notes**: Chapter-by-chapter summaries via topic segmentation
- **Multilingual analysis**: Auto-detect KO/EN/JA subtitles + summarize
- **Comment insights**: Sentiment analysis reveals content improvement points
- **Playlist batch processing**: Summarize entire lecture series at once

---

## 🚀 Quick Start

### Installation

```bash
# uv (recommended)
uv pip install mcp-youtube-intelligence

# pip
pip install mcp-youtube-intelligence

# Optional dependencies
pip install "mcp-youtube-intelligence[all-llm]"        # All LLMs (OpenAI + Anthropic + Google)
pip install "mcp-youtube-intelligence[llm]"            # OpenAI only
pip install "mcp-youtube-intelligence[anthropic-llm]"  # Anthropic only
pip install "mcp-youtube-intelligence[google-llm]"     # Google only
pip install "mcp-youtube-intelligence[postgres]"       # PostgreSQL backend
pip install "mcp-youtube-intelligence[dev]"            # Development (pytest, etc.)
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
mcp-yt transcript https://youtube.com/watch?v=LV6Juz0xcrY

# Full transcript (saved to file)
mcp-yt transcript https://youtube.com/watch?v=LV6Juz0xcrY --mode full

# Split into chunks
mcp-yt transcript https://youtube.com/watch?v=LV6Juz0xcrY --mode chunks

# JSON output
mcp-yt --json transcript https://youtube.com/watch?v=LV6Juz0xcrY

# Save to file
mcp-yt transcript https://youtube.com/watch?v=LV6Juz0xcrY -o summary.txt
```

#### YouTube Search

```bash
mcp-yt search "transformer explained"
mcp-yt search "python tutorial" --max 5 --order date
mcp-yt search "AI news" --channel UCxxxx
```

#### Video Metadata + Summary

```bash
mcp-yt video https://youtube.com/watch?v=LV6Juz0xcrY
```

Sample output:
```
video_id: LV6Juz0xcrY
title: Video Title
channel_name: Channel Name
duration_seconds: 612
view_count: 1500000
summary: This video covers three main topics...
```

#### Comment Collection

```bash
# Top 10 comments
mcp-yt comments https://youtube.com/watch?v=LV6Juz0xcrY

# Newest 20 comments
mcp-yt comments https://youtube.com/watch?v=LV6Juz0xcrY --max 20 --sort newest

# Positive comments only
mcp-yt comments https://youtube.com/watch?v=LV6Juz0xcrY --sentiment positive

# Negative comments only
mcp-yt comments https://youtube.com/watch?v=LV6Juz0xcrY --sentiment negative
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
mcp-yt entities https://youtube.com/watch?v=LV6Juz0xcrY
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
mcp-yt segments https://youtube.com/watch?v=LV6Juz0xcrY
```

#### Playlist

```bash
mcp-yt playlist https://youtube.com/playlist?list=PLrAXtmErZgOe...
mcp-yt playlist PLrAXtmErZgOe... --max 10
```

#### Batch Processing

```bash
mcp-yt batch LV6Juz0xcrY abc123def45 xyz789ghi01
mcp-yt batch LV6Juz0xcrY abc123def45 --mode full
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
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza...",
        "MYI_LLM_PROVIDER": "auto"
      }
    }
  }
}
```

> 💡 Only set the API key(s) for the provider(s) you want to use. `auto` mode detects automatically.

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
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza..."
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
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza..."
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

## ⭐ Key Features at a Glance

> 💡 **Vibe coders**: Just connect the MCP server and say "summarize this video" — done!
> 💡 **Developers**: Use the CLI (`mcp-yt`) to integrate into scripts and pipelines

### 1. 🎯 Transcript Extraction + Token-Optimized Summarization
Fetches YouTube subtitles and **summarizes server-side**. Instead of sending 5,000–50,000 raw tokens to your LLM, MYI delivers **~300 tokens**.
- **Multilingual auto-detection** (Korean, English, Japanese, etc.)
- Prefers manual captions, falls back to auto-generated
- **Basic summarization works without any API key** (LLM summarization optional)
- ⚠️ Extractive summary is sentence-extraction level. For high-quality summaries, LLM integration is recommended.

### 2. 🏷️ Entity Extraction
Automatically identifies **people, companies, technologies, and products** from transcripts. 200+ built-in entities.
- Domains: AI/ML, crypto, programming, global companies, economics, etc.
- Korean + English simultaneous support
- Custom entities can be added

### 3. 📑 Topic Segmentation
Splits long videos into **topic-based segments**. Instantly see "what's discussed where."
- Keyword-shift-based boundary detection
- Auto-labels each segment with a representative topic
- Timestamp integration for jumping to specific sections

### 4. 💬 Comment Collection + Sentiment Analysis
Collects video **comments** and analyzes **positive/negative/neutral** sentiment.
- Sort: by popularity / newest
- Noise filtering: auto-removes spam and bot comments
- Sentiment filter: positive only / negative only / all

### 5. 📡 Channel Monitoring
**Subscribe to YouTube channels via RSS** — detects new uploads automatically.
- Periodic checks (cron/script integration)
- Build auto-summarization pipelines for new videos
- yt-dlp fallback for reliability

### 6. 🔍 YouTube Search + Transcript Search
- **YouTube Search**: Find videos by keyword (Data API v3 + yt-dlp fallback)
- **Transcript Search**: Search saved transcripts → returns relevant snippets
- Full playlist analysis supported

### 7. 📦 Batch Processing
Process **multiple videos at once**. Perfect for seminar series, lecture playlists.
- Async parallel processing (semaphore-limited for stability)
- Accepts video ID lists or playlist URLs

### 8. 💾 Data Storage
Analysis results are **automatically saved to a local DB**.
- SQLite (default, zero config) / PostgreSQL (optional)
- Cached results returned instantly on duplicate requests
- Search index for fast keyword lookups

---

## 🔧 MCP Tools Reference (9 tools)

### 1. `get_video`

Get video metadata + summary in one call. Results are cached.

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `video_id` | string | ✅ | YouTube video ID |

```json
// Request
{"tool": "get_video", "arguments": {"video_id": "LV6Juz0xcrY"}}

// Response (~300 tokens)
{
  "video_id": "LV6Juz0xcrY",
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
| `MYI_LLM_PROVIDER` | `auto` | LLM provider: `auto` · `openai` · `anthropic` · `google` · `ollama` · `vllm` · `lmstudio` |
| `MYI_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `MYI_OLLAMA_MODEL` | `llama3.1:8b` | Ollama model name |
| `MYI_VLLM_BASE_URL` | `http://localhost:8000` | vLLM server URL |
| `MYI_VLLM_MODEL` | — | vLLM model name |
| `MYI_LMSTUDIO_BASE_URL` | `http://localhost:1234` | LM Studio server URL |
| `MYI_LMSTUDIO_MODEL` | — | LM Studio model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_BASE_URL` | — | OpenAI-compatible endpoint |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `MYI_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model name |
| `GOOGLE_API_KEY` | — | Google API key |
| `MYI_GOOGLE_MODEL` | `gemini-2.0-flash` | Google model name |

### LLM Integration

By default, **basic summarization** (preview-level, no API/model needed) is used. Connect an LLM for higher-quality summaries.

> ⚠️ Extractive summary is sentence-extraction level. For high-quality summaries, LLM integration is recommended.

6 providers (3 cloud + 3 local) are supported, selected via `MYI_LLM_PROVIDER`:

| Provider | API Key Variable | Model Variable | Default Model |
|----------|-----------------|---------------|---------------|
| OpenAI | `OPENAI_API_KEY` | `MYI_OPENAI_MODEL` | `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `MYI_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` |
| Google | `GOOGLE_API_KEY` | `MYI_GOOGLE_MODEL` | `gemini-2.0-flash` |

`MYI_LLM_PROVIDER` defaults to `auto`, which auto-detects based on available API keys.

**OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini          # optional
```

**Anthropic**
```bash
pip install "mcp-youtube-intelligence[anthropic-llm]"
export ANTHROPIC_API_KEY=sk-ant-...
export MYI_ANTHROPIC_MODEL=claude-sonnet-4-20250514  # optional
```

**Google**
```bash
pip install "mcp-youtube-intelligence[google-llm]"
export GOOGLE_API_KEY=AIza...
export MYI_GOOGLE_MODEL=gemini-2.0-flash     # optional
```

**Explicit provider selection** (when multiple API keys are set):
```bash
export MYI_LLM_PROVIDER=anthropic  # openai / anthropic / google / auto
```

### 🏠 Local LLM (Free, Offline-capable)

Get LLM-quality summaries without API costs.

#### Ollama (Recommended)
```bash
# 1. Install Ollama (https://ollama.ai)
# 2. Download a recommended model
ollama pull llama3.1:8b          # English (4.7GB, general purpose)
ollama pull gemma2:9b            # Multilingual (5.4GB, good Korean)
ollama pull qwen2.5:7b           # Multilingual (4.4GB, strong CJK)
ollama pull aya-expanse:8b       # Multilingual specialist (4.8GB, 23 languages)

# 3. Set environment variables
export MYI_LLM_PROVIDER=ollama
export MYI_OLLAMA_MODEL=qwen2.5:7b
```

#### vLLM
```bash
export MYI_LLM_PROVIDER=vllm
export MYI_VLLM_BASE_URL=http://localhost:8000
export MYI_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

#### LM Studio
```bash
export MYI_LLM_PROVIDER=lmstudio
export MYI_LMSTUDIO_BASE_URL=http://localhost:1234
```

### 📋 Recommended Models Guide

| Purpose | Model | Size | Korean | English | Quality |
|---------|-------|------|:------:|:-------:|:-------:|
| **Multilingual (Recommended)** | `qwen2.5:7b` | 4.4GB | ✅ Good | ✅ Good | ⭐⭐⭐ |
| **Multilingual specialist** | `aya-expanse:8b` | 4.8GB | ✅ Good | ✅ Good | ⭐⭐⭐ |
| **Best English** | `llama3.1:8b` | 4.7GB | ⚠️ Fair | ✅ Best | ⭐⭐⭐ |
| **Lightweight (low-spec PC)** | `qwen2.5:3b` | 1.9GB | ✅ OK | ✅ OK | ⭐⭐⭐ |
| **Ultra-light (Raspberry Pi)** | `qwen2.5:1.5b` | 0.9GB | ⚠️ Fair | ✅ OK | ⭐⭐ |
| **Korean specialist** | `gemma2:9b` | 5.4GB | ✅ Good | ✅ Good | ⭐⭐⭐ |
| **Cloud best** | GPT-4o / Claude Sonnet | API | ✅ Best | ✅ Best | ⭐⭐⭐⭐ |

**Legacy approach** (Local LLM via OpenAI-compatible API):
```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**Token cost comparison**:

| Mode | Client Tokens | Server Cost |
|------|:-:|:-:|
| No API key (extractive) | ~300 | Free |
| LLM (gpt-4o-mini) | ~500 | ~$0.001/video |
| LLM (claude-sonnet-4-20250514) | ~500 | ~$0.003/video |
| LLM (gemini-2.0-flash) | ~500 | ~$0.0005/video |
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

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

## 📝 Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-02-18 | v0.1.0 | Initial release — 9 MCP tools, CLI (`mcp-yt`), SQLite storage |
| 2025-02-18 | v0.1.1 | Multi-LLM support (OpenAI/Anthropic/Google), license → Apache 2.0 |
| 2025-02-18 | v0.1.2 | yt-dlp transcript fallback, multilingual fallback, extractive summary improvements |
