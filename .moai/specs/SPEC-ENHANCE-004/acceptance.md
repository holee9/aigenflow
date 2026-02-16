# SPEC-ENHANCE-004: 인수 조건 (Acceptance Criteria)

## 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-ENHANCE-004 |
| **버전** | 1.0.0 |
| **작성일** | 2026-02-16 |
| **상태** | Planned |
| **테스트 프레임워크** | pytest |
| **목표 커버리지** | 85%+ |

---

## 1. 캐싱 시스템 (Caching System)

### AC-1.1: 캐시 키 생성

**Given** 프롬프트 텍스트와 에이전트 타입이 제공됨
**When** 캐시 키를 생성하면
**Then** SHA-256 기반 32자 고유 키가 반환됨

```gherkin
Scenario: 동일 프롬프트는 동일 키 생성
  Given 프롬프트 "사업 아이디어 분석"
  And 에이전트 타입 CLAUDE
  And Phase 1
  When 캐시 키를 생성하면
  Then 키는 "a1b2c3d4e5f6..." 형식의 32자 문자열
  And 동일 입력으로 다시 생성하면 동일한 키 반환

Scenario: 다른 프롬프트는 다른 키 생성
  Given 프롬프트 "사업 아이디어 분석"
  And 프롬프트 "시장 조사 분석"
  When 각각 캐시 키를 생성하면
  Then 두 키는 서로 다름
```

### AC-1.2: 캐시 적중 (Cache Hit)

**Given** 캐시에 이전 응답이 저장됨
**When** 동일한 요청이 다시 들어오면
**Then** 캐시된 응답이 반환됨 (API 호출 없음)

```gherkin
Scenario: 캐시된 응답 재사용
  Given 캐시에 키 "abc123"으로 응답이 저장됨
  And 응답 내용이 "분석 결과..." 임
  When 동일한 키로 요청이 들어오면
  Then 캐시된 응답이 즉시 반환됨
  And API 호출이 발생하지 않음
  And 응답 시간이 10ms 미만임
```

### AC-1.3: 캐시 미스 (Cache Miss)

**Given** 캐시에 해당 요청이 없음
**When** 새 요청이 들어오면
**Then** API 호출 후 응답을 캐시에 저장함

```gherkin
Scenario: 새 요청 캐싱
  Given 캐시에 키 "xyz789"에 대한 항목이 없음
  When 해당 키로 요청이 들어오면
  Then AI API 호출이 발생함
  And 응답이 캐시에 저장됨
  And TTL이 24시간으로 설정됨
```

### AC-1.4: TTL 만료

**Given** 캐시 항목의 TTL이 만료됨
**When** 해당 키로 요청이 들어오면
**Then** 새 API 호출이 발생하고 캐시가 갱신됨

```gherkin
Scenario: 만료된 캐시 갱신
  Given 캐시 항목이 25시간 전에 생성됨
  And TTL이 24시간으로 설정됨
  When 해당 키로 요청이 들어오면
  Then 캐시 미스로 처리됨
  And 새 API 호출이 발생함
  And 새 응답으로 캐시가 갱신됨
```

### AC-1.5: 캐시 크기 제한

**Given** 캐시 크기가 최대 용량에 도달함
**When** 새 항목을 추가하면
**Then** LRU 정책에 따라 가장 오래된 항목이 삭제됨

```gherkin
Scenario: LRU 삭제
  Given 캐시 최대 크기가 500MB로 설정됨
  And 현재 캐시 크기가 498MB임
  And 새 항목 크기가 5MB임
  When 새 항목을 추가하면
  Then 가장 오래된 항목이 삭제됨
  And 캐시 크기가 500MB 이하로 유지됨
  And 새 항목이 성공적으로 추가됨
```

### AC-1.6: 캐시 CLI 명령

```gherkin
Scenario: 캐시 통계 조회
  Given 캐시에 156개 항목이 저장됨
  And 총 캐시 크기가 12.5MB임
  And 적중률이 23.5%임
  When "aigenflow cache stats" 명령을 실행하면
  Then 통계 정보가 테이블 형식으로 출력됨
  And Total Entries, Cache Size, Hit Rate가 포함됨

Scenario: 캐시 삭제
  Given 캐시에 여러 항목이 저장됨
  When "aigenflow cache clear" 명령을 실행하면
  Then 모든 캐시 항목이 삭제됨
  And "Cache cleared successfully" 메시지가 출력됨
```

---

## 2. 배치 처리 (Batch Processing)

### AC-2.1: 배치 그룹화

**Given** 여러 AI 요청이 큐에 대기 중
**When** 배치 처리를 시작하면
**Then** 동일 Provider 요청끼리 그룹화됨

```gherkin
Scenario: Provider별 그룹화
  Given 큐에 5개의 요청이 있음
  And 3개는 Gemini 요청
  And 2개는 Perplexity 요청
  When 배치 처리를 시작하면
  Then Gemini 요청 3개가 하나의 배치로 그룹화됨
  And Perplexity 요청 2개가 하나의 배치로 그룹화됨
```

### AC-2.2: 병렬 배치 실행

**Given** 여러 Provider 배치가 준비됨
**When** 배치를 실행하면
**Then** 각 Provider 배치가 병렬로 실행됨

```gherkin
Scenario: 병렬 배치 실행
  Given Gemini 배치 1개와 Perplexity 배치 1개가 있음
  When 배치를 실행하면
  Then 두 배치가 동시에 실행됨
  And 총 실행 시간이 개별 실행 시간의 합보다 작음
```

### AC-2.3: 응답 순서 보장

**Given** 배치로 여러 요청이 처리됨
**When** 응답을 반환하면
**Then** 원래 요청 순서대로 응답이 반환됨

```gherkin
Scenario: 응답 순서 유지
  Given 요청 순서가 [Req1, Req2, Req3]임
  When 배치 처리가 완료되면
  Then 응답 순서가 [Res1, Res2, Res3]임
  And 각 응답이 대응하는 요청과 매칭됨
```

### AC-2.4: 부분 실패 처리

**Given** 배치 중 일부 요청이 실패함
**When** 배치 처리가 완료되면
**Then** 성공한 요청의 응답만 반환됨

```gherkin
Scenario: 일부 실패 시 부분 반환
  Given 배치에 3개 요청이 있음
  And Req2만 실패함
  When 배치 처리가 완료되면
  Then Res1과 Res3이 반환됨
  And Req2에 대한 에러 정보가 포함됨
```

### AC-2.5: 타임아웃 폴백

**Given** 배치 처리가 타임아웃됨
**When** 타임아웃이 발생하면
**Then** 개별 요청으로 처리를 전환함

```gherkin
Scenario: 타임아웃 시 개별 처리
  Given 배치 대기 시간이 2초로 설정됨
  And 2초 내에 충분한 요청이 모이지 않음
  When 타임아웃이 발생하면
  Then 현재 큐의 요청들이 개별로 처리됨
```

---

## 3. 모니터링 시스템 (Monitoring System)

### AC-3.1: 토큰 사용량 추적

**Given** AI 요청이 처리됨
**When** 응답이 반환되면
**Then** 토큰 사용량이 기록됨

```gherkin
Scenario: 토큰 추적
  Given Claude API 호출이 발생함
  When 응답이 반환되면
  Then 입력 토큰 수가 기록됨
  And 출력 토큰 수가 기록됨
  And 총 토큰 수가 계산됨
  And 타임스탬프가 기록됨
```

### AC-3.2: 비용 계산

**Given** 토큰 사용량이 기록됨
**When** 비용을 계산하면
**Then** Provider별 가격표가 적용됨

```gherkin
Scenario: 비용 계산
  Given Claude 입력 토큰 10,000개
  And Claude 출력 토큰 5,000개
  When 비용을 계산하면
  Then 입력 비용이 $0.03 (10K * $3/M)
  And 출력 비용이 $0.075 (5K * $15/M)
  And 총 비용이 $0.105로 계산됨
```

### AC-3.3: 통계 집계

**Given** 여러 토큰 사용 기록이 있음
**When** 통계를 조회하면
**Then** 기간별/Provider별 집계가 반환됨

```gherkin
Scenario: 일일 통계 집계
  Given 오늘 Claude 50K 토큰 사용
  And 오늘 ChatGPT 30K 토큰 사용
  When 일일 통계를 조회하면
  Then Claude 비용이 계산됨
  And ChatGPT 비용이 계산됨
  And 총 비용이 합산됨
```

### AC-3.4: 예산 경고

**Given** 예산이 설정됨
**When** 사용량이 임계값에 도달하면
**Then** 경고가 발생함

```gherkin
Scenario: 50% 예산 경고
  Given 일일 예산이 $1.00로 설정됨
  And 현재 사용량이 $0.50임
  When 토큰 사용이 기록되면
  Then "50% of daily budget used" 경고가 출력됨

Scenario: 100% 예산 초과
  Given 일일 예산이 $1.00로 설정됨
  And 현재 사용량이 $1.00임
  When 추가 토큰 사용이 기록되면
  Then "Daily budget exceeded" 경고가 출력됨
  And 선택적으로 파이프라인이 일시 중지됨
```

### AC-3.5: Stats CLI 명령

```gherkin
Scenario: 토큰 사용량 조회
  Given 오늘 총 81,700 토큰 사용
  And 총 비용이 $0.41임
  When "aigenflow stats" 명령을 실행하면
  Then Provider별 사용량이 테이블로 출력됨
  And 총 사용량과 비용이 표시됨
  And 예산 사용 비율이 표시됨

Scenario: 기간별 조회
  Given 지난 7일간 사용 기록이 있음
  When "aigenflow stats --period weekly" 명령을 실행하면
  Then 주간 통계가 출력됨
  And 일별 추이가 그래프로 표시됨 (ASCII)
```

---

## 4. 통합 테스트 (Integration Tests)

### AC-4.1: 캐싱 + 파이프라인 통합

```gherkin
Scenario: 파이프라인 실행 중 캐시 활용
  Given 캐시 시스템이 활성화됨
  And Phase 1이 이미 실행된 적이 있음
  When 동일한 주제로 다시 파이프라인을 실행하면
  Then Phase 1에서 캐시가 활용됨
  And 총 API 호출 횟수가 감소함
  And 실행 시간이 단축됨
```

### AC-4.2: 배치 + 모니터링 통합

```gherkin
Scenario: 배치 처리 중 토큰 추적
  Given 배치 처리가 활성화됨
  And 모니터링이 활성화됨
  When 배치가 실행되면
  Then 각 요청의 토큰이 개별로 추적됨
  And 총 토큰이 정확히 집계됨
```

### AC-4.3: 전체 시스템 E2E

```gherkin
Scenario: 전체 파이프라인 비용 최적화
  Given 캐시, 배치, 모니터링이 모두 활성화됨
  When 동일 주제로 3회 파이프라인을 실행하면
  Then 2회차부터 캐시 적중이 발생함
  And 배치 처리로 병렬 효율이 향상됨
  And 총 비용이 최소 25% 절감됨
  And 모든 토큰 사용량이 추적됨
```

---

## 5. 성능 인수 조건

### AC-5.1: 캐시 성능

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 캐시 조회 지연 | < 10ms | 벤치마크 |
| 캐시 저장 지연 | < 50ms | 벤치마크 |
| 적중률 (3회 실행) | > 20% | 통계 |

### AC-5.2: 배치 성능

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 배치 오버헤드 | < 5% | 실행 시간 비교 |
| 배치 크기 효율 | > 15% 감소 | Before/After |
| 최대 배치 크기 | 5개 | 설정 검증 |

### AC-5.3: 모니터링 성능

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| 추적 오버헤드 | < 1% | 실행 시간 비교 |
| 메모리 증가 | < 50MB | 프로파일링 |
| 통계 조회 속도 | < 100ms | 벤치마크 |

---

## 6. 품질 게이트 (TRUST 5)

### Tested

- [ ] 모든 단위 테스트 통과 (85%+ 커버리지)
- [ ] 모든 통합 테스트 통과
- [ ] 성능 벤치마크 기준 충족

### Readable

- [ ] 함수명이 명확하고 설명적임
- [ ] 코드 주석이 영어로 작성됨
- [ ] Docstring이 모든 public 함수에 있음

### Unified

- [ ] 코딩 스타일이 ruff 규칙 준수
- [ ] import 순서가 isort 규칙 준수
- [ ] 타입 힌트가 모든 함수에 있음

### Secured

- [ ] 캐시 데이터 암호화 옵션 있음
- [ ] 민감 정보 마스킹 처리됨
- [ ] 입력 검증이 모든 진입점에 있음

### Trackable

- [ ] 모든 주요 작업에 로깅이 있음
- [ ] 에러가 구조화된 형식으로 기록됨
- [ ] 통계가 지속적으로 수집됨

---

## 7. 테스트 체크리스트

### Phase 1: 캐싱

- [ ] test_cache_key_generation_identical
- [ ] test_cache_key_generation_different
- [ ] test_cache_hit_returns_cached_response
- [ ] test_cache_miss_stores_response
- [ ] test_cache_expiry_triggers_new_request
- [ ] test_cache_size_limit_eviction
- [ ] test_cache_cli_stats
- [ ] test_cache_cli_clear

### Phase 2: 배치

- [ ] test_batch_grouping_by_provider
- [ ] test_batch_parallel_execution
- [ ] test_batch_response_ordering
- [ ] test_batch_partial_failure
- [ ] test_batch_timeout_fallback

### Phase 3: 모니터링

- [ ] test_token_tracking
- [ ] test_cost_calculation
- [ ] test_stats_aggregation
- [ ] test_budget_alert_50_percent
- [ ] test_budget_alert_100_percent
- [ ] test_stats_cli_command

### Phase 4: 통합

- [ ] test_cache_pipeline_integration
- [ ] test_batch_monitoring_integration
- [ ] test_full_cost_optimization
- [ ] test_e2e_pipeline_with_optimization

---

**작성자**: MoAI Plan Agent
**작성일**: 2026-02-16
**상태**: Draft
