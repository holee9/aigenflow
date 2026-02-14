# agent-compare 디렉토리 구조

## 프로젝트 전체 구조

```
agent-compare/
├── .moai/                          # MoAI-ADK 설정 및 메타데이터
│   ├── specs/                      # SPEC 문서 저장소
│   │   └── SPEC-XXX/               # 개별 스펙 파일
│   │       └── spec.md
│   ├── project/                    # 프로젝트 문서
│   │   ├── product.md              # 프로젝트 개요
│   │   ├── structure.md            # 디렉토리 구조 (본 파일)
│   │   ├── tech.md                 # 기술 스택
│   │   └── roadmap.md              # 개발 로드맵
│   ├── docs/                       # 자동 생성 문서
│   │   ├── api/                    # API 문서
│   │   ├── guides/                 # 사용자 가이드
│   │   └── architecture/           # 아키텍처 문서
│   └── config/                     # MoAI 설정
│       └── sections/
│           ├── quality.yaml        # 품질 게이트 설정
│           ├── language.yaml       # 다국어 설정
│           └── user.yaml           # 사용자 설정
│
├── src/                            # Python 코어 파이프라인
│   ├── __init__.py
│   ├── main.py                     # CLI 진입점
│   ├── pipeline/                   # 5단계 파이프라인 구현
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # 파이프라인 조정자
│   │   ├── phase1_framing.py       # 1단계: 개념 프레이밍
│   │   ├── phase2_research.py      # 2단계: 심층 연구
│   │   ├── phase3_strategy.py      # 3단계: 전략/로드맵
│   │   ├── phase4_writing.py       # 4단계: 초안 작성
│   │   └── phase5_review.py        # 5단계: 검증/검토
│   ├── agents/                     # AI 에이전트 조정
│   │   ├── __init__.py
│   │   ├── base_agent.py           # 기본 에이전트 클래스
│   │   ├── claude_agent.py         # Claude 에이전트
│   │   ├── chatgpt_agent.py        # ChatGPT 에이전트
│   │   ├── gemini_agent.py         # Gemini 에이전트
│   │   ├── perplexity_agent.py     # Perplexity 에이전트
│   │   └── agent_router.py         # 에이전트 라우터
│   ├── core/                       # 핵심 기능
│   │   ├── __init__.py
│   │   ├── config.py               # 설정 관리
│   │   ├── logger.py               # 로깅 설정
│   │   ├── exceptions.py           # 커스텀 예외
│   │   ├── models.py               # 데이터 모델
│   │   └── utils.py                # 유틸리티 함수
│   ├── proxima_integration/        # Proxima 게이트웨이 통합
│   │   ├── __init__.py
│   │   ├── client.py               # Proxima 클라이언트
│   │   ├── models.py               # Proxima 데이터 모델
│   │   ├── mcp_tools.py            # MCP 도구 래퍼
│   │   └── session_manager.py      # 세션 관리
│   ├── templates/                  # 템플릿 및 프롬프트
│   │   ├── __init__.py
│   │   ├── prompt_templates.py     # 프롬프트 템플릿
│   │   └── output_templates.py     # 출력 템플릿
│   └── output/                     # 생성 결과 저장
│       ├── __init__.py
│       ├── formatter.py            # 출력 포맷팅
│       └── validators.py           # 출력 검증
│
├── web/                            # Next.js/React 웹 대시보드
│   ├── app/                        # Next.js App Router
│   │   ├── layout.tsx              # 레이아웃
│   │   ├── page.tsx                # 홈페이지
│   │   ├── dashboard/              # 대시보드
│   │   │   ├── page.tsx
│   │   │   ├── [id]/page.tsx       # 프로젝트 상세
│   │   │   └── components/
│   │   ├── api/                    # API 라우트
│   │   │   ├── pipeline/route.ts   # 파이프라인 API
│   │   │   └── agents/route.ts     # 에이전트 상태 API
│   │   └── settings/page.tsx       # 설정 페이지
│   ├── components/                 # React 컴포넌트
│   │   ├── PipelineMonitor.tsx     # 파이프라인 모니터
│   │   ├── AgentStatus.tsx         # 에이전트 상태
│   │   ├── DocumentViewer.tsx      # 문서 뷰어
│   │   └── common/                 # 공통 컴포넌트
│   ├── hooks/                      # Custom React hooks
│   │   └── usePipeline.ts
│   ├── lib/                        # 유틸리티 라이브러리
│   │   ├── api.ts                  # API 클라이언트
│   │   └── utils.ts
│   ├── styles/                     # CSS 스타일
│   ├── public/                     # 정적 파일
│   ├── next.config.js              # Next.js 설정
│   ├── tsconfig.json               # TypeScript 설정
│   └── package.json
│
├── tests/                          # 테스트 스위트
│   ├── __init__.py
│   ├── conftest.py                 # pytest 설정
│   ├── unit/                       # 단위 테스트
│   │   ├── test_agents.py
│   │   ├── test_pipeline.py
│   │   └── test_proxima.py
│   ├── integration/                # 통합 테스트
│   │   ├── test_pipeline_flow.py
│   │   └── test_ai_coordination.py
│   └── fixtures/                   # 테스트 픽스처
│       ├── sample_specs.py
│       └── mock_responses.py
│
├── templates/                      # 비즈니스 계획서 템플릿
│   ├── business_plan_default.md    # 기본 템플릿
│   ├── business_plan_startup.md    # 스타트업용
│   ├── business_plan_rd.md         # R&D 제안서용
│   └── components/
│       ├── executive_summary.md
│       ├── market_analysis.md
│       ├── financial_projections.md
│       └── implementation_roadmap.md
│
├── docs/                           # 프로젝트 문서
│   ├── README.md                   # 프로젝트 개요
│   ├── GETTING_STARTED.md          # 시작 가이드
│   ├── API.md                      # API 문서
│   ├── ARCHITECTURE.md             # 아키텍처 문서
│   ├── DEVELOPMENT.md              # 개발 가이드
│   ├── DEPLOYMENT.md               # 배포 가이드
│   └── guides/
│       ├── proxima_integration.md  # Proxima 통합 가이드
│       └── extending_agents.md     # 에이전트 확장 가이드
│
├── .claude/                        # Claude Code 설정
│   ├── agents/                     # 커스텀 에이전트
│   │   └── agent-compare-docs.md
│   ├── skills/                     # 커스텀 스킬
│   └── rules/                      # 규칙 정의
│
├── config/                         # 설정 파일
│   ├── default.yaml                # 기본 설정
│   ├── development.yaml            # 개발 환경
│   ├── production.yaml             # 프로덕션 환경
│   └── templates.yaml              # 템플릿 설정
│
├── scripts/                        # 유틸리티 스크립트
│   ├── setup.py                    # 초기 설정
│   ├── migrate.py                  # 마이그레이션
│   └── deploy.sh                   # 배포 스크립트
│
├── .github/                        # GitHub 설정
│   ├── workflows/
│   │   ├── test.yml                # 테스트 자동화
│   │   ├── lint.yml                # 린트 검사
│   │   └── deploy.yml              # 배포 자동화
│   └── ISSUE_TEMPLATE/
│
├── .gitignore
├── .env.example                    # 환경 변수 템플릿
├── README.md                       # 프로젝트 README
├── CHANGELOG.md                    # 변경 로그
├── LICENSE
├── pyproject.toml                  # Python 프로젝트 설정
├── requirements.txt                # Python 의존성
├── requirements-dev.txt            # 개발 의존성
└── CLAUDE.md                       # MoAI 실행 지침

```

## 핵심 모듈 설명

### src/pipeline/ - 5단계 파이프라인 구현

파이프라인 오케스트레이터가 5개의 단계를 순차적으로 관리합니다. 각 단계는 특정 AI 에이전트들의 협업으로 진행되며, 입력 데이터를 처리하여 다음 단계로 전달합니다.

**phase1_framing.py**: 개념 프레이밍 단계. ChatGPT로 아이디어 브레인스토밍, Claude로 논리 검증을 수행합니다.

**phase2_research.py**: 심층 연구 단계. Gemini와 Perplexity가 병렬로 시장 조사를 수행합니다.

**phase3_strategy.py**: 전략 수립 단계. ChatGPT로 SWOT 분석, Claude로 통합 검증을 수행합니다.

**phase4_writing.py**: 초안 작성 단계. Claude가 주로 작성하고 ChatGPT와 Gemini가 보조합니다.

**phase5_review.py**: 최종 검토 단계. Perplexity가 사실 검증, Claude가 최종 정렬을 수행합니다.

### src/agents/ - AI 에이전트 조정

각 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)는 base_agent.py의 기본 클래스를 상속하여 구현됩니다. 에이전트 라우터는 각 단계에 적합한 에이전트를 선택하고 조정합니다.

### src/core/ - 핵심 기능

설정 관리, 로깅, 커스텀 예외, 데이터 모델, 유틸리티 함수를 포함합니다. 이 모듈들은 전체 파이프라인에서 공통으로 사용됩니다.

### src/proxima_integration/ - Proxima 게이트웨이 통합

Proxima 클라이언트는 localhost:3210의 REST API를 통해 4개의 AI 에이전트와 45+ MCP 도구에 접근합니다. 세션 관리자가 AI 대화 세션을 유지합니다.

### web/ - Next.js 웹 대시보드

사용자가 브라우저를 통해 파이프라인을 실행하고, 진행 상황을 모니터링하며, 생성된 사업 계획서를 확인할 수 있는 인터페이스를 제공합니다.

### tests/ - 테스트 스위트

단위 테스트는 개별 함수 및 클래스를 검증합니다. 통합 테스트는 전체 파이프라인의 동작을 검증합니다.

### templates/ - 비즈니스 계획서 템플릿

다양한 사용 사례(스타트업, R&D 제안서 등)에 맞춘 템플릿을 제공합니다.

## 주요 파일 위치

| 목적 | 파일 경로 |
|------|---------|
| CLI 진입점 | src/main.py |
| 파이프라인 조정 | src/pipeline/orchestrator.py |
| Proxima 통합 | src/proxima_integration/client.py |
| 웹 API | web/app/api/ |
| 환경 설정 | config/default.yaml |
| 테스트 실행 | tests/conftest.py |
| 배포 설정 | .github/workflows/deploy.yml |

## 모듈 간 의존성

**pipeline → agents**: 파이프라인이 에이전트를 호출하여 작업 수행
**agents → proxima_integration**: 에이전트가 Proxima 클라이언트를 통해 AI 호출
**pipeline → core**: 모든 모듈이 core의 설정, 로깅, 모델 사용
**web/api → pipeline**: 웹 API가 파이프라인을 백엔드에서 호출
**output → templates**: 생성 결과를 템플릿에 맞춰 포맷

## 설정 및 실행 파일

- **pyproject.toml**: Python 프로젝트 메타데이터, 의존성, 빌드 설정
- **package.json**: Node.js 의존성 및 스크립트
- **.env.example**: 필수 환경 변수 템플릿
- **CLAUDE.md**: MoAI-ADK 실행 지침

---

**최종 업데이트**: 2026-02-15
**상태**: 디렉토리 구조 정의 완료
