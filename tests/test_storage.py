"""Tests for SQLite storage."""
import pytest
import pytest_asyncio
import tempfile
import os
from mcp_youtube_intelligence.storage.sqlite import SQLiteStorage


@pytest_asyncio.fixture
async def storage():
    """Create a temporary SQLite storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        s = SQLiteStorage(db_path)
        await s.initialize()
        yield s
        await s.close()


@pytest.mark.asyncio
class TestVideosCRUD:
    async def test_upsert_and_get(self, storage):
        await storage.upsert_video({"video_id": "v1", "title": "Test Video"})
        result = await storage.get_video("v1")
        assert result is not None
        assert result["title"] == "Test Video"

    async def test_get_nonexistent(self, storage):
        result = await storage.get_video("nonexistent")
        assert result is None

    async def test_update_existing(self, storage):
        await storage.upsert_video({"video_id": "v1", "title": "Old Title"})
        await storage.upsert_video({"video_id": "v1", "title": "New Title"})
        result = await storage.get_video("v1")
        assert result["title"] == "New Title"

    async def test_search_transcripts(self, storage):
        await storage.upsert_video({
            "video_id": "v1", "title": "AI Video",
            "transcript_text": "This video discusses transformer architecture in depth",
            "published_at": "2024-01-01",
        })
        results = await storage.search_transcripts("transformer")
        assert len(results) == 1
        assert "transformer" in results[0]["snippet"].lower()

    async def test_search_no_results(self, storage):
        await storage.upsert_video({
            "video_id": "v1", "title": "Test",
            "transcript_text": "Nothing relevant here",
        })
        results = await storage.search_transcripts("quantum")
        assert len(results) == 0


@pytest.mark.asyncio
class TestChannelsCRUD:
    async def test_upsert_and_get(self, storage):
        await storage.upsert_channel({
            "channel_id": "UC123", "channel_name": "Test Channel",
        })
        result = await storage.get_channel("UC123")
        assert result is not None
        assert result["channel_name"] == "Test Channel"

    async def test_list_channels(self, storage):
        await storage.upsert_channel({"channel_id": "UC1", "channel_name": "Ch1"})
        await storage.upsert_channel({"channel_id": "UC2", "channel_name": "Ch2"})
        channels = await storage.list_channels()
        assert len(channels) == 2

    async def test_disable_channel(self, storage):
        await storage.upsert_channel({"channel_id": "UC1", "channel_name": "Ch1"})
        await storage.upsert_channel({"channel_id": "UC1", "enabled": 0})
        channels = await storage.list_channels()
        assert len(channels) == 0  # disabled channels excluded

    async def test_update_checked(self, storage):
        await storage.upsert_channel({"channel_id": "UC1", "channel_name": "Ch1"})
        await storage.update_channel_checked("UC1")
        ch = await storage.get_channel("UC1")
        assert ch["last_checked_at"] is not None


@pytest.mark.asyncio
class TestCommentsCRUD:
    async def test_save_and_get(self, storage):
        comments = [
            {"comment_id": "c1", "author": "Alice", "text": "Great!", "like_count": 10},
            {"comment_id": "c2", "author": "Bob", "text": "Nice", "like_count": 5},
        ]
        await storage.save_comments("v1", comments)
        result = await storage.get_comments("v1")
        assert len(result) == 2

    async def test_comments_sorted_by_likes(self, storage):
        comments = [
            {"comment_id": "c1", "author": "A", "text": "Low", "like_count": 1},
            {"comment_id": "c2", "author": "B", "text": "High", "like_count": 100},
        ]
        await storage.save_comments("v1", comments)
        result = await storage.get_comments("v1")
        assert result[0]["like_count"] >= result[1]["like_count"]

    async def test_duplicate_comments_ignored(self, storage):
        comment = [{"comment_id": "c1", "author": "A", "text": "Hello", "like_count": 0}]
        await storage.save_comments("v1", comment)
        await storage.save_comments("v1", comment)  # duplicate
        result = await storage.get_comments("v1")
        assert len(result) == 1

    async def test_get_comments_limit(self, storage):
        comments = [{"comment_id": f"c{i}", "author": f"U{i}", "text": "Hi", "like_count": i} for i in range(10)]
        await storage.save_comments("v1", comments)
        result = await storage.get_comments("v1", limit=3)
        assert len(result) == 3

    async def test_get_comments_empty(self, storage):
        result = await storage.get_comments("nonexistent")
        assert result == []
