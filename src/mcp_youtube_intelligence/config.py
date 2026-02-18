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

    # LLM Provider selection: "openai" | "anthropic" | "google" | "ollama" | "vllm" | "lmstudio" | "auto"
    llm_provider: str = "auto"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Google
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # vLLM
    vllm_base_url: str = "http://localhost:8000"
    vllm_model: str = ""

    # LM Studio
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_model: str = ""

    # YouTube Data API
    youtube_api_key: str = ""

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
            youtube_api_key=os.getenv("MYI_YOUTUBE_API_KEY", ""),
            llm_provider=os.getenv("MYI_LLM_PROVIDER", "auto"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("MYI_OPENAI_MODEL", "gpt-4o-mini"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("MYI_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            google_model=os.getenv("MYI_GOOGLE_MODEL", "gemini-2.0-flash"),
            ollama_base_url=os.getenv("MYI_OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("MYI_OLLAMA_MODEL", "llama3.1:8b"),
            vllm_base_url=os.getenv("MYI_VLLM_BASE_URL", "http://localhost:8000"),
            vllm_model=os.getenv("MYI_VLLM_MODEL", ""),
            lmstudio_base_url=os.getenv("MYI_LMSTUDIO_BASE_URL", "http://localhost:1234"),
            lmstudio_model=os.getenv("MYI_LMSTUDIO_MODEL", ""),
            max_comments=int(os.getenv("MYI_MAX_COMMENTS", "20")),
            max_transcript_chars=int(os.getenv("MYI_MAX_TRANSCRIPT_CHARS", "500000")),
        )
        # Ensure directories exist
        Path(cfg.data_dir).mkdir(parents=True, exist_ok=True)
        Path(cfg.transcript_dir).mkdir(parents=True, exist_ok=True)
        return cfg
