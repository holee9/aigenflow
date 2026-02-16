# SPEC-ENHANCE-004: AI 비용 최적화 (AI Cost Optimization)

## SPEC 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-ENHANCE-004 |
| **제목** | AI 비용 최적화 (AI Cost Optimization) |
| **작성일** | 2026-02-16 |
| **상태** | Completed |
| **버전** | 1.2.0 |
| **우선순위** | High |
| **관련 문서** | SPEC-ENHANCE-003, SPEC-PIPELINE-001 |
| **라이프사이클** | spec-anchored |
| **완료율** | 100% (15/15 tasks) |
| **의존성** | SPEC-ENHANCE-003 (ContextSummary, TokenCounter) |

---

## 1. 배경 및 개요

### 1.1 문제 정의

AigenFlow는 5단계 파이프라인에서 4개의 AI 에이전트(Claude, ChatGPT, Gemini, Perplexity)를 활용하여 사업 계획서를 생성합니다. 이 과정에서 다음과 같은 비용 문제가 발생합니다:

| 문제점 | 현재 상황 | 비용 영향 |
|--------|----------|----------|
| 중복 요청 | 동일한 프롬프트 재전송 | 토큰 낭비 15-20% |
| 배치 미활용 | 개별 API 호출 | 오버헤드 증가 |
| 모니터링 부재 | 토큰 사용량 미측정 | 비용 가시성 없음 |
| 캐싱 없음 | 매번 새 요청 | 반복 작업 비용 증가 |

### 1.2 개요

본 SPEC은 AigenFlow의 AI 비용 최적화를 위한 3가지 핵심 기능을 정의합니다:

1. **캐싱 전략**: 동일 요청 재사용으로 API 호출 감소
2. **배치 처리**: 다중 요청 일괄 처리로 오버헤드 절감
3. **토큰 모니터링 대시보드**: 실시간 사용량 추적 및 비용 가시화

### 1.3 기대 효과

| 개선 항목 | 기대 효과 | 측정 지표 |
|-----------|----------|----------|
| 캐싱 도입 | API 호출 20-30% 감소 | Cache Hit Rate |
| 배치 처리 | 오버헤드 15% 감소 | 요청당 평균 비용 |
| 모니터링 | 비용 가시성 확보 | 토큰/달러 추적 |
| 종합 효과 | **총 비용 25-40% 절감** | 월간 AI 비용 |

---

## 2. 요구사항 (Requirements) - EARS 형식

### 2.1 사용자 스토리 (User Stories)

#### US-1: 캐싱된 응답 재사용

**WHEN** 사용자가 이전에 요청한 것과 동일하거나 유사한 프롬프트를 제출하면 **THEN** 시스템은 캐시된 응답을 반환하여 API 호출을 건너뛰어야 한다.

**인수 조건**:
- 프롬프트 + 컨텍스트 기반 캐시 키 생성
- TTL(Time-To-Live) 기반 캐시 만료 (기본 24시간)
- 캐시 적중률 20% 이상 달성
- 파일 시스템 기반 캐시 저장

#### US-2: 배치 처리로 효율화

**WHEN** 여러 AI 요청이 대기 중이면 **THEN** 시스템은 이를 배치로 묶어 한 번에 처리해야 한다.

**인수 조건**:
- Phase 2(Gemini + Perplexity) 병렬 처리 개선
- 요청 큐 기반 배치 처리
- 최대 배치 크기 설정 가능 (기본 5개)
- 응답 순서 보장

#### US-3: 토큰 사용량 모니터링

**WHEN** 사용자가 파이프라인을 실행하면 **THEN** 시스템은 실시간으로 토큰 사용량을 추적하고 보고해야 한다.

**인수 조건**:
- Provider별 토큰 사용량 추적
- 세션별, Phase별 사용량 집계
- CLI 명령으로 현재 사용량 확인 (`aigenflow stats`)
- 비용 추정 기능 (토큰 → 달러 변환)

#### US-4: 비용 예산 경고

**WHEN** 토큰 사용량이 설정된 예산 임계값에 도달하면 **THEN** 시스템은 사용자에게 경고를 표시해야 한다.

**인수 조건**:
- 일일/주간/월간 예산 설정
- 50%, 75%, 90%, 100% 임계값 경고
- CLI 출력 및 로그 기록
- 예산 초과 시 선택적 일시 중지

#### US-5: 캐시 관리

**WHEN** 사용자가 캐시를 관리하려고 하면 **THEN** 시스템은 캐시 조회, 삭제, 통계 기능을 제공해야 한다.

**인수 조건**:
- `aigenflow cache list`: 캐시된 항목 목록
- `aigenflow cache clear`: 캐시 삭제
- `aigenflow cache stats`: 캐시 통계 (적중률, 크기)

### 2.2 기능 요구사항 (Functional Requirements)

#### FR-1: 캐시 키 생성

시스템은 **항상** 프롬프트와 컨텍스트를 기반으로 고유한 캐시 키를 생성해야 한다.

상세 요구사항:
```python
# 캐시 키 생성 알고리즘
cache_key = hash(
    prompt_text +
    context_hash +
    agent_type +
    phase_number +
    model_version
)
```

- SHA-256 해시 알고리즘 사용
- 정규화(Normalization): 공백, 대소문자 일관화
- 컨텍스트 해시: 이전 Phase 결과 요약 포함

#### FR-2: 캐시 저장소

시스템은 **항상** 파일 시스템 기반 캐시 저장소를 유지해야 한다.

상세 요구사항:
```yaml
# 캐시 저장소 구조
cache_dir: ~/.aigenflow/cache/
├── responses/
│   ├── {cache_key}.json      # 응답 데이터
│   └── metadata.json         # 메타데이터 인덱스
├── stats.json                # 통계 데이터
└── config.yaml               # 캐시 설정
```

- 최대 캐시 크기: 500MB (설정 가능)
- LRU(Least Recently Used) 삭제 정책
- 압축 저장 옵션 (gzip)

#### FR-3: 배치 처리 큐

시스템은 **항상** AI 요청을 배치로 묶어 처리해야 한다.

상세 요구사항:
```python
# 배치 처리 구조
class BatchQueue:
    max_batch_size: int = 5       # 최대 배치 크기
    max_wait_time: float = 2.0    # 최대 대기 시간(초)
    providers: List[AgentType]    # 배치 지원 Provider
```

- Phase 2(Gemini, Perplexity) 병렬 배치
- 동일 Provider 요청 그룹화
- 타임아웃 시 개별 처리 폴백

#### FR-4: 토큰 추적

시스템은 **항상** 모든 AI 요청의 토큰 사용량을 추적해야 한다.

상세 요구사항:
```python
# 토큰 추적 데이터 구조
class TokenUsage:
    provider: AgentType
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float         # USD
    timestamp: datetime
    phase: int
    task: str
```

- Provider별 가격표 적용 (2026년 기준)
- 실시간 집계 및 누적 추적
- 세션/일일/월간 통계 제공

#### FR-5: 비용 계산

시스템은 **항상** 토큰 사용량을 기반으로 비용을 추정해야 한다.

상세 요구사항:
```yaml
# Provider별 가격표 (2026년 2월 기준, USD/1M tokens)
pricing:
  claude:
    input: 3.00
    output: 15.00
  chatgpt:
    input: 10.00
    output: 30.00
  gemini:
    input: 1.25
    output: 5.00
  perplexity:
    input: 1.00
    output: 1.00
```

- 최신 가격표 자동 업데이트 (설정 파일)
- 입력/출력 토큰 구분 계산
- 환율 적용 (현지화 지원)

### 2.3 비기능 요구사항 (Non-Functional Requirements)

#### NFR-1: 성능

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 캐시 조회 속도 | 10ms 이내 | 벤치마크 |
| 배치 처리 오버헤드 | 5% 이내 | Before/After 비교 |
| 모니터링 영향 | 1% 이하 | 파이프라인 실행 시간 |

#### NFR-2: 신뢰성

- 캐시 손상 시 자동 복구
- 배치 실패 시 개별 처리 폴백
- 통계 데이터 정합성 보장

#### NFR-3: 확장성

- 캐시 저장소: SQLite/Redis 확장 지원
- 배치 처리: 외부 큐 시스템 연동 가능
- 모니터링: 외부 대시보드 연동 (Prometheus, Grafana)

#### NFR-4: 보안

- 캐시 데이터 암호화 옵션
- 민감 정보(프롬프트 내 개인정보) 마스킹
- 접근 권한 관리

---

## 3. 기술 접근법 (Technical Approach)

### 3.1 아키텍처 설계

```
src/
├── cache/                        # NEW: 캐싱 시스템
│   ├── __init__.py
│   ├── manager.py                # CacheManager
│   ├── key_generator.py          # 캐시 키 생성
│   ├── storage.py                # 파일 시스템 저장소
│   └── tests/
│       └── test_cache.py
├── batch/                        # NEW: 배치 처리
│   ├── __init__.py
│   ├── queue.py                  # BatchQueue
│   ├── processor.py              # BatchProcessor
│   └── tests/
│       └── test_batch.py
├── monitoring/                   # NEW: 모니터링
│   ├── __init__.py
│   ├── tracker.py                # TokenTracker
│   ├── cost_calculator.py        # CostCalculator
│   ├── stats.py                  # StatsCollector
│   └── tests/
│       └── test_monitoring.py
└── cli/
    ├── stats.py                  # MOD: stats 명령
    └── cache.py                  # NEW: cache 명령
```

### 3.2 핵심 컴포넌트

#### 3.2.1 CacheManager

```python
class CacheManager:
    """
    AI 응답 캐싱 관리자.

    책임:
    - 캐시 키 생성 및 조회
    - TTL 기반 만료 관리
    - LRU 삭제 정책
    - 통계 수집
    """

    def __init__(
        self,
        cache_dir: Path,
        max_size_mb: int = 500,
        default_ttl_hours: int = 24,
    ): ...

    async def get(self, key: str) -> CacheEntry | None: ...
    async def set(self, key: str, response: GatewayResponse, ttl_hours: int = None): ...
    async def invalidate(self, key: str): ...
    def get_stats(self) -> CacheStats: ...
```

#### 3.2.2 BatchProcessor

```python
class BatchProcessor:
    """
    AI 요청 배치 처리기.

    책임:
    - 요청 큐 관리
    - 배치 그룹화
    - 병렬 실행
    - 응답 순서 보장
    """

    def __init__(
        self,
        router: AgentRouter,
        max_batch_size: int = 5,
        max_wait_seconds: float = 2.0,
    ): ...

    async def enqueue(self, request: AgentRequest) -> str: ...
    async def process_batch(self) -> List[AgentResponse]: ...
    async def flush(self): ...
```

#### 3.2.3 TokenTracker

```python
class TokenTracker:
    """
    토큰 사용량 추적기.

    책임:
    - 실시간 토큰 추적
    - Provider별 집계
    - 비용 계산
    - 예산 경고
    """

    def __init__(
        self,
        pricing_config: dict[str, PricingInfo],
        budgets: BudgetConfig,
    ): ...

    def track(self, usage: TokenUsage): ...
    def get_summary(self, period: Period) -> UsageSummary: ...
    def check_budget(self) -> List[BudgetAlert]: ...
    def estimate_cost(self, tokens: int, provider: str, is_input: bool) -> float: ...
```

### 3.3 구현 순서

**Phase 1: 캐싱 시스템** (2-3일)
1. 캐시 키 생성 로직 구현
2. 파일 시스템 저장소 구현
3. CacheManager 클래스 구현
4. AgentRouter에 캐싱 통합
5. 캐시 CLI 명령 구현

**Phase 2: 배치 처리** (2-3일)
1. BatchQueue 클래스 구현
2. BatchProcessor 구현
3. Phase 2 병렬 처리에 배치 통합
4. 폴백 메커니즘 구현
5. 배치 통계 수집

**Phase 3: 모니터링 시스템** (2-3일)
1. TokenTracker 구현
2. CostCalculator 구현
3. StatsCollector 구현
4. stats CLI 명령 구현
5. 예산 경고 시스템

**Phase 4: 통합 및 최적화** (1-2일)
1. 전체 시스템 통합
2. 성능 벤치마크
3. 통합 테스트
4. 문서화

### 3.4 핵심 설계 결정

| # | 결정 사항 | 선택 | 근거 |
|---|---------|------|------|
| D-1 | 캐시 저장소 | 파일 시스템 | 단순성, 이식성, 의존성 최소화 |
| D-2 | 캐시 키 알고리즘 | SHA-256 | 충돌 최소화, 표준 알고리즘 |
| D-3 | 배치 크기 | 5개 | 메모리/지연 시간 균형 |
| D-4 | TTL | 24시간 | 콘텐츠 신선도 vs 적중률 |
| D-5 | 비용 계산 | 설정 파일 | 가격 변동 대응 용이 |

---

## 4. 구현 계획

### 4.1 태스크 분해 (WBS)

| Phase | 태스크 | 설명 | 의존성 |
|-------|-------|------|--------|
| **1** | CacheKeyGenerator 구현 | 프롬프트 해시 생성 | - |
| **1** | CacheStorage 구현 | 파일 시스템 저장소 | CacheKeyGenerator |
| **1** | CacheManager 구현 | 캐시 관리 로직 | CacheStorage |
| **1** | AgentRouter 통합 | 캐싱 로직 적용 | CacheManager |
| **1** | cache CLI 명령 | list/clear/stats | CacheManager |
| **2** | BatchQueue 구현 | 요청 큐 | - |
| **2** | BatchProcessor 구현 | 배치 실행 | BatchQueue |
| **2** | Phase 2 통합 | 병렬 배치 처리 | BatchProcessor |
| **2** | 폴백 메커니즘 | 개별 처리 전환 | BatchProcessor |
| **3** | PricingConfig 구현 | 가격표 관리 | - |
| **3** | CostCalculator 구현 | 비용 계산 | PricingConfig |
| **3** | TokenTracker 구현 | 사용량 추적 | CostCalculator |
| **3** | BudgetAlert 구현 | 예산 경고 | TokenTracker |
| **3** | stats CLI 명령 | 통계 조회 | TokenTracker |
| **4** | 통합 테스트 | E2E 테스트 | 모든 Phase |
| **4** | 성능 벤치마크 | 최적화 검증 | 통합 테스트 |

### 4.2 마일스톤

| 마일스톤 | 완료 기준 |
|---------|----------|
| M1: 캐싱 시스템 | 캐시 적중률 측정 가능, CLI 명령 동작 |
| M2: 배치 처리 | Phase 2 배치 처리 동작, 폴백 확인 |
| M3: 모니터링 | 토큰/비용 추적 동작, 예산 경고 동작 |
| M4: 통합 완료 | 25% 비용 절감 검증, 모든 테스트 통과 |

---

## 5. 리스크 및 완화

| ID | 리스크 | 심각도 | 완화 전략 |
|----|-------|--------|----------|
| R-1 | 캐시 충돌 (다른 프롬프트 동일 키) | LOW | SHA-256 사용, 키에 컨텍스트 포함 |
| R-2 | 캐시 데이터 손상 | MEDIUM | 체크섬 검증, 자동 복구 |
| R-3 | 배치 처리 지연 증가 | MEDIUM | 타임아웃 설정, 폴백 메커니즘 |
| R-4 | 가격표 변경 | LOW | 설정 파일 분리, 버전 관리 |
| R-5 | 캐시 적중률 낮음 | MEDIUM | TTL 조정, 키 생성 알고리즘 개선 |

---

## 6. 성공 기준

### 6.1 기능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 캐시 적중률 | 20% 이상 | CacheStats |
| 배치 처리 효율 | 15% 이상 오버헤드 감소 | Before/After 비교 |
| 토큰 추적 정확도 | 100% | 수동 검증 |
| 비용 추정 오차 | 5% 이내 | 실제 청구서 비교 |
| **총 비용 절감** | **25% 이상** | 월간 비용 비교 |

### 6.2 비기능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 캐시 조회 지연 | 10ms 이내 | 벤치마크 |
| 배치 처리 오버헤드 | 5% 이내 | 파이프라인 실행 시간 |
| 메모리 사용량 증가 | 50MB 이내 | 프로파일링 |

---

## 추적 태그 (Traceability)

| TAG | 연결 |
|-----|------|
| SPEC-ENHANCE-004 | SPEC-ENHANCE-003 → 비용 최적화 확장 |
| FR-1 | src/cache/key_generator.py |
| FR-2 | src/cache/storage.py |
| FR-3 | src/batch/queue.py |
| FR-4 | src/monitoring/tracker.py |
| FR-5 | src/monitoring/cost_calculator.py |
| US-1 | CacheManager |
| US-2 | BatchProcessor |
| US-3 | TokenTracker, stats CLI |
| US-4 | BudgetAlert |
| US-5 | cache CLI |

---

**작성자**: MoAI Plan Agent
**작성일**: 2026-02-16
**상태**: Draft
**다음 단계**: 사용자 승인 후 `/moai run SPEC-ENHANCE-004` 로 구현 시작
