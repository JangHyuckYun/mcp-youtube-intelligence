"""Abstract storage interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class BaseStorage(ABC):
    """Abstract interface for video/channel/comment storage."""

    @abstractmethod
    async def initialize(self) -> None:
        """Create tables if needed."""
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    # --- Videos ---
    @abstractmethod
    async def get_video(self, video_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def upsert_video(self, data: dict) -> None:
        ...

    @abstractmethod
    async def search_transcripts(self, query: str, limit: int = 10) -> list[dict]:
        ...

    # --- Channels ---
    @abstractmethod
    async def get_channel(self, channel_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def upsert_channel(self, data: dict) -> None:
        ...

    @abstractmethod
    async def list_channels(self) -> list[dict]:
        ...

    @abstractmethod
    async def update_channel_checked(self, channel_id: str) -> None:
        ...

    # --- Comments ---
    @abstractmethod
    async def save_comments(self, video_id: str, comments: list[dict]) -> None:
        ...

    @abstractmethod
    async def get_comments(self, video_id: str, limit: int = 20) -> list[dict]:
        ...
