# AigenFlow 프로젝트 추가 개선 계획

## Context

AigenFlow는 현재 **안정화 단계**에 있습니다. 2026-02-18 브라우저 풀 이벤트 루프 관리 개선을 통해 안정성 문제가 대부분 해결되었으며, PyPI 배포가 준비된 상태입니다.

**현재 상태:**
- 테스트 통과: 866/873 (99.2%)
- 코드 커버리지: 73%
- 안정성 테스트: 10/10 (100%)
- Lint: 0 errors
- 배포 상태: PyPI 준비 완료

**완료된 최근 개선:**
- BrowserPool 싱글톤 패턴 (메모리 최적화)
- 이벤트 루프 라이프사이클 관리 강화
- Windows 서브프로세스 정리 경고 억제
- Graceful Shutdown 구현
- 환경 변수 문서화 완료
- TODO 주석 정리 완료

본 계획은 프로젝트의 **다음 단계(Next Phase)**를 위한 개선 영역을 식별하고 우선순위를 제안합니다.

---

## 추천 접근법

프로젝트가 안정화 단계에 있으므로, **점진적 개선**과 **사용자 가치 중심**의 접근을 권장합니다.

---

## 1. 테스트 커버리지 향상 (우선순위: 높음)

### 목표
코드 커버리지 73% → 85%+ 달성 (TRUST 5 품질 기준)

### 현재 상황
- 90개 이상의 테스트 파일이 존재
- 핵심 모듈 커버리지는 높음 (97%+)
- 일부 모듈의 커버리지 부족

### 개선 작업

| 모듈 | 작업 | 예상 시간 |
|------|------|----------|
| `src/agents/*.py` | 단위 테스트 추가 | 2-3시간 |
| `src/gateway/*.py` | edge case 테스트 | 2-3시간 |
| `src/pipeline/*.py` | 통합 테스트 강화 | 3-4시간 |
| `src/cli/*.py` | CLI 명령어 테스트 | 1-2시간 |

### 검증 방법
```bash
pytest --cov=src --cov-report=html --cov-report=term
# 목표: 85%+ coverage
```

---

## 2. 문서화 강화 (우선순위: 중간)

### 목표
사용자 및 개발자를 위한 포괄적인 문서 제공

### 현재 상황
- README.md: 설치 및 기본 사용법 포함
- product.md, tech.md, structure.md: MoAI 내부용
- API 문서: 부재

### 개선 작업

#### 2.1 API 문서 (Sphinx 또는 MkDocs)
```bash
# docs/api/ 디렉토리 구조
docs/api/
├── gateway.md      # Playwright 게이트웨이 API
├── pipeline.md     # 파이프라인 오케스트레이션 API
├── agents.md       # AI 에이전트 라우터 API
└── configuration.md # 설정 관리 API
```

#### 2.2 사용자 가이드
```markdown
docs/guides/
├── getting-started.md    # 첫 실행 가이드
├── customization.md      # 커스텀 템플릿 만들기
├── troubleshooting.md    # 일반적인 문제 해결
└── production-tips.md    # 프로덕션 사용 팁
```

#### 2.3 개발자 가이드
```markdown
docs/development/
├── contributing.md       # 기여 가이드
├── architecture.md       # 아키텍처 개요
├── adding-providers.md   # 새 AI 프로바이더 추가
└── testing.md            # 테스트 작성 가이드
```

### 검증 방법
- 문서 빌드: `mkdocs build` 또는 `sphinx-build`
- 링크 확인: 모든 내부 링크 유효성 검사

---

## 3. 확장성 개선 (우선순위: 중간)

### 목표
플러그인 시스템과 커스터마이제이션 용이성 확보

### 현재 상황
- 하드코딩된 4개 AI 프로바이더
- 5단계 파이프라인 고정
- 템플릿 시스템은 있지만 확장 API 없음

### 개선 작업

#### 3.1 Provider 인터페이스 표준화
```python
# src/gateway/registry.py (신규)
class ProviderRegistry:
    """플러그인 방식의 AI 프로바이더 등록"""

    @staticmethod
    def register(name: str, provider_class: type[BaseProvider]) -> None:
        """커스텀 프로바이더 등록"""

    @staticmethod
    def get(name: str) -> type[BaseProvider]:
        """등록된 프로바이더 가져오기"""
```

#### 3.2 커스텀 파이프라인 단계 지원
```python
# src/pipeline/registry.py (신규)
class PhaseRegistry:
    """커스텀 파이프라인 단계 등록"""

    @staticmethod
    def register_phase(
        name: str,
        phase_class: type[BasePhase],
        position: int | None = None,
    ) -> None:
        """커스텀 단계 등록"""
```

### 검증 방법
- 커스텀 프로바이더 예제 작성 및 테스트
- 커스텀 파이프라인 단계 예제 작성 및 테스트

---

## 4. 사용자 경험 개선 (우선순위: 낮음)

### 목표
더 나은 설정 관리와 오류 메시지

### 개선 작업

#### 4.1 설정 관리 개선
```python
# src/cli/config.py 개선
- 현재: .env 파일 직접 편집 안내
- 개선: `aigenflow config set KEY VALUE` 명령어 구현
```

#### 4.2 오류 메시지 개선
```python
# 각 예외별 상세 가이드 제공
class SessionExpiredError(AigenFlowError):
    def __str__(self) -> str:
        return (
            "AI 서비스 세션이 만료되었습니다.\n"
            "해결 방법: `aigenflow relogin --provider {provider}` 실행\n"
            "자세한 내용: https://github.com/holee9/aigenflow/docs/troubleshooting"
        )
```

#### 4.3 진행 상황 표시 개선
```python
# Rich UI 컴포넌트 활용
- 현재 단계 표시
- 예상 소요 시간
- 남은 작업량
```

---

## 5. 성능 최적화 (우선순위: 낮음)

### 목표
추가적인 병렬화와 캐싱 최적화

### 개선 작업

#### 5.1 단계별 병렬화
```python
# Phase 2 이미 병렬 처리됨 (Gemini + Perplexity)
# 추가 기회:
- Phase 4: 초안 작성 병렬화 (Claude 주, ChatGPT/Gemini 보조)
- Phase 5: 사실 검증 병렬화 (Perplexity 주, Claude 보조)
```

#### 5.2 캐시 최적화
```python
# src/cache/manager.py 개선
- 현재: 파일 기반 캐시
- 개선: 선택적 Redis/SQLite 백엔드
- TTL(만료) 정책 개선
```

---

## 우선순위 요약

| 우선순위 | 작업 | 예상 시간 | 가치 |
|---------|------|----------|------|
| 1 (높음) | 테스트 커버리지 85%+ 달성 | 8-12시간 | 높음 |
| 2 (중간) | 문서화 강화 (API/가이드) | 10-15시간 | 높음 |
| 3 (중간) | 확장성 개선 (플러그인) | 15-20시간 | 중간 |
| 4 (낮음) | 사용자 경험 개선 | 8-10시간 | 중간 |
| 5 (낮음) | 성능 최적화 | 10-15시간 | 낮음 |

---

## 구현 전략

### Phase 1: 품질 기반 (1-2주)
- 테스트 커버리지 85%+ 달성
- 기존 코드 문서화 (docstrings)

### Phase 2: 문서화 (2-3주)
- API 문서 작성
- 사용자/개발자 가이드 작성

### Phase 3: 확장성 (3-4주)
- 플러그인 시스템 설계
- Provider/Phase 레지스트리 구현

### Phase 4: UX/성능 (선택)
- 사용자 경험 개선
- 성능 최적화

---

## 주요 파일

### 수정 필요
- `tests/` - 테스트 파일 추가
- `docs/` - 새로운 문서 추가
- `src/gateway/registry.py` - 신규 (프로바이더 레지스트리)
- `src/pipeline/registry.py` - 신규 (단계 레지스트리)
- `src/cli/config.py` - 설정 명령어 구현

### 참조 파일
- `src/pipeline/orchestrator.py` - 파이프라인 조정 로직
- `src/gateway/base.py` - BaseProvider 인터페이스
- `src/pipeline/base.py` - BasePhase 인터페이스
- `src/core/config.py` - 설정 관리
- `pyproject.toml` - 프로젝트 설정

---

## 검증 계획

### 1. 테스트 커버리지
```bash
pytest --cov=src --cov-report=term-missing
# 목표: 85%+ coverage, 핵심 모듈 95%+
```

### 2. 문서 빌드
```bash
# API 문서
sphinx-build docs/api docs/api/_build

# 사용자 가이드
mkdocs build
```

### 3. 확장성 테스트
```python
# 커스텀 프로바이더 예제 작성 후 로드 확인
from gateway.registry import ProviderRegistry
ProviderRegistry.register("custom", CustomProvider)
assert ProviderRegistry.get("custom") == CustomProvider
```

### 4. E2E 테스트
```bash
# 전체 파이프라인 실행
aigenflow run --topic "test" --type bizplan --lang ko
# 결과물 품질 확인
```

---

## 참고 사항

### 현재 아키텍처 강점
1. **명확한 계층 구조**: pipeline → agents → gateway → core
2. **추상화 잘 됨**: BaseProvider, BasePhase, BaseAgent
3. **설정 관리**: Pydantic Settings로 타입 안전성 확보
4. **로깅**: structlog로 구조화된 로깅

### 개선 기회
1. **하드코딩된 부분**: 프로바이더, 파이프라인 단계
2. **확장성**: 플러그인 시스템 부재
3. **문서화**: API 문서, 사용자 가이드 부족
4. **테스트**: 일부 모듈 커버리지 부족

---

**작성일**: 2026-02-18
**버전**: 1.0.0
**상태**: 승인 대기 중
