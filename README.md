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

### With environment variables

```bash
export MYI_DATA_DIR=~/.mcp-youtube-intelligence
export MYI_STORAGE=sqlite
export OPENAI_API_KEY=sk-...          # Optional: enables LLM summarization
export MYI_YT_DLP=yt-dlp             # Path to yt-dlp binary
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
