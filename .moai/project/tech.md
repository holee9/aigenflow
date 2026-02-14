# agent-compare 기술 스택

## 전체 기술 스택 개요

agent-compare는 Python 기반의 코어 파이프라인과 JavaScript 기반의 웹 UI를 조합한 하이브리드 아키텍처를 사용합니다. Proxima v3.0.0 다중 AI 게이트웨이를 통해 4개의 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)를 통합적으로 관리합니다.

## 백엔드 기술 스택 (Python)

### 핵심 언어 및 런타임

**Python 3.13+**: 최신 Python 3.13 이상 필수. 최신 언어 기능, 성능 개선, 보안 패치를 활용합니다. 가상 환경 도구로 UV를 사용하여 빠른 패키지 관리를 구현합니다.

### CLI 프레임워크

**Typer** (권장): 최신 Python 타입 힌트 기반 CLI 프레임워크. Click과 비교하여 코드 가독성과 자동 문서화가 우수합니다. async/await 지원으로 비동기 파이프라인 구현이 용이합니다. FastAPI와 동일한 개발 경험을 제공합니다.

**Click** (대안): 성숙한 CLI 프레임워크. Typer가 과할 경우 선택합니다.

### 의존성 관리

**uv**: 매우 빠른 Python 패키지 설치 도구. pip 대비 10배 이상 빠른 성능. pyproject.toml 기반 프로젝트 관리.

**pyproject.toml**: Python 표준 프로젝트 설정. 의존성, 빌드 시스템, 도구 설정을 통합 관리합니다.

### 비동기 처리

**asyncio**: Python 표준 비동기 라이브러리. 파이프라인의 병렬 작업(Phase 2 병렬 연구 등) 구현에 사용됩니다.

**aiohttp**: 비동기 HTTP 클라이언트. Proxima API와의 비동기 통신을 처리합니다.

### 로깅 및 모니터링

**structlog**: 구조화된 로깅. JSON 형식의 로그로 분석 및 모니터링이 용이합니다.

**loguru** (대안): 더 간단한 로깅 라이브러리.

### 설정 관리

**pydantic**: 데이터 검증 및 설정 관리. 타입 안전성을 제공합니다.

**python-dotenv**: .env 파일에서 환경 변수 로딩.

### 템플릿 엔진

**jinja2**: 파이썬 표준 템플릿 엔진. 비즈니스 계획서 렌더링에 사용됩니다.

### 문서 생성

**python-docx**: Word 문서 생성. 출력 포맷 지원.

**markdown**: Markdown 포맷 지원.

## AI 게이트웨이 및 통합

### Proxima v3.0.0

**개요**: Electron 기반 데스크톱 애플리케이션. localhost:3210에서 REST API 제공. OpenAI 호환 인터페이스로 표준화된 통합.

**주요 기능**:
- 4개 AI 에이전트 지원: ChatGPT, Claude, Gemini, Perplexity
- 45+ MCP 도구: 검색, 코드 분석, 번역, 브레인스토밍, 텍스트 분석 등
- API 키 불필요: 브라우저 세션 기반 인증
- 스마트 라우터: 작업에 최적의 AI 자동 선택
- 가벼운 설치: 사전 설치된 Proxima 사용

**Python SDK 사용**:
```
from proxima import Proxima
client = Proxima()
response = client.chat("message", model="claude")
```

**JavaScript SDK 사용**:
```
const client = new Proxima();
await client.chat("message", {model: "claude"})
```

### Proxima API 엔드포인트

**메인 엔드포인트**: http://localhost:3210/v1/chat/completions (OpenAI 호환)

**스트리밍**: Server-Sent Events (SSE) 지원으로 실시간 응답 처리.

**MCP 도구**: 45+ 도구 포함 (검색, 분석, 생성, 번역, 코드 등).

## 웹 UI 기술 스택 (JavaScript)

### 핵심 프레임워크

**Next.js 15** (권장): React 기반 풀스택 프레임워크. App Router로 최신 아키텍처 구현. API 라우트로 백엔드 통합. 자동 최적화와 정적 생성으로 성능 우수.

**React 18**: UI 컴포넌트 라이브러리. Concurrent Features와 Suspense로 사용자 경험 향상.

### 언어 및 타입

**TypeScript 5+**: 타입 안전성과 개발 생산성. Next.js 15와 완벽한 통합.

### 상태 관리

**Zustand**: 가벼운 상태 관리 라이브러리. 복잡한 상태 관리 불필요 시 최적.

**TanStack Query (React Query)**: 서버 상태 관리와 캐싱. API 데이터 동기화 자동화.

### 스타일링

**Tailwind CSS**: 유틸리티 기반 CSS 프레임워크. 빠른 UI 개발, 일관된 디자인.

**shadcn/ui**: Tailwind 기반 고수준 컴포넌트 라이브러리. 버튼, 카드, 모달 등 재사용 가능한 컴포넌트 제공.

### 실시간 통신

**Socket.IO** (선택사항): 실시간 파이프라인 진행 상황 업데이트. 양방향 통신으로 즉각적인 피드백 가능.

## 개발 환경

### 런타임 요구사항

**Python 3.13+**: 최신 버전 필수.

**Node.js 18+**: LTS 버전 권장. npm 또는 yarn 포함.

**Proxima v3.0.0**: 사전 설치 필요. https://proxima.kr에서 다운로드.

### 개발 도구

**pytest**: Python 테스트 프레임워크. 80% 이상 코드 커버리지 목표.

**pytest-asyncio**: 비동기 테스트 지원.

**coverage.py**: 코드 커버리지 측정.

**black**: Python 코드 포맷터. 일관된 코드 스타일.

**ruff**: 고속 Python 린터. 코드 품질 검사.

**mypy**: 정적 타입 검사.

**ESLint**: JavaScript 린터. 코드 품질 검사.

**Prettier**: JavaScript 코드 포매터.

**husky**: Git 훅 자동화. 커밋 전 린트 및 포맷 자동 실행.

## 빌드 및 배포

### 컨테이너화

**Docker**: 프로덕션 배포용 컨테이너. Dockerfile로 일관된 환경 구성.

**docker-compose**: 다중 컨테이너 관리 (Python 파이프라인, Node.js 웹, 선택사항 FastAPI).

### CI/CD 파이프라인

**GitHub Actions**: 자동화된 테스트, 린트, 배포 파이프라인.

**workflow/test.yml**: 모든 PR에 대해 테스트 및 린트 실행.

**workflow/deploy.yml**: main 브랜치 푸시 시 자동 배포.

### 배포 환경

**Vercel** (권장): Next.js 웹 배포. 자동 확장, 엣지 함수 지원.

**AWS Lambda + API Gateway**: Python 파이프라인 배포 (선택사항).

**Docker Hub / GitHub Container Registry**: 컨테이너 이미지 저장소.

## 아키텍처 결정사항

### Python vs JavaScript 분할 이유

**코어 파이프라인 (Python)**: 복잡한 AI 조정 로직, 여러 AI와의 상호작용, 프롬프트 엔지니어링. Python의 동적 특성과 풍부한 AI/ML 라이브러리가 적합합니다.

**웹 UI (JavaScript)**: 사용자 인터페이스, 실시간 상태 표시, 문서 뷰어. JavaScript의 DOM 조작과 비동기 이벤트 처리가 적합합니다.

### 비동기 아키텍처

파이프라인의 2단계(Gemini + Perplexity 병렬 연구) 등에서 asyncio를 사용하여 동시성을 확보합니다. 웹 UI는 실시간 업데이트를 위해 Socket.IO로 백엔드와 통신합니다.

### 마이크로서비스 고려사항

현재는 모놀리식 아키텍처이나, 향후 확장성을 위해 다음과 같은 서비스 분리를 고려합니다:
- 파이프라인 서비스 (Python)
- 웹 UI 서비스 (Next.js)
- 에이전트 조정 서비스 (FastAPI 선택사항)
- 결과 저장소 서비스 (선택사항)

## 보안 및 규정 준수

### 환경 변수 관리

민감한 정보(API 키, 토큰)는 .env 파일에 저장합니다. 버전 컨트롤에서 제외하고, .env.example 템플릿만 포함합니다.

### 인증 및 인가

현재 Proxima는 로컬 환경에서 실행되므로 별도의 인증이 필요하지 않습니다. 프로덕션 배포 시 사용자 인증(JWT 토큰 등) 추가.

### 입력 검증

Pydantic으로 모든 입력 데이터 검증. 악의적인 입력으로부터 보호.

## 성능 최적화

### 파이프라인 병렬화

Phase 2에서 Gemini와 Perplexity 요청을 asyncio.gather()로 병렬 처리. 총 실행 시간 단축.

### 캐싱 전략

자주 요청되는 데이터(템플릿, 설정)는 메모리 캐시. Redis 고려 (향후 확장).

### 웹 성능

Next.js의 자동 코드 분할로 초기 로딩 속도 개선. Image 컴포넌트로 이미지 최적화. 정적 생성(SSG) 활용.

## 의존성 버전

**주요 패키지**:
- Python 3.13+
- typer 0.10+
- pydantic 2.5+
- aiohttp 3.9+
- jinja2 3.1+
- pytest 7.4+

**웹 의존성**:
- next 15.0+
- react 18.2+
- typescript 5.3+
- tailwindcss 3.3+
- zustand 4.4+

**Proxima**:
- proxima >= 3.0.0
- openai-compatible API

## 개발 환경 구성

### 로컬 설정

1. Python 가상 환경: `python -m venv venv` 및 `source venv/bin/activate` (또는 `uv`)
2. 의존성 설치: `pip install -r requirements.txt` (또는 `uv pip install`)
3. Node.js 설정: `node --version` (18+ 확인) 및 `npm install`
4. Proxima 설정: 별도 Proxima 애플리케이션 실행 (localhost:3210)
5. 환경 변수: `.env.example` → `.env` 복사 및 수정

### 개발 실행

**백엔드**: `python src/main.py --dev`
**웹 UI**: `npm run dev` (localhost:3000)
**테스트**: `pytest tests/` (또는 `npm test`)

## 프로덕션 배포

### Docker 빌드

Dockerfile을 통해 Python 및 Node.js 환경 포함 컨테이너 생성.

### 배포 플랫폼

**Vercel**: Next.js 웹 UI 자동 배포.
**AWS**: Python 파이프라인 Lambda 또는 EC2 배포.
**Docker Hub**: 컨테이너 이미지 저장 및 배포.

---

**최종 업데이트**: 2026-02-15
**상태**: 기술 스택 정의 완료
