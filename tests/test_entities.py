"""Tests for entity extraction."""
import pytest
from mcp_youtube_intelligence.core.entities import extract_entities, DEFAULT_ENTITY_DICT


class TestExtractEntities:
    def test_empty_text(self):
        assert extract_entities("") == []

    def test_single_korean_company(self):
        result = extract_entities("삼성전자가 신제품을 발표했습니다")
        names = [e["name"] for e in result]
        assert "Samsung Electronics" in names

    def test_single_english_company(self):
        result = extract_entities("Apple announced a new iPhone today")
        names = [e["name"] for e in result]
        assert "Apple" in names

    def test_count_accuracy(self):
        text = "테슬라 주가가 올랐습니다. 테슬라 CEO는 테슬라 공장을 방문했습니다."
        result = extract_entities(text)
        tesla = next(e for e in result if e["name"] == "Tesla")
        assert tesla["count"] == 3

    def test_synonym_merging(self):
        text = "삼성전자와 삼성의 미래"
        result = extract_entities(text)
        samsung_entries = [e for e in result if e["name"] == "Samsung Electronics"]
        assert len(samsung_entries) == 1
        assert samsung_entries[0]["count"] >= 2

    def test_multiple_entity_types(self):
        text = "비트코인과 나스닥이 동반 상승했고 트럼프가 발언했습니다"
        result = extract_entities(text)
        types = {e["type"] for e in result}
        assert "crypto" in types
        assert "index" in types
        assert "person" in types

    def test_sorted_by_count(self):
        text = "AI AI AI 반도체 반도체 삼성전자"
        result = extract_entities(text)
        counts = [e["count"] for e in result]
        assert counts == sorted(counts, reverse=True)

    def test_extra_dict(self):
        extra = {"커피": ("commodity", "Coffee")}
        result = extract_entities("오늘 커피 가격이 올랐습니다", extra_dict=extra)
        names = [e["name"] for e in result]
        assert "Coffee" in names

    def test_no_false_positives(self):
        text = "오늘 날씨가 좋습니다"
        result = extract_entities(text)
        assert len(result) == 0

    def test_entity_has_required_keys(self):
        result = extract_entities("Google은 좋은 회사입니다")
        for entity in result:
            assert "type" in entity
            assert "name" in entity
            assert "keyword" in entity
            assert "count" in entity

    # --- New tests for expanded dictionary and case-insensitive matching ---

    def test_case_insensitive_english(self):
        """English entities should match regardless of case."""
        result = extract_entities("nvidia is beating amd in the GPU market")
        names = [e["name"] for e in result]
        assert "NVIDIA" in names
        assert "AMD" in names

    def test_word_boundary_go_no_false_match(self):
        """'Go' language should not match 'going' or 'good'."""
        extra = {"Go": ("technology", "Go")}
        result = extract_entities("I'm going to do something good", extra_dict=extra)
        names = [e["name"] for e in result]
        assert "Go" not in names

    def test_word_boundary_go_exact_match(self):
        """'Go' should match when standalone."""
        extra = {"Go": ("technology", "Go")}
        result = extract_entities("I use Go for backend development", extra_dict=extra)
        names = [e["name"] for e in result]
        assert "Go" in names

    def test_ai_no_false_match(self):
        """'AI' should not match 'AGAIN' or 'SAID'."""
        result = extract_entities("AGAIN he SAID something")
        names = [e["name"] for e in result]
        assert "AI" not in names

    def test_ai_ml_terms(self):
        """AI/ML terms should be detected."""
        text = "The Transformer architecture uses attention mechanism for deep learning"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Transformer" in names
        assert "Deep Learning" in names

    def test_global_tech_companies(self):
        """Global tech companies should be detected."""
        text = "Microsoft and Anthropic are investing heavily in OpenAI competitors"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Microsoft" in names
        assert "Anthropic" in names

    def test_programming_languages(self):
        """Programming languages should be detected."""
        text = "We migrated from Python to Rust with Docker and Kubernetes"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Python" in names
        assert "Rust" in names
        assert "Docker" in names
        assert "Kubernetes" in names

    def test_crypto_entities(self):
        """Crypto entities should be detected."""
        text = "Bitcoin and Solana are outperforming in the DeFi space"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "BTC" in names
        assert "SOL" in names
        assert "DeFi" in names

    def test_global_people(self):
        """Global notable people should be detected."""
        text = "Sam Altman and Jensen Huang discussed AI at the conference"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Sam Altman" in names
        assert "Jensen Huang" in names

    def test_finance_macro(self):
        """Finance/macro terms should be detected."""
        text = "The Fed raised interest rate amid rising inflation and GDP growth"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Federal Reserve" in names
        assert "Inflation" in names

    def test_sector_terms(self):
        """Sector terms should be detected."""
        text = "semiconductor and cloud computing are driving the cybersecurity market"
        result = extract_entities(text)
        names = [e["name"] for e in result]
        assert "Semiconductor" in names
        assert "Cloud Computing" in names
        assert "Cybersecurity" in names

    def test_english_tech_video_not_empty(self):
        """Simulated English tech video transcript should yield entities."""
        text = (
            "Today we're going to look at how NVIDIA's new GPU compares to AMD. "
            "We'll be using Python and Docker to benchmark performance. "
            "OpenAI just released GPT-4o and it's incredible for machine learning tasks. "
            "Meanwhile Tesla stock is soaring on NASDAQ."
        )
        result = extract_entities(text)
        assert len(result) >= 5  # Should find many entities
