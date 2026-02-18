"""Tests for transcript cleaning, chunking, and extractive summarization."""
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from mcp_youtube_intelligence.core.transcript import (
    clean_transcript,
    fetch_transcript,
    make_chunks,
    summarize_extractive,
    _parse_vtt,
    _parse_srt,
    _fetch_via_ytdlp,
    _select_best_from_list,
    LANG_FALLBACK_ORDER,
)


class TestCleanTranscript:
    def test_empty_input(self):
        assert clean_transcript("") == ""

    def test_none_input(self):
        assert clean_transcript(None) == ""

    def test_removes_music_tag(self):
        assert "[Music]" not in clean_transcript("Hello [Music] world")

    def test_removes_korean_noise(self):
        result = clean_transcript("안녕하세요 [음악] 여러분 [박수]")
        assert "[음악]" not in result
        assert "[박수]" not in result

    def test_removes_timestamps(self):
        result = clean_transcript("At 1:23 we see something and at 1:23:45 another")
        assert "1:23" not in result

    def test_normalizes_whitespace(self):
        result = clean_transcript("hello    world   foo")
        assert "  " not in result

    def test_removes_filler_sounds(self):
        result = clean_transcript("그래서 아 어 음 이것은")
        assert result.strip()

    def test_preserves_meaningful_content(self):
        text = "오늘은 삼성전자에 대해 알아보겠습니다"
        assert clean_transcript(text) == text

    # --- New tests for English noise patterns ---

    def test_removes_inaudible(self):
        result = clean_transcript("He said [inaudible] and then continued")
        assert "[inaudible]" not in result

    def test_removes_english_fillers_um(self):
        result = clean_transcript("So um I think uh this is great")
        assert " um " not in result
        assert " uh " not in result

    def test_removes_empty_brackets(self):
        result = clean_transcript("Hello [  ] world [ __ ] test")
        assert "[ __ ]" not in result

    def test_removes_music_note_brackets(self):
        result = clean_transcript("Intro [♪♪] Main content here")
        assert "[♪♪]" not in result

    def test_removes_duplicate_sentences(self):
        result = clean_transcript(
            "This is a long enough sentence to be detected "
            "This is a long enough sentence to be detected"
        )
        # Should only appear once
        count = result.count("This is a long enough sentence")
        assert count == 1

    def test_removes_standalone_music_symbols(self):
        """Standalone ♪ and ♫ should be removed."""
        result = clean_transcript("♪♪♪ Hello world ♫♫ test ♪")
        assert "♪" not in result
        assert "♫" not in result
        assert "Hello world" in result

    def test_removes_music_symbols_in_music_video(self):
        """Music video transcripts full of ♪ should be cleaned."""
        result = clean_transcript("♪ La la la ♪♪ Do re mi ♫ End ♪♪♪")
        assert "♪" not in result
        assert "♫" not in result
        assert "La la la" in result

    def test_preserves_meaningful_like(self):
        """The word 'like' in normal context should be preserved."""
        text = "I like this approach to machine learning"
        result = clean_transcript(text)
        assert "like" in result


class TestMakeChunks:
    def test_empty_input(self):
        assert make_chunks("") == []

    def test_single_chunk(self):
        text = "Hello world"
        chunks = make_chunks(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["index"] == 0

    def test_multiple_chunks(self):
        text = "A" * 5000
        chunks = make_chunks(text, chunk_size=2000)
        assert len(chunks) == 3
        assert chunks[0]["char_count"] == 2000
        assert chunks[2]["char_count"] == 1000

    def test_chunk_indices_sequential(self):
        chunks = make_chunks("A" * 6000, chunk_size=2000)
        for i, c in enumerate(chunks):
            assert c["index"] == i

    def test_custom_chunk_size(self):
        text = "A" * 100
        chunks = make_chunks(text, chunk_size=30)
        assert len(chunks) == 4


class TestSummarizeExtractive:
    def test_empty_input(self):
        assert summarize_extractive("") == ""

    def test_short_text_fallback(self):
        result = summarize_extractive("Short.")
        assert result

    def test_picks_sentences(self):
        text = "This is a very important first sentence about the topic at hand. Second sentence is also quite relevant and informative. Third one covers additional ground nicely."
        result = summarize_extractive(text, max_sentences=2)
        assert result.endswith(".")

    def test_respects_max_sentences(self):
        sentences = ". ".join(f"Sentence number {i} has enough characters to pass filter" for i in range(10))
        result = summarize_extractive(sentences, max_sentences=3)
        assert len(result) < len(sentences)

    def test_long_text_truncation(self):
        text = ". ".join("This is a moderately long sentence number whatever" for _ in range(100))
        result = summarize_extractive(text)
        assert len(result) > 0


class TestParseVtt:
    def test_basic_vtt(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello world

00:00:05.000 --> 00:00:08.000
Second line here
"""
        segs = _parse_vtt(vtt)
        assert len(segs) == 2
        assert segs[0]["text"] == "Hello world"
        assert segs[0]["start"] == 1.0
        assert segs[1]["text"] == "Second line here"

    def test_deduplicates_consecutive(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:02.000
Same text

00:00:02.000 --> 00:00:03.000
Same text

00:00:03.000 --> 00:00:04.000
Different text
"""
        segs = _parse_vtt(vtt)
        assert len(segs) == 2

    def test_strips_tags(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:04.000
<c>Hello</c> <00:00:02.500>world
"""
        segs = _parse_vtt(vtt)
        assert segs[0]["text"] == "Hello world"


class TestParseSrt:
    def test_basic_srt(self):
        srt = """1
00:00:01,000 --> 00:00:04,000
Hello world

2
00:00:05,000 --> 00:00:08,000
Second line
"""
        segs = _parse_srt(srt)
        assert len(segs) == 2
        assert segs[0]["text"] == "Hello world"


class TestMultilingualFallback:
    def _make_tr(self, lang_code, is_generated, texts):
        tr = MagicMock()
        tr.language_code = lang_code
        tr.is_generated = is_generated
        seg_mocks = []
        for i, t in enumerate(texts):
            s = MagicMock()
            s.start = float(i)
            s.duration = 1.0
            s.text = t
            seg_mocks.append(s)
        tr.fetch.return_value = seg_mocks
        return tr

    def test_ko_preferred(self):
        trs = [
            self._make_tr("ko", True, ["안녕하세요"]),
            self._make_tr("en", True, ["Hello"]),
        ]
        result = _select_best_from_list(trs)
        assert result["lang"] == "ko_auto"
        assert result["best"] == "안녕하세요"

    def test_fallback_to_ja(self):
        trs = [self._make_tr("ja", True, ["こんにちは"])]
        result = _select_best_from_list(trs)
        assert result["lang"] == "ja_auto"
        assert result["best"] == "こんにちは"

    def test_fallback_to_any(self):
        trs = [self._make_tr("ru", False, ["Привет"])]
        result = _select_best_from_list(trs)
        assert result["best"] == "Привет"
        assert "ru" in result["lang"]

    def test_empty_list(self):
        result = _select_best_from_list([])
        assert result["best"] is None


class TestYtdlpFallback:
    @patch("mcp_youtube_intelligence.core.transcript.subprocess.run")
    @patch("mcp_youtube_intelligence.core.transcript.glob.glob")
    @patch("mcp_youtube_intelligence.core.transcript.tempfile.mkdtemp")
    def test_ytdlp_parses_vtt(self, mock_mkdtemp, mock_glob, mock_run):
        mock_mkdtemp.return_value = "/tmp/test_ytdlp"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello from yt-dlp
"""
        mock_glob.side_effect = [
            ["/tmp/test_ytdlp/dQw4w9WgXcQ.en.vtt"],  # .vtt files
            [],  # .srt files
        ]

        with patch("pathlib.Path.read_text", return_value=vtt_content):
            with patch("pathlib.Path.name", new_callable=PropertyMock, return_value="dQw4w9WgXcQ.en.vtt"):
                result = _fetch_via_ytdlp("dQw4w9WgXcQ")

        assert result["best"] is not None
        assert "Hello from yt-dlp" in result["best"]

    @patch("mcp_youtube_intelligence.core.transcript.subprocess.run")
    @patch("mcp_youtube_intelligence.core.transcript.tempfile.mkdtemp")
    def test_ytdlp_failure(self, mock_mkdtemp, mock_run):
        mock_mkdtemp.return_value = "/tmp/test_ytdlp"
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = _fetch_via_ytdlp("bad_id")
        assert result["best"] is None


class TestFetchTranscriptIntegration:
    @patch("mcp_youtube_intelligence.core.transcript._fetch_via_ytdlp")
    def test_falls_back_to_ytdlp_on_exception(self, mock_ytdlp):
        """When youtube-transcript-api raises, should fall back to yt-dlp."""
        mock_ytdlp.return_value = {
            "auto_ko": None, "auto_en": "Hello", "manual": None,
            "best": "Hello", "lang": "en_ytdlp", "timed_segments": [{"start": 0, "duration": 1, "text": "Hello"}],
        }

        with patch("youtube_transcript_api.YouTubeTranscriptApi") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            mock_instance.list.side_effect = Exception("RequestBlocked")
            result = fetch_transcript("dQw4w9WgXcQ")

        assert result["best"] == "Hello"
        assert result["lang"] == "en_ytdlp"
        assert result["error"] is not None
