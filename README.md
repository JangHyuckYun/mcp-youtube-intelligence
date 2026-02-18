[![Python](https://img.shields.io/badge/python-≥3.10-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io/)
[![PyPI](https://img.shields.io/pypi/v/mcp-youtube-intelligence)](https://pypi.org/project/mcp-youtube-intelligence/)

🌐 [English](README.en.md) | **한국어**

# MCP YouTube Intelligence

> **YouTube 영상을 지능적으로 분석하는 [MCP](https://modelcontextprotocol.io/) 서버 + CLI**
>
> MCP (Model Context Protocol)는 Claude, Cursor 같은 AI 도구가 외부 서비스를 사용할 수 있게 해주는 표준 프로토콜입니다. 이 서버를 연결하면 "이 영상 요약해줘" 한마디로 분석이 완료됩니다.

🎯 **핵심 가치**: 원본 자막(5,000~50,000 토큰)을 **서버에서 처리**하여 LLM에는 **~300 토큰**만 전달합니다.

---

## 🤔 왜 이 서버인가?

대부분의 YouTube MCP 서버는 원본 자막을 그대로 LLM에 던집니다.

| 기능 | 기존 MCP 서버 | MCP YouTube Intelligence |
|------|:---:|:---:|
| 자막 추출 | ✅ | ✅ |
| **서버사이드 요약** (토큰 최적화) | ❌ | ✅ |
| **구조화된 리포트** (요약+토픽+엔티티+댓글) | ❌ | ✅ |
| **채널 모니터링** (RSS) | ❌ | ✅ |
| **댓글 감성 분석** | ❌ | ✅ |
| **토픽 세그멘테이션** | ❌ | ✅ |
| **엔티티 추출** (한/영 200+개) | ❌ | ✅ |
| **자막/YouTube 검색** | ❌ | ✅ |
| **배치 처리** | ❌ | ✅ |
| SQLite/PostgreSQL 캐시 | ❌ | ✅ |

---

## 🚀 빠른 시작

### 1. 설치

```bash
pip install mcp-youtube-intelligence
pip install yt-dlp  # 자막 추출에 필요
```

> 💡 LLM 없이도 기본 요약(핵심 문장 추출)은 동작합니다. 고품질 요약을 원하면 아래 [LLM 설정](#llm-프로바이더-설정)을 참고하세요.

### 2. 첫 번째 명령어 실행

```bash
# 리포트 생성 — 요약, 토픽, 엔티티, 댓글을 한번에 분석
mcp-yt report "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 자막 요약만
mcp-yt transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 영상 ID만 써도 됩니다
mcp-yt report dQw4w9WgXcQ
```

> ⚠️ zsh 사용자: URL에 `?`가 있으므로 반드시 **따옴표**로 감싸세요.

### 📋 리포트 출력 예시

`mcp-yt report` 실행 결과 (바이브 코딩 해설 영상, Ollama qwen2.5:7b):

```markdown
# 📹 Video Analysis Report: 바이브코딩이 뭔데? 10분 핵심 정리

> Channel: 코딩채널 | Duration: 5:19 | Language: ko

## 1. Summary

Vibecoding is a new approach to programming where developers give natural
language instructions to AI tools like Cursor, Windsurf, and Copilot, which
then generate code automatically. While this dramatically increases development
speed, concerns exist around code quality validation, potential security
vulnerabilities, and the risk of beginners neglecting fundamental coding skills.
Experts recommend using vibe coding as a supplementary tool while maintaining
thorough code review and testing practices.

## 2. Key Topics

| # | Topic | Timespan |
|---|-------|----------|
| 1 | AI 코딩 도구 소개 | 0:00~2:30 |
| 2 | 장단점 분석 | 2:30~4:15 |
| 3 | 전문가 조언 | 4:15~5:19 |

## 4. Keywords & Entities

- **Technology**: Cursor, Windsurf, Copilot, AI
- **Concept**: Vibe Coding, Code Review

## 5. Viewer Reactions

- Total comments: 20
- Sentiment: Positive 75% / Negative 5% / Neutral 20%
- Top opinions:
  - **@user1** (positive, 👍1600): 이거 보고 바로 시작했습니다
```

---

## 📖 CLI 전체 명령어

### 📊 리포트 (핵심 기능)

```bash
mcp-yt report "https://youtube.com/watch?v=VIDEO_ID"
mcp-yt report VIDEO_ID --provider ollama     # LLM 프로바이더 지정
mcp-yt report VIDEO_ID --no-comments         # 댓글 제외
mcp-yt report VIDEO_ID -o report.md          # 파일 저장
```

### 🎯 자막 추출 + 요약

```bash
mcp-yt transcript VIDEO_ID                   # 요약 (~300 토큰)
mcp-yt transcript VIDEO_ID --mode full       # 전체 자막
mcp-yt transcript VIDEO_ID --mode chunks     # 청크 분할
mcp-yt --json transcript VIDEO_ID            # JSON 출력
```

### 기타

```bash
mcp-yt video VIDEO_ID                        # 메타데이터
mcp-yt comments VIDEO_ID --max 20            # 댓글 (감성 분석 포함)
mcp-yt entities VIDEO_ID                     # 엔티티 추출
mcp-yt segments VIDEO_ID                     # 토픽 세그멘테이션
mcp-yt search "키워드" --max 5               # YouTube 검색
mcp-yt monitor subscribe @채널핸들           # 채널 모니터링
mcp-yt playlist PLAYLIST_ID                  # 플레이리스트
mcp-yt batch ID1 ID2 ID3                     # 배치 처리
mcp-yt search-transcripts "키워드"           # 저장된 자막 검색
```

> 💡 모든 명령어에 `--json` 플래그를 추가하면 JSON 출력됩니다.

---

## 🔌 MCP 서버 연결

> MCP 서버는 **stdio** 프로토콜로 통신합니다.

### Claude Desktop / Cursor / OpenCode

설정 파일에 추가 (`claude_desktop_config.json`, `.cursor/mcp.json`, `mcp.json`):

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["mcp-youtube-intelligence"],
      "env": {
        "MYI_LLM_PROVIDER": "ollama",
        "MYI_OLLAMA_MODEL": "qwen2.5:7b"
      }
    }
  }
}
```

> 💡 `uvx`는 [`uv`](https://docs.astral.sh/uv/) 패키지 매니저의 실행 명령어입니다. `pip install uv`로 설치하세요.
>
> 클라우드 LLM을 쓰려면 `env`에 API 키를 추가하면 됩니다: `"OPENAI_API_KEY": "sk-..."`

### Claude Code

```bash
claude mcp add youtube -- uvx mcp-youtube-intelligence
```

### MCP Tools (9개)

| Tool | 설명 | 예상 토큰 |
|------|------|:---------:|
| `get_video` | 메타데이터 + 요약 | ~300 |
| `get_transcript` | 자막 (summary/full/chunks) | ~300 |
| `get_comments` | 댓글 + 감성 분석 | ~200–500 |
| `monitor_channel` | RSS 채널 모니터링 | ~100–300 |
| `search_transcripts` | 저장된 자막 검색 | ~100–400 |
| `extract_entities` | 엔티티 추출 | ~150–300 |
| `segment_topics` | 토픽 분할 | ~100–250 |
| `search_youtube` | YouTube 검색 | ~200 |
| `get_playlist` | 플레이리스트 분석 | ~200–500 |

<details>
<summary>📖 Tool 파라미터 상세</summary>

### `get_video`
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

### `get_transcript`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `video_id` | string | ✅ | — | YouTube 영상 ID |
| `mode` | string | ❌ | `"summary"` | `summary` · `full` · `chunks` |

### `get_comments`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `video_id` | string | ✅ | — | YouTube 영상 ID |
| `top_n` | int | ❌ | `10` | 반환할 댓글 수 |
| `summarize` | bool | ❌ | `false` | 요약 뷰 |

### `monitor_channel`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `channel_ref` | string | ✅ | — | 채널 URL/@핸들/ID |
| `action` | string | ❌ | `"check"` | `add`·`check`·`list`·`remove` |

### `search_transcripts`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `limit` | int | ❌ | `10` | 최대 결과 수 |

### `extract_entities` / `segment_topics`
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

### `search_youtube`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `max_results` | int | ❌ | `10` | 최대 결과 수 |
| `order` | string | ❌ | `"relevance"` | `relevance`·`date`·`rating`·`viewCount` |

### `get_playlist`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `playlist_id` | string | ✅ | — | 플레이리스트 ID |
| `max_videos` | int | ❌ | `50` | 최대 영상 수 |

</details>

---

## ⚙️ 설정

### LLM 프로바이더 설정

LLM 없이도 기본 요약(핵심 문장 추출)은 동작합니다. 고품질 요약을 원하면:

#### Ollama (추천 — 무료, 오프라인)

```bash
# 1. Ollama 설치: https://ollama.ai
# 2. 모델 다운로드
ollama pull qwen2.5:7b

# 3. 환경변수 설정
export MYI_LLM_PROVIDER=ollama
export MYI_OLLAMA_MODEL=qwen2.5:7b
```

#### 클라우드 LLM

```bash
# API 키만 설정하면 자동 감지 (MYI_LLM_PROVIDER=auto)
export OPENAI_API_KEY=sk-...          # OpenAI
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic
export GOOGLE_API_KEY=AIza...         # Google

# 특정 프로바이더 지정
export MYI_LLM_PROVIDER=anthropic
```

> 클라우드 LLM 패키지: `pip install "mcp-youtube-intelligence[llm]"` (OpenAI) / `[anthropic-llm]` / `[google-llm]` / `[all-llm]`

### 추천 Ollama 모델

| 목적 | 모델 | 크기 | 한국어 | 영어 | 품질 |
|------|------|:----:|:------:|:----:|:----:|
| **다국어 (추천)** | `qwen2.5:7b` | 4.4GB | ✅ | ✅ | ⭐⭐⭐⭐ |
| **영어 중심** | `llama3.1:8b` | 4.7GB | ⚠️ | ✅ | ⭐⭐⭐⭐ |
| **한국어 특화** | `gemma2:9b` | 5.4GB | ✅ | ✅ | ⭐⭐⭐⭐ |
| **경량** | `qwen2.5:3b` | 1.9GB | ✅ | ✅ | ⭐⭐⭐ |
| **다국어 특화** | `aya-expanse:8b` | 4.8GB | ✅ | ✅ | ⭐⭐⭐ |

### ⏱️ 실측 벤치마크

> RTX 3070 8GB · Ollama · 한국어 자막 ~2,900자 (5분 19초 영상)
> `load_duration` 제외, 순수 생성 시간 기준

| 모델 | Prompt 처리 | 생성 시간 | 속도 | 출력 | 품질 |
|------|:-----------:|:---------:|:----:|:----:|:----:|
| **Extractive** | - | 즉시 | - | 379자 | ⭐⭐ |
| **qwen2.5:1.5b** | 7.8s | **4.7s** | 30.4 tok/s | 232자 | ⭐⭐ |
| **qwen2.5:7b** | 34.5s | **18.8s** | 7.3 tok/s | 766자 | ⭐⭐⭐⭐ |
| **aya-expanse:8b** | 29.5s | **34.5s** | 6.2 tok/s | 405자 | ⭐⭐⭐ |

> ⚠️ 첫 실행 시 모델 로드에 15~60초 추가. `keep_alive`로 메모리 유지하면 이후 로드 없음.

<details>
<summary>📖 전체 환경변수 목록</summary>

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `MYI_DATA_DIR` | `~/.mcp-youtube-intelligence` | 데이터 디렉토리 |
| `MYI_STORAGE` | `sqlite` | `sqlite` · `postgres` |
| `MYI_SQLITE_PATH` | `{DATA_DIR}/data.db` | SQLite 경로 |
| `MYI_POSTGRES_DSN` | — | PostgreSQL DSN |
| `MYI_YT_DLP` | `yt-dlp` | yt-dlp 경로 |
| `MYI_MAX_COMMENTS` | `20` | 최대 댓글 수 |
| `MYI_LLM_PROVIDER` | `auto` | `auto`·`openai`·`anthropic`·`google`·`ollama`·`vllm`·`lmstudio` |
| `OPENAI_API_KEY` | — | OpenAI 키 |
| `MYI_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI 모델 |
| `ANTHROPIC_API_KEY` | — | Anthropic 키 |
| `MYI_ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic 모델 |
| `GOOGLE_API_KEY` | — | Google 키 |
| `MYI_GOOGLE_MODEL` | `gemini-2.0-flash` | Google 모델 |
| `MYI_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama URL |
| `MYI_OLLAMA_MODEL` | `llama3.1:8b` | Ollama 모델 |
| `MYI_VLLM_BASE_URL` | `http://localhost:8000` | vLLM URL |
| `MYI_VLLM_MODEL` | — | vLLM 모델 |
| `MYI_LMSTUDIO_BASE_URL` | `http://localhost:1234` | LM Studio URL |
| `MYI_LMSTUDIO_MODEL` | — | LM Studio 모델 |

</details>

---

## 🔍 트러블슈팅

| 문제 | 해결 |
|------|------|
| `zsh: no matches found` | URL을 따옴표로 감싸기: `mcp-yt transcript "https://..."` |
| `yt-dlp not found` | `pip install yt-dlp` 또는 `export MYI_YT_DLP=/path/to/yt-dlp` |
| 자막 없는 영상 | `mcp-yt video`로 메타데이터만 가져오기 |
| SQLite database locked | 서버 인스턴스 하나만 실행 중인지 확인 |
| LLM 요약 실패 | 자동으로 extractive 폴백됨. API 키 확인. |

---

## 🤝 Contributing

```bash
git clone https://github.com/JangHyuckYun/mcp-youtube-intelligence.git
cd mcp-youtube-intelligence
pip install -e ".[dev]"
pytest tests/ -v
```

## 📄 라이선스

Apache 2.0 — [LICENSE](LICENSE)

## 📝 변경 이력

| 날짜 | 버전 | 주요 변경 |
|------|------|----------|
| 2025-02-18 | v0.1.0 | 초기 릴리스 — 9개 MCP 도구, CLI, SQLite |
| 2025-02-18 | v0.1.1 | Multi-LLM (OpenAI/Anthropic/Google), Apache 2.0 |
| 2025-02-18 | v0.1.2 | Local LLM (Ollama/vLLM/LM Studio), yt-dlp 자막 개선, 영어 기본 출력 |
