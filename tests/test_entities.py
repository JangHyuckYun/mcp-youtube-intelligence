"""Tests for entities.py longest-match-first extraction."""
from mcp_youtube_intelligence.core.entities import extract_entities


def test_longest_match_first():
    """삼성전자 should not also count as 삼성."""
    text = "삼성전자가 실적을 발표했습니다. 삼성전자 주가가 올랐습니다."
    result = extract_entities(text)
    samsung = [e for e in result if e["name"] == "Samsung Electronics"]
    assert len(samsung) == 1
    assert samsung[0]["count"] == 2  # Two occurrences of 삼성전자
    assert samsung[0]["keyword"] == "삼성전자"  # Matched via longer keyword


def test_separate_short_match():
    """삼성 alone (not part of 삼성전자) should still be counted."""
    text = "삼성전자와 삼성이 다릅니다."
    result = extract_entities(text)
    samsung = [e for e in result if e["name"] == "Samsung Electronics"]
    assert len(samsung) == 1
    # 삼성전자 (1) + 삼성 (1, the standalone one) = 2 total for Samsung Electronics
    assert samsung[0]["count"] == 2


def test_no_entities():
    result = extract_entities("오늘 날씨가 좋습니다.")
    assert result == []


def test_multiple_entity_types():
    text = "삼성전자와 비트코인이 반도체 시장에서 주목받고 있습니다."
    result = extract_entities(text)
    types = {e["type"] for e in result}
    assert "company" in types
    assert "crypto" in types
    assert "sector" in types


def test_sk_hynix_longest_match():
    """SK하이닉스 should not double-count 하이닉스."""
    text = "SK하이닉스가 성장했습니다."
    result = extract_entities(text)
    hynix = [e for e in result if e["name"] == "SK Hynix"]
    assert len(hynix) == 1
    assert hynix[0]["count"] == 1
