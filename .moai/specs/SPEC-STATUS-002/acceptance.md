# SPEC-STATUS-002: 인수 조건 (Acceptance Criteria)

## 1. 기능 인수 조건

### 1.1 CLI 명령 완성 (FR-1)

#### AC-1.1: `aigenflow check` 명령

**Given** Playwright 브라우저가 설치되어 있고 4개 AI 프로바이더 세션이 설정되어 있을 때
**When** 사용자가 `aigenflow check` 명령을 실행하면
**Then** 시스템은 다음 정보를 Rich Table 형식으로 표시해야 한다:
- Playwright Browser 상태 (Installed/Not Installed)
- ChatGPT 세션 상태 (Available/Expired/Not Setup)
- Claude 세션 상태 (Available/Expired/Not Setup)
- Gemini 세션 상태 (Available/Expired/Not Setup)
- Perplexity 세션 상태 (Available/Expired/Not Setup)

```bash
# 예상 출력
$ aigenflow check

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Component         ┃ Status   ┃ Details             ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Playwright Browser│ ✅ OK    │ Chromium 1.49.0     │
│ ChatGPT Session   │ ✅ OK    │ Last login: 2h ago  │
│ Claude Session    │ ⚠️ Expired│ Re-login required   │
│ Gemini Session    │ ✅ OK    │ Last login: 1d ago  │
│ Perplexity Session│ ❌ Not Setup│ Run aigenflow setup│
└───────────────────┴──────────┴────────────────────┘
```

#### AC-1.2: `aigenflow setup` 명령

**Given** 처음 설치된 환경에서
**When** 사용자가 `aigenflow setup` 명령을 실행하면
**Then** 시스템은 다음 절차를 따라야 한다:
1. 헤드드 모드로 Chromium 브라우저 실행
2. ChatGPT 로그인 페이지 표시 및 사용자 입력 대기
3. Enter 입력 후 프로필 저장
4. Claude 로그인 페이지 표시 및 사용자 입력 대기
5. Enter 입력 후 프로필 저장
6. Gemini 로그인 페이지 표시 및 사용자 입력 대기
7. Enter 입력 후 프로필 저장
8. Perplexity 로그인 페이지 표시 및 사용자 입력 대기
9. Enter 입력 후 프로필 저장
10. 모든 프로바이더 설정 완료 메시지 출력

#### AC-1.3: `aigenflow relogin [PROVIDER]` 명령

**Given** 특정 AI 프로바이더의 세션이 만료되었을 때
**When** 사용자가 `aigenflow relogin claude` 명령을 실행하면
**Then** 시스템은:
1. 헤드드 모드로 브라우저 실행
2. Claude 로그인 페이지 표시
3. 사용자 로그인 완료 대기
4. 프로필 저장
5. "Claude session renewed" 메시지 출력

**Edge Case**: 프로바이더를 지정하지 않으면 대화형 선택지 표시

#### AC-1.4: `aigenflow status [SESSION_ID]` 명령

**Given** 파이프라인 실행이 완료되었거나 진행 중일 때
**When** 사용자가 `aigenflow status` 명령을 실행하면 (SESSION_ID 미지정)
**Then** 시스템은 최근 5개 세션의 목록을 표시해야 한다:
- Session ID
- 상태 (Completed/Failed/Running)
- 주제 (Topic)
- 생성 시간

**Given** 특정 SESSION_ID를 지정했을 때
**When** 사용자가 `aigenflow status abc-123` 명령을 실행하면
**Then** 시스템은 해당 세션의 상세 정보를 표시해야 한다:
- 전체 상태
- 각 Phase별 상태 및 결과 요약
- 소요 시간
- 출력 파일 경로

#### AC-1.5: `aigenflow resume SESSION_ID` 명령

**Given** 중단된 파이프라인 세션이 있을 때
**When** 사용자가 `aigenflow resume abc-123` 명령을 실행하면
**Then** 시스템은:
1. 세션 상태 파일 로드
2. 마지막 성공 단계 다음부터 재개
3. 진행 상황 실시간 표시

**Option**: `--from-phase 3` 플래그로 특정 단계부터 재시작

#### AC-1.6: `aigenflow config show` 명령

**When** 사용자가 `aigenflow config show` 명령을 실행하면
**Then** 시스템은 현재 설정을 YAML 형식으로 표시해야 한다:
- 프로바이더 설정
- 출력 경로
- 언어 설정
- 템플릿 설정

#### AC-1.7: `aigenflow config set KEY VALUE` 명령

**Given** 유효한 설정 키와 값일 때
**When** 사용자가 `aigenflow config set language en` 명령을 실행하면
**Then** 시스템은:
1. 설정 값 검증
2. 설정 파일 업데이트
3. "Config updated: language = en" 메시지 출력

**Edge Case**: 유효하지 않은 키/값이면 에러 메시지 및 사용 가능한 키 목록 표시

### 1.2 Phase 모듈 분리 (FR-2)

#### AC-2.1: BasePhase 추상 클래스

**Given** BasePhase 추상 클래스가 정의되어 있을 때
**When** 개발자가 새로운 Phase 클래스를 구현할 때
**Then** 다음 메서드를 구현해야 한다:
- `get_tasks()`: list[tuple[str, str]] - (task_name, agent_type) 튜플 목록 반환
- `execute(context)`: PhaseResult - 비동기 실행 및 결과 반환
- `validate_result(result)`: bool - 결과 검증

#### AC-2.2: Phase 1-5 독립 실행

**Given** 각 Phase가 독립적인 파일로 분리되어 있을 때
**When** 개발자가 Phase 1만 단위 테스트하면
**Then** 다음 조건을 충족해야 한다:
- `tests/pipeline/test_phase1.py`가 존재
- Mock Agent 응답으로 Phase 로직 테스트 가능
- 다른 Phase의 의존성 없이 실행 가능

#### AC-2.3: Orchestrator Phase 조정

**Given** Orchestrator가 분리된 Phase들을 사용할 때
**When** 파이프라인이 실행되면
**Then** Orchestrator는 다음 책임만 담당해야 한다:
- Phase 인스턴스 생성 및 관리
- Phase 순차적 실행 조정
- 컨텍스트 체인 관리
- 상태 영속화 (단계 완료 시)
- Phase 자체의 로직은 각 Phase 파일에 존재

### 1.3 Rich UI 개선 (FR-3)

#### AC-3.1: Progress Bar 표시

**Given** 파이프라인이 실행 중일 때
**When** 사용자가 터미널을 보면
**Then** 다음 정보가 Rich Progress Bar로 표시되어야 한다:
- 전체 진행률 (0-100%)
- 현재 실행 중인 Phase 번호 및 이름
- 현재 사용 중인 AI 에이전트
- 경과 시간

```
Phase 3: Strategy (ChatGPT)  ████████████░░░░░░░░  60%  [3m 24s]
```

#### AC-3.2: 실시간 로그 스트림

**Given** 파이프라인이 실행 중일 때
**When** AI 에이전트가 응답을 반환하면
**Then** Rich Panel로 실시간 로그가 표시되어야 한다:
- 로그 레벨 (INFO/ERROR/DEBUG)
- 타임스탬프
- 메시지 내용

```
╭─────────────────────────────────────────────────╮
│ [INFO] 2026-02-16 10:24:15                       │
│ Phase 3: Task 'swot_analysis' assigned to ChatGPT │
│ Response received (1247 tokens, 15.3s)           │
╰─────────────────────────────────────────────────╯
```

#### AC-3.3: Phase 완료 요약

**Given** Phase가 완료되었을 때
**When** 다음 Phase가 시작되기 전에
**Then** Rich Table로 완료된 Phase의 요약이 표시되어야 한다:
- Phase 번호 및 이름
- 사용된 AI 에이전트들
- 소요 시간
- 상태 (Completed/Failed)
- 주요 결과 요약 (2-3문장)

## 2. 비기능 인수 조건

### 2.1 사용성 (NFR-1)

#### AC-NFR-1.1: 한글 도움말

**When** 사용자가 `aigenflow --help` 또는 `aigenflow run --help`를 실행하면
**Then** 모든 도움말 텍스트가 한국어로 표시되어야 한다

#### AC-NFR-1.2: 에러 메시지 사용자 친화화

**Given** 에러가 발생했을 때
**When** 사용자에게 에러가 표시되면
**Then** 다음 정보가 포함되어야 한다:
- 사용자 친화적 에러 설명 (기술적 용어 최소화)
- 가능한 원인 (2-3가지)
- 복구 방법 (구체적인 명령 또는 절차)
- 기술적 스택 트레이스는 `--debug` 플래그 시에만 표시

### 2.2 모듈성 (NFR-2)

#### AC-NFR-2.1: Phase 단위 독립성

**Given** 5개 Phase가 각각 독립적인 파일로 분리되어 있을 때
**When** 개발자가 Phase 3의 로직을 수정하면
**Then** 다른 Phase (1, 2, 4, 5)의 동작에는 영향이 없어야 한다
- 단위 테스트로 검증 가능
- Phase 3만 다시 빌드/테스트 가능

#### AC-NFR-2.2: 템플릿 확장성

**Given** 새로운 프롬프트 템플릿을 추가할 때
**When** 개발자가 `src/templates/prompts/phase_6/new_template.jinja2`를 추가하면
**Then** 코드 수정 없이 템플릿이 로드되어야 한다

### 2.3 테스트 가능성 (NFR-3)

#### AC-NFR-3.1: Phase 단위 테스트 커버리지

**Given** 모든 Phase가 분리되어 있을 때
**When** 단위 테스트를 실행하면
**Then** 각 Phase의 커버리지가 85% 이상이어야 한다

#### AC-NFR-3.2: CLI 명령 통합 테스트

**Given** 모든 CLI 명령이 구현되어 있을 때
**When** 통합 테스트를 실행하면
**Then** 다음 시나리오가 통과해야 한다:
- setup → check → run → status → config show

## 3. 엣지 케이스 및 시나리오

### 3.1 엣지 케이스

| ID | 시나리오 | 예상 동작 |
|----|---------|----------|
| EC-CLI-1 | `check` 실행 중 Playwright 미설치 | "Playwright not installed. Run: playwright install chromium" |
| EC-CLI-2 | `status` 실행 중 세션 없음 | "No sessions found. Run: aigenflow run" |
| EC-CLI-3 | `resume` 실행 중 세션 ID 없음 | "Session not found: abc-123" |
| EC-CLI-4 | `config set` 실행 중 잘못된 키 | "Invalid key: foo. Available keys: language, output_dir..." |
| EC-PHASE-1 | Phase 실행 중 AI 응답 타임아웃 | 폴백 AI로 자동 전환 |
| EC-PHASE-2 | Phase 실행 중 모든 AI 실패 | 파이프라인 중단 및 상태 저장 |
| EC-UI-1 | 터미널 크기 매우 작음 (80x24) | Progress Bar 최소화 모드 |
| EC-UI-2 | 로그 출력이 너무 빠름 | 로그 throttling (최대 10건/초) |

### 3.2 Given-When-Then 시나리오

#### Scenario 1: 처음 사용자 설정 흐름

**Given** 처음 AigenFlow를 설치한 사용자가 있을 때
**When** 사용자가 다음 명령을 순서대로 실행하면:
1. `aigenflow setup` - 모든 프로바이더 로그인 완료
2. `aigenflow check` - 모든 상태 Available 표시
3. `aigenflow run --topic "AI SaaS 스타트업"` - 파이프라인 실행 시작
4. `aigenflow status <session_id>` - 진행 상황 확인

**Then** 모든 단계가 오류 없이 완료되어야 한다

#### Scenario 2: 세션 만료 후 재로그인

**Given** 30일 전에 설정한 세션이 만료되었을 때
**When** 사용자가 `aigenflow run`을 실행하면
**Then** 시스템은:
1. 세션 만료 감지
2. "Claude session expired. Run: aigenflow relogin claude" 메시지
3. 사용자가 `aigenflow relogin claude` 실행
4. 파이프라인 계속 실행

#### Scenario 3: 파이프라인 중단 후 재개

**Given** Phase 3 실행 중 네트워크 오류로 파이프라인이 중단되었을 때
**When** 사용자가 `aigenflow resume <session_id>`를 실행하면
**Then** 시스템은:
1. Phase 2까지 완료된 상태 복원
2. Phase 3부터 재시작
3. 완료 시 전체 문서 생성

## 4. 성능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| CLI 명령 응답 시간 | < 2초 (setup 제외) | time 명령으로 측정 |
| Progress Bar 업데이트 | 최대 10회/초 | 터미널 출력 빈도 |
| Phase 단위 테스트 실행 시간 | < 30초/Phase | pytest --durations |
| 전체 파이프라인 실행 시간 | < 2시간 | Orchestrator 로그 |

---

**작성자**: MoAI Plan Team
**최종 업데이트**: 2026-02-16
