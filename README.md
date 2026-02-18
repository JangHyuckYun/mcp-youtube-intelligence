[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
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

## 🚀 빠른 시작

### 설치

```bash
# uv (권장)
uv pip install mcp-youtube-intelligence

# pip
pip install mcp-youtube-intelligence

# 선택적 의존성
pip install "mcp-youtube-intelligence[llm]"       # OpenAI LLM 요약
pip install "mcp-youtube-intelligence[postgres]"  # PostgreSQL 백엔드
pip install "mcp-youtube-intelligence[dev]"       # 개발 (pytest 등)
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
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

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
        "OPENAI_API_KEY": "sk-..."
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
        "OPENAI_API_KEY": "sk-..."
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
| `OPENAI_API_KEY` | — | OpenAI API 키 (LLM 요약용) |
| `OPENAI_BASE_URL` | — | OpenAI 호환 엔드포인트 |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | LLM 모델명 |

### LLM 연동 가이드

기본적으로 **추출식 요약** (API 키 불필요)을 사용합니다. LLM을 연결하면 더 높은 품질의 요약을 생성합니다.

**OpenAI**
```bash
pip install "mcp-youtube-intelligence[llm]"
export OPENAI_API_KEY=sk-...
export MYI_OPENAI_MODEL=gpt-4o-mini
```

**Ollama (로컬)**
```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MYI_OPENAI_MODEL=llama3.2
```

**LM Studio (로컬)**
```bash
export OPENAI_API_KEY=lm-studio
export OPENAI_BASE_URL=http://localhost:1234/v1
export MYI_OPENAI_MODEL=your-model-name
```

**토큰 비용 비교**:

| 모드 | 클라이언트 토큰 | 서버 비용 |
|------|:-:|:-:|
| API 키 없음 (추출식) | ~300 | 무료 |
| LLM (gpt-4o-mini) | ~500 | ~$0.001/영상 |
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

MIT — [LICENSE](LICENSE) 참조
