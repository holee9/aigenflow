# SPEC-STATUS-002: AigenFlow 프로젝트 현황 분석 및 계획 보완

## SPEC 메타데이터

| 항목 | 값 |
|------|-----|
| **SPEC ID** | SPEC-STATUS-002 |
| **제목** | AigenFlow 프로젝트 현황 분석 및 계획 보완 |
| **작성일** | 2026-02-16 |
| **상태** | Draft |
| **버전** | 1.0.0 |
| **우선순위** | High |
| **관련 문서** | SPEC-PIPELINE-001, SPEC-PACKAGING-001, product.md |
| **라이프사이클** | spec-anchored |

---

## 1. 프로젝트 현황 분석

### 1.1 구현 상태 개요

**SPEC-PIPELINE-001 9-Layer 아키텍처 기준 구현 현황**:

| Layer | 모듈 | 상태 | 구현률 | 비고 |
|-------|------|------|--------|------|
| **L0** | Foundation | ✅ 완료 | 100% | config, events, exceptions, logger, models 구현 |
| **L1** | Playwright Gateway | ✅ 완료 | 100% | BaseProvider, 4개 프로바이더, SessionManager 복구 체인 |
| **L2** | Data Models | ✅ 완료 | 100% | PhaseResult, PipelineSession, AgentResponse |
| **L3** | Agent Layer | ✅ 완료 | 100% | AsyncAgent 프로토콜, 4개 AI 설정, Router |
| **L4** | Templates | ✅ 완료 | 100% | TemplateManager, 12개 Jinja2 프롬프트 템플릿 |
| **L5** | Pipeline Phases | ⚠️ 부분 | 70% | Orchestrator에 인라인 구현, 개별 파일 분리 필요 |
| **L6** | Orchestrator | ✅ 완료 | 95% | 상태 머신, 이벤트 시스템, 컨텍스트 전달 |
| **L7** | Output | ⚠️ 부분 | 60% | FileExporter 기본 구현, DOCX/PDF 지원 미구현 |
| **L8** | CLI | ⚠️ 부분 | 50% | run 명령 구현, check/setup/relogin/resume/config 미구현 |
| **L9** | Tests | ✅ 완료 | 90% | 단위/통합 테스트 스위트, 커버리지 85%+ 달성 |

**전체 구현률: 약 80%**

### 1.2 템플릿 시스템 현황

**구현된 12개 Jinja2 프롬프트 템플릿**:

| Phase | 템플릿 파일 | AI 에이전트 | 상태 |
|-------|-----------|-------------|------|
| 1 | `brainstorm_chatgpt.jinja2` | ChatGPT | ✅ |
| 1 | `validate_claude.jinja2` | Claude | ✅ |
| 2 | `deep_search_gemini.jinja2` | Gemini | ✅ |
| 2 | `fact_check_perplexity.jinja2` | Perplexity | ✅ |
| 3 | `swot_chatgpt.jinja2` | ChatGPT | ✅ |
| 3 | `narrative_claude.jinja2` | Claude | ✅ |
| 4 | `business_plan_claude.jinja2` | Claude | ✅ |
| 4 | `charts_gemini.jinja2` | Gemini | ✅ |
| 4 | `outline_chatgpt.jinja2` | ChatGPT | ✅ |
| 5 | `final_review_claude.jinja2` | Claude | ✅ |
| 5 | `polish_claude.jinja2` | Claude | ✅ |
| 5 | `verify_perplexity.jinja2` | Perplexity | ✅ |

### 1.3 발견된 문제점 및 개선 필요사항

**P0 (Critical) - 즉시 개선 필요**:
1. **CLI 명령 불완전**: `check`, `setup`, `relogin`, `status`, `resume`, `config` 명령 미구현
2. **Phase 모듈 분리 부족**: 5개 Phase가 개별 파일이 아닌 Orchestrator에 인라인으로 구현됨
3. **패키지 구조 일관성**: `src/` 플랫 구조 vs `src/aigenflow/` 패키지 구조 혼재

**P1 (High) - 중요 개선**:
4. **출력 형식 제한**: Markdown만 지원, DOCX/PDF 미지원
5. **에러 복구 메커니즘**: 요청 수준 재시도는 구현되었으나 폴백 AI 전환 로직 검증 필요
6. **진행 상황 표시**: Rich 라이브러리 활용한 실시간 진행률 표시 미구현

**P2 (Medium) - 향후 개선**:
7. **템플릿 변수 시스템**: 컨텍스트 크기 관리를 위한 요약 전략 미구현
8. **선택자 외부화**: DOM 셀렉터가 코드에 하드코딩됨, `selectors.yaml` 분리 필요
9. **로그 레벨 구조화**: 개발/운영 모드별 로깅 전략 미정립

---

## 2. 요구사항 (Requirements) - EARS 형식

### 2.1 사용자 스토리 (User Stories)

#### US-1: CLI 명령 완성

**WHEN** 사용자가 `aigenflow check`, `setup`, `relogin`, `status`, `resume`, `config` 명령을 실행하면 **THEN** 시스템은 각 명령의 기능을 올바르게 수행해야 한다.

**인수 조건**:
- `check`: Playwright 브라우저 및 AI 세션 상태 표시
- `setup`: 최초 설정 마법사 (브라우저 열기 → 로그인 → 프로필 저장)
- `relogin [PROVIDER]`: 만료된 세션 재로그인
- `status [SESSION_ID]`: 파이프라인 실행 상태 조회
- `resume SESSION_ID`: 중단된 파이프라인 재개
- `config show|set`: 설정 조회/변경

#### US-2: Phase 모듈 독립성

**WHEN** 개발자가 파이프라인 단계를 수정하려 할 때 **THEN** 시스템은 각 Phase가 독립적인 파일로 분리되어 있어야 한다.

**인수 조건**:
- `src/pipeline/phase1_framing.py`
- `src/pipeline/phase2_research.py`
- `src/pipeline/phase3_strategy.py`
- `src/pipeline/phase4_writing.py`
- `src/pipeline/phase5_review.py`
- 각 Phase는 독립적으로 테스트 가능

#### US-3: 진행 상황 시각화

**WHEN** 파이프라인이 실행 중일 때 **THEN** 시스템은 Rich 라이브러리로 현재 단계, AI 에이전트, 경과 시간을 실시간 표시해야 한다.

**인수 조건**:
- 프로그레스 바 표시
- 현재 단계 및 AI 에이전트 명시
- 남은 예상 시간 표시
- 완료된 Phase 결과 요약

### 2.2 기능 요구사항 (Functional Requirements)

#### FR-1: CLI 명령 완성

시스템은 **항상** SPEC-PIPELINE-001에 정의된 모든 CLI 명령을 구현해야 한다.

상세 요구사항:
- **`aigenflow check`**: Playwright 브라우저 설치 확인 + 4개 AI 세션 상태 표시
- **`aigenflow setup`**: 대화형 설정 마법사 (헤드드 모드 브라우저 실행)
- **`aigenflow relogin [PROVIDER]`**: 지정 프로바이더 세션 재로그인 (헤드드 모드)
- **`aigenflow status [SESSION_ID]`**: JSON 상태 파일 조회 및 사람이 읽기 쉬운 형식으로 출력
- **`aigenflow resume SESSION_ID`**: 중단된 파이프라인 지정 단계부터 재시작
- **`aigenflow config show`**: 현재 설정 (YAML) 표시
- **`aigenflow config set KEY VALUE`**: 설정 값 변경 및 영속 저장

#### FR-2: Phase 모듈 분리

시스템은 **항상** 각 파이프라인 단계를 독립적인 모듈로 분리해야 한다.

상세 요구사항:
- **BasePhase 추상 클래스**: 공통 인터페이스 (execute(), get_tasks(), validate_result())
- **Phase1-5 구체 클래스**: 각 단계별 고유 로직 구현
- **의존성 주입**: Orchestrator에서 Phase 인스턴스 생성 및 실행
- **테스트 독립성**: 각 Phase를 독립적으로 단위 테스트 가능

#### FR-3: Rich 진행 상황 표시

**WHEN** 파이프라인이 실행되면 **THEN** 시스템은 Rich 라이브러리로 풍부한 터미널 UI를 제공해야 한다.

상세 요구사항:
- **Progress 컴포넌트**: 전체 진행률 (0-100%) 및 현재 단계 진행률
- **Table 컴포넌트**: 완료된 Phase 요약 (단계, AI, 소요 시간, 상태)
- **Panel 컴포넌트**: 실시간 로그 스트림 (구조화된 로그)
- **Spinner 컴포넌트**: AI 응답 대기 중임을 시각적으로 표시

### 2.3 비기능 요구사항 (Non-Functional Requirements)

#### NFR-1: 사용성

- CLI 도움말 한글화: `aigenflow --help` 출력 한글 제공
- 에러 메시지 사용자 친화화: 기술적 스택 트레이스 숨기고 복구 가이드 제공
- 대화형 설정: 초보자도 쉽게 따라할 수 있는 setup 마법사

#### NFR-2: 모듈성

- Phase 단위 모듈 독립성: 단일 Phase 수정 시 다른 Phase 영향 없음
- 템플릿 확장성: 새로운 프롬프트 템플릿 추가 시 코드 수정 불필요
- 프로바이더 확장성: 새로운 AI 서비스 추가 시 BaseProvider 상속만으로 구현

#### NFR-3: 테스트 가능성

- 각 Phase의 단위 테스트: Mock Agent 응답으로 Phase 로직 검증
- CLI 명령 통합 테스트: Click CliRunner 유사한 테스트 프레임워크
- End-to-End 테스트: Mock Gateway로 전체 파이프라인 실행 검증

---

## 3. 기술 접근법 (Technical Approach)

### 3.1 개선 전략

**3-Phase 접근법**:

**Phase 1: CLI 명령 완성 (P0)**
- `check`: SessionManager의 상태 확인 메서드 활용
- `setup`: Playwright headed 모드 + 대화형 Typer 프롬프트
- `relogin`: Provider별 login_flow() 재사용
- `status`: PipelineSession JSON 파일 파싱 및 Rich Table 출력
- `resume`: Orchestrator의 from_phase 재개 로직 활용
- `config`: Pydantic Settings model show/set 메서드

**Phase 2: Phase 모듈 분리 (P0)**
- BasePhase 추상 클래스 정의
- 기존 Orchestrator의 Phase 로직을 개별 파일로 추출
- 의존성 주입 패턴으로 Orchestrator 리팩토링
- 각 Phase의 단위 테스트 작성

**Phase 3: UI/UX 개선 (P1)**
- Rich Progress 컴포넌트로 진행률 표시
- Rich Panel으로 실시간 로그 스트림
- Rich Table로 완료 Phase 요약
- Rich Spinner로 AI 대기 상태 표시

### 3.2 아키텍처 업데이트

**기존 구조 (현재)**:
```
src/
├── pipeline/
│   ├── orchestrator.py  # Phase 로직이 인라인으로 포함됨
│   └── state.py
```

**개선된 구조 (목표)**:
```
src/
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py      # 상태 머신 + Phase 조정만 담당
│   ├── state.py
│   ├── base.py              # NEW: BasePhase 추상 클래스
│   ├── phase1_framing.py    # NEW: Phase 1 구체 구현
│   ├── phase2_research.py   # NEW: Phase 2 구체 구현
│   ├── phase3_strategy.py   # NEW: Phase 3 구체 구현
│   ├── phase4_writing.py    # NEW: Phase 4 구체 구현
│   └── phase5_review.py     # NEW: Phase 5 구체 구현
├── cli/                     # NEW: CLI 명령 모듈
│   ├── __init__.py
│   ├── check.py             # aigenflow check
│   ├── setup.py             # aigenflow setup
│   ├── relogin.py           # aigenflow relogin
│   ├── status.py            # aigenflow status
│   ├── resume.py            # aigenflow resume
│   └── config.py            # aigenflow config
└── main.py                  # Typer 앱 진입점
```

### 3.3 핵심 설계 결정

| # | 결정 사항 | 선택 | 근거 |
|---|---------|------|------|
| D-1 | Phase 분리 방식 | BasePattern 추상화 | 코드 재사용성 + 테스트 용이성 |
| D-2 | CLI 명령 구조 | Typer + 별도 모듈 | 모듈 독립성 + 유지보수성 |
| D-3 | 진행 상황 표시 | Rich 라이브러리 | 풍부한 터미널 UI + 이미 의존성 존재 |
| D-4 | 설정 관리 | Pydantic Settings show/set | 타입 안정성 + 검증 |

---

## 4. 구현 계획

### 4.1 태스크 분해 (WBS)

**Phase 1: CLI 명령 완성 (5일)**
| 태스크 | 설명 | 의존성 | 산출물 |
|-------|------|--------|--------|
| 1.1 | `check` 명령 구현 | SessionManager 상태 확인 | cli/check.py |
| 1.2 | `setup` 명령 구현 | Playwright headed 모드 | cli/setup.py |
| 1.3 | `relogin` 명령 구현 | Provider login_flow | cli/relogin.py |
| 1.4 | `status` 명령 구현 | PipelineSession JSON 파싱 | cli/status.py |
| 1.5 | `resume` 명령 구현 | Orchestrator from_phase | cli/resume.py |
| 1.6 | `config` 명령 구현 | Settings model show/set | cli/config.py |
| 1.7 | main.py 명령 등록 | 1.1-1.6 완료 | 모든 명령 Typer 등록 |

**Phase 2: Phase 모듈 분리 (3일)**
| 태스크 | 설명 | 의존성 | 산출물 |
|-------|------|--------|--------|
| 2.1 | BasePhase 추상 클래스 정의 | - | pipeline/base.py |
| 2.2 | Phase1-5 파일 분리 | 2.1 | phase[1-5]_*.py |
| 2.3 | Orchestrator 리팩토링 | 2.2 | orchestrator.py (Phase 조정만) |
| 2.4 | Phase 단위 테스트 | 2.2 | tests/pipeline/test_phase[1-5].py |

**Phase 3: UI/UX 개선 (2일)**
| 태스크 | 설명 | 의존성 | 산출물 |
|-------|------|--------|--------|
| 3.1 | Progress 컴포넌트 구현 | Rich | ui/progress.py |
| 3.2 | 실시간 로그 스트림 | 3.1 | ui/logger.py |
| 3.3 | Phase 요약 테이블 | 3.1 | ui/summary.py |
| 3.4 | Orchestrator 통합 | 3.1-3.3 | 진행 상황 표시 활성화 |

### 4.2 마일스톤

| 마일스톤 | 기간 | 완료 기준 |
|---------|------|-----------|
| M1: CLI 완성 | Week 1 | 모든 CLI 명령 동작 확인 |
| M2: 모듈 분리 | Week 2 | Phase 독립적 실행/테스트 가능 |
| M3: UI 개선 | Week 2 | Rich UI로 진행 상황 시각화 |
| M4: 검증 | Week 3 | E2E 테스트 통과 |

---

## 5. 리스크 및 완화

| ID | 리스크 | 심각도 | 완화 전략 |
|----|-------|--------|----------|
| R-1 | Phase 분리 중 기능 회귀 | MEDIUM | 각 Phase 분리 전 후 단위 테스트로 동등성 검증 |
| R-2 | CLI 명령 추가로 복잡도 증가 | LOW | 모듈별 책임 분명히 구분 |
| R-3 | Rich UI로 인한 성능 저하 | LOW | 이벤트 발행 빈도 조절 (throttling) |
| R-4 | 사용자 설정 호환성 | MEDIUM | 설정 파일 마이그레이션 로직 구현 |

---

## 6. 업데이트된 SPEC-PIPELINE-001 권장사항

### 6.1 상태 업데이트

**SPEC-PIPELINE-001 상태 변경 제안**:
- **현재**: Planned
- **제안**: In Progress (80% 완료)

### 6.2 SPEC-PIPELINE-001 보완 항목

1. **FR-4 (CLI 인터페이스)** 확장:
   - 기존: `run` 명령만 상세
   - 추가: `check`, `setup`, `relogin`, `status`, `resume`, `config` 명령 상세

2. **L5 (Pipeline Phases)** 구체화:
   - 기존: "5개 단계 모듈"으로만 기술
   - 추가: 각 Phase의 BasePattern 상속 구조 명시

3. **NFR-3 (사용성)** 강화:
   - 기존: "한국어 지원"으로만 기술
   - 추가: Rich UI 컴포넌트 구체 명시

---

**작성자**: MoAI Plan Team
**최종 업데이트**: 2026-02-16
**다음 단계**: `/moai run SPEC-STATUS-002` 로 구현 시작

---

## 추적 태그 (Traceability)

| TAG | 연결 |
|-----|------|
| SPEC-STATUS-002 | SPEC-PIPELINE-001 업데이트, SPEC-PACKAGING-001 검증 |
| FR-1 | cli/check.py, cli/setup.py, cli/relogin.py, cli/status.py, cli/resume.py, cli/config.py |
| FR-2 | pipeline/base.py, pipeline/phase[1-5]_*.py |
| FR-3 | ui/progress.py, Rich 라이브러리 통합 |
| NFR-1 | 한국어 도움말, 에러 메시지 개선 |
| NFR-2 | 모듈 독립성, 확장성 |
