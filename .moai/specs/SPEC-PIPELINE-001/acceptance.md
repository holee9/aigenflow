# SPEC-PIPELINE-001: 인수 조건

## 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-PIPELINE-001 |
| **문서 유형** | 인수 조건 (Acceptance Criteria) |
| **작성일** | 2026-02-15 |
| **테스트 형식** | Given-When-Then (Gherkin) |

---

## 1. 파이프라인 실행 (US-1 / FR-1)

### AC-1.1: 전체 파이프라인 성공 실행

```gherkin
Given Proxima 게이트웨이가 localhost:3210에서 실행 중이고
  And 4개 AI 프로바이더 세션이 모두 유효하고
  And 기본 설정이 정상 로드되어 있을 때
When 사용자가 "aigenflow run --topic 'AI SaaS Platform'" 명령을 실행하면
Then 시스템은 5단계 파이프라인을 순차적으로 실행하고
  And 각 단계 시작/완료 이벤트를 발행하고
  And 각 단계 결과를 PhaseResult로 축적하고
  And 최종 사업 계획서를 output/{session_id}/final/business_plan.md에 저장하고
  And pipeline_state.json에 COMPLETED 상태를 기록한다
```

### AC-1.2: 단계별 상태 전이 검증

```gherkin
Given 파이프라인이 IDLE 상태일 때
When Phase 1이 시작되면
Then 상태가 PHASE_1로 전이되고
  And PhaseStarted 이벤트가 발행되고
  And Phase 1 완료 후 상태가 PHASE_2로 전이되고
  And PhaseCompleted 이벤트가 발행되고
  And 이 패턴이 Phase 5까지 반복되며
  And Phase 5 완료 후 COMPLETED 상태로 전이된다
```

### AC-1.3: 무효 상태 전이 차단

```gherkin
Given 파이프라인이 PHASE_2 상태일 때
When PHASE_4로 직접 전이를 시도하면
Then InvalidStateTransition 예외가 발생하고
  And 파이프라인 상태는 PHASE_2를 유지한다
```

---

## 2. 단계별 제어 (US-2)

### AC-2.1: 특정 단계부터 재개

```gherkin
Given 이전 실행에서 Phase 2까지 완료된 상태 파일이 존재할 때
When 사용자가 "aigenflow run --topic 'AI SaaS' --from-phase 3" 명령을 실행하면
Then 시스템은 pipeline_state.json에서 Phase 1-2 결과를 로드하고
  And Phase 3부터 파이프라인을 재개하고
  And Phase 1-2 결과를 Phase 3의 입력 컨텍스트에 포함한다
```

### AC-2.2: 누락된 상태 파일 처리

```gherkin
Given 이전 실행 상태 파일이 존재하지 않을 때
When 사용자가 "aigenflow run --from-phase 3" 명령을 실행하면
Then 시스템은 "이전 단계의 실행 결과를 찾을 수 없습니다" 에러 메시지를 출력하고
  And 사용자에게 Phase 1부터 실행하도록 안내한다
```

### AC-2.3: resume 명령으로 재개

```gherkin
Given 파이프라인이 Phase 3에서 실패하여 FAILED 상태이고
  And 해당 세션의 상태 파일이 저장되어 있을 때
When 사용자가 "aigenflow resume {session_id}" 명령을 실행하면
Then 시스템은 해당 세션의 마지막 성공 상태를 복원하고
  And 실패한 Phase 3부터 재실행한다
```

---

## 3. AI 에이전트 헬스체크 (US-3)

### AC-3.1: 전체 정상 상태

```gherkin
Given Proxima 게이트웨이가 정상 실행 중이고
  And 4개 AI 프로바이더 세션이 모두 유효할 때
When 사용자가 "aigenflow check" 명령을 실행하면
Then 시스템은 다음을 표시한다:
  | 항목 | 상태 |
  | Proxima Gateway | Connected (localhost:3210) |
  | ChatGPT | Available |
  | Claude | Available |
  | Gemini | Available |
  | Perplexity | Available |
  | 준비 상태 | Ready |
```

### AC-3.2: 부분 장애 상태

```gherkin
Given Proxima 게이트웨이가 실행 중이나
  And Gemini 세션이 만료되었을 때
When 사용자가 "aigenflow check" 명령을 실행하면
Then 시스템은 Gemini를 "Unavailable - 세션 만료"로 표시하고
  And 폴백 에이전트(Perplexity)가 사용 가능함을 안내하고
  And 준비 상태를 "Partial - 일부 기능 제한"으로 표시한다
```

### AC-3.3: Proxima 미실행

```gherkin
Given Proxima 게이트웨이가 실행되지 않고 있을 때
When 사용자가 "aigenflow check" 명령을 실행하면
Then 시스템은 "Proxima Gateway에 연결할 수 없습니다"를 표시하고
  And Proxima 시작 방법을 안내한다
```

---

## 4. 설정 관리 (US-4)

### AC-4.1: 설정 조회

```gherkin
Given 기본 설정이 로드되어 있을 때
When 사용자가 "aigenflow config show" 명령을 실행하면
Then 시스템은 현재 설정을 테이블 형식으로 표시한다:
  And AI-to-Phase 매핑이 표시되고
  And 출력 형식, 언어, 템플릿 설정이 표시되고
  And 타임아웃 및 재시도 설정이 표시된다
```

### AC-4.2: 설정 변경

```gherkin
Given 현재 기본 언어가 "ko"일 때
When 사용자가 "aigenflow config set language en" 명령을 실행하면
Then 시스템은 언어 설정을 "en"으로 변경하고
  And 설정 파일에 영속 저장하고
  And "설정이 변경되었습니다: language = en" 메시지를 출력한다
```

### AC-4.3: 잘못된 설정 값 검증

```gherkin
Given 사용자가 존재하지 않는 설정 키를 변경하려 할 때
When 사용자가 "aigenflow config set nonexistent value" 명령을 실행하면
Then 시스템은 "알 수 없는 설정 키: nonexistent" 에러를 표시하고
  And 사용 가능한 설정 키 목록을 안내한다
```

---

## 5. 출력 관리 (US-5)

### AC-5.1: 출력 디렉토리 구조

```gherkin
Given 파이프라인이 성공적으로 완료되었을 때
Then 출력 디렉토리는 다음 구조를 가진다:
  | 경로 | 내용 |
  | output/{session_id}/phase1/results.json | Phase 1 결과 |
  | output/{session_id}/phase2/results.json | Phase 2 결과 |
  | output/{session_id}/phase3/results.json | Phase 3 결과 |
  | output/{session_id}/phase4/results.json | Phase 4 결과 |
  | output/{session_id}/phase5/results.json | Phase 5 결과 |
  | output/{session_id}/final/business_plan.md | 최종 사업 계획서 |
  | output/{session_id}/pipeline_state.json | 파이프라인 상태 |
  | output/{session_id}/metadata.json | 세션 메타데이터 |
```

### AC-5.2: 중간 결과 보존

```gherkin
Given 파이프라인이 Phase 3에서 실패했을 때
Then Phase 1과 Phase 2의 결과는 output 디렉토리에 보존되어 있고
  And pipeline_state.json에 마지막 성공 상태가 기록되어 있다
```

---

## 6. 프롬프트 템플릿 시스템 (US-6)

### AC-6.1: 기본 템플릿 사용

```gherkin
Given 기본 프롬프트 템플릿이 templates/prompts/ 에 존재할 때
When 사용자가 "aigenflow run --template startup --topic 'AI SaaS'" 명령을 실행하면
Then 시스템은 startup 템플릿의 Jinja2 파일을 로드하고
  And topic, language, phase_context 변수를 주입하여 프롬프트를 생성한다
```

### AC-6.2: 사용자 커스텀 템플릿

```gherkin
Given 사용자가 ~/.aigenflow/templates/custom/ 디렉토리에 커스텀 템플릿을 생성했을 때
When 사용자가 "aigenflow run --template custom --topic 'Fintech'" 명령을 실행하면
Then 시스템은 사용자 커스텀 템플릿을 우선 로드한다
```

---

## 7. Proxima 비동기 클라이언트 (FR-2)

### AC-7.1: 정상 요청/응답

```gherkin
Given AsyncProximaClient가 초기화되어 있고
  And Proxima 게이트웨이가 정상 실행 중일 때
When Claude 에이전트에게 프롬프트를 전송하면
Then 시스템은 POST /v1/chat/completions 요청을 전송하고
  And 응답을 AgentResponse 모델로 파싱하고
  And content, tokens_used, response_time을 기록한다
```

### AC-7.2: 타임아웃 처리

```gherkin
Given AI 요청 타임아웃이 120초로 설정되어 있을 때
When AI 프로바이더가 120초 이내에 응답하지 않으면
Then 시스템은 ProximaTimeoutError를 발생시키고
  And 재시도 로직을 트리거한다
```

---

## 8. 오류 복구 및 재시도 (FR-5)

### AC-8.1: 요청 수준 재시도 + 폴백

```gherkin
Given ChatGPT 에이전트가 Phase 1 브레인스토밍을 수행 중일 때
When ChatGPT 요청이 2회 연속 실패하면
Then 시스템은 폴백 에이전트(Claude)로 전환하여 동일 작업을 시도하고
  And 폴백 전환 이벤트를 로깅한다
```

### AC-8.2: 지수 백오프

```gherkin
Given AI 요청이 실패했을 때
When 재시도를 수행하면
Then 첫 번째 재시도는 1초 후에
  And 두 번째 재시도는 2초 후에
  And 세 번째 재시도(폴백 포함)는 4초 후에 수행된다
```

### AC-8.3: 단계 실패 시 상태 저장

```gherkin
Given Phase 3 실행 중 모든 재시도와 폴백이 실패했을 때
Then 시스템은 파이프라인 상태를 FAILED로 전환하고
  And Phase 1-2 성공 결과를 pipeline_state.json에 저장하고
  And "Phase 3 실패. 'aigenflow resume {session_id}'로 재개하세요" 메시지를 출력한다
```

---

## 9. 컨텍스트 전달 (FR-3)

### AC-9.1: 컨텍스트 체인 검증

```gherkin
Given Phase 1이 완료되어 PhaseResult가 생성되었을 때
When Phase 2가 시작되면
Then Phase 2의 입력 컨텍스트에 Phase 1의 요약(summary)이 포함되고
  And Phase 3 시작 시 Phase 1+2의 요약이 포함되고
  And 이 패턴이 Phase 5까지 누적된다
```

### AC-9.2: 컨텍스트 크기 제한

```gherkin
Given 누적 컨텍스트가 설정된 최대 크기(기본 4000자)를 초과할 때
Then 시스템은 이전 단계 결과를 자동으로 요약하여 크기를 줄이고
  And 요약 전략이 적용되었음을 로깅한다
```

---

## 10. 비기능 요구사항 검증

### AC-10.1: 성능 (NFR-1)

```gherkin
Given 표준 테스트 환경에서
When 전체 파이프라인이 실행되면
Then 총 실행 시간은 2시간 이내이고
  And 개별 AI 요청은 120초 이내에 완료되고
  And Phase 2/5의 병렬 요청이 동시에 실행된다
```

### AC-10.2: 안정성 (NFR-2)

```gherkin
Given 파이프라인 실행 중 AI 프로바이더 1개가 장애 상태일 때
When 해당 프로바이더에 요청이 발생하면
Then 폴백 AI로 자동 전환하여 파이프라인을 계속 실행하고
  And 장애 프로바이더 우회 사실을 로깅한다
```

### AC-10.3: 사용성 (NFR-3)

```gherkin
Given 사용자가 파이프라인을 실행할 때
Then CLI는 현재 단계, AI 에이전트 이름, 경과 시간을 실시간으로 표시하고
  And Rich 프로그레스 바로 진행률을 시각화하고
  And 에러 발생 시 한국어로 사용자 친화적 메시지를 출력한다
```

### AC-10.4: 확장성 (NFR-4)

```gherkin
Given 새로운 Phase 6을 추가하려 할 때
When 개발자가 AbstractPhase를 상속한 Phase6 클래스를 생성하고
  And 설정 파일에 Phase 6을 등록하면
Then 오케스트레이터가 자동으로 Phase 6을 인식하고 실행한다
```

---

## 11. 엣지 케이스 검증

### AC-11.1: Proxima 미실행 (EC-1)

```gherkin
Given Proxima 게이트웨이가 실행되지 않고 있을 때
When 사용자가 "aigenflow run" 명령을 실행하면
Then 시스템은 "Proxima Gateway에 연결할 수 없습니다. Proxima를 먼저 실행해주세요." 에러를 출력하고
  And 파이프라인을 시작하지 않는다
```

### AC-11.2: 가비지 AI 응답 (EC-3)

```gherkin
Given AI가 파싱 불가능한 응답을 반환했을 때
When 응답 유효성 검사에서 실패하면
Then 시스템은 동일 프로바이더에 재시도하고
  And 재시도 실패 시 폴백 AI로 전환하고
  And 모든 시도 실패 시 Phase를 FAILED로 처리한다
```

### AC-11.3: 빈 사용자 입력 (EC-9)

```gherkin
Given 사용자가 빈 문자열로 topic을 지정했을 때
When "aigenflow run --topic ''" 명령을 실행하면
Then 시스템은 "주제를 10자 이상 입력해주세요" 에러를 표시하고
  And 파이프라인을 시작하지 않는다
```

### AC-11.4: 매우 긴 AI 응답 (EC-8)

```gherkin
Given AI가 50,000자를 초과하는 응답을 반환했을 때
Then 시스템은 응답을 50,000자로 자르고
  And 잘림 경고를 로깅한다
```

---

## 12. 품질 게이트 기준 (Definition of Done)

### 코드 품질

- [ ] 전체 테스트 커버리지 85% 이상
- [ ] ruff 린트 에러 0개
- [ ] mypy 타입 에러 0개
- [ ] black 포맷팅 적용 완료

### 기능 완성

- [ ] 5개 파이프라인 단계 모두 실행 가능
- [ ] CLI 명령 5개 (run, check, status, resume, config) 모두 작동
- [ ] 폴백 AI 매핑 정상 작동
- [ ] 상태 저장/복원 (resume) 정상 작동

### 문서화

- [ ] 사용자 가이드 (README.md) 작성
- [ ] API 문서 (주요 클래스/함수 docstring)
- [ ] 설정 파일 예제 (config/default.yaml)

### 통합 검증

- [ ] Proxima Gateway 연동 E2E 테스트 통과
- [ ] 전체 파이프라인 E2E 실행 성공
- [ ] 출력 사업 계획서 구조 검증

---

## 추적 태그

| TAG | 연결 |
|-----|------|
| SPEC-PIPELINE-001 | spec.md, plan.md |
| US-1 ~ US-6 | spec.md 사용자 스토리 |
| FR-1 ~ FR-5 | spec.md 기능 요구사항 |
| NFR-1 ~ NFR-5 | spec.md 비기능 요구사항 |
| EC-1 ~ EC-9 | spec.md 엣지 케이스 |
| AC-1.1 ~ AC-11.4 | 본 문서 인수 조건 |

---

**작성자**: manager-spec agent
**최종 업데이트**: 2026-02-15
**검증 방법**: pytest + pytest-asyncio + aiohttp 목 서버
