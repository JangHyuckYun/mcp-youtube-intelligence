"""General-purpose entity extraction from text.

Provides a default dictionary covering companies, indices, crypto, countries,
sectors, macro topics, commodities, and notable people. The dictionary is
extensible — callers can supply additional entries.
"""
from __future__ import annotations

import re
from typing import Optional

# (keyword) -> (entity_type, canonical_name)
DEFAULT_ENTITY_DICT: dict[str, tuple[str, str]] = {
    # --- Companies (KR) ---
    "삼성전자": ("company", "Samsung Electronics"),
    "삼성": ("company", "Samsung Electronics"),
    "SK하이닉스": ("company", "SK Hynix"),
    "하이닉스": ("company", "SK Hynix"),
    "현대차": ("company", "Hyundai Motor"),
    "LG": ("company", "LG"),
    "카카오": ("company", "Kakao"),
    "네이버": ("company", "Naver"),
    "쿠팡": ("company", "Coupang"),
    "토스": ("company", "Toss"),
    # --- Companies (US) ---
    "Apple": ("company", "Apple"), "애플": ("company", "Apple"),
    "Tesla": ("company", "Tesla"), "테슬라": ("company", "Tesla"),
    "NVIDIA": ("company", "NVIDIA"), "엔비디아": ("company", "NVIDIA"),
    "Google": ("company", "Google"), "구글": ("company", "Google"),
    "Amazon": ("company", "Amazon"), "아마존": ("company", "Amazon"),
    "Microsoft": ("company", "Microsoft"), "마이크로소프트": ("company", "Microsoft"),
    "Meta": ("company", "Meta"), "메타": ("company", "Meta"),
    "Netflix": ("company", "Netflix"), "넷플릭스": ("company", "Netflix"),
    "OpenAI": ("company", "OpenAI"), "오픈AI": ("company", "OpenAI"),
    "TSMC": ("company", "TSMC"),
    # --- Companies (CN/JP) ---
    "알리바바": ("company", "Alibaba"), "Alibaba": ("company", "Alibaba"),
    "텐센트": ("company", "Tencent"), "Tencent": ("company", "Tencent"),
    "바이두": ("company", "Baidu"), "BYD": ("company", "BYD"), "비야디": ("company", "BYD"),
    "소프트뱅크": ("company", "SoftBank"),
    "딥시크": ("company", "DeepSeek"), "DeepSeek": ("company", "DeepSeek"),
    # --- Finance ---
    "버크셔": ("company", "Berkshire Hathaway"),
    "JP모건": ("company", "JPMorgan"), "골드만삭스": ("company", "Goldman Sachs"),
    # --- Indices ---
    "코스피": ("index", "KOSPI"), "코스닥": ("index", "KOSDAQ"),
    "나스닥": ("index", "NASDAQ"), "NASDAQ": ("index", "NASDAQ"),
    "S&P": ("index", "S&P 500"), "다우": ("index", "Dow Jones"),
    "니케이": ("index", "Nikkei"), "항셍": ("index", "Hang Seng"),
    # --- Crypto ---
    "비트코인": ("crypto", "BTC"), "Bitcoin": ("crypto", "BTC"),
    "이더리움": ("crypto", "ETH"), "Ethereum": ("crypto", "ETH"),
    "리플": ("crypto", "XRP"),
    # --- Countries ---
    "미국": ("country", "US"), "중국": ("country", "CN"), "일본": ("country", "JP"),
    "한국": ("country", "KR"), "유럽": ("region", "EU"), "독일": ("country", "DE"),
    "영국": ("country", "UK"), "인도": ("country", "IN"), "대만": ("country", "TW"),
    # --- Sectors / Macro ---
    "반도체": ("sector", "Semiconductor"), "AI": ("sector", "AI"),
    "인공지능": ("sector", "AI"), "부동산": ("sector", "Real Estate"),
    "금리": ("macro", "Interest Rate"), "인플레이션": ("macro", "Inflation"),
    "관세": ("macro", "Tariff"), "환율": ("macro", "Exchange Rate"),
    # --- Commodities ---
    "금값": ("commodity", "Gold"), "유가": ("commodity", "Oil"),
    "원유": ("commodity", "Oil"), "천연가스": ("commodity", "Natural Gas"),
    # --- Products ---
    "ETF": ("product", "ETF"), "채권": ("product", "Bond"), "국채": ("product", "Government Bond"),
    # --- People ---
    "트럼프": ("person", "Trump"), "Trump": ("person", "Trump"),
    "바이든": ("person", "Biden"), "머스크": ("person", "Elon Musk"),
    "파월": ("person", "Jerome Powell"), "버핏": ("person", "Warren Buffett"),
}


def extract_entities(
    text: str,
    extra_dict: Optional[dict[str, tuple[str, str]]] = None,
) -> list[dict]:
    """Extract entities from text using longest-match-first dictionary matching.

    Returns list of dicts: {type, name, keyword, count}.
    """
    entity_dict = {**DEFAULT_ENTITY_DICT}
    if extra_dict:
        entity_dict.update(extra_dict)

    # Sort keywords by length descending for longest-match-first
    sorted_keywords = sorted(entity_dict.keys(), key=len, reverse=True)

    # Track which character positions have been matched
    matched_positions: set[int] = set()
    # canonical_key -> count
    counts: dict[str, int] = {}
    # canonical_key -> first keyword that matched
    first_keyword: dict[str, str] = {}

    for keyword in sorted_keywords:
        etype, ename = entity_dict[keyword]
        canon_key = f"{etype}:{ename}"
        pattern = re.compile(re.escape(keyword))

        for m in pattern.finditer(text):
            span = set(range(m.start(), m.end()))
            if span & matched_positions:
                # Overlaps with already-matched region, skip
                continue
            matched_positions |= span
            counts[canon_key] = counts.get(canon_key, 0) + 1
            if canon_key not in first_keyword:
                first_keyword[canon_key] = keyword

    found: list[dict] = []
    for canon_key, count in counts.items():
        etype, ename = canon_key.split(":", 1)
        found.append({
            "type": etype,
            "name": ename,
            "keyword": first_keyword[canon_key],
            "count": count,
        })

    found.sort(key=lambda x: x["count"], reverse=True)
    return found
