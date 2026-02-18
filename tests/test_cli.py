"""Tests for CLI argument parsing and URL extraction."""
from __future__ import annotations

import pytest
from mcp_youtube_intelligence.cli import build_parser, extract_video_id, extract_playlist_id


# ── URL parsing ──

class TestExtractVideoId:
    def test_bare_id(self):
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_watch_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120") == "dQw4w9WgXcQ"

    def test_non_url_passthrough(self):
        assert extract_video_id("not-a-valid-id-string") == "not-a-valid-id-string"


class TestExtractPlaylistId:
    def test_bare_id(self):
        assert extract_playlist_id("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf") == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"

    def test_url(self):
        assert extract_playlist_id("https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf") == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"


# ── Argparse ──

class TestArgparse:
    def setup_method(self):
        self.parser = build_parser()

    def test_transcript_basic(self):
        args = self.parser.parse_args(["transcript", "dQw4w9WgXcQ"])
        assert args.command == "transcript"
        assert args.url_or_id == "dQw4w9WgXcQ"
        assert args.mode == "summary"

    def test_transcript_full(self):
        args = self.parser.parse_args(["transcript", "abc12345678", "--mode", "full", "-o", "out.txt"])
        assert args.mode == "full"
        assert args.output == "out.txt"

    def test_search_basic(self):
        args = self.parser.parse_args(["search", "python tutorial"])
        assert args.command == "search"
        assert args.query == "python tutorial"
        assert args.max == 10

    def test_search_options(self):
        args = self.parser.parse_args(["search", "rust", "--max", "5", "--order", "date"])
        assert args.max == 5
        assert args.order == "date"

    def test_video(self):
        args = self.parser.parse_args(["video", "dQw4w9WgXcQ"])
        assert args.command == "video"

    def test_comments(self):
        args = self.parser.parse_args(["comments", "dQw4w9WgXcQ", "--max", "20", "--sort", "newest", "--no-filter"])
        assert args.max == 20
        assert args.sort == "newest"
        assert args.no_filter is True

    def test_comments_sentiment(self):
        args = self.parser.parse_args(["comments", "x", "--sentiment", "positive"])
        assert args.sentiment == "positive"

    def test_monitor_subscribe(self):
        args = self.parser.parse_args(["monitor", "subscribe", "@channel"])
        assert args.command == "monitor"
        assert args.monitor_action == "subscribe"
        assert args.url_or_handle == "@channel"

    def test_monitor_check(self):
        args = self.parser.parse_args(["monitor", "check", "--channel", "UC123"])
        assert args.monitor_action == "check"
        assert args.channel == "UC123"

    def test_monitor_list(self):
        args = self.parser.parse_args(["monitor", "list"])
        assert args.monitor_action == "list"

    def test_entities(self):
        args = self.parser.parse_args(["entities", "dQw4w9WgXcQ"])
        assert args.command == "entities"

    def test_segments(self):
        args = self.parser.parse_args(["segments", "dQw4w9WgXcQ"])
        assert args.command == "segments"

    def test_search_transcripts(self):
        args = self.parser.parse_args(["search-transcripts", "machine learning"])
        assert args.command == "search-transcripts"
        assert args.query == "machine learning"

    def test_playlist(self):
        args = self.parser.parse_args(["playlist", "PLxxx", "--max", "20"])
        assert args.command == "playlist"
        assert args.max == 20

    def test_batch(self):
        args = self.parser.parse_args(["batch", "id1", "id2", "id3", "--mode", "full"])
        assert args.command == "batch"
        assert args.ids == ["id1", "id2", "id3"]
        assert args.mode == "full"

    def test_json_flag(self):
        args = self.parser.parse_args(["--json", "video", "dQw4w9WgXcQ"])
        assert args.json is True

    def test_no_command(self):
        args = self.parser.parse_args([])
        assert args.command is None
