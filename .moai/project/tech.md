# AigenFlow 기술 스택

## 전체 기술 스택 개요

AigenFlow는 Python 기반의 CLI 파이프라인 도구입니다. Playwright 영구 프로필을 통해 4개의 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)를 통합적으로 관리합니다.

## 백엔드 기술 스택 (Python)

### 핵심 언어 및 런타임

**Python 3.11+**: Python 3.11 이상 필수. 최신 언어 기능, 성능 개선, 보안 패치를 활용합니다.

### CLI 프레임워크

**Typer**: 최신 Python 타입 힌트 기반 CLI 프레임워크. 코드 가독성과 자동 문서화가 우수합니다. async/await 지원으로 비동기 파이프라인 구현이 용이합니다.

### 패키징

**hatchling**: PEP 517/518 준수 빌드 백엔드. src 레이아웃 네이티브 지원, 빠른 빌드 속도.

**pyproject.toml**: Python 표준 프로젝트 설정. 의존성, 빌드 시스템, 도구 설정을 통합 관리합니다.

### 비동기 처리

**asyncio**: Python 표준 비동기 라이브러리. 파이프라인의 병렬 작업(Phase 2 병렬 연구 등) 구현에 사용됩니다.

### 로깅 및 모니터링

**structlog**: 구조화된 로깅. JSON 형식의 로그로 분석 및 모니터링이 용이합니다.

### 설정 관리

**pydantic**: 데이터 검증 및 설정 관리. 타입 안전성을 제공합니다.

**pydantic-settings**: 환경 변수 기반 설정 관리.

### 템플릿 엔진

**jinja2**: 파이썬 표준 템플릿 엔진. 프롬프트 템플릿 렌더링에 사용됩니다.

### 터미널 UI

**rich**: 풍부한 터미널 출력. 진행률 표시, 테이블, 색상 지원.

## AI 게이트웨이

### Playwright 영구 프로필

**개요**: 브라우저 자동화 프레임워크. 영구 프로필을 통해 AI 서비스 웹 인터페이스에 직접 접근합니다.

**주요 기능**:
- 4개 AI 에이전트 지원: ChatGPT, Claude, Gemini, Perplexity
- API 키 불필요: 구독형 웹 세션 기반 인증
- 영구 프로필: `~/.aigenflow/profiles/{provider}/` 에 세션 저장
- 4단계 복구 체인: 리프레시 → 재로그인 → 폴백 → Claude 안전망

### Provider 구조

**BaseProvider 추상 클래스**: send_message(), check_session(), login_flow(), detect_response()

**서비스별 Provider**:
- ChatGPTProvider: chat.openai.com
- ClaudeProvider: claude.ai
- GeminiProvider: gemini.google.com
- PerplexityProvider: perplexity.ai

## 개발 환경

### 런타임 요구사항

**Python 3.11+**: 필수.

**Playwright**: Chromium 브라우저 자동 설치 (`playwright install chromium`)

### 개발 도구

**pytest**: Python 테스트 프레임워크. 85% 이상 코드 커버리지 목표.

**pytest-asyncio**: 비동기 테스트 지원.

**pytest-cov**: 코드 커버리지 측정.

**ruff**: 고속 Python 린터 및 포매터. 코드 품질 검사.

**mypy**: 정적 타입 검사.

## 빌드 및 배포

### 패키지 배포

**PyPI**: `pip install aigenflow`로 전역 설치 지원.

**pipx**: 독립 실행형 설치 지원 (`pipx install aigenflow`).

### CI/CD 파이프라인

**GitHub Actions**: 자동화된 테스트, 린트, 배포 파이프라인.

## 아키텍처 결정사항

### Python 선택 이유

복잡한 AI 조정 로직, 여러 AI와의 상호작용, 프롬프트 엔지니어링에 Python의 동적 특성과 풍부한 라이브러리가 적합합니다.

### 비동기 아키텍처

파이프라인의 2단계(Gemini + Perplexity 병렬 연구) 등에서 asyncio를 사용하여 동시성을 확보합니다.

## 보안 및 규정 준수

### 환경 변수 관리

민감한 정보는 .env 파일에 저장합니다. 버전 컨트롤에서 제외하고, .env.example 템플릿만 포함합니다.

### 입력 검증

Pydantic으로 모든 입력 데이터 검증. 악의적인 입력으로부터 보호.

## 성능 최적화

### 파이프라인 병렬화

Phase 2에서 Gemini와 Perplexity 요청을 asyncio.gather()로 병렬 처리. 총 실행 시간 단축.

### 지연 로딩

CLI 시작 시간 최적화를 위해 모듈 지연 로딩 구현.

## 의존성 버전

**주요 패키지**:
- Python 3.11+
- typer 0.12+
- pydantic 2.9+
- pydantic-settings 2.6+
- jinja2 3.1+
- playwright 1.49+
- rich 13.0+
- structlog 24.0+
- pytest 8.0+

## 개발 환경 구성

### 로컬 설정

1. Python 가상 환경: `python -m venv .venv` 및 `source .venv/bin/activate`
2. 의존성 설치: `pip install -e .`
3. Playwright 브라우저: `playwright install chromium`
4. 환경 변수: `.env.example` → `.env` 복사 및 수정

### 개발 실행

**CLI**: `aigenflow run --topic "test"`
**테스트**: `pytest tests/`

## 프로덕션 배포

### 패키지 배포

**PyPI**: `pip install aigenflow`로 전역 설치.
**소스**: GitHub 저장소에서 소스 코드 다운로드.

---

**최종 업데이트**: 2026-02-15
**상태**: 기술 스택 정의 완료
