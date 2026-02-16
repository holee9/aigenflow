# SPEC-ENHANCE-004: 구현 계획 (Implementation Plan)

## 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-ENHANCE-004 |
| **버전** | 1.0.0 |
| **작성일** | 2026-02-16 |
| **상태** | Planned |
| **예상 파일 수** | 15-20개 |

---

## 1. 마일스톤 개요

| 마일스톤 | 설명 | 우선순위 | 핵심 산출물 |
|---------|------|----------|------------|
| **M1** | 캐싱 시스템 | Primary | CacheManager, cache CLI |
| **M2** | 배치 처리 | Primary | BatchProcessor, Phase 2 통합 |
| **M3** | 모니터링 | Secondary | TokenTracker, stats CLI |
| **M4** | 통합/최적화 | Final | 성능 검증, 문서화 |

---

## 2. Phase별 상세 계획

### Phase 1: 캐싱 시스템 (M1)

#### 2.1.1 목표

동일한 AI 요청에 대한 응답을 캐싱하여 API 호출을 줄이고 비용을 절감합니다.

#### 2.1.2 구현 파일

| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `src/cache/__init__.py` | 모듈 초기화 | High |
| `src/cache/key_generator.py` | 캐시 키 생성 | High |
| `src/cache/storage.py` | 파일 시스템 저장소 | High |
| `src/cache/manager.py` | 캐시 관리자 | High |
| `src/cache/models.py` | 데이터 모델 | High |
| `src/cli/cache.py` | CLI 명령 | Medium |
| `tests/cache/test_manager.py` | 단위 테스트 | High |

#### 2.1.3 기술 세부사항

**캐시 키 생성 알고리즘**:
```python
def generate_cache_key(
    prompt: str,
    agent_type: AgentType,
    phase: int,
    context_hash: str,
) -> str:
    """
    Generate unique cache key for AI request.

    Algorithm:
    1. Normalize prompt (strip, lowercase, remove extra whitespace)
    2. Combine with agent_type, phase, context_hash
    3. Generate SHA-256 hash
    """
    normalized = " ".join(prompt.strip().lower().split())
    combined = f"{normalized}|{agent_type.value}|{phase}|{context_hash}"
    return hashlib.sha256(combined.encode()).hexdigest()[:32]
```

**저장소 구조**:
```
~/.aigenflow/cache/
├── entries/
│   ├── {key_1}.json
│   ├── {key_2}.json
│   └── ...
├── index.json          # 메타데이터 인덱스
└── stats.json          # 통계 데이터
```

#### 2.1.4 테스트 계획

| 테스트 케이스 | 설명 | 예상 결과 |
|--------------|------|----------|
| test_cache_hit | 동일 요청 재전송 | 캐시에서 반환 |
| test_cache_miss | 새 요청 | API 호출 후 캐싱 |
| test_cache_expiry | TTL 만료 | 새 API 호출 |
| test_cache_invalidation | 수동 삭제 | 캐시 제거 |
| test_cache_key_collision | 유사 프롬프트 | 다른 키 생성 |
| test_cache_size_limit | 크기 제한 | LRU 삭제 |

---

### Phase 2: 배치 처리 (M2)

#### 2.2.1 목표

여러 AI 요청을 배치로 묶어 처리 효율을 높이고 오버헤드를 줄입니다.

#### 2.2.2 구현 파일

| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `src/batch/__init__.py` | 모듈 초기화 | High |
| `src/batch/queue.py` | 요청 큐 | High |
| `src/batch/processor.py` | 배치 처리기 | High |
| `src/batch/models.py` | 데이터 모델 | High |
| `tests/batch/test_processor.py` | 단위 테스트 | High |

#### 2.2.3 기술 세부사항

**배치 처리 흐름**:
```python
async def process_batch(batch: List[BatchRequest]) -> List[BatchResponse]:
    """
    Process a batch of AI requests.

    Flow:
    1. Group by provider
    2. Execute in parallel per provider
    3. Maintain response ordering
    4. Handle partial failures
    """
    grouped = group_by_provider(batch)
    results = await asyncio.gather(
        *[execute_provider_batch(p, reqs) for p, reqs in grouped.items()],
        return_exceptions=True
    )
    return flatten_results(results, batch)
```

**Phase 2 배치 최적화**:
- 현재: `asyncio.gather(gemini_task, perplexity_task)` (개별 실행)
- 개선: 배치 큐에서 수집 후 일괄 실행

#### 2.2.4 테스트 계획

| 테스트 케이스 | 설명 | 예상 결과 |
|--------------|------|----------|
| test_batch_grouping | 요청 그룹화 | Provider별 분리 |
| test_batch_execution | 배치 실행 | 병렬 처리 |
| test_batch_ordering | 응답 순서 | 원래 순서 유지 |
| test_partial_failure | 일부 실패 | 성공 항목만 반환 |
| test_timeout_fallback | 타임아웃 | 개별 처리 전환 |

---

### Phase 3: 모니터링 시스템 (M3)

#### 2.3.1 목표

토큰 사용량과 비용을 실시간으로 추적하고 예산 경고를 제공합니다.

#### 2.3.2 구현 파일

| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `src/monitoring/__init__.py` | 모듈 초기화 | High |
| `src/monitoring/tracker.py` | 토큰 추적기 | High |
| `src/monitoring/cost_calculator.py` | 비용 계산 | High |
| `src/monitoring/stats.py` | 통계 수집 | High |
| `src/monitoring/budget.py` | 예산 관리 | Medium |
| `src/monitoring/pricing.yaml` | 가격표 | High |
| `src/cli/stats.py` | CLI 명령 | Medium |
| `tests/monitoring/test_tracker.py` | 단위 테스트 | High |

#### 2.3.3 기술 세부사항

**토큰 추적 흐름**:
```python
# GatewayResponse에 토큰 정보 포함
class GatewayResponse(BaseModel):
    content: str
    success: bool
    tokens_used: int = 0          # 기존
    input_tokens: int = 0         # NEW
    output_tokens: int = 0        # NEW
    estimated_cost: float = 0.0   # NEW

# TokenTracker가 집계
tracker.track(usage=TokenUsage(
    provider=agent_type,
    input_tokens=response.input_tokens,
    output_tokens=response.output_tokens,
    phase=current_phase,
    task=task_name,
))
```

**가격표 구조** (pricing.yaml):
```yaml
version: "2026-02-16"
currency: "USD"
providers:
  claude:
    name: "Claude 3"
    input_per_million: 3.00
    output_per_million: 15.00
  chatgpt:
    name: "GPT-4"
    input_per_million: 10.00
    output_per_million: 30.00
  gemini:
    name: "Gemini 1.5 Pro"
    input_per_million: 1.25
    output_per_million: 5.00
  perplexity:
    name: "Perplexity"
    input_per_million: 1.00
    output_per_million: 1.00
```

#### 2.3.4 CLI 명령

```bash
# 토큰 사용량 조회
aigenflow stats

# 출력 예시
╭──────────────────────────────────────────────╮
│           Token Usage Summary                 │
├──────────────────────────────────────────────┤
│ Session: abc123                               │
│ Period: Today                                 │
├──────────────────────────────────────────────┤
│ Provider   │ Input    │ Output   │ Cost      │
├────────────┼──────────┼──────────┼───────────┤
│ Claude     │ 12,500   │ 8,200    │ $0.16     │
│ ChatGPT    │ 5,000    │ 3,000    │ $0.14     │
│ Gemini     │ 25,000   │ 15,000   │ $0.10     │
│ Perplexity │ 8,000    │ 5,000    │ $0.01     │
├────────────┼──────────┼──────────┼───────────┤
│ Total      │ 50,500   │ 31,200   │ $0.41     │
╰──────────────────────────────────────────────╯

# 캐시 관리
aigenflow cache stats

# 출력 예시
╭──────────────────────────────────────────────╮
│           Cache Statistics                    │
├──────────────────────────────────────────────┤
│ Total Entries: 156                            │
│ Cache Size: 12.5 MB                           │
│ Hit Rate: 23.5%                               │
│ Miss Rate: 76.5%                              │
│ Evictions: 12                                 │
│ Avg Hit Latency: 3.2 ms                       │
╰──────────────────────────────────────────────╯

aigenflow cache clear
aigenflow cache list --provider claude
```

#### 2.3.5 테스트 계획

| 테스트 케이스 | 설명 | 예상 결과 |
|--------------|------|----------|
| test_token_tracking | 토큰 추적 | 정확한 집계 |
| test_cost_calculation | 비용 계산 | 가격표 적용 |
| test_budget_alert_50 | 50% 임계값 | 경고 발생 |
| test_budget_alert_100 | 100% 초과 | 중지 옵션 |
| test_stats_aggregation | 통계 집계 | 정확한 합계 |

---

### Phase 4: 통합 및 최적화 (M4)

#### 2.4.1 목표

모든 컴포넌트를 통합하고 성능을 최적화합니다.

#### 2.4.2 통합 작업

| 작업 | 설명 |
|------|------|
| AgentRouter 통합 | 캐싱 로직을 라우터에 적용 |
| Pipeline 통합 | 배치 처리를 파이프라인에 적용 |
| GatewayResponse 확장 | 토큰/비용 정보 추가 |
| Config 확장 | 캐시/배치/모니터링 설정 추가 |

#### 2.4.3 성능 벤치마크

| 항목 | 측정 방법 | 목표 |
|------|----------|------|
| 캐시 적중률 | CacheStats | 20%+ |
| 배치 효율 | 실행 시간 비교 | 15%+ 감소 |
| 총 비용 절감 | 월간 비용 비교 | 25%+ |

---

## 3. 의존성 관계

```
Phase 1 (캐싱)
    │
    ├──→ Phase 2 (배치) ──→ Phase 4 (통합)
    │                           ↑
    └──→ Phase 3 (모니터링) ────┘
```

- Phase 1, 2, 3은 병렬 개발 가능
- Phase 4는 모든 Phase 완료 후 진행

---

## 4. 파일 생성 계획

### 4.1 새로 생성할 파일

| 경로 | 설명 | Phase |
|------|------|-------|
| `src/cache/__init__.py` | 모듈 초기화 | 1 |
| `src/cache/models.py` | 데이터 모델 | 1 |
| `src/cache/key_generator.py` | 캐시 키 생성 | 1 |
| `src/cache/storage.py` | 저장소 | 1 |
| `src/cache/manager.py` | 캐시 관리자 | 1 |
| `src/batch/__init__.py` | 모듈 초기화 | 2 |
| `src/batch/models.py` | 데이터 모델 | 2 |
| `src/batch/queue.py` | 요청 큐 | 2 |
| `src/batch/processor.py` | 배치 처리기 | 2 |
| `src/monitoring/__init__.py` | 모듈 초기화 | 3 |
| `src/monitoring/models.py` | 데이터 모델 | 3 |
| `src/monitoring/pricing.yaml` | 가격표 | 3 |
| `src/monitoring/tracker.py` | 토큰 추적기 | 3 |
| `src/monitoring/cost_calculator.py` | 비용 계산 | 3 |
| `src/monitoring/stats.py` | 통계 수집 | 3 |
| `src/monitoring/budget.py` | 예산 관리 | 3 |
| `src/cli/cache.py` | cache 명령 | 1 |
| `src/cli/stats.py` | stats 명령 | 3 |
| `tests/cache/test_manager.py` | 캐시 테스트 | 1 |
| `tests/batch/test_processor.py` | 배치 테스트 | 2 |
| `tests/monitoring/test_tracker.py` | 모니터링 테스트 | 3 |

### 4.2 수정할 파일

| 경로 | 수정 내용 | Phase |
|------|----------|-------|
| `src/agents/router.py` | 캐싱 로직 통합 | 1 |
| `src/gateway/base.py` | 토큰 정보 추가 | 3 |
| `src/core/config.py` | 캐시/모니터링 설정 추가 | 1, 3 |
| `src/main.py` | CLI 명령 등록 | 1, 3 |
| `src/pipeline/phase2_research.py` | 배치 처리 적용 | 2 |

---

## 5. 테스트 전략

### 5.1 단위 테스트

- 각 모듈별 독립 테스트
- Mock을 활용한 격리 테스트
- 85%+ 코드 커버리지 목표

### 5.2 통합 테스트

- 캐시 + 라우터 통합 테스트
- 배치 + 파이프라인 통합 테스트
- 모니터링 + 전체 시스템 테스트

### 5.3 성능 테스트

- 캐시 적중률 벤치마크
- 배치 처리 효율 벤치마크
- 메모리 사용량 프로파일링

---

## 6. 롤백 계획

### 6.1 기능 플래그

```python
# config.yaml
features:
  caching_enabled: true
  batch_processing_enabled: true
  monitoring_enabled: true
```

### 6.2 비상시 비활성화

```bash
# 캐싱 비활성화
aigenflow config set caching_enabled false

# 배치 처리 비활성화
aigenflow config set batch_processing_enabled false
```

---

## 7. 문서화 계획

| 문서 | 설명 | 작성 시점 |
|------|------|----------|
| README 업데이트 | 새 기능 설명 추가 | Phase 4 |
| CHANGELOG | 버전별 변경 사항 | Phase 4 |
| API 문서 | 함수/클래스 문서화 | 각 Phase |
| 사용자 가이드 | CLI 명령 사용법 | Phase 4 |

---

**작성자**: MoAI Plan Agent
**작성일**: 2026-02-16
**상태**: Draft
