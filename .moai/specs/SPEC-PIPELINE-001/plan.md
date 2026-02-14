# SPEC-PIPELINE-001: 구현 계획

## 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-PIPELINE-001 |
| **문서 유형** | 구현 계획 (Implementation Plan) |
| **작성일** | 2026-02-15 |
| **개발 방법론** | Hybrid (TDD for new + DDD for legacy) |

---

## 1. 구현 전략 개요

### 1.1 Async-First 설계 원칙

전체 파이프라인은 asyncio 기반으로 설계한다. Phase 2(심층 연구), Phase 4(초안 작성 보조), Phase 5(교차 검증)에서 병렬 AI 호출이 필수적이며, aiohttp를 통한 비동기 HTTP 통신이 핵심이다.

Proxima Python SDK는 동기(sync) 전용이므로 사용하지 않고, aiohttp 기반 AsyncProximaClient를 직접 구현한다. OpenAI 호환 API 형식(`POST /v1/chat/completions`)을 따르므로 표준화된 요청/응답 모델을 활용한다.

### 1.2 State Machine 기반 오케스트레이션

파이프라인 상태를 enum으로 관리하며, 각 단계 완료 후 JSON 파일로 상태를 영속화한다. 이를 통해:
- 비정상 종료 후 `resume` 명령으로 재개 가능
- 특정 단계부터 `--from-phase` 옵션으로 재실행 가능
- 각 단계 결과가 PhaseResult 체인으로 축적

### 1.3 Agent Config (Not Subclass) 접근

AI 에이전트를 서브클래스로 구현하지 않고, 설정 모듈로 경량화한다:
- 각 에이전트는 이름, 모델 ID, 폴백 에이전트, 프롬프트 템플릿 경로를 설정값으로 가짐
- AsyncAgent Protocol로 인터페이스 통일
- 새 에이전트 추가 시 설정 파일 수정만으로 가능

---

## 2. Layer별 구현 상세

### Layer 0: Foundation (프로젝트 기반)

**산출물**:
- `pyproject.toml`: 의존성, 빌드 설정, 도구 설정 (ruff, pytest, mypy)
- `src/__init__.py`: 패키지 초기화
- `src/core/config.py`: Pydantic 기반 설정 관리 (PipelineSettings)
- `src/core/exceptions.py`: 커스텀 예외 클래스 계층
- `src/core/events.py`: 이벤트 시스템 (Observer 패턴)
- `src/core/logger.py`: structlog 기반 구조화 로깅

**핵심 구현 포인트**:
- PipelineSettings: Pydantic BaseSettings로 환경 변수 + YAML 설정 통합
- 예외 계층: PipelineError -> ProximaError, AgentError, PhaseError, ConfigError
- 이벤트 타입: PhaseStarted, AgentCalled, AgentResponded, PhaseCompleted, PipelineFailed
- 로깅: JSON 포맷, 단계/에이전트별 컨텍스트 자동 바인딩

### Layer 1: Proxima Client (비동기 HTTP 래퍼)

**산출물**:
- `src/proxima/client.py`: AsyncProximaClient 클래스
- `src/proxima/models.py`: ProximaRequest, ProximaResponse, ChatMessage 모델

**핵심 구현 포인트**:
- aiohttp.ClientSession 기반, 컨텍스트 매니저 패턴 (`async with`)
- 요청 형식: OpenAI 호환 (`model`, `messages`, `functions`)
- 타임아웃: 기본 120초, 설정 가능
- 재시도: tenacity 또는 자체 구현, 지수 백오프
- 에러 처리: HTTP 4xx/5xx, 타임아웃, 연결 실패 분리 처리
- 헬스체크 메서드: `async def health_check() -> ProximaStatus`

### Layer 2: Data Models (공유 데이터 구조)

**산출물**:
- `src/core/models.py`: 공유 모델 (AgentResponse, SessionMetadata)
- `src/pipeline/state.py`: PipelineState enum, PhaseResult, PipelineSession

**핵심 구현 포인트**:
- PipelineState enum: IDLE, PHASE_1-5, COMPLETED, FAILED
- PhaseResult dataclass: phase_number, status, ai_responses, summary, artifacts, timestamps
- PipelineSession: session_id(UUID), config, state, results, timestamps
- JSON 직렬화/역직렬화: Pydantic model_validate_json / model_dump_json
- 상태 파일: `output/{session_id}/pipeline_state.json`

### Layer 3: Agent Layer (AI 에이전트 + 라우터)

**산출물**:
- `src/agents/base.py`: AsyncAgent Protocol
- `src/agents/claude.py`, `chatgpt.py`, `gemini.py`, `perplexity.py`: 에이전트 설정
- `src/agents/router.py`: AgentRouter (단계/작업 -> AI 매핑)

**핵심 구현 포인트**:
- AsyncAgent Protocol:
  ```
  class AsyncAgent(Protocol):
      name: str
      model_id: str
      async def execute(self, prompt: str, context: dict) -> AgentResponse
  ```
- AgentRouter: YAML 설정 기반 (단계, 작업) -> 에이전트 매핑
- 폴백 매핑: ChatGPT <-> Claude, Gemini <-> Perplexity
- 에이전트 팩토리: 이름으로 에이전트 인스턴스 생성

### Layer 4: Templates (Jinja2 프롬프트) - Layer 3과 병렬 가능

**산출물**:
- `src/templates/prompts/phase1-5/`: 단계별 프롬프트 템플릿
- `src/templates/output/`: 출력 템플릿 (startup, rd, strategy)
- 템플릿 로더 유틸리티

**핵심 구현 포인트**:
- Jinja2 Environment: FileSystemLoader + 자동 이스케이프
- 템플릿 변수: `topic`, `language`, `phase_context`, `previous_results`
- 기본 템플릿 세트: 3개 (startup, rd, strategy)
- 사용자 커스텀 디렉토리 지원: `~/.agent-compare/templates/`

### Layer 5: Pipeline Phases (5단계 모듈)

**산출물**:
- `src/pipeline/phase1_framing.py`: 개념 프레이밍
- `src/pipeline/phase2_research.py`: 심층 연구 (병렬)
- `src/pipeline/phase3_strategy.py`: 전략/로드맵
- `src/pipeline/phase4_writing.py`: 초안 작성
- `src/pipeline/phase5_review.py`: 최종 검증

**단계별 상세**:

| Phase | AI 에이전트 | 작업 | 실행 방식 |
|-------|-----------|------|---------|
| 1 | ChatGPT(주), Claude(보조) | 브레인스토밍 -> 논리 검증 | 순차 |
| 2 | Gemini(주), Perplexity(보조) | 소스 수집 + 인용 검증 | **병렬** (asyncio.gather) |
| 3 | ChatGPT(주), Claude(보조) | SWOT/PESTEL -> 통합 검증 | 순차 |
| 4 | Claude(주), ChatGPT/Gemini(보조) | 본문 작성 + 요약/시각화 | 순차+병렬 |
| 5 | Perplexity(주), Claude/Gemini(보조) | 사실 검증 + 최종 정렬 | **병렬** (asyncio.gather) |

### Layer 6: Orchestrator (상태 머신)

**산출물**:
- `src/pipeline/orchestrator.py`: PipelineOrchestrator 클래스

**핵심 구현 포인트**:
- 상태 전이 매트릭스 검증
- PhaseResult 축적 및 컨텍스트 체인 관리
- 각 단계 완료 후 상태 JSON 영속화
- 이벤트 발행 (옵저버 패턴)
- 에러 처리 및 FAILED 상태 전환
- resume 로직: 저장된 상태에서 복원

### Layer 7: Output (포매팅 + 내보내기)

**산출물**:
- `src/output/formatter.py`: Markdown 포매터
- `src/output/exporter.py`: 파일 내보내기

**핵심 구현 포인트**:
- PhaseResult 컬렉션 -> 최종 사업 계획서 Markdown 조합
- 출력 디렉토리 구조:
  ```
  output/{session_id}/
  ├── phase1/results.json
  ├── phase2/results.json
  ├── phase3/results.json
  ├── phase4/results.json
  ├── phase5/results.json
  ├── final/business_plan.md
  ├── pipeline_state.json
  └── metadata.json
  ```
- Jinja2 출력 템플릿으로 최종 문서 렌더링

### Layer 8: CLI (Typer 진입점)

**산출물**:
- `src/main.py`: Typer 앱 + Rich 출력

**핵심 구현 포인트**:
- 명령 체계: `run`, `check`, `status`, `resume`, `config`
- Rich 통합: 프로그레스 바, 테이블, 색상 출력
- 비동기 실행: `asyncio.run()` 래퍼
- 글로벌 에러 핸들링: 사용자 친화적 에러 메시지

### Layer 9: Tests (테스트 스위트)

**산출물**:
- `tests/conftest.py`: 공유 픽스처
- `tests/unit/`: 단위 테스트
- `tests/integration/`: 통합 테스트
- `tests/fixtures/`: 목 응답 데이터

**핵심 구현 포인트**:
- Proxima 목 서버: aiohttp test_utils로 로컬 목 서버
- AI 응답 픽스처: 성공/실패/부분 응답 JSON 파일
- 상태 머신 테스트: 모든 유효/무효 전이 검증
- async 테스트: pytest-asyncio + asyncio_mode="auto"

---

## 3. 아키텍처 설계 방향

### 3.1 디렉토리 구조 (최종)

```
src/
├── main.py                          # [L8] CLI 진입점
├── __init__.py
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py              # [L6] 상태 머신 + 이벤트
│   ├── state.py                     # [L2] PipelineState, PhaseResult
│   ├── phase1_framing.py            # [L5]
│   ├── phase2_research.py           # [L5]
│   ├── phase3_strategy.py           # [L5]
│   ├── phase4_writing.py            # [L5]
│   └── phase5_review.py             # [L5]
├── agents/
│   ├── __init__.py
│   ├── base.py                      # [L3] AsyncAgent Protocol
│   ├── claude.py                    # [L3]
│   ├── chatgpt.py                   # [L3]
│   ├── gemini.py                    # [L3]
│   ├── perplexity.py                # [L3]
│   └── router.py                    # [L3] AgentRouter
├── proxima/
│   ├── __init__.py
│   ├── client.py                    # [L1] AsyncProximaClient
│   └── models.py                    # [L1] Request/Response
├── core/
│   ├── __init__.py
│   ├── config.py                    # [L0] PipelineSettings
│   ├── models.py                    # [L2] 공유 모델
│   ├── events.py                    # [L0] 이벤트 시스템
│   ├── exceptions.py                # [L0] 예외 계층
│   └── logger.py                    # [L0] structlog
├── templates/
│   ├── prompts/phase1-5/            # [L4] Jinja2 프롬프트
│   └── output/                      # [L4] 출력 템플릿
└── output/
    ├── __init__.py
    ├── formatter.py                 # [L7]
    └── exporter.py                  # [L7]
```

### 3.2 모듈 간 의존성 그래프

```
L8 (CLI) ──────> L6 (Orchestrator) ──> L5 (Phases) ──> L3 (Agents) ──> L1 (Proxima Client)
     │                  │                    │              │                   │
     └──> L7 (Output)   └──> L2 (Models)     └──> L4 (Templates)              └──> L0 (Foundation)
              │                │
              └────────────────┘
```

### 3.3 이벤트 흐름

```
CLI -> Orchestrator -> Phase Module -> Agent Router -> AsyncProximaClient -> Proxima Gateway
                                                                                 |
CLI <- EventHandler <- Orchestrator <- Phase Module <- Agent Router <- Response <-+
```

---

## 4. 기술적 고려사항

### 4.1 컨텍스트 윈도우 관리 전략

| 단계 | 입력 컨텍스트 | 전략 |
|------|-------------|------|
| Phase 1 | 사용자 입력 (topic) | 전체 전달 |
| Phase 2 | Phase 1 요약 (500자 이내) | 핵심 포인트 요약 |
| Phase 3 | Phase 1 요약 + Phase 2 핵심 데이터 | 선별적 전달 |
| Phase 4 | Phase 1-3 구조화된 요약 | 섹션별 키포인트 |
| Phase 5 | Phase 4 전문 + 검증 대상 목록 | 전문 + 체크리스트 |

### 4.2 프롬프트 엔지니어링 가이드라인

- AI 프롬프트는 **영어**로 작성 (한국어 인코딩 이슈 회피)
- 응답 형식을 명시적으로 지정 (JSON, Markdown 섹션 구분)
- 역할 지정: "You are a [role]. Your task is to [specific task]."
- 출력 구조 지정: "Respond in the following format: ..."
- 제약 조건 명시: "Do not include...", "Focus only on..."

### 4.3 병렬 실행 패턴

```python
# Phase 2 병렬 실행 의사코드
async def execute_phase2(context: dict) -> PhaseResult:
    gemini_task = asyncio.create_task(
        agent_router.execute("gemini", "deep_search", context)
    )
    perplexity_task = asyncio.create_task(
        agent_router.execute("perplexity", "fact_check", context)
    )
    results = await asyncio.gather(gemini_task, perplexity_task, return_exceptions=True)
    # 결과 병합 및 불일치 감지
    return merge_research_results(results)
```

---

## 5. 리스크 대응 계획

| 리스크 | 대응 전략 | 모니터링 방법 |
|--------|---------|-------------|
| Proxima 세션 만료 (R-1) | 단계별 상태 저장, resume 기능, 주기적 헬스체크 | 이벤트 시스템에서 AgentFailed 감지 |
| AI 응답 품질 편차 (R-2) | 응답 유효성 검사, 재시도, 폴백 AI | 응답 길이/구조 자동 검증 |
| 컨텍스트 오버플로 (R-3) | 단계별 요약, 크기 모니터링, 동적 압축 | 컨텍스트 토큰 수 로깅 |
| 플랫폼 종속 (R-4) | AsyncAgent Protocol 추상화 | 인터페이스 분리 원칙 준수 |
| 프롬프트 품질 (R-5) | Jinja2 외부화, 버전 관리, 반복 개선 | 응답 품질 점수 추적 |

---

## 추적 태그

| TAG | 연결 |
|-----|------|
| SPEC-PIPELINE-001 | spec.md, acceptance.md |
| L0-L9 | 각 Layer 구현 파일 |
| FR-1 ~ FR-5 | spec.md 기능 요구사항 |
| NFR-1 ~ NFR-5 | spec.md 비기능 요구사항 |

---

**작성자**: manager-spec agent
**최종 업데이트**: 2026-02-15
