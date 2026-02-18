"""General-purpose entity extraction from text.

Provides a comprehensive dictionary covering global tech companies, AI/ML terms,
programming languages, crypto, finance, people, and more. Case-insensitive
matching with word-boundary support for English entities.
"""
from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Entity dictionaries by category
# Each entry: keyword -> (entity_type, canonical_name)
# ---------------------------------------------------------------------------

_COMPANIES_KR: dict[str, tuple[str, str]] = {
    "삼성전자": ("company", "Samsung Electronics"),
    "삼성": ("company", "Samsung Electronics"),
    "SK하이닉스": ("company", "SK Hynix"),
    "하이닉스": ("company", "SK Hynix"),
    "현대차": ("company", "Hyundai Motor"),
    "LG전자": ("company", "LG Electronics"),
    "카카오": ("company", "Kakao"),
    "네이버": ("company", "Naver"),
    "쿠팡": ("company", "Coupang"),
    "토스": ("company", "Toss"),
    "셀트리온": ("company", "Celltrion"),
    "하이브": ("company", "HYBE"),
    "크래프톤": ("company", "Krafton"),
}

_COMPANIES_GLOBAL: dict[str, tuple[str, str]] = {
    # US Big Tech
    "Apple": ("company", "Apple"), "애플": ("company", "Apple"),
    "Tesla": ("company", "Tesla"), "테슬라": ("company", "Tesla"),
    "NVIDIA": ("company", "NVIDIA"), "엔비디아": ("company", "NVIDIA"),
    "Google": ("company", "Google"), "구글": ("company", "Google"),
    "Alphabet": ("company", "Google"),
    "Amazon": ("company", "Amazon"), "아마존": ("company", "Amazon"),
    "Microsoft": ("company", "Microsoft"), "마이크로소프트": ("company", "Microsoft"),
    "Meta": ("company", "Meta"), "메타": ("company", "Meta"),
    "Facebook": ("company", "Meta"),
    "Netflix": ("company", "Netflix"), "넷플릭스": ("company", "Netflix"),
    "AMD": ("company", "AMD"),
    "Intel": ("company", "Intel"), "인텔": ("company", "Intel"),
    "Qualcomm": ("company", "Qualcomm"), "퀄컴": ("company", "Qualcomm"),
    "Broadcom": ("company", "Broadcom"),
    "Oracle": ("company", "Oracle"), "오라클": ("company", "Oracle"),
    "Salesforce": ("company", "Salesforce"),
    "Adobe": ("company", "Adobe"),
    "IBM": ("company", "IBM"),
    "Cisco": ("company", "Cisco"),
    "PayPal": ("company", "PayPal"),
    "Uber": ("company", "Uber"),
    "Airbnb": ("company", "Airbnb"),
    "Spotify": ("company", "Spotify"),
    "Snap": ("company", "Snap"),
    "Pinterest": ("company", "Pinterest"),
    "Block": ("company", "Block"),
    "Palantir": ("company", "Palantir"),
    "Snowflake": ("company", "Snowflake"),
    "Databricks": ("company", "Databricks"),
    "Shopify": ("company", "Shopify"),
    "Stripe": ("company", "Stripe"),
    "CrowdStrike": ("company", "CrowdStrike"),
    "Palo Alto Networks": ("company", "Palo Alto Networks"),
    "Samsung": ("company", "Samsung Electronics"),
    "TSMC": ("company", "TSMC"),
    # AI companies
    "OpenAI": ("company", "OpenAI"), "오픈AI": ("company", "OpenAI"),
    "Anthropic": ("company", "Anthropic"), "앤트로픽": ("company", "Anthropic"),
    "DeepMind": ("company", "DeepMind"), "딥마인드": ("company", "DeepMind"),
    "Mistral": ("company", "Mistral"),
    "Cohere": ("company", "Cohere"),
    "xAI": ("company", "xAI"),
    "Hugging Face": ("company", "Hugging Face"),
    "Stability AI": ("company", "Stability AI"),
    "Midjourney": ("company", "Midjourney"),
    # CN/JP
    "Alibaba": ("company", "Alibaba"), "알리바바": ("company", "Alibaba"),
    "Tencent": ("company", "Tencent"), "텐센트": ("company", "Tencent"),
    "Baidu": ("company", "Baidu"), "바이두": ("company", "Baidu"),
    "BYD": ("company", "BYD"), "비야디": ("company", "BYD"),
    "SoftBank": ("company", "SoftBank"), "소프트뱅크": ("company", "SoftBank"),
    "DeepSeek": ("company", "DeepSeek"), "딥시크": ("company", "DeepSeek"),
    "ByteDance": ("company", "ByteDance"), "바이트댄스": ("company", "ByteDance"),
    # Finance
    "Berkshire Hathaway": ("company", "Berkshire Hathaway"), "버크셔": ("company", "Berkshire Hathaway"),
    "JPMorgan": ("company", "JPMorgan"), "JP모건": ("company", "JPMorgan"),
    "Goldman Sachs": ("company", "Goldman Sachs"), "골드만삭스": ("company", "Goldman Sachs"),
    "Morgan Stanley": ("company", "Morgan Stanley"),
    "BlackRock": ("company", "BlackRock"),
    "Citadel": ("company", "Citadel"),
}

_AI_ML: dict[str, tuple[str, str]] = {
    "Transformer": ("technology", "Transformer"),
    "GPT": ("technology", "GPT"),
    "GPT-4": ("technology", "GPT-4"),
    "GPT-4o": ("technology", "GPT-4o"),
    "GPT-3": ("technology", "GPT-3"),
    "ChatGPT": ("technology", "ChatGPT"),
    "BERT": ("technology", "BERT"),
    "LLM": ("technology", "LLM"),
    "diffusion": ("technology", "Diffusion Model"),
    "Stable Diffusion": ("technology", "Stable Diffusion"),
    "DALL-E": ("technology", "DALL-E"),
    "RAG": ("technology", "RAG"),
    "fine-tuning": ("technology", "Fine-tuning"),
    "finetuning": ("technology", "Fine-tuning"),
    "embedding": ("technology", "Embedding"),
    "attention mechanism": ("technology", "Attention"),
    "neural network": ("technology", "Neural Network"),
    "deep learning": ("technology", "Deep Learning"),
    "machine learning": ("technology", "Machine Learning"),
    "reinforcement learning": ("technology", "Reinforcement Learning"),
    "NLP": ("technology", "NLP"),
    "computer vision": ("technology", "Computer Vision"),
    "generative AI": ("technology", "Generative AI"),
    "생성형 AI": ("technology", "Generative AI"),
    "AGI": ("technology", "AGI"),
    "multimodal": ("technology", "Multimodal"),
    "prompt engineering": ("technology", "Prompt Engineering"),
    "LoRA": ("technology", "LoRA"),
    "vector database": ("technology", "Vector Database"),
    "langchain": ("technology", "LangChain"),
    "LangChain": ("technology", "LangChain"),
    "인공지능": ("technology", "AI"),
}

_PROGRAMMING: dict[str, tuple[str, str]] = {
    "Python": ("technology", "Python"),
    "JavaScript": ("technology", "JavaScript"),
    "TypeScript": ("technology", "TypeScript"),
    "Rust": ("technology", "Rust"),
    "Java": ("technology", "Java"),
    "C++": ("technology", "C++"),
    "C#": ("technology", "C#"),
    "Swift": ("technology", "Swift"),
    "Kotlin": ("technology", "Kotlin"),
    "React": ("technology", "React"),
    "Next.js": ("technology", "Next.js"),
    "Node.js": ("technology", "Node.js"),
    "Vue.js": ("technology", "Vue.js"),
    "Angular": ("technology", "Angular"),
    "Svelte": ("technology", "Svelte"),
    "Docker": ("technology", "Docker"),
    "Kubernetes": ("technology", "Kubernetes"),
    "AWS": ("technology", "AWS"),
    "GCP": ("technology", "GCP"),
    "Azure": ("technology", "Azure"),
    "Linux": ("technology", "Linux"),
    "Git": ("technology", "Git"),
    "GitHub": ("technology", "GitHub"),
    "PostgreSQL": ("technology", "PostgreSQL"),
    "MongoDB": ("technology", "MongoDB"),
    "Redis": ("technology", "Redis"),
    "Kafka": ("technology", "Kafka"),
    "GraphQL": ("technology", "GraphQL"),
    "Terraform": ("technology", "Terraform"),
    "FastAPI": ("technology", "FastAPI"),
    "Django": ("technology", "Django"),
    "Flask": ("technology", "Flask"),
    "Spring Boot": ("technology", "Spring Boot"),
    "WebAssembly": ("technology", "WebAssembly"),
    "WASM": ("technology", "WebAssembly"),
}

_CRYPTO: dict[str, tuple[str, str]] = {
    "Bitcoin": ("crypto", "BTC"), "비트코인": ("crypto", "BTC"),
    "Ethereum": ("crypto", "ETH"), "이더리움": ("crypto", "ETH"),
    "Solana": ("crypto", "SOL"), "솔라나": ("crypto", "SOL"),
    "Cardano": ("crypto", "ADA"),
    "Polkadot": ("crypto", "DOT"),
    "Chainlink": ("crypto", "LINK"),
    "Avalanche": ("crypto", "AVAX"),
    "Polygon": ("crypto", "MATIC"),
    "Arbitrum": ("crypto", "ARB"),
    "Optimism": ("crypto", "OP"),
    "Uniswap": ("crypto", "UNI"),
    "Aave": ("crypto", "AAVE"),
    "DeFi": ("crypto", "DeFi"),
    "NFT": ("crypto", "NFT"),
    "Web3": ("crypto", "Web3"),
    "리플": ("crypto", "XRP"), "XRP": ("crypto", "XRP"),
    "Ripple": ("crypto", "XRP"),
    "stablecoin": ("crypto", "Stablecoin"),
    "USDT": ("crypto", "USDT"),
    "USDC": ("crypto", "USDC"),
}

_INDICES: dict[str, tuple[str, str]] = {
    "코스피": ("index", "KOSPI"), "KOSPI": ("index", "KOSPI"),
    "코스닥": ("index", "KOSDAQ"), "KOSDAQ": ("index", "KOSDAQ"),
    "나스닥": ("index", "NASDAQ"), "NASDAQ": ("index", "NASDAQ"),
    "S&P 500": ("index", "S&P 500"), "S&P": ("index", "S&P 500"),
    "다우": ("index", "Dow Jones"), "Dow Jones": ("index", "Dow Jones"),
    "니케이": ("index", "Nikkei"), "Nikkei": ("index", "Nikkei"),
    "항셍": ("index", "Hang Seng"), "Hang Seng": ("index", "Hang Seng"),
    "FTSE": ("index", "FTSE"),
    "DAX": ("index", "DAX"),
    "Russell 2000": ("index", "Russell 2000"),
}

_MACRO_FINANCE: dict[str, tuple[str, str]] = {
    "금리": ("macro", "Interest Rate"), "interest rate": ("macro", "Interest Rate"),
    "인플레이션": ("macro", "Inflation"), "inflation": ("macro", "Inflation"),
    "관세": ("macro", "Tariff"), "tariff": ("macro", "Tariff"),
    "환율": ("macro", "Exchange Rate"),
    "recession": ("macro", "Recession"), "경기침체": ("macro", "Recession"),
    "GDP": ("macro", "GDP"),
    "CPI": ("macro", "CPI"),
    "yield curve": ("macro", "Yield Curve"),
    "quantitative easing": ("macro", "Quantitative Easing"),
    "quantitative tightening": ("macro", "Quantitative Tightening"),
    "Fed": ("institution", "Federal Reserve"),
    "Federal Reserve": ("institution", "Federal Reserve"),
    "연준": ("institution", "Federal Reserve"),
    "ECB": ("institution", "ECB"),
    "BOJ": ("institution", "BOJ"),
    "한국은행": ("institution", "Bank of Korea"),
    "treasury": ("product", "Treasury"),
    "국채": ("product", "Government Bond"),
    "채권": ("product", "Bond"), "bond": ("product", "Bond"),
    "ETF": ("product", "ETF"),
    "IPO": ("macro", "IPO"),
}

_COMMODITIES: dict[str, tuple[str, str]] = {
    "금값": ("commodity", "Gold"), "gold": ("commodity", "Gold"),
    "유가": ("commodity", "Oil"), "원유": ("commodity", "Oil"),
    "천연가스": ("commodity", "Natural Gas"), "natural gas": ("commodity", "Natural Gas"),
    "구리": ("commodity", "Copper"), "copper": ("commodity", "Copper"),
}

_COUNTRIES: dict[str, tuple[str, str]] = {
    "미국": ("country", "US"), "중국": ("country", "CN"), "일본": ("country", "JP"),
    "한국": ("country", "KR"), "유럽": ("region", "EU"), "독일": ("country", "DE"),
    "영국": ("country", "UK"), "인도": ("country", "IN"), "대만": ("country", "TW"),
}

_PEOPLE: dict[str, tuple[str, str]] = {
    "트럼프": ("person", "Trump"), "Trump": ("person", "Trump"),
    "바이든": ("person", "Biden"), "Biden": ("person", "Biden"),
    "머스크": ("person", "Elon Musk"), "Elon Musk": ("person", "Elon Musk"),
    "파월": ("person", "Jerome Powell"), "Jerome Powell": ("person", "Jerome Powell"),
    "버핏": ("person", "Warren Buffett"), "Warren Buffett": ("person", "Warren Buffett"),
    "Sam Altman": ("person", "Sam Altman"), "샘 알트만": ("person", "Sam Altman"),
    "Jensen Huang": ("person", "Jensen Huang"), "젠슨 황": ("person", "Jensen Huang"),
    "Satya Nadella": ("person", "Satya Nadella"),
    "Tim Cook": ("person", "Tim Cook"), "팀 쿡": ("person", "Tim Cook"),
    "Mark Zuckerberg": ("person", "Mark Zuckerberg"), "저커버그": ("person", "Mark Zuckerberg"),
    "Sundar Pichai": ("person", "Sundar Pichai"),
    "Jeff Bezos": ("person", "Jeff Bezos"), "베이조스": ("person", "Jeff Bezos"),
    "Linus Torvalds": ("person", "Linus Torvalds"),
    "Andrej Karpathy": ("person", "Andrej Karpathy"),
    "Yann LeCun": ("person", "Yann LeCun"),
    "Demis Hassabis": ("person", "Demis Hassabis"),
    "이재용": ("person", "Jay Y. Lee"),
}

_SECTORS: dict[str, tuple[str, str]] = {
    "반도체": ("sector", "Semiconductor"), "semiconductor": ("sector", "Semiconductor"),
    "부동산": ("sector", "Real Estate"), "real estate": ("sector", "Real Estate"),
    "electric vehicle": ("sector", "Electric Vehicle"), "EV": ("sector", "Electric Vehicle"),
    "전기차": ("sector", "Electric Vehicle"),
    "autonomous driving": ("sector", "Autonomous Driving"), "자율주행": ("sector", "Autonomous Driving"),
    "quantum computing": ("sector", "Quantum Computing"), "양자컴퓨팅": ("sector", "Quantum Computing"),
    "blockchain": ("sector", "Blockchain"), "블록체인": ("sector", "Blockchain"),
    "cloud computing": ("sector", "Cloud Computing"), "클라우드": ("sector", "Cloud Computing"),
    "cybersecurity": ("sector", "Cybersecurity"), "사이버보안": ("sector", "Cybersecurity"),
    "biotech": ("sector", "Biotech"), "바이오": ("sector", "Biotech"),
    "fintech": ("sector", "Fintech"), "핀테크": ("sector", "Fintech"),
    "edtech": ("sector", "Edtech"),
    "robotics": ("sector", "Robotics"), "로봇": ("sector", "Robotics"),
    "SaaS": ("sector", "SaaS"),
    "metaverse": ("sector", "Metaverse"), "메타버스": ("sector", "Metaverse"),
}

# Merge all into DEFAULT_ENTITY_DICT
DEFAULT_ENTITY_DICT: dict[str, tuple[str, str]] = {}
for _d in (
    _COMPANIES_KR, _COMPANIES_GLOBAL, _AI_ML, _PROGRAMMING,
    _CRYPTO, _INDICES, _MACRO_FINANCE, _COMMODITIES,
    _COUNTRIES, _PEOPLE, _SECTORS,
):
    DEFAULT_ENTITY_DICT.update(_d)

# ---------------------------------------------------------------------------
# Short English keywords that need strict word-boundary matching to avoid
# false positives (e.g. "Go" in "going", "AI" in "AGAIN", "EV" in "every").
# All others also use word-boundary but these are especially ambiguous.
# ---------------------------------------------------------------------------
_SHORT_KEYWORDS: set[str] = {
    "AI", "Go", "EV", "Git", "C#", "C++", "Fed", "GPU", "API",
    "Meta", "Block", "Snap", "Rust", "Java", "Swift",
    "LG", "AMD", "IBM", "S&P", "DAX", "BOJ", "ECB",
    "ETF", "IPO", "CPI", "GDP", "NLP", "AGI", "RAG",
    "NFT", "DeFi", "Web3", "LoRA", "WASM", "SaaS",
    "BYD", "XRP", "USDT", "USDC",
    "bond", "gold", "copper",
}

# Keywords that are pure Korean (no ASCII letters) — use substring match
def _is_korean_keyword(kw: str) -> bool:
    return bool(re.search(r"[가-힣]", kw)) and not re.search(r"[a-zA-Z]", kw)


def _build_pattern(keyword: str) -> re.Pattern:
    """Build a regex pattern for a keyword.
    
    - Korean-only keywords: substring match (case-sensitive)
    - English/mixed keywords: word-boundary match (case-insensitive)
    """
    escaped = re.escape(keyword)
    if _is_korean_keyword(keyword):
        return re.compile(escaped)
    else:
        # Word boundary matching, case-insensitive
        return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


def extract_entities(
    text: str,
    extra_dict: Optional[dict[str, tuple[str, str]]] = None,
) -> list[dict]:
    """Extract entities from text using longest-match-first dictionary matching.

    Features:
    - Case-insensitive matching for English entities
    - Word-boundary matching to prevent partial matches
    - Synonym grouping (multiple keywords → one canonical entity)

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
        pattern = _build_pattern(keyword)

        for m in pattern.finditer(text):
            span = set(range(m.start(), m.end()))
            if span & matched_positions:
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
