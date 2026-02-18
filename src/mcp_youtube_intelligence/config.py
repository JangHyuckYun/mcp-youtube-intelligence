"""Configuration management."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Server configuration, resolved from env vars with sensible defaults."""

    # Storage
    storage_backend: str = "sqlite"  # "sqlite" or "postgres"
    sqlite_path: str = ""
    postgres_dsn: str = ""

    # Paths
    data_dir: str = ""
    transcript_dir: str = ""

    # yt-dlp
    yt_dlp_path: str = "yt-dlp"

    # LLM (optional, for server-side summarization)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Limits
    max_comments: int = 20
    max_transcript_chars: int = 500_000

    @classmethod
    def from_env(cls) -> Config:
        """Build config from environment variables."""
        data_dir = os.getenv("MYI_DATA_DIR", str(Path.home() / ".mcp-youtube-intelligence"))
        cfg = cls(
            storage_backend=os.getenv("MYI_STORAGE", "sqlite"),
            sqlite_path=os.getenv("MYI_SQLITE_PATH", str(Path(data_dir) / "data.db")),
            postgres_dsn=os.getenv("MYI_POSTGRES_DSN", ""),
            data_dir=data_dir,
            transcript_dir=os.getenv("MYI_TRANSCRIPT_DIR", str(Path(data_dir) / "transcripts")),
            yt_dlp_path=os.getenv("MYI_YT_DLP", "yt-dlp"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("MYI_OPENAI_MODEL", "gpt-4o-mini"),
            max_comments=int(os.getenv("MYI_MAX_COMMENTS", "20")),
            max_transcript_chars=int(os.getenv("MYI_MAX_TRANSCRIPT_CHARS", "500000")),
        )
        # Ensure directories exist
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
        Path(cfg.transcript_dir).mkdir(parents=True, exist_ok=True)
        return cfg
