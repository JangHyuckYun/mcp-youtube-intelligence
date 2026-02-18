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
        # "삼성전자" and "삼성" both map to Samsung Electronics
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
