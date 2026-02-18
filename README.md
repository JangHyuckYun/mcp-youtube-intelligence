[![Python](https://img.shields.io/badge/python-≥3.10-blue)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green)]()
[![PyPI](https://img.shields.io/pypi/v/mcp-youtube-intelligence)](https://pypi.org/project/mcp-youtube-intelligence/)

# MCP YouTube Intelligence

> **YouTube 영상을 지능적으로 분석하는 MCP 서버 + CLI** — 자막 추출, 요약, 리포트, 엔티티 추출, 댓글 분석, 토픽 세그멘테이션, 채널 모니터링

🎯 **핵심 가치**: 원본 자막(5,000~50,000 토큰)을 **서버에서 처리**하여 LLM에는 **~300 토큰**만 전달합니다.

> ### ⚡ 요약 품질은 LLM이 결정합니다
>
> LLM 없이도 동작하지만, **기본 요약은 핵심 문장 추출 수준** (미리보기)입니다.
> 고품질 요약을 원한다면 **Local LLM (Ollama)을 권장**합니다 — **무료, 오프라인, API 키 불필요**.
>
> ```bash
> # Ollama 설치 후 모델 하나만 받으면 끝
> ollama pull qwen2.5:7b    # 다국어 추천 (4.4GB)
> export MYI_LLM_PROVIDER=ollama
> export MYI_OLLAMA_MODEL=qwen2.5:7b
> ```
>
> **실측 결과** (RTX 3070 8GB, 한국어 ~2,900자, 모델 로드 완료 상태):
>
> | 방식 | 생성 시간 | 품질 | 비용 |
> |------|:---------:|:----:|:----:|
> | Extractive (LLM 없음) | 즉시 | ⭐⭐ 핵심 문장 나열 | 무료 |
> | **Ollama qwen2.5:7b** | **~19초** | ⭐⭐⭐⭐ 구조화된 영어 요약 | **무료** |
> | Ollama aya-expanse:8b | ~35초 | ⭐⭐⭐ 다국어 요약 | 무료 |
> | GPT-4o / Claude | 3~5초 | ⭐⭐⭐⭐⭐ 최고 품질 | ~$0.001/영상 |
>
> ⚠️ **첫 실행 시 모델 로드에 30~60초 추가 소요**됩니다.

[English](README.en.md)

---

## 🚀 빠른 시작

### 1. 설치

```bash
pip install mcp-youtube-intelligence
pip install yt-dlp  # 필수 의존성
```

LLM 요약을 쓰려면 (선택):
```bash
# 클라우드 LLM
pip install "mcp-youtube-intelligence[llm]"            # OpenAI
pip install "mcp-youtube-intelligence[anthropic-llm]"  # Anthropic
pip install "mcp-youtube-intelligence[google-llm]"     # Google
pip install "mcp-youtube-intelligence[all-llm]"        # 전부

# 로컬 LLM (추천 — 무료)
# Ollama 설치 후: ollama pull qwen2.5:7b
export MYI_LLM_PROVIDER=ollama
export MYI_OLLAMA_MODEL=qwen2.5:7b
```

### 2. CLI 사용법

설치하면 `mcp-yt` 명령어를 바로 사용할 수 있습니다.

#### 📊 리포트 생성 (핵심 기능)

영상 하나를 **요약 + 토픽 + 엔티티 + 댓글**까지 한번에 분석합니다:

```bash
mcp-yt report "https://youtube.com/watch?v=VIDEO_ID"

# LLM 프로바이더 지정
mcp-yt report "https://youtube.com/watch?v=VIDEO_ID" --provider ollama

# 댓글 제외
mcp-yt report "https://youtube.com/watch?v=VIDEO_ID" --no-comments

# 파일로 저장
mcp-yt report "https://youtube.com/watch?v=VIDEO_ID" -o report.md
```

<details>
<summary>📋 리포트 출력 예시 (바이브 코딩 해설 영상)</summary>

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

## 3. Detailed Analysis

### Topic 1: AI 코딩 도구 소개
바이브 코딩이라는 개념이 최근 화제가 되고 있습니다. AI를 활용해서
코딩을 하는 새로운 방식인데요...

## 4. Keywords & Entities

- **Technology**: Cursor, Windsurf, Copilot, AI
- **Concept**: Vibe Coding, Code Review

## 5. Viewer Reactions

- Total comments: 20
- Sentiment: Positive 75% / Negative 5% / Neutral 20%
- Top opinions:
  - **@user1** (positive, 👍1600): 이거 보고 바로 시작했습니다
  - **@user2** (positive, 👍890): 깔끔한 정리 감사합니다
```
</details>

#### 🎯 자막 추출 + 요약

```bash
# 요약 (기본, ~300 토큰)
mcp-yt transcript "https://youtube.com/watch?v=VIDEO_ID"

# 전체 자막
mcp-yt transcript VIDEO_ID --mode full

# JSON 출력
mcp-yt --json transcript VIDEO_ID
```

#### 기타 명령어

```bash
# 영상 메타데이터
mcp-yt video VIDEO_ID

# 댓글 수집 (인기순 10개)
mcp-yt comments VIDEO_ID
mcp-yt comments VIDEO_ID --max 20 --sentiment positive

# 엔티티 추출
mcp-yt entities VIDEO_ID

# 토픽 세그멘테이션
mcp-yt segments VIDEO_ID

# YouTube 검색
mcp-yt search "transformer 설명" --max 5

# 채널 모니터링
mcp-yt monitor subscribe @3blue1brown
mcp-yt monitor check --channel UCYO_jab_esuFRV4b17AJtAw

# 플레이리스트
mcp-yt playlist PLAYLIST_ID --max 10

# 배치 처리
mcp-yt batch VIDEO_ID1 VIDEO_ID2 VIDEO_ID3

# 저장된 자막 검색
mcp-yt search-transcripts "transformer architecture"
```

> 💡 모든 명령어에 `--json` 플래그를 추가하면 JSON 출력됩니다.
>
> ⚠️ zsh에서는 URL을 따옴표로 감싸세요: `mcp-yt transcript "https://..."` (`?`가 glob으로 인식됨)

### 3. MCP 서버 연결

#### Claude Desktop / Cursor / OpenCode

`claude_desktop_config.json` (또는 `.cursor/mcp.json`, `mcp.json`)에 추가:

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

클라우드 LLM을 쓰려면 `env`에 API 키 추가:
```json
{
  "OPENAI_API_KEY": "sk-...",
  "MYI_LLM_PROVIDER": "openai"
}
```

#### Claude Code

```bash
claude mcp add youtube -- uvx mcp-youtube-intelligence
```

---

## 🤔 왜 이 서버인가?

대부분의 YouTube MCP 서버는 원본 자막을 그대로 LLM에 던집니다.

| 기능 | 기존 MCP 서버 | MCP YouTube Intelligence |
|------|:---:|:---:|
| 자막 추출 | ✅ | ✅ |
| **서버사이드 요약** (토큰 최적화) | ❌ | ✅ |
| **구조화된 리포트** | ❌ | ✅ |
| **채널 모니터링** (RSS) | ❌ | ✅ |
| **댓글 감성 분석** | ❌ | ✅ |
| **토픽 세그멘테이션** | ❌ | ✅ |
| **엔티티 추출** (한/영 200+개) | ❌ | ✅ |
| **자막/YouTube 검색** | ❌ | ✅ |
| **배치 처리** | ❌ | ✅ |
| SQLite/PostgreSQL 캐시 | ❌ | ✅ |

---

## 🔧 MCP Tools (9개)

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
<summary>📖 MCP Tool 상세 파라미터</summary>

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
| `summarize` | bool | ❌ | `false` | 요약 뷰 반환 |

### `monitor_channel`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `channel_ref` | string | ✅ | — | 채널 URL, @핸들, 채널 ID |
| `action` | string | ❌ | `"check"` | `add` · `check` · `list` · `remove` |

### `search_transcripts`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `limit` | int | ❌ | `10` | 최대 결과 수 |

### `extract_entities`
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

### `segment_topics`
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `video_id` | string | ✅ | YouTube 영상 ID |

### `search_youtube`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `query` | string | ✅ | — | 검색 키워드 |
| `max_results` | int | ❌ | `10` | 최대 결과 수 |
| `order` | string | ❌ | `"relevance"` | `relevance` · `date` · `rating` · `viewCount` |

### `get_playlist`
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `playlist_id` | string | ✅ | — | 플레이리스트 ID |
| `max_videos` | int | ❌ | `50` | 최대 영상 수 |

</details>

---

## ⚙️ 설정

모든 설정은 환경변수 (`MYI_` 접두사):

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
| `MYI_LLM_PROVIDER` | `auto` | `auto` · `openai` · `anthropic` · `google` · `ollama` · `vllm` · `lmstudio` |
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

### LLM 프로바이더 설정

```bash
# 클라우드 (API 키만 설정하면 auto 감지)
export OPENAI_API_KEY=sk-...          # OpenAI
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic
export GOOGLE_API_KEY=AIza...         # Google

# 로컬 (무료)
export MYI_LLM_PROVIDER=ollama
export MYI_OLLAMA_MODEL=qwen2.5:7b

# 명시 지정
export MYI_LLM_PROVIDER=anthropic
```

### 추천 Ollama 모델

| 목적 | 모델 | 크기 | 한국어 | 영어 | 품질 |
|------|------|:----:|:------:|:----:|:----:|
| **다국어 (추천)** | `qwen2.5:7b` | 4.4GB | ✅ | ✅ | ⭐⭐⭐⭐ |
| **영어 중심** | `llama3.1:8b` | 4.7GB | ⚠️ | ✅ | ⭐⭐⭐⭐ |
| **한국어 특화** | `gemma2:9b` | 5.4GB | ✅ | ✅ | ⭐⭐⭐⭐ |
| **경량** | `qwen2.5:3b` | 1.9GB | ✅ | ✅ | ⭐⭐⭐ |
| **다국어 특화** | `aya-expanse:8b` | 4.8GB | ✅ | ✅ | ⭐⭐⭐ |

### ⏱️ 실측 벤치마크

> RTX 3070 8GB, 한국어 자막 ~2,900자 (5분 19초 영상)
> Ollama API `total_duration`에서 `load_duration` 제외한 순수 생성 시간

| 모델 | Prompt 처리 | 생성 시간 | 속도 | 출력 | 품질 |
|------|:-----------:|:---------:|:----:|:----:|:----:|
| **Extractive** | - | 즉시 | - | 379자 | ⭐⭐ |
| **qwen2.5:1.5b** | 7.8s | **4.7s** | 30.4 tok/s | 232자 | ⭐⭐ |
| **qwen2.5:7b** | 34.5s | **18.8s** | 7.3 tok/s | 766자 | ⭐⭐⭐⭐ |
| **aya-expanse:8b** | 29.5s | **34.5s** | 6.2 tok/s | 405자 | ⭐⭐⭐ |

> ⚠️ 첫 실행 시 모델 로드에 15~60초 추가. `keep_alive` 설정으로 메모리 유지하면 이후 로드 없음.

---

## 🔍 트러블슈팅

| 문제 | 해결 |
|------|------|
| `zsh: no matches found` | URL을 따옴표로 감싸기: `mcp-yt transcript "https://..."` |
| `yt-dlp not found` | `pip install yt-dlp` 또는 `export MYI_YT_DLP=/path/to/yt-dlp` |
| 자막 없는 영상 | `get_video`로 메타데이터만 가져오기 |
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

---

## 📄 라이선스

Apache 2.0 — [LICENSE](LICENSE)

## 📝 변경 이력

| 날짜 | 버전 | 주요 변경 |
|------|------|----------|
| 2025-02-18 | v0.1.0 | 초기 릴리스 — 9개 MCP 도구, CLI, SQLite |
| 2025-02-18 | v0.1.1 | Multi-LLM (OpenAI/Anthropic/Google), Apache 2.0 |
| 2025-02-18 | v0.1.2 | Local LLM (Ollama/vLLM/LM Studio), yt-dlp 자막 개선, 영어 기본 출력 |
