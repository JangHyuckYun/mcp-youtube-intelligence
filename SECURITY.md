# Security Policy

## Supported Versions

Only the latest release on PyPI receives security fixes. Please reproduce
against the newest version before reporting.

| Version | Supported |
| ------- | --------- |
| latest release | ✅ |
| older releases | ❌ (upgrade first) |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Report privately through one of these channels:

- Open a [private security advisory](https://github.com/JangHyuckYun/mcp-youtube-intelligence/security/advisories/new) on GitHub (preferred), or
- Email the maintainer at skg09203@naver.com

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal example is ideal)
- The affected version and environment
- Any suggested fix (optional)

## What to Expect

Reports are handled on a best-effort basis by a single maintainer. You can
expect an initial acknowledgment within a few days. Once a fix is available it
will be released to PyPI and a GitHub advisory will be published crediting the
reporter unless you prefer to remain anonymous.

## Scope Notes

This project runs locally and calls YouTube, `yt-dlp`, and optional LLM
providers with credentials supplied by the user. Areas of particular interest:

- Command injection through video/channel identifiers passed to subprocesses
- Leakage of API keys or tokens into logs, cache files, or reports
- Unsafe handling of untrusted transcript or comment content
