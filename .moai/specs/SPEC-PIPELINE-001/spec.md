# SPEC-PIPELINE-001: Multi-AI Pipeline CLI Tool

## SPEC 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-PIPELINE-001 |
| **제목** | Multi-AI Pipeline CLI Tool for Automated Business Plan Generation |
| **작성일** | 2026-02-15 |
| **상태** | Planned |
| **버전** | 1.0.0 |
| **우선순위** | High |
| **관련 문서** | product.md, structure.md, tech.md |
| **라이프사이클** | spec-anchored |

---

## 1. 프로젝트 개요

### 1.1 목적

Proxima 게이트웨이(v3.0.0)를 통해 4개의 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)를 활용하여 자동화된 사업 계획서를 생성하는 CLI 파이프라인 도구를 구축한다. 단일 CLI 명령으로 5단계 파이프라인(개념 프레이밍 - 심층 연구 - 전략 수립 - 초안 작성 - 최종 검증)을 순차적/병렬적으로 실행하며, 각 AI의 강점을 교차 활용하여 높은 품질의 결과물을 생산한다.

### 1.2 범위

**포함 범위 (In-Scope)**:
- Python CLI 도구 (Typer 기반)
- 5단계 파이프라인 오케스트레이션 엔진
- Proxima Gateway 비동기 클라이언트 (aiohttp)
- 단계 간 컨텍스트 전달 메커니즘
- 파이프라인 상태 관리 및 재개(Resume) 기능
- Jinja2 기반 프롬프트 템플릿 시스템
- 구조화된 출력 포매팅 (Markdown, 향후 DOCX/PDF)
- 에이전트 헬스체크 및 폴백 라우팅

**제외 범위 (Out-of-Scope)**:
- 웹 대시보드 (향후 확장으로 분리)
- API 키 기반 직접 AI 호출 (Proxima 전용)
- 모바일 클라이언트
- 다중 사용자 동시 접속
- 클라우드 배포 인프라

### 1.3 대상 사용자

| 사용자 유형 | 설명 | 주요 시나리오 |
|------------|------|-------------|
| 스타트업 창업자 | 신사업 계획 수립, 투자 유치 준비 | `agent-compare run --template startup --topic "AI SaaS"` |
| 연구개발 팀 | R&D 제안서, 신기술 추진 계획 | `agent-compare run --template rd --topic "양자 컴퓨팅 응용"` |
| 경영진/컨설턴트 | 사업 전략 검토, 신규 사업 진출 | `agent-compare run --template strategy --topic "동남아 진출"` |
| 비즈니스 플래너 | 체계적 사업 계획서 자동 생성 | `agent-compare run --topic "친환경 물류 플랫폼"` |

---

## 2. 환경 (Environment)

### 2.1 시스템 전제조건

- **운영체제**: Windows 10/11 (MINGW64 호환)
- **Python**: 3.13+ (asyncio, match-case 지원 필수)
- **Proxima**: v3.0.0 이상, localhost:3210에서 실행 중
- **네트워크**: localhost 전용 통신 (외부 네트워크 불필요)
- **인증**: API 키 불필요 (Proxima 브라우저 세션 기반)

### 2.2 Proxima Gateway 환경

- **엔드포인트**: `POST http://localhost:3210/v1/chat/completions` (OpenAI 호환)
- **지원 AI 프로바이더**: ChatGPT, Claude, Gemini, Perplexity
- **MCP 도구**: 60+ 도구 (검색 8, 코드 7, AI 프로바이더 6, 콘텐츠 8, 분석 5, 파일 2, 윈도우 4, 세션 2, 모니터링 2)
- **스마트 라우터**: ChatGPT -> Claude -> Perplexity -> Gemini 폴백, 프로바이더당 2회 시도
- **알려진 제한**: 한국어 쿼리 시 DOM 스크래핑 인코딩 이슈 (AI 프롬프트는 영어 권장)

### 2.3 주요 MCP 도구 매핑

| 파이프라인 단계 | 사용 MCP 도구 | 실행 방식 |
|---------------|-------------|---------|
| Phase 1: 개념 프레이밍 | `brainstorm`, `generate_article` | 순차 |
| Phase 2: 심층 연구 | `deep_search`, `pro_search`, `academic_search`, `fact_check` | **병렬** |
| Phase 3: 전략/로드맵 | `analyze_document`, `find_stats`, `compare` | 순차 |
| Phase 4: 초안 작성 | `summarize_url`, `generate_code` (시각화) | 순차+병렬 |
| Phase 5: 최종 검증 | `fact_check`, `ask_all_ais`, `compare_ais` | 병렬 |

---

## 3. 가정 (Assumptions)

### 3.1 기술적 가정

| ID | 가정 | 신뢰도 | 근거 | 위험(오류 시) | 검증 방법 |
|----|------|--------|------|-------------|---------|
| A-1 | Proxima v3.0.0이 localhost:3210에서 안정적으로 실행된다 | Medium | 기존 테스트 결과 확인됨 | 전체 파이프라인 실행 불가 | `agent-compare check` 헬스체크 |
| A-2 | 4개 AI 프로바이더의 브라우저 세션이 유효하다 | Medium | 쿠키 임포트 파이프라인 검증됨 | 특정 AI 응답 실패 | 폴백 AI 매핑으로 대체 |
| A-3 | aiohttp가 Proxima REST API와 호환된다 | High | OpenAI 호환 API 표준 | 비동기 통신 실패 | 통합 테스트로 검증 |
| A-4 | 단일 파이프라인 실행이 2시간 이내에 완료된다 | Medium | AI 응답 속도에 의존 | 사용자 경험 저하 | 타임아웃 및 단계별 재개 |
| A-5 | AI 응답이 파싱 가능한 구조화된 텍스트로 반환된다 | Medium | 프롬프트 엔지니어링 의존 | 파싱 실패, 가비지 응답 | 응답 검증 + 재시도 로직 |

### 3.2 비즈니스 가정

| ID | 가정 | 신뢰도 | 근거 |
|----|------|--------|------|
| B-1 | 사용자는 CLI 기본 사용에 익숙하다 | High | 타겟 사용자 프로필 |
| B-2 | 사업 계획서 템플릿이 대부분의 사용 사례를 커버한다 | Medium | 3가지 기본 템플릿 제공 |
| B-3 | 영어 프롬프트가 한국어 입력보다 안정적인 결과를 생성한다 | High | Proxima DOM 스크래핑 이슈 문서화됨 |

---

## 4. 요구사항 (Requirements) - EARS 형식

### 4.1 사용자 스토리 (User Stories)

#### US-1: 파이프라인 실행

**WHEN** 사용자가 `agent-compare run --topic "주제"` 명령을 실행하면 **THEN** 시스템은 5단계 파이프라인을 순차적으로 실행하고, 각 단계의 결과를 다음 단계에 컨텍스트로 전달하며, 최종 사업 계획서를 생성하여 출력 디렉토리에 저장해야 한다.

**인수 조건**:
- 5개 단계 모두 순차적으로 실행 완료
- 각 단계 결과가 PhaseResult 객체로 축적
- 최종 출력물이 Markdown 형식으로 저장
- 실행 로그가 구조화된 형식으로 기록

#### US-2: 단계별 제어

**WHEN** 사용자가 `agent-compare run --from-phase 3` 명령을 실행하면 **THEN** 시스템은 이전 단계의 저장된 상태를 로드하고, 지정된 단계부터 파이프라인을 재개해야 한다.

**인수 조건**:
- 이전 상태 파일(JSON)에서 PhaseResult 복원
- 지정 단계부터 정상 실행
- 누락된 상태 파일 시 명확한 오류 메시지 출력

#### US-3: AI 에이전트 헬스체크

**WHEN** 사용자가 `agent-compare check` 명령을 실행하면 **THEN** 시스템은 Proxima 게이트웨이 연결 상태와 4개 AI 프로바이더의 가용성을 확인하고 결과를 표시해야 한다.

**인수 조건**:
- Proxima 게이트웨이 연결 확인 (localhost:3210)
- 각 AI 프로바이더별 상태 표시 (Available / Unavailable / Degraded)
- 세션 만료 감지 및 갱신 안내
- 전체 준비 상태 요약 출력

#### US-4: 설정 관리

**WHEN** 사용자가 `agent-compare config show` 또는 `agent-compare config set <key> <value>` 명령을 실행하면 **THEN** 시스템은 현재 설정을 표시하거나 지정된 설정을 업데이트해야 한다.

**인수 조건**:
- AI-to-Phase 매핑 설정 조회/변경
- 출력 형식, 언어, 템플릿 설정
- 설정 파일 (YAML) 영속 저장
- 잘못된 설정 값에 대한 검증

#### US-5: 출력 관리

시스템은 **항상** 파이프라인 실행 결과를 타임스탬프 기반 디렉토리 구조로 정리하여 저장해야 한다.

**인수 조건**:
- 출력 디렉토리: `output/{session-id}/`
- 단계별 중간 결과 보존: `output/{session-id}/phase{N}/`
- 최종 사업 계획서: `output/{session-id}/final/business_plan.md`
- 메타데이터 파일: `output/{session-id}/metadata.json`

#### US-6: 프롬프트 템플릿 시스템

**가능하면** 시스템은 사용자 정의 프롬프트 템플릿을 지원하여, 각 단계별 AI에 대한 프롬프트를 커스터마이즈할 수 있도록 해야 한다.

**인수 조건**:
- Jinja2 기반 템플릿 파일
- 기본 템플릿 세트 (startup, rd, strategy)
- 사용자 커스텀 템플릿 디렉토리 지원
- 템플릿 변수: `topic`, `phase_context`, `previous_results`

---

### 4.2 기능 요구사항 (Functional Requirements)

#### FR-1: 파이프라인 오케스트레이션 엔진

**WHEN** 파이프라인이 시작되면 **THEN** 오케스트레이터는 상태 머신(IDLE -> PHASE_1 -> PHASE_2 -> ... -> PHASE_5 -> COMPLETED / FAILED)을 통해 단계를 관리하고, 각 단계 완료 후 PhaseResult를 축적하며, 상태를 JSON으로 영속화해야 한다.

상세 요구사항:
- **상태 머신**: `PipelineState` enum으로 상태 전이 관리
  - 유효 전이: IDLE->PHASE_1, PHASE_N->PHASE_N+1, ANY->FAILED, PHASE_5->COMPLETED
  - 무효 전이 시 `InvalidStateTransition` 예외 발생
- **PhaseResult 축적**: 이전 단계의 결과가 다음 단계의 입력 컨텍스트에 포함
- **상태 영속화**: 각 단계 완료 후 `pipeline_state.json`에 저장
- **이벤트 시스템**: PhaseStarted, AgentCalled, AgentResponded, PhaseCompleted, PipelineFailed 이벤트 발행

#### FR-2: Proxima Gateway 비동기 클라이언트

시스템은 **항상** aiohttp 기반 비동기 HTTP 클라이언트를 통해 Proxima Gateway와 통신해야 한다.

상세 요구사항:
- **AsyncProximaClient 클래스**: aiohttp.ClientSession 기반
- **OpenAI 호환 요청 형식**: `POST /v1/chat/completions`
- **모델 매핑**: `claude`, `chatgpt`, `gemini`, `perplexity`
- **MCP 도구 호출**: `function` 파라미터로 MCP 도구 지정
- **타임아웃**: 요청당 120초 기본값, 설정 가능
- **연결 풀링**: aiohttp 커넥터 풀 활용
- **에러 핸들링**: HTTP 에러, 타임아웃, 연결 실패 각각 처리

#### FR-3: 단계 간 컨텍스트 전달

**WHEN** 단계 N이 완료되면 **THEN** 시스템은 해당 단계의 PhaseResult를 단계 N+1의 입력 컨텍스트에 포함하여, 누적된 정보를 기반으로 작업을 수행해야 한다.

상세 요구사항:
- **컨텍스트 체인**: Phase 1 결과 -> Phase 2 입력, Phase 1+2 결과 -> Phase 3 입력, ...
- **컨텍스트 크기 관리**: 누적 컨텍스트가 AI 토큰 한도를 초과하지 않도록 요약 전략 적용
- **요약 전략**: 이전 단계 결과를 핵심 포인트로 압축 (전체 텍스트 대신 요약 포함)
- **PhaseResult 구조**:
  ```
  PhaseResult:
    phase_number: int
    phase_name: str
    status: PhaseStatus
    ai_responses: list[AgentResponse]
    summary: str
    artifacts: dict[str, Any]
    started_at: datetime
    completed_at: datetime
  ```

#### FR-4: CLI 인터페이스

**WHEN** 사용자가 CLI 명령을 입력하면 **THEN** 시스템은 Typer 기반으로 명령을 파싱하고, 적절한 핸들러를 호출하며, 풍부한 터미널 출력(Rich 라이브러리)을 제공해야 한다.

CLI 명령 체계:
```
agent-compare run [OPTIONS]
  --topic TEXT        사업 주제 (필수)
  --template TEXT     템플릿 이름 (기본: default)
  --from-phase INT    재개 시작 단계 (1-5)
  --lang TEXT         출력 언어 (기본: ko)
  --output-dir PATH   출력 디렉토리

agent-compare check
  Proxima 및 AI 프로바이더 헬스체크

agent-compare status [SESSION_ID]
  파이프라인 실행 상태 조회

agent-compare resume SESSION_ID
  중단된 파이프라인 재개

agent-compare config show
agent-compare config set KEY VALUE
  설정 조회/변경
```

#### FR-5: 오류 복구 및 재시도

시스템은 **항상** 요청 수준 재시도와 단계 수준 복구를 지원해야 한다.

**IF** AI 프로바이더 요청이 실패하면 **THEN** 시스템은 동일 프로바이더에 최대 2회 재시도한 후, 폴백 AI로 전환해야 한다.

**IF** 단계 전체가 실패하면 **THEN** 시스템은 파이프라인 상태를 FAILED로 전환하고, 마지막 성공 상태를 저장하여 `resume` 명령으로 재개 가능하게 해야 한다.

상세 요구사항:
- **요청 수준 재시도**: 동일 프로바이더 2회 -> 폴백 AI
- **폴백 AI 매핑**:
  - ChatGPT <-> Claude (상호 대체)
  - Gemini <-> Perplexity (상호 대체)
- **단계 수준 복구**: 상태 저장 -> `resume` 명령 -> 실패 단계부터 재시작
- **지수 백오프**: 재시도 간격 1초, 2초, 4초
- **최대 재시도 횟수**: 프로바이더당 2회, 폴백 포함 총 4회

---

### 4.3 비기능 요구사항 (Non-Functional Requirements)

#### NFR-1: 성능

- 전체 파이프라인 실행 시간: 2시간 이내
- 개별 AI 요청 타임아웃: 120초
- Phase 2, 4, 5의 병렬 요청: asyncio.gather() 활용
- 파이프라인 상태 저장: 단계 완료 후 1초 이내

#### NFR-2: 안정성

- 그레이스풀 디그레이데이션: AI 프로바이더 1개 장애 시에도 파이프라인 계속 실행
- 크래시 복구: 비정상 종료 후 `resume` 명령으로 마지막 성공 단계부터 재개
- 세션 상태 영속화: 각 단계 완료 시 JSON 파일로 저장
- 네트워크 일시 중단: 자동 재연결 시도 (3회)

#### NFR-3: 사용성

- CLI 출력: Rich 라이브러리로 색상, 프로그레스 바, 테이블 출력
- 한국어 지원: CLI 메시지, 도움말, 출력 템플릿 한국어 제공
- 에러 메시지: 사용자 친화적 한국어 에러 메시지 + 복구 가이드
- 실행 진행률: 현재 단계, AI 에이전트, 경과 시간 실시간 표시

#### NFR-4: 확장성

- 플러그인 방식 단계 추가: 새 Phase 클래스 추가만으로 단계 확장
- AI 에이전트 매핑 설정화: YAML 설정으로 단계별 AI 할당 변경
- 템플릿 시스템: 사용자 정의 프롬프트 및 출력 템플릿
- 이벤트 기반 아키텍처: 향후 웹 대시보드 SSE 연동 준비

#### NFR-5: 보안

- API 키 불필요: Proxima 브라우저 세션 기반 인증
- localhost 전용: 외부 네트워크 노출 없음
- 입력 검증: Pydantic 모델로 모든 사용자 입력 및 AI 응답 검증
- 민감 데이터: 사업 계획서 내용은 로컬에만 저장

---

## 5. 기술 접근법 (Technical Approach)

### 5.1 아키텍처 패턴: Pipeline Orchestrator Pattern

```
+------------------+
|    CLI (Typer)   |  <- 사용자 인터페이스
+--------+---------+
         |
+--------v---------+
|   Orchestrator   |  <- 상태 머신 + 이벤트 시스템
|   (State Machine)|
+--------+---------+
         |
+--------v---------+     +------------------+
| Phase 1-5 Modules| --> | Agent Router     |  <- (단계, 작업) -> AI 매핑
+--------+---------+     +--------+---------+
                                  |
                         +--------v---------+
                         | AsyncProximaClient|  <- aiohttp 비동기 클라이언트
                         +--------+---------+
                                  |
                         +--------v---------+
                         | Proxima Gateway  |  <- localhost:3210
                         | (ChatGPT/Claude/ |
                         |  Gemini/Perplexity)|
                         +------------------+
```

### 5.2 모듈 구조

```
src/
├── main.py                          # Typer CLI 진입점
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py              # 상태 머신 + 이벤트 시스템
│   ├── state.py                     # PipelineState enum, PhaseResult dataclass
│   ├── phase1_framing.py            # 1단계: 개념 프레이밍
│   ├── phase2_research.py           # 2단계: 심층 연구 (병렬)
│   ├── phase3_strategy.py           # 3단계: 전략/로드맵
│   ├── phase4_writing.py            # 4단계: 초안 작성
│   └── phase5_review.py             # 5단계: 최종 검증
├── agents/
│   ├── __init__.py
│   ├── base.py                      # AsyncAgent Protocol (추상 인터페이스)
│   ├── claude.py                    # Claude 에이전트 설정
│   ├── chatgpt.py                   # ChatGPT 에이전트 설정
│   ├── gemini.py                    # Gemini 에이전트 설정
│   ├── perplexity.py                # Perplexity 에이전트 설정
│   └── router.py                    # (단계, 작업) -> AI 에이전트 매핑
├── proxima/
│   ├── __init__.py
│   ├── client.py                    # AsyncProximaClient (aiohttp)
│   └── models.py                    # ProximaRequest, ProximaResponse
├── core/
│   ├── __init__.py
│   ├── config.py                    # Pydantic 기반 설정 관리
│   ├── models.py                    # 공유 데이터 모델
│   ├── events.py                    # 이벤트 시스템 (PhaseStarted, AgentCalled 등)
│   ├── exceptions.py                # 커스텀 예외 클래스
│   └── logger.py                    # structlog 기반 구조화 로깅
├── templates/
│   ├── prompts/
│   │   ├── phase1/                  # 단계 1 프롬프트 (Jinja2)
│   │   │   ├── brainstorm.j2
│   │   │   └── validate.j2
│   │   ├── phase2/
│   │   │   ├── deep_search.j2
│   │   │   └── fact_check.j2
│   │   ├── phase3/
│   │   │   ├── swot_analysis.j2
│   │   │   └── narrative.j2
│   │   ├── phase4/
│   │   │   ├── business_plan.j2
│   │   │   └── executive_summary.j2
│   │   └── phase5/
│   │       ├── verification.j2
│   │       └── final_review.j2
│   └── output/
│       ├── business_plan_default.j2
│       ├── business_plan_startup.j2
│       └── business_plan_rd.j2
└── output/
    ├── __init__.py
    ├── formatter.py                 # 출력 포매팅 (Markdown, 향후 DOCX)
    └── exporter.py                  # 파일 내보내기
```

### 5.3 핵심 설계 결정

| # | 결정 사항 | 선택 | 근거 | 대안 |
|---|---------|------|------|------|
| D-1 | HTTP 클라이언트 | aiohttp (비동기) | Phase 2/4/5 병렬 실행 필수, Proxima SDK는 동기 전용 | requests (동기), httpx (비동기 대안) |
| D-2 | 상태 관리 | JSON 파일 영속화 | 외부 DB 의존성 없음, resume 기능 지원 | SQLite, Redis |
| D-3 | AI 에이전트 구현 | 설정 모듈 (서브클래스 아님) | 경량, 프롬프트 템플릿 기반 | ABC 상속 패턴 |
| D-4 | 프롬프트 관리 | Jinja2 외부화 | 코드 수정 없이 프롬프트 변경, 다국어 지원 | Python 문자열, YAML |
| D-5 | 진행 상황 보고 | 이벤트 기반 시스템 | CLI 출력 + 향후 웹 대시보드 SSE 연동 | 직접 print() |
| D-6 | 폴백 전략 | AI 상호 대체 매핑 | 가용성 극대화 | 단일 폴백, 폴백 없음 |

### 5.4 데이터 모델 핵심 설계

```python
# 핵심 데이터 모델 (의사코드)

@dataclass
class PipelineConfig:
    topic: str
    template: str = "default"
    language: str = "ko"
    output_dir: Path = Path("output")
    phases: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])

class PipelineState(Enum):
    IDLE = "idle"
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    PHASE_5 = "phase_5"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentResponse:
    agent_name: str           # "claude", "chatgpt", "gemini", "perplexity"
    task_name: str            # "brainstorm", "deep_search", ...
    content: str              # AI 응답 본문
    tokens_used: int
    response_time: float      # 초
    success: bool
    error: str | None = None

@dataclass
class PhaseResult:
    phase_number: int
    phase_name: str
    status: Literal["completed", "failed", "skipped"]
    ai_responses: list[AgentResponse]
    summary: str              # 다음 단계 전달용 요약
    artifacts: dict[str, Any] # 단계별 산출물
    started_at: datetime
    completed_at: datetime

@dataclass
class PipelineSession:
    session_id: str           # UUID
    config: PipelineConfig
    state: PipelineState
    results: list[PhaseResult]
    created_at: datetime
    updated_at: datetime
```

---

## 6. 구현 계획

### 6.1 9-Layer 구현 순서 (의존성 기반)

| Layer | 이름 | 내용 | 산출물 | 의존성 |
|-------|------|------|--------|--------|
| **L0** | Foundation | pyproject.toml, 프로젝트 구조, 설정, 예외, 이벤트 | 프로젝트 뼈대 | 없음 |
| **L1** | Proxima Client | aiohttp 래퍼, 요청/응답 모델, 에러 핸들링 | `proxima/` | L0 |
| **L2** | Data Models | PhaseResult, PipelineSession, AgentResponse | `core/models.py`, `pipeline/state.py` | L0 |
| **L3** | Agent Layer | 에이전트 프로토콜, 4개 AI 설정, 라우터 | `agents/` | L1, L2 |
| **L4** | Templates | Jinja2 프롬프트 템플릿, 출력 템플릿 | `templates/` | L2 (병렬 가능) |
| **L5** | Pipeline Phases | 5개 단계 모듈 구현 | `pipeline/phase1-5.py` | L3, L4 |
| **L6** | Orchestrator | 상태 머신, 이벤트 발행, 컨텍스트 전달 | `pipeline/orchestrator.py` | L5 |
| **L7** | Output | Markdown 포매터, 파일 내보내기 | `output/` | L2, L6 |
| **L8** | CLI | Typer 명령, Rich 출력, 진행률 표시 | `main.py` | L6, L7 |
| **L9** | Tests | 단위/통합 테스트, 목 응답, 픽스처 | `tests/` | L0-L8 전체 |

### 6.2 마일스톤 (우선순위 기반)

**Primary Goal (핵심 기능)**:
- L0-L2: Foundation + Proxima Client + Data Models
- L3: Agent Layer (4개 AI 에이전트 + 라우터)
- L5: 5개 Pipeline Phase 모듈
- L6: Orchestrator (상태 머신 + 이벤트)
- L8: CLI 기본 명령 (`run`, `check`)

**Secondary Goal (완성도)**:
- L4: Jinja2 프롬프트 템플릿 전체
- L7: Output 포매팅 (Markdown)
- L8: CLI 확장 명령 (`resume`, `status`, `config`)
- FR-5: 오류 복구 + 폴백 매핑

**Tertiary Goal (품질)**:
- L9: 테스트 스위트 (85%+ 커버리지)
- NFR-3: Rich 기반 CLI UX 개선
- NFR-4: 플러그인 방식 확장 인터페이스
- 문서화: 사용자 가이드, API 문서

**Optional Goal (향후 확장)**:
- 웹 대시보드 SSE 연동 준비
- DOCX/PDF 출력 지원
- 추가 AI 프로바이더 지원
- 국제화 (i18n)

---

## 7. 엣지 케이스 및 리스크

### 7.1 엣지 케이스 (9개)

| ID | 엣지 케이스 | 영향 | 대응 전략 |
|----|-----------|------|---------|
| EC-1 | Proxima가 실행되지 않음 | 파이프라인 시작 불가 | `check` 명령으로 사전 감지, 명확한 에러 메시지 + Proxima 시작 가이드 |
| EC-2 | AI 프로바이더 세션 만료 | 특정 AI 응답 실패 | 폴백 AI 매핑으로 대체, 세션 갱신 안내 메시지 |
| EC-3 | AI 불완전/가비지 응답 | 다음 단계 입력 품질 저하 | 응답 유효성 검사 (길이, 구조, 키워드), 재시도 + 폴백 |
| EC-4 | 네트워크 연결 중단 | 진행 중인 요청 실패 | 자동 재연결 3회 시도, 상태 저장 후 resume 안내 |
| EC-5 | 컨텍스트 윈도우 오버플로 | AI 토큰 한도 초과 | 이전 단계 결과 요약 전략, 컨텍스트 크기 모니터링 |
| EC-6 | AI 레이트 리미팅 | 연속 요청 거부 | 지수 백오프 (1/2/4초), 프로바이더 간 로드 분산 |
| EC-7 | 상충하는 연구 결과 (Phase 2) | 비일관적인 정보 | Phase 5 교차검증에서 해결, 불일치 항목 명시적 표시 |
| EC-8 | 매우 긴 AI 응답 | 메모리/저장 부담 | 응답 최대 길이 제한 (50,000자), 초과 시 요약 요청 |
| EC-9 | 빈/최소 사용자 입력 | 파이프라인 품질 저하 | 최소 입력 검증 (10자 이상), 부족 시 추가 정보 요청 안내 |

### 7.2 리스크 (5개)

| ID | 리스크 | 심각도 | 발생 가능성 | 완화 전략 |
|----|-------|--------|-----------|---------|
| R-1 | Proxima 안정성 (2시간+ 세션 유지) | HIGH | Medium | 단계별 상태 저장 + resume 기능, 헬스체크 주기 실행 |
| R-2 | AI 응답 품질 편차 | MEDIUM | High | 다중 AI 교차검증, 프롬프트 엔지니어링 최적화, 응답 품질 점수 산정 |
| R-3 | 컨텍스트 누적으로 토큰 한도 초과 | MEDIUM | Medium | 단계별 요약 전략, 컨텍스트 윈도우 모니터링, 필수 정보만 전달 |
| R-4 | 플랫폼 종속성 (Proxima) | LOW | Low | 추상화 계층 (AsyncAgent Protocol), 향후 직접 API 지원 가능하도록 설계 |
| R-5 | 프롬프트 엔지니어링 노력 | MEDIUM | High | Jinja2 외부화로 코드 수정 없이 반복 개선, A/B 테스트 프레임워크 고려 |

---

## 8. 제약사항 및 의존성

### 8.1 플랫폼 제약

| 제약 | 상세 |
|------|------|
| 운영체제 | Windows 10/11 (주 대상), MINGW64 호환 |
| 네트워크 | localhost 전용 (Proxima 통신) |
| 인증 | API 키 불필요 (Proxima 브라우저 세션) |
| 동시 사용자 | 단일 사용자 (파이프라인 인스턴스 1개) |

### 8.2 기술 제약

| 제약 | 상세 |
|------|------|
| Python | 3.13+ 필수 (match-case, asyncio 개선 활용) |
| Proxima | v3.0.0+ 필수, localhost:3210 실행 중 |
| AI 프로바이더 | 4개 고정 (ChatGPT, Claude, Gemini, Perplexity) |
| 한국어 프롬프트 | DOM 스크래핑 인코딩 이슈로 AI 프롬프트는 영어 권장 |

### 8.3 외부 의존성

| 의존성 | 버전 | 역할 | 대체 가능 여부 |
|--------|------|------|-------------|
| aiohttp | 3.9+ | 비동기 HTTP 클라이언트 | httpx (대안) |
| typer | 0.12+ | CLI 프레임워크 | click (대안) |
| pydantic | 2.9+ | 데이터 검증/설정 | dataclasses (제한적) |
| jinja2 | 3.1+ | 프롬프트 템플릿 | string.Template (제한적) |
| rich | 13.0+ | 터미널 UI | colorama (제한적) |
| structlog | 24.0+ | 구조화 로깅 | loguru (대안) |
| pytest | 8.0+ | 테스트 프레임워크 | unittest (기본) |
| pytest-asyncio | 0.23+ | 비동기 테스트 지원 | - |

---

## 9. 테스트 전략

### 9.1 개발 방법론: Hybrid (TDD + DDD)

프로젝트 설정에 따라 Hybrid 모드를 적용한다:
- **새 코드 (전체)**: TDD (RED-GREEN-REFACTOR) - 모든 코드가 신규이므로 테스트 우선 개발
- **기존 코드 수정 시**: DDD (ANALYZE-PRESERVE-IMPROVE) - 향후 리팩토링 시 적용

### 9.2 커버리지 목표

| 범위 | 목표 | 비고 |
|------|------|------|
| 전체 코드 커버리지 | 85%+ | TRUST 5 기준 |
| 신규 코드 커버리지 | 85%+ | Hybrid 모드 기준 |
| 핵심 모듈 (orchestrator, client) | 90%+ | 핵심 비즈니스 로직 |
| 유틸리티/설정 | 75%+ | 설정 검증 중심 |

### 9.3 테스트 우선순위

**Priority High (먼저 작성)**:
1. AsyncProximaClient - 핵심 외부 통신
2. PipelineOrchestrator - 상태 머신 전이
3. AgentRouter - AI 매핑 및 폴백
4. PhaseResult 컨텍스트 전달

**Priority Medium**:
5. 각 Phase 모듈 (Phase 1-5)
6. Jinja2 템플릿 렌더링
7. CLI 명령 파싱
8. 출력 포매팅

**Priority Low**:
9. 설정 관리
10. 로깅 검증
11. 파일 내보내기

### 9.4 테스트 유형

| 유형 | 범위 | 도구 |
|------|------|------|
| 단위 테스트 | 개별 함수/클래스 | pytest, pytest-asyncio |
| 통합 테스트 | 모듈 간 상호작용 | pytest + Mock Proxima |
| E2E 테스트 | 전체 파이프라인 | pytest + Proxima 목 서버 |
| 스냅샷 테스트 | 출력 포맷 일관성 | pytest-snapshot |

### 9.5 목(Mock) 전략

- **Proxima Gateway**: aiohttp 목 서버로 AI 응답 시뮬레이션
- **AI 응답**: 사전 정의된 JSON 픽스처 (성공/실패/부분 응답)
- **파일 시스템**: tmp_path 픽스처로 격리된 테스트 디렉토리

---

## 10. 향후 확장

### 10.1 웹 대시보드 (향후 SPEC으로 분리)

- **프레임워크**: Next.js 16 + App Router
- **실시간 통신**: SSE (Server-Sent Events) for pipeline progress
- **상태 공유**: 파일시스템 기반 상태 공유 (MVP), Redis (확장)
- **주요 기능**: 파이프라인 모니터링, 문서 뷰어, 에이전트 상태

### 10.2 추가 AI 프로바이더

- AsyncAgent Protocol을 통한 새 프로바이더 추가 용이
- 설정 파일 수정만으로 에이전트 매핑 변경
- Proxima 업데이트 시 자동 지원

### 10.3 국제화 (i18n)

- 프롬프트 템플릿 다국어 지원 (en, ko, ja, zh)
- CLI 메시지 번역 시스템
- 출력 사업 계획서 다국어 생성

### 10.4 고급 기능

- A/B 테스트: 프롬프트 변형 자동 비교
- 품질 점수: AI 응답 자동 품질 평가
- 파이프라인 병렬화: 독립 단계 동시 실행
- 캐싱: 동일 주제 재실행 시 이전 결과 활용

---

## 추적 태그 (Traceability)

| TAG | 연결 |
|-----|------|
| SPEC-PIPELINE-001 | product.md, structure.md, tech.md |
| FR-1 | orchestrator.py, state.py |
| FR-2 | proxima/client.py, proxima/models.py |
| FR-3 | pipeline/state.py, orchestrator.py |
| FR-4 | main.py |
| FR-5 | agents/router.py, orchestrator.py |
| NFR-1 | pipeline/*.py (asyncio.gather) |
| NFR-2 | orchestrator.py, state.py |
| NFR-3 | main.py (Rich), templates/ |
| NFR-4 | agents/base.py (Protocol), core/events.py |
| NFR-5 | proxima/client.py, core/config.py |

---

**작성자**: manager-spec agent
**최종 업데이트**: 2026-02-15
**다음 단계**: `/moai:2-run SPEC-PIPELINE-001` 으로 구현 시작
