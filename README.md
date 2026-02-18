[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)]()
[![PyPI](https://img.shields.io/pypi/v/mcp-youtube-intelligence)](https://pypi.org/project/mcp-youtube-intelligence/)

# MCP YouTube Intelligence

> **YouTube 영상을 지능적으로 분석하는 MCP 서버** — 자막 추출, 요약, 엔티티 추출, 댓글 분석, 토픽 세그멘테이션, 채널 모니터링

🎯 **핵심 가치**: 원본 자막(5,000~50,000 토큰)을 **서버에서 처리**하여 LLM에는 **~300 토큰**만 전달합니다. 컨텍스트 윈도우를 낭비하지 않습니다.

[English](README.en.md)

---

## 🤔 왜 이 서버인가?

대부분의 YouTube MCP 서버는 원본 자막을 그대로 LLM에 던집니다. 영상 하나에 수만 토큰이 소모됩니다.

| 기능 | 기존 MCP 서버 | MCP YouTube Intelligence |
|------|:---:|:---:|
| 자막 추출 | ✅ | ✅ |
| **서버사이드 요약** (토큰 최적화) | ❌ | ✅ |
| **채널 모니터링** (RSS) | ❌ | ✅ |
| **댓글 수집 + 감성 분석** | ❌ | ✅ |
| **토픽 세그멘테이션** | ❌ | ✅ |
| **엔티티 추출** (한/영, 200+개) | ❌ | ✅ |
| **자막 검색** (키워드 → 스니펫) | ❌ | ✅ |
| **YouTube 검색** | ❌ | ✅ |
| **플레이리스트 분석** | ❌ | ✅ |
| **배치 처리** | ❌ | ✅ |
| SQLite/PostgreSQL 저장 | ❌ | ✅ |
| 추출식 요약 (API 키 불필요) | ❌ | ✅ |

**토큰 절감**: 영상 1개당 ~300 토큰 (요약) vs. 5,000~50,000 (원본 자막)

---

## 🏗️ 아키텍처

```
                         ┌─────────────────────────────────────────┐
                         │        MCP YouTube Intelligence         │
                         │                                         │
YouTube ──► yt-dlp/API ──┤  자막 ──► 정제 ──► 요약 ────────────────┤──► MCP Client
                         │   │                                     │    (~300 토큰)
                         │   ├──► 엔티티 추출                      │
                         │   ├──► 토픽 세그멘테이션                │
                         │   └──► 키워드 검색                      │
                         │                                         │
                         │  댓글 ──► 필터 + 감성분석 ──► 요약      │
                         │  RSS ──► 채널 모니터링 ──► 신규 영상    │
                         │                                         │
                         │      ▼                                  │
                         │  SQLite / PostgreSQL                    │
                         └─────────────────────────────────────────┘
```

무거운 처리(정제, 요약, 분석)는 **서버에서** 수행합니다. MCP 클라이언트는 **압축된 결과만** 수신합니다.

---

## 💡 활용 사례

### 🔬 리서치 & 학습

| 시나리오 | 기존 방식 | MYI 사용 후 | 개선 효과 |
|---------|----------|------------|----------|
| 1시간 강의 요약 | 영상 전체 시청 (60분) | 요약 읽기 (2분) | ⏱️ **97% 시간 절감** |
| 논문 리뷰 영상 분석 | 수동 메모 + 타임스탬프 찾기 | 토픽 세그멘테이션 자동 분할 | 📑 핵심 구간 즉시 탐색 |
| 기술 트렌드 파악 | 10개 영상 각각 시청 | 배치 처리로 한번에 요약 | 🚀 **10x 처리량** |

**예시**: "Anthropic Agent SDK" 튜토리얼 영상 (20분)
```
원본 자막: 15,000+ 토큰
→ MYI 요약: ~300 토큰 (98% 절감)
→ 추출된 엔티티: [Anthropic, Agent SDK, Claude, Tool Use, MCP, Python]
→ 토픽 세그먼트: [설치, 기본 구조, 도구 연결, 에이전트 실행, 배포]
```

### 📊 시장 & 트렌드 모니터링

| 시나리오 | 활용 방법 | 효과 |
|---------|----------|------|
| 크립토 유튜버 추적 | `monitor_channel`로 신규 영상 감지 → 자동 요약 | 📡 실시간 시장 인사이트 |
| 경쟁사 제품 분석 | 제품 발표 영상 엔티티 추출 + 댓글 감성 분석 | 🎯 시장 반응 즉시 파악 |
| 투자 리서치 | 애널리스트 영상 배치 요약 → Notion DB 저장 | 📚 체계적 지식 축적 |

**예시**: 채널 모니터링 → AI 에이전트 자동화
```bash
# 1. 채널 등록
mcp-yt monitor UC_x5XG1OV2P6uZZ5FSM9Ttw --interval 3600

# 2. 신규 영상 감지 시 자동 요약 (cron/스크립트 연동)
mcp-yt transcript <new_video_id> --summarize
# → 슬랙/디스코드 웹훅으로 요약 전송
```

### 🤖 AI 에이전트 연동

| 에이전트 | 연동 방식 | 활용 |
|---------|----------|------|
| Claude Code | MCP 서버 직접 연결 | "이 영상 요약해줘" 한마디로 분석 완료 |
| OpenClaw | Skills로 등록 | 자동 리서치 파이프라인 구축 |
| Cursor | MCP 설정 | 코딩 튜토리얼 즉시 분석 |
| 커스텀 봇 | CLI 파이프라인 | `mcp-yt transcript ID \| jq .summary` |

**토큰 비용 절감 실측**:
```
영상 1개 (20분) 원본 자막을 LLM에 직접 전달:  ~15,000 토큰 ($0.015)
MYI 요약 후 전달:                              ~300 토큰 ($0.0003)
──────────────────────────────────────────────────────────
절감: 98%, 50배 비용 효율 (영상 100개 처리 시 $1.50 → $0.03)
```

### 🎓 교육 & 콘텐츠 제작

- **강의 노트 자동 생성**: 토픽 세그멘테이션으로 챕터별 요약
- **다국어 콘텐츠 분석**: 한/영/일 자막 자동 감지 + 요약
- **댓글 인사이트**: 시청자 반응 감성 분석으로 콘텐츠 개선 포인트 도출
- **플레이리스트 일괄 처리**: 강의 시리즈 전체를 한번에 요약

---

## 🚀 빠른 시작

### 설치

```bash
# uv (권장)
uv pip install mcp-youtube-intelligence

# pip
pip install mcp-youtube-intelligence

# 선택적 의존성
pip install "mcp-youtube-intelligence[all-llm]"        # 모든 LLM (OpenAI + Anthropic + Google)
pip install "mcp-youtube-intelligence[llm]"            # OpenAI만
pip install "mcp-youtube-intelligence[anthropic-llm]"  # Anthropic만
pip install "mcp-youtube-intelligence[google-llm]"     # Google만
pip install "mcp-youtube-intelligence[postgres]"       # PostgreSQL 백엔드
pip install "mcp-youtube-intelligence[dev]"            # 개발 (pytest 등)
```

> **필수 조건**: `yt-dlp`가 PATH에 있어야 합니다.
> ```bash
> pip install yt-dlp
> ```

### CLI 사용법

설치하면 `mcp-yt` 명령어를 사용할 수 있습니다.

#### 자막 추출

```bash
# 요약 (기본, ~300 토큰)
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ

# 전체 자막 (파일로 저장)
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ --mode full

# 청크 분할
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ --mode chunks

# JSON 출력
mcp-yt --json transcript https://youtube.com/watch?v=dQw4w9WgXcQ

# 파일로 저장
mcp-yt transcript https://youtube.com/watch?v=dQw4w9WgXcQ -o summary.txt
```

#### YouTube 검색

```bash
mcp-yt search "transformer 설명"
mcp-yt search "파이썬 튜토리얼" --max 5 --order date
mcp-yt search "AI 뉴스" --channel UCxxxx
```

#### 영상 메타데이터 + 요약

```bash
mcp-yt video https://youtube.com/watch?v=dQw4w9WgXcQ
```

출력 예시:
```
video_id: dQw4w9WgXcQ
title: Video Title
channel_name: Channel Name
duration_seconds: 612
view_count: 1500000
summary: 이 영상은 세 가지 핵심 주제를 다룹니다...
```

#### 댓글 수집

```bash
# 인기 댓글 10개
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ

# 최신순 20개
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --max 20 --sort newest

# 긍정 댓글만
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --sentiment positive

# 부정 댓글만
mcp-yt comments https://youtube.com/watch?v=dQw4w9WgXcQ --sentiment negative
```

#### 채널 모니터링

```bash
# 구독
mcp-yt monitor subscribe @3blue1brown

# 신규 영상 확인
mcp-yt monitor check --channel UCYO_jab_esuFRV4b17AJtAw

# 구독 목록
mcp-yt monitor list
```

#### 엔티티 추출

```bash
mcp-yt entities https://youtube.com/watch?v=dQw4w9WgXcQ
```

출력 예시:
```
entity_count: 5
entities: (5 items)
  [1] type: company, name: NVIDIA, keyword: 엔비디아, count: 12
  [2] type: sector, name: AI, keyword: AI, count: 8
  [3] type: index, name: NASDAQ, keyword: 나스닥, count: 5
```

#### 토픽 세그멘테이션

```bash
mcp-yt segments https://youtube.com/watch?v=dQw4w9WgXcQ
```

#### 플레이리스트

```bash
mcp-yt playlist https://youtube.com/playlist?list=PLrAXtmErZgOe...
mcp-yt playlist PLrAXtmErZgOe... --max 10
```

#### 배치 처리

```bash
mcp-yt batch dQw4w9WgXcQ abc123def45 xyz789ghi01
mcp-yt batch dQw4w9WgXcQ abc123def45 --mode full
```

#### 저장된 자막 검색

```bash
mcp-yt search-transcripts "transformer architecture"
```

> 💡 모든 명령어에 `--json` 플래그를 추가하면 JSON 형식으로 출력됩니다.

---

## 🔌 MCP 서버 연결 가이드

### Claude Desktop

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza...",
        "MYI_LLM_PROVIDER": "auto"
      }
    }
  }
}
```

> 💡 사용할 프로바이더의 API 키만 설정하면 됩니다. `auto` 모드에서 자동 감지합니다.

### Claude Code

```bash
claude mcp add youtube -- uvx mcp-youtube-intelligence
```

### OpenCode

`mcp.json` 또는 프로젝트 설정 파일에 추가:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza..."
      }
    }
  }
}
```

### Cursor

`.cursor/mcp.json` 파일을 생성하고 추가:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "GOOGLE_API_KEY": "AIza..."
      }
    }
  }
}
```

### Claude Code Skills 연동

CLI가 제공되므로, Claude Code에서 스킬로 등록하여 사용할 수 있습니다.

```
skills/
  youtube/
    SKILL.md
```

`SKILL.md` 예시:

```markdown
# YouTube 분석 스킬

YouTube 영상 분석이 필요할 때 `mcp-yt` CLI를 사용합니다.

## 사용 가능한 명령어

- `mcp-yt transcript <URL>` — 자막 추출/요약
- `mcp-yt video <URL>` — 영상 메타데이터
- `mcp-yt comments <URL>` — 댓글 분석
- `mcp-yt entities <URL>` — 엔티티 추출
- `mcp-yt segments <URL>` — 토픽 분류
- `mcp-yt search "키워드"` — YouTube 검색
- `mcp-yt search-transcripts "키워드"` — 저장된 자막 검색
- `mcp-yt monitor subscribe <URL>` — 채널 모니터링
- `mcp-yt playlist <URL>` — 플레이리스트
- `mcp-yt batch <id1> <id2>` — 배치 처리

## 규칙

- 항상 `--json` 플래그로 구조화된 출력을 받습니다
- 영상 URL이나 11자리 ID 모두 사용 가능합니다
- 자막 요약은 기본적으로 ~300 토큰입니다
```

---

## ⭐ 핵심 기능 한눈에 보기

> 💡 **바이브코딩 개발자**: MCP 서버로 연결만 하면 "이 영상 요약해줘" 한마디로 끝!
> 💡 **일반 개발자**: CLI(`mcp-yt`)로 스크립트/파이프라인에 바로 통합 가능

### 1. 🎯 자막 추출 + 토큰 최적화 요약
YouTube 영상의 자막을 가져와서 **서버에서 요약**합니다. LLM에 원본 자막을 보내면 5,000~50,000 토큰이 날아가지만, MYI는 **~300 토큰**으로 압축해서 전달합니다.
- 한국어/영어/일본어 등 **다국어 자동 감지**
- 수동 자막 우선, 없으면 자동 자막 사용
- API 키 없이도 **추출식 요약** 동작 (LLM 요약은 선택)

### 2. 🏷️ 엔티티 추출
자막에서 **인물, 기업, 기술, 제품명**을 자동으로 뽑아냅니다. 200+ 엔티티 사전 내장.
- 도메인: AI/ML, 크립토, 프로그래밍, 글로벌 기업, 경제 용어 등
- 한국어 + 영어 동시 지원
- 커스텀 엔티티 추가 가능

### 3. 📑 토픽 세그멘테이션
긴 영상을 **주제별로 자동 분할**합니다. "어디서 뭘 얘기하는지" 바로 파악 가능.
- 키워드 변화 기반 세그먼트 경계 감지
- 각 세그먼트에 대표 토픽 라벨 자동 부여
- 타임스탬프 연동으로 원하는 구간으로 바로 점프

### 4. 💬 댓글 수집 + 감성 분석
영상의 **댓글을 수집**하고 **긍정/부정/중립** 감성을 분석합니다.
- 정렬: 인기순 / 최신순
- 노이즈 필터링: 스팸, 봇 댓글 자동 제거
- 감성 필터: 긍정만 / 부정만 / 전체

### 5. 📡 채널 모니터링
YouTube 채널을 **RSS로 구독**하여 새 영상이 올라오면 감지합니다.
- 주기적 체크 (cron/스크립트 연동)
- 신규 영상 자동 요약 파이프라인 구축 가능
- yt-dlp 폴백으로 안정성 확보

### 6. 🔍 YouTube 검색 + 자막 검색
- **YouTube 검색**: 키워드로 영상 검색 (Data API v3 + yt-dlp 폴백)
- **자막 내 검색**: 저장된 자막에서 키워드 → 관련 스니펫 반환
- 플레이리스트 전체 분석도 지원

### 7. 📦 배치 처리
여러 영상을 **한 번에** 처리합니다. 세미나 시리즈, 강의 플레이리스트 등.
- 비동기 병렬 처리 (세마포어 제한으로 안정적)
- 영상 ID 목록 또는 플레이리스트 URL 입력

### 8. 💾 데이터 저장
분석 결과를 **로컬 DB에 자동 저장**합니다.
- SQLite (기본, 설정 불필요) / PostgreSQL (선택)
- 중복 요청 시 캐시에서 즉시 반환
- 검색 인덱스로 빠른 키워드 조회

---

## 🔧 MCP Tools 상세 (9개)

### 1. `get_video`

영상 메타데이터 + 요약을 한 번에 가져옵니다. 결과를 캐시합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

```json
// 요청
{"tool": "get_video", "arguments": {"video_id": "dQw4w9WgXcQ"}}

// 응답 (~300 토큰)
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "channel_name": "Channel",
  "duration_seconds": 612,
  "view_count": 1500000,
  "like_count": 45000,
  "summary": "이 영상은...",
  "transcript_length": 15420,
  "status": "done"
}
```

**예상 토큰**: ~300

---

### 2. `get_transcript`

자막을 3가지 모드로 가져옵니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `video_id` | string | ✅ | — | YouTube 영상 ID |
| `mode` | string | ❌ | `"summary"` | `summary` · `full` · `chunks` |

**모드별 응답**:

- **`summary`** — 요약 반환 (~300 토큰, **권장**)
- **`full`** — 자막을 파일로 저장, 경로 반환 (~50 토큰)
- **`chunks`** — ~2000자씩 분할하여 순차 처리

```json
// summary 모드
{"video_id": "abc123", "mode": "summary", "summary": "...", "char_count": 15420}

// full 모드
{"video_id": "abc123", "mode": "full", "file_path": "~/.mcp-youtube-intelligence/transcripts/abc123.txt", "char_count": 15420}

// chunks 모드
{"video_id": "abc123", "mode": "chunks", "chunk_count": 8, "chunks": [{"index": 0, "text": "...", "char_count": 2000}]}
```

**예상 토큰**: summary ~300 | full ~50 | chunks ~N×500

---

### 3. `get_comments`

댓글을 수집하고 선택적으로 요약합니다. 스팸/노이즈 자동 필터링, 감성 분석 포함.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `video_id` | string | ✅ | — | YouTube 영상 ID |
| `top_n` | int | ❌ | `10` | 반환할 댓글 수 |
| `summarize` | bool | ❌ | `false` | 요약 뷰 반환 여부 |

```json
// 응답
{
  "video_id": "abc123",
  "count": 10,
  "comments": [
    {"author": "User1", "text": "Great explanation!", "likes": 245, "sentiment": "positive"},
    {"author": "User2", "text": "도움이 많이 됐습니다", "likes": 132, "sentiment": "positive"}
  ]
}
```

**예상 토큰**: ~200–500

---

### 4. `monitor_channel`

RSS 기반 채널 모니터링. 구독 → 신규 영상 감지.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `channel_ref` | string | ✅ | — | 채널 URL, @핸들, 또는 채널 ID |
| `action` | string | ❌ | `"check"` | `add` · `check` · `list` · `remove` |

```json
// 구독
{"tool": "monitor_channel", "arguments": {"channel_ref": "@3blue1brown", "action": "add"}}

// 신규 확인
{"tool": "monitor_channel", "arguments": {"channel_ref": "UCYO_jab...", "action": "check"}}
// → {"channel_id": "...", "new_videos": [{"video_id": "abc123", "title": "New Video", "published": "..."}]}
```

**예상 토큰**: ~100–300

---

### 5. `search_transcripts`

저장된 자막에서 키워드 검색. 컨텍스트 스니펫 반환.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `limit` | int | ❌ | `10` | 최대 결과 수 |

```json
{
  "query": "transformer",
  "count": 3,
  "results": [
    {"video_id": "abc123", "title": "Attention Is All You Need", "snippet": "...transformer architecture uses..."}
  ]
}
```

**예상 토큰**: ~100–400

---

### 6. `extract_entities`

자막에서 구조화된 엔티티 추출. 회사, 주가지수, 암호화폐, 기술, 인물 등 200+개 엔티티 사전.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

```json
{
  "video_id": "abc123",
  "entity_count": 5,
  "entities": [
    {"type": "company", "name": "NVIDIA", "keyword": "엔비디아", "count": 12},
    {"type": "technology", "name": "GPT-4", "keyword": "GPT-4", "count": 8},
    {"type": "person", "name": "Sam Altman", "keyword": "샘 알트만", "count": 3}
  ]
}
```

**예상 토큰**: ~150–300

---

### 7. `segment_topics`

자막을 토픽 전환 마커 기반으로 구간 분할합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

```json
{
  "video_id": "abc123",
  "segment_count": 4,
  "segments": [
    {"segment": 0, "char_count": 3200, "preview": "첫 200자 미리보기..."},
    {"segment": 1, "char_count": 2800, "preview": "다음 구간 미리보기..."}
  ]
}
```

**예상 토큰**: ~100–250

---

### 8. `search_youtube`

YouTube 영상을 키워드로 검색합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `max_results` | int | ❌ | `10` | 최대 결과 수 (1–50) |
| `channel_id` | string | ❌ | — | 특정 채널 제한 |
| `published_after` | string | ❌ | — | 게시일 필터 (ISO 8601) |
| `order` | string | ❌ | `"relevance"` | `relevance` · `date` · `rating` · `viewCount` |

**예상 토큰**: ~200

---

### 9. `get_playlist`

플레이리스트 메타데이터와 영상 목록을 가져옵니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `playlist_id` | string | ✅ | — | YouTube 플레이리스트 ID |
| `max_videos` | int | ❌ | `50` | 최대 영상 수 |

**예상 토큰**: ~200–500

---

## ⚙️ 설정 (Configuration)

모든 설정은 환경변수로 관리합니다 (`MYI_` 접두사):

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `MYI_DATA_DIR` | `~/.mcp-youtube-intelligence` | 데이터 디렉토리 (DB, 자막 파일) |
| `MYI_STORAGE` | `sqlite` | 스토리지 백엔드: `sqlite` · `postgres` |
| `MYI_SQLITE_PATH` | `{DATA_DIR}/data.db` | SQLite DB 경로 |
| `MYI_POSTGRES_DSN` | — | PostgreSQL 연결 문자열 |
| `MYI_TRANSCRIPT_DIR` | `{DATA_DIR}/transcripts` | 자막 파일 저장 경로 |
| `MYI_YT_DLP` | `yt-dlp` | yt-dlp 바이너리 경로 |
| `MYI_YOUTUBE_API_KEY` | — | YouTube Data API 키 |
| `MYI_MAX_COMMENTS` | `20` | 최대 댓글 수집 수 |
| `MYI_MAX_TRANSCRIPT_CHARS` | `500000` | 최대 자막 길이 |
| `MYI_LLM_PROVIDER` | `auto` | LLM 프로바이더: `auto` · `openai` · `anthropic` · `google` |
| `OPENAI_API_KEY` | — | OpenAI API 키 |
| `OPENAI_BASE_URL` | — | OpenAI 호환 엔드포인트 |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI 모델명 |
| `ANTHROPIC_API_KEY` | — | Anthropic API 키 |
| `MYI_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic 모델명 |
| `GOOGLE_API_KEY` | — | Google API 키 |
| `MYI_GOOGLE_MODEL` | `gemini-2.0-flash` | Google 모델명 |

### LLM 연동 가이드

기본적으로 **추출식 요약** (API 키 불필요)을 사용합니다. LLM을 연결하면 더 높은 품질의 요약을 생성합니다.

3개 프로바이더를 지원하며, `MYI_LLM_PROVIDER` 환경변수로 선택합니다:

| 프로바이더 | API 키 환경변수 | 모델 환경변수 | 기본 모델 |
|-----------|----------------|-------------|----------|
| OpenAI | `OPENAI_API_KEY` | `MYI_OPENAI_MODEL` | `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `MYI_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` |
| Google | `GOOGLE_API_KEY` | `MYI_GOOGLE_MODEL` | `gemini-2.0-flash` |

`MYI_LLM_PROVIDER`의 기본값은 `auto`로, 설정된 API 키를 자동 감지하여 사용합니다.

**OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini          # 선택
```

**Anthropic**
```bash
pip install "mcp-youtube-intelligence[anthropic-llm]"
export ANTHROPIC_API_KEY=sk-ant-...
export MYI_ANTHROPIC_MODEL=claude-sonnet-4-20250514  # 선택
```

**Google**
```bash
pip install "mcp-youtube-intelligence[google-llm]"
export GOOGLE_API_KEY=AIza...
export MYI_GOOGLE_MODEL=gemini-2.0-flash     # 선택
```

**프로바이더 명시 지정** (여러 API 키가 설정된 경우):
```bash
export MYI_LLM_PROVIDER=anthropic  # openai / anthropic / google / auto
```

**OpenAI 호환 API** (Ollama, LM Studio, vLLM 등):
```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**토큰 비용 비교**:

| 모드 | 클라이언트 토큰 | 서버 비용 |
|------|:-:|:-:|
| API 키 없음 (추출식) | ~300 | 무료 |
| LLM (gpt-4o-mini) | ~500 | ~$0.001/영상 |
| LLM (claude-sonnet-4-20250514) | ~500 | ~$0.003/영상 |
| LLM (gemini-2.0-flash) | ~500 | ~$0.0005/영상 |
| 원본 자막 (기존 MCP 서버) | 5,000–50,000 | 무료지만 컨텍스트 파괴 |

---

## 📐 추출식 요약 파이프라인

LLM 없이도 효과적인 요약을 제공합니다. 작동 방식:

```
원본 자막
  │
  ▼
① 문장 분리 (한국어 종결어미 + 영어 구두점 인식)
  │
  ▼
② 균등 청킹 (전체 텍스트를 N개 청크로 분할)
  │  → 긴 영상도 앞/중간/뒤 골고루 커버
  │
  ▼
③ 문장 점수 산출
  │  • 길이 가중치 (긴 문장 = 정보량 ↑)
  │  • 위치 가중치 (앞쪽 문장 약간 우선)
  │  • 키워드 보너스 ("결론", "핵심", "in summary" 등 → ×1.6)
  │  • 숫자 보너스 (통계/데이터 포함 → ×1.4)
  │
  ▼
④ 적응형 길이 (원문 길이에 비례, 500~2000자)
  │
  ▼
⑤ 원래 순서대로 재조합 → 요약 완성
```

---

## 🔍 트러블슈팅

### `zsh: no matches found` 오류

zsh에서 URL의 `?` 문자를 glob 패턴으로 인식합니다. **URL을 따옴표로 감싸세요:**

```bash
# ❌ 오류
mcp-yt transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ

# ✅ 해결
mcp-yt transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# ✅ 또는 영상 ID만 사용
mcp-yt transcript dQw4w9WgXcQ
```

### `yt-dlp` not found

```bash
pip install yt-dlp
# 또는 경로 지정:
export MYI_YT_DLP=/usr/local/bin/yt-dlp
```

### 자막이 없는 영상

일부 영상은 자동/수동 자막이 없습니다. `get_video`를 사용하면 자막 없이도 메타데이터를 가져올 수 있습니다.

### 댓글 로딩이 느림

yt-dlp 댓글 추출은 30~60초가 걸릴 수 있습니다. 기본적으로 20개로 제한됩니다.

### SQLite database locked

서버 인스턴스가 하나만 실행 중인지 확인하세요.

### OpenAI API 오류

LLM 요약이 실패하면 자동으로 추출식 요약으로 폴백합니다. `OPENAI_API_KEY`와 `MYI_OPENAI_MODEL`을 확인하세요.

---

## 🤝 Contributing

### 개발 환경 설정

```bash
git clone https://github.com/JangHyuckYun/mcp-youtube-intelligence.git
cd mcp-youtube-intelligence
pip install -e ".[dev]"
```

### 테스트

```bash
pytest tests/ -v
```

### 기여 아이디어

- 추가 엔티티 사전 (일본어, 중국어 등)
- Whisper 연동 (자막 없는 영상)
- 댓글 감성 분석 고도화
- 다양한 내보내기 형식 (CSV, Markdown)

---

## 📋 요구사항

- Python ≥ 3.10
- `yt-dlp` (PATH에 설치)
- 인터넷 연결

## 📄 라이선스

Apache 2.0 — [LICENSE](LICENSE) 참조

---

## 📝 변경 이력

| 날짜 | 버전 | 주요 변경 |
|------|------|----------|
| 2025-02-18 | v0.1.0 | 초기 릴리스 — 9개 MCP 도구, CLI(`mcp-yt`), SQLite 저장 |
| 2025-02-18 | v0.1.1 | Multi-LLM 지원 (OpenAI/Anthropic/Google), 라이선스 Apache 2.0 변경 |
| 2025-02-18 | v0.1.2 | yt-dlp 자막 폴백, 다국어 fallback, extractive 요약 개선 |
