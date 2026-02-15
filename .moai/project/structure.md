# AigenFlow 디렉토리 구조

## 프로젝트 전체 구조

```
aigenflow/
├── .moai/                          # MoAI-ADK 설정 및 메타데이터
│   ├── specs/                      # SPEC 문서 저장소
│   │   ├── SPEC-PACKAGING-001/     # 패키징 SPEC
│   │   │   └── spec.md
│   │   └── SPEC-PIPELINE-001/      # 파이프라인 SPEC
│   │       ├── spec.md
│   │       └── acceptance.md
│   ├── project/                    # 프로젝트 문서
│   │   ├── product.md              # 프로젝트 개요
│   │   ├── structure.md            # 디렉토리 구조 (본 파일)
│   │   └── tech.md                 # 기술 스택
│   └── config/                     # MoAI 설정
│       └── sections/
│           ├── quality.yaml        # 품질 게이트 설정
│           ├── language.yaml       # 다국어 설정
│           └── user.yaml           # 사용자 설정
│
├── src/                            # Python 코어 파이프라인
│   └── aigenflow/                  # 메인 패키지 (pip install aigenflow)
│       ├── __init__.py             # 패키지 버전
│       ├── __main__.py             # python -m aigenflow 지원
│       ├── main.py                 # CLI 진입점
│       ├── py.typed                # PEP 561 타입 마커
│       ├── pipeline/               # 5단계 파이프라인 구현
│       │   ├── __init__.py
│       │   ├── orchestrator.py     # 파이프라인 조정자
│       │   ├── state.py            # 상태 관리
│       │   ├── phase1_framing.py   # 1단계: 개념 프레이밍
│       │   ├── phase2_research.py  # 2단계: 심층 연구
│       │   ├── phase3_strategy.py  # 3단계: 전략/로드맵
│       │   ├── phase4_writing.py   # 4단계: 초안 작성
│       │   └── phase5_review.py    # 5단계: 검증/검토
│       ├── agents/                 # AI 에이전트 조정
│       │   ├── __init__.py
│       │   ├── base.py             # 기본 에이전트 클래스
│       │   ├── claude_agent.py     # Claude 에이전트
│       │   ├── chatgpt_agent.py    # ChatGPT 에이전트
│       │   ├── gemini_agent.py     # Gemini 에이전트
│       │   ├── perplexity_agent.py # Perplexity 에이전트
│       │   └── router.py           # 에이전트 라우터
│       ├── gateway/                # Playwright AI 게이트웨이
│       │   ├── __init__.py
│       │   ├── base.py             # BaseProvider 추상 클래스
│       │   ├── chatgpt_provider.py # ChatGPT Provider
│       │   ├── claude_provider.py  # Claude Provider
│       │   ├── gemini_provider.py  # Gemini Provider
│       │   ├── perplexity_provider.py # Perplexity Provider
│       │   ├── session.py          # 세션 관리자
│       │   └── models.py           # 게이트웨이 데이터 모델
│       ├── core/                   # 핵심 기능
│       │   ├── __init__.py
│       │   ├── config.py           # 설정 관리 (AigenFlowSettings)
│       │   ├── logger.py           # structlog 로깅
│       │   ├── exceptions.py       # 커스텀 예외
│       │   ├── events.py           # 이벤트 시스템
│       │   └── models.py           # 데이터 모델
│       ├── templates/              # Jinja2 템플릿
│       │   ├── __init__.py
│       │   ├── manager.py          # TemplateManager
│       │   └── prompts/            # 프롬프트 템플릿
│       │       ├── phase1/         # 단계 1 프롬프트
│       │       ├── phase2/         # 단계 2 프롬프트
│       │       ├── phase3/         # 단계 3 프롬프트
│       │       ├── phase4/         # 단계 4 프롬프트
│       │       └── phase5/         # 단계 5 프롬프트
│       └── output/                 # 생성 결과 저장
│           ├── __init__.py
│           └── formatter.py        # Markdown 포맷팅
│
├── tests/                          # 테스트 스위트
│   ├── __init__.py
│   ├── conftest.py                 # pytest 설정
│   ├── unit/                       # 단위 테스트
│   │   ├── test_agents.py
│   │   ├── test_gateway.py
│   │   └── test_pipeline.py
│   ├── integration/                # 통합 테스트
│   │   └── test_pipeline_flow.py
│   └── fixtures/                   # 테스트 픽스처
│       └── mock_responses.py
│
├── docs/                           # 프로젝트 문서
│   ├── AigenFlow-종합평가보고서.md
│   └── ...
│
├── output/                         # 파이프라인 출력 (런타임)
│   └── {session-id}/
│       ├── phase1/
│       ├── phase2/
│       ├── phase3/
│       ├── phase4/
│       ├── phase5/
│       ├── final/
│       │   └── business_plan.md
│       └── metadata.json
│
├── aigenflow/                      # Git submodule (Electron 앱)
│
├── .claude/                        # Claude Code 설정
│   ├── agents/                     # 커스텀 에이전트
│   ├── skills/                     # 커스텀 스킬
│   └── rules/                      # 규칙 정의
│
├── .gitignore
├── .env.example                    # 환경 변수 템플릿
├── README.md                       # 프로젝트 README
├── CHANGELOG.md                    # 변경 로그
├── LICENSE
├── CLAUDE.md                       # MoAI 실행 지침
└── pyproject.toml                  # Python 프로젝트 설정

```

## 핵심 모듈 설명

### src/aigenflow/pipeline/ - 5단계 파이프라인 구현

파이프라인 오케스트레이터가 5개의 단계를 순차적으로 관리합니다. 각 단계는 특정 AI 에이전트들의 협업으로 진행되며, 입력 데이터를 처리하여 다음 단계로 전달합니다.

**phase1_framing.py**: 개념 프레이밍 단계. ChatGPT로 아이디어 브레인스토밍, Claude로 논리 검증을 수행합니다.

**phase2_research.py**: 심층 연구 단계. Gemini와 Perplexity가 병렬로 시장 조사를 수행합니다.

**phase3_strategy.py**: 전략 수립 단계. ChatGPT로 SWOT 분석, Claude로 통합 검증을 수행합니다.

**phase4_writing.py**: 초안 작성 단계. Claude가 주로 작성하고 ChatGPT와 Gemini가 보조합니다.

**phase5_review.py**: 최종 검토 단계. Perplexity가 사실 검증, Claude가 최종 정렬을 수행합니다.

### src/aigenflow/agents/ - AI 에이전트 조정

각 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)는 base.py의 기본 클래스를 상속하여 구현됩니다. 에이전트 라우터는 각 단계에 적합한 에이전트를 선택하고 조정합니다.

### src/aigenflow/gateway/ - Playwright AI 게이트웨이

BaseProvider 추상 클래스를 기반으로 4개의 Provider가 구현됩니다. SessionManager가 Playwright 영구 프로필을 통해 AI 서비스 웹 인터페이스에 직접 접근합니다.

### src/aigenflow/core/ - 핵심 기능

설정 관리(AigenFlowSettings), 로깅(structlog), 커스텀 예외, 이벤트 시스템, 데이터 모델을 포함합니다. 이 모듈들은 전체 파이프라인에서 공통으로 사용됩니다.

### src/aigenflow/templates/ - Jinja2 템플릿

각 단계별 프롬프트 템플릿을 Jinja2로 관리합니다. TemplateManager가 템플릿 경로를 해석하고 로드합니다.

### tests/ - 테스트 스위트

단위 테스트는 개별 함수 및 클래스를 검증합니다. 통합 테스트는 전체 파이프라인의 동작을 검증합니다.

## 주요 파일 위치

| 목적 | 파일 경로 |
|------|---------|
| CLI 진입점 | src/aigenflow/main.py |
| 파이프라인 조정 | src/aigenflow/pipeline/orchestrator.py |
| AI 게이트웨이 | src/aigenflow/gateway/ |
| 환경 설정 | src/aigenflow/core/config.py |
| 테스트 실행 | tests/conftest.py |
| 패키지 설정 | pyproject.toml |

## 모듈 간 의존성

**pipeline → agents**: 파이프라인이 에이전트를 호출하여 작업 수행
**agents → gateway**: 에이전트가 Playwright 게이트웨이를 통해 AI 호출
**pipeline → core**: 모든 모듈이 core의 설정, 로깅, 모델 사용
**pipeline → templates**: 각 단계가 프롬프트 템플릿 사용
**output → templates**: 생성 결과를 템플릿에 맞춰 포맷

## 설정 및 실행 파일

- **pyproject.toml**: Python 프로젝트 메타데이터, 의존성, 빌드 설정 (hatchling)
- **.env.example**: 필수 환경 변수 템플릿
- **CLAUDE.md**: MoAI-ADK 실행 지침

---

**최종 업데이트**: 2026-02-15
**상태**: 디렉토리 구조 정의 완료
