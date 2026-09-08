# Contributing to MCP YouTube Intelligence

Thanks for your interest in contributing! This document explains how to set up
a development environment, what we expect in issues and pull requests, and how
the project is organized.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Language Policy](#language-policy)
- [Before You Start](#before-you-start)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
  - [Adding a New MCP Tool](#adding-a-new-mcp-tool)
  - [Adding an LLM Provider](#adding-an-llm-provider)
- [Pull Request Process](#pull-request-process)
- [AI-Assisted Contributions](#ai-assisted-contributions)
- [Security](#security)
- [Getting Help](#getting-help)

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be
respectful, inclusive, and constructive.

## Language Policy

**English is the primary language for issues, pull requests, code, and
comments** so that contributors from any region can follow along. Korean is
welcome in the `README.md` (the Korean edition) and in discussions where
everyone involved reads it. If English isn't your first language, don't worry
about perfect grammar — clear and simple is enough.

## Before You Start

- **Bugs and small fixes**: open an issue (or go straight to a PR for typos and
  one-line fixes) with a minimal reproduction. Public video or channel IDs are
  fine; never paste API keys or private data.
- **New MCP tools, new providers, or architectural changes**: open an issue
  first so we can agree on the shape before code is written. The project is
  opinionated about staying local-first, provider-neutral, and token-efficient.
- Check existing issues and the [README](README.en.md) before filing.

## Development Setup

Requirements: Python 3.10+ and [uv](https://docs.astral.sh/uv/) (recommended)
or plain `pip`.

```bash
# Fork, then clone your fork
git clone https://github.com/YOUR-USERNAME/mcp-youtube-intelligence.git
cd mcp-youtube-intelligence

# Install with dev dependencies (pytest, ruff, httpx)
uv sync --extra dev
# or: pip install -e ".[dev]"

# Verify
uv run pytest -q
uv run ruff check src tests
```

Optional extras (`llm`, `anthropic-llm`, `google-llm`, `semantic`, `nlp`,
`postgres`, `full`) are listed in `pyproject.toml`. LLM keys go in a local
`.env` (gitignored); see the README configuration section. The test suite runs
fully offline — network calls are mocked.

To try your local build as an MCP server, point your client at the checkout:

```json
{
  "mcpServers": {
    "youtube-intelligence": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/mcp-youtube-intelligence", "mcp-youtube-intelligence"]
    }
  }
}
```

## Development Workflow

1. Create a branch from `main` (`feat/...`, `fix/...`, `docs/...`).
2. Make your changes with tests.
3. Run the same checks CI runs:

   ```bash
   uv run ruff check src tests   # lint + import order (auto-fix: --fix)
   uv run pytest -q              # tests, Python 3.10–3.13 in CI
   uv build                      # sdist + wheel build must succeed
   ```

4. Commit with a clear message. We loosely follow
   [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
5. Open a pull request against `main` using the PR template.

Ruff enforces `E`, `F`, and `I` (import sorting) with a 120-character line
limit. Formatting is not enforced yet; keep new code consistent with the
surrounding file.

## Project Structure

```
src/mcp_youtube_intelligence/
├── server.py        # MCP server entry point: registers tools, wires storage/config
├── tools.py         # MCP tool schemas and handlers
├── cli.py           # `mcp-yt` command-line interface
├── config.py        # Environment/config loading (LLM providers, cache, languages)
├── core/
│   ├── transcript.py   # Fetch + clean transcripts (yt-dlp / youtube-transcript-api)
│   ├── summarizer.py   # Extractive (TextRank/SBERT) and LLM summaries
│   ├── segmenter.py    # Topic segmentation
│   ├── entities.py     # Entity extraction (dictionary + optional spaCy)
│   ├── comments.py     # Comment fetching, noise filtering, sentiment
│   ├── report.py       # Structured report assembly
│   ├── monitor.py      # Channel monitoring via RSS with yt-dlp fallback
│   ├── search.py       # Transcript / YouTube search
│   ├── playlist.py     # Playlist expansion
│   └── collector.py    # Batch collection orchestration
└── storage/
    ├── base.py         # Storage interface
    ├── sqlite.py       # Default local cache
    └── postgres.py     # Optional PostgreSQL backend
tests/                  # pytest suite (offline, mocked network)
scripts/experiments/    # Ad-hoc quality experiments, not part of the package
```

## Making Changes

### Adding a New MCP Tool

1. Implement the logic in the relevant `core/` module with a plain async
   function that takes explicit arguments and returns plain data.
2. Add the tool schema and handler in `tools.py`, and register it in
   `server.py`. Keep tool outputs compact — the whole point of this server is
   to return hundreds of tokens, not thousands.
3. Add a CLI subcommand in `cli.py` if it makes sense for humans to call it.
4. Add tests under `tests/` with mocked network calls.
5. Document the tool in the **MCP Tools Reference** section of both
   `README.md` and `README.en.md`, including an example call and output.

### Adding an LLM Provider

Providers live in `core/summarizer.py` behind a common `summarize()` entry
point and are selected by config. New providers must be **optional
dependencies** (add an extra in `pyproject.toml`), must fail with a clear
error message when the package is missing, and must not change the default
provider. Add a mocked test alongside the existing provider tests.

## Pull Request Process

- Keep PRs focused. Unrelated refactors or reformatting make review slow;
  send them separately.
- Fill in the PR template: what changed, why, and how you tested it.
- CI (ruff, pytest on Python 3.10–3.13, package build) must pass.
- A maintainer will review as capacity allows. This is a small project
  maintained in spare time, so replies may take a few days.
- Squash-merge is the default; your PR title becomes the commit message.

## AI-Assisted Contributions

Using AI tools is fine. What matters is that a person is accountable for the
result:

- Mention it in the PR description.
- Be able to explain the change in your own words and answer review questions
  yourself.
- Do not have an agent open issues or PRs autonomously against this
  repository. Auto-generated PRs without a human who has read and tested the
  change may be closed without review.

## Security

Do **not** report vulnerabilities in public issues. See [SECURITY.md](SECURITY.md)
for the private reporting channel.

## Getting Help

- Usage questions: open a [Question issue](https://github.com/JangHyuckYun/mcp-youtube-intelligence/issues/new?template=question.yml)
- Bugs: [Bug Report](https://github.com/JangHyuckYun/mcp-youtube-intelligence/issues/new?template=bug_report.yml)
- Ideas: [Feature Request](https://github.com/JangHyuckYun/mcp-youtube-intelligence/issues/new?template=feature_request.yml)
