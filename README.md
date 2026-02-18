# MCP YouTube Intelligence

An MCP (Model Context Protocol) server that provides YouTube video intelligence — transcripts, summaries, entity extraction, topic segmentation, and channel monitoring.

Designed for **token efficiency**: raw transcripts are never returned directly to the LLM. The server processes them and returns summaries, snippets, or file paths instead.

## Features

- **7 MCP Tools**: `get_video`, `get_transcript`, `get_comments`, `monitor_channel`, `search_transcripts`, `extract_entities`, `segment_topics`
- **Token-optimized**: Summaries and snippets by default; full transcripts saved to files
- **Extractive + LLM summarization**: Works without an API key (extractive fallback)
- **SQLite by default**: Zero-config storage, PostgreSQL optional
- **Multilingual entity extraction**: Korean + English companies, indices, crypto, macro topics
- **RSS channel monitoring**: Subscribe to channels and detect new uploads

## Installation

```bash
# Using uv (recommended)
uv pip install .

# Or with pip
pip install .

# With optional dependencies
pip install ".[llm]"       # OpenAI for server-side summarization
pip install ".[postgres]"  # PostgreSQL storage backend
```

## Usage

### As an MCP server (stdio)

```bash
mcp-youtube-intelligence
```

### With Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"]
    }
  }
}
```

### Configuration

All config via environment variables (`MYI_*` prefix):

```bash
export MYI_DATA_DIR=~/.mcp-youtube-intelligence   # Data directory (default: ~/.mcp-youtube-intelligence)
export MYI_STORAGE=sqlite                          # Storage backend: sqlite (default) or postgres
export MYI_YT_DLP=yt-dlp                           # Path to yt-dlp binary
```

### LLM Summarization (Optional)

By default, the server uses **extractive summarization** (no API key needed) — it picks prominent sentences from the transcript. For higher-quality summaries, you can connect an LLM:

**Option 1: OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"   # installs openai package
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini           # optional, default: gpt-4o-mini
```

**Option 2: Any OpenAI-compatible API** (Ollama, LM Studio, vLLM, etc.)
```bash
export OPENAI_API_KEY=ollama                   # any non-empty string
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**How it works:**
- With API key → LLM generates a concise summary server-side (~500 tokens)
- Without API key → Extractive summary from first N sentences (~300 tokens)
- Either way, the **MCP client (Claude Code, Cursor, etc.) never sees the raw transcript** — only the summary is returned

**Token cost comparison:**
| Mode | Client tokens | Server cost |
|------|--------------|-------------|
| No API key (extractive) | ~300 | Free |
| With LLM (gpt-4o-mini) | ~500 | ~$0.001/video |
| Raw transcript (other MCP servers) | 5,000–50,000 | Free but destroys context |

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
        "MYI_OPENAI_MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

### OpenCode / Cursor

Add to your MCP config:

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

## Tools

| Tool | Description |
|------|-------------|
| `get_video` | Video metadata + summary (~300 tokens) |
| `get_transcript` | Transcript in summary/full/chunks mode |
| `get_comments` | Top N comments with optional summary |
| `monitor_channel` | RSS-based channel subscribe/check/list |
| `search_transcripts` | Keyword search across stored transcripts |
| `extract_entities` | Structured entity list (companies, indices, people, etc.) |
| `segment_topics` | Topic segmentation based on transition markers |

## Requirements

- Python ≥ 3.10
- `yt-dlp` installed and accessible in PATH
- Internet access for YouTube API calls

## License

MIT
