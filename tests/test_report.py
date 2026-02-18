"""Tests for report generation."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from mcp_youtube_intelligence.core.report import generate_report


@pytest.fixture
def mock_meta():
    return {
        "video_id": "test123",
        "title": "테스트 영상",
        "channel_name": "테스트채널",
        "duration_seconds": 600,
        "view_count": 1000,
    }


@pytest.fixture
def mock_transcript():
    return {
        "best": "이것은 테스트 자막입니다. 인공지능과 코딩에 대한 내용입니다. " * 20,
        "lang": "ko",
        "timed_segments": [],
    }


@pytest.fixture
def mock_segments():
    return [
        {"segment": 0, "text": "첫 번째 토픽 내용", "char_count": 50, "topic": "인공지능, 코딩"},
        {"segment": 1, "text": "두 번째 토픽 내용", "char_count": 50, "topic": "개발, 도구"},
    ]


@pytest.fixture
def mock_entities():
    return [
        {"type": "technology", "name": "AI", "keyword": "AI", "count": 5},
        {"type": "company", "name": "Google", "keyword": "Google", "count": 3},
    ]


@pytest.fixture
def mock_comments():
    return [
        {"author": "user1", "text": "좋은 영상입니다", "like_count": 10, "sentiment": "positive"},
        {"author": "user2", "text": "별로예요", "like_count": 2, "sentiment": "negative"},
    ]


@pytest.mark.asyncio
async def test_generate_report_basic(mock_meta, mock_transcript, mock_segments, mock_entities, mock_comments):
    with patch("mcp_youtube_intelligence.core.report.collector") as m_collector, \
         patch("mcp_youtube_intelligence.core.report.transcript") as m_transcript, \
         patch("mcp_youtube_intelligence.core.report.segmenter") as m_segmenter, \
         patch("mcp_youtube_intelligence.core.report.entities") as m_entities, \
         patch("mcp_youtube_intelligence.core.report.comments") as m_comments:

        m_collector.get_video_metadata.return_value = mock_meta
        m_transcript.fetch_transcript.return_value = mock_transcript
        m_transcript.clean_transcript.return_value = mock_transcript["best"]
        m_transcript.summarize_extractive.return_value = "Test summary."
        m_segmenter.segment_topics.return_value = mock_segments
        m_entities.extract_entities.return_value = mock_entities
        m_comments.fetch_comments.return_value = mock_comments
        m_comments.summarize_comments.return_value = {
            "count": 2,
            "sentiment_ratio": {"positive": 0.5, "negative": 0.5, "neutral": 0.0},
            "top_comments": [
                {"author": "user1", "text": "좋은 영상입니다", "likes": 10, "sentiment": "positive"},
            ],
            "top_keywords": [],
        }

        report = await generate_report("test123")

        assert "Video Analysis Report" in report
        assert "테스트 영상" in report
        assert "테스트채널" in report
        assert "Summary" in report
        assert "Key Topics" in report
        assert "Detailed Analysis" in report
        assert "Entities" in report
        assert "Viewer Reactions" in report


@pytest.mark.asyncio
async def test_generate_report_no_comments(mock_meta, mock_transcript, mock_segments, mock_entities):
    with patch("mcp_youtube_intelligence.core.report.collector") as m_collector, \
         patch("mcp_youtube_intelligence.core.report.transcript") as m_transcript, \
         patch("mcp_youtube_intelligence.core.report.segmenter") as m_segmenter, \
         patch("mcp_youtube_intelligence.core.report.entities") as m_entities:

        m_collector.get_video_metadata.return_value = mock_meta
        m_transcript.fetch_transcript.return_value = mock_transcript
        m_transcript.clean_transcript.return_value = mock_transcript["best"]
        m_transcript.summarize_extractive.return_value = "Summary."
        m_segmenter.segment_topics.return_value = mock_segments
        m_entities.extract_entities.return_value = mock_entities

        report = await generate_report("test123", include_comments=False)

        assert "Comment analysis excluded" in report
        assert "Video Analysis Report" in report


@pytest.mark.asyncio
async def test_generate_report_no_transcript(mock_meta):
    with patch("mcp_youtube_intelligence.core.report.collector") as m_collector, \
         patch("mcp_youtube_intelligence.core.report.transcript") as m_transcript:

        m_collector.get_video_metadata.return_value = mock_meta
        m_transcript.fetch_transcript.return_value = {"best": None, "lang": None, "timed_segments": []}
        m_transcript.clean_transcript.return_value = ""

        report = await generate_report("test123")

        assert "Report Generation Failed" in report


@pytest.mark.asyncio
async def test_generate_report_comments_fail(mock_meta, mock_transcript, mock_segments, mock_entities):
    with patch("mcp_youtube_intelligence.core.report.collector") as m_collector, \
         patch("mcp_youtube_intelligence.core.report.transcript") as m_transcript, \
         patch("mcp_youtube_intelligence.core.report.segmenter") as m_segmenter, \
         patch("mcp_youtube_intelligence.core.report.entities") as m_entities, \
         patch("mcp_youtube_intelligence.core.report.comments") as m_comments:

        m_collector.get_video_metadata.return_value = mock_meta
        m_transcript.fetch_transcript.return_value = mock_transcript
        m_transcript.clean_transcript.return_value = mock_transcript["best"]
        m_transcript.summarize_extractive.return_value = "Summary."
        m_segmenter.segment_topics.return_value = mock_segments
        m_entities.extract_entities.return_value = mock_entities
        m_comments.fetch_comments.side_effect = Exception("API error")

        report = await generate_report("test123", include_comments=True)

        assert "Comments unavailable" in report
        assert "Summary" in report  # rest of report still works
