# agent-compare

> 4개의 AI 에이전트(ChatGPT, Claude, Gemini, Perplexity)를 활용한 사업계획서/R&D 제안서 자동 생성 CLI 파이프라인

하나의 CLI 명령으로 5단계 파이프라인을 자동 실행하여, 각 AI의 강점을 교차 활용한 고품질 문서를 생성합니다. `--type` 옵션으로 사업계획서(`bizplan`)와 연구개발제안서(`rd`)를 모드 전환하여 생성할 수 있습니다.

Playwright 영구 프로필 기반으로 API 키 없이 구독형 AI 서비스에 직접 접근합니다. 최초 1회 로그인 후 세션이 자동 유지되며, 만료 시 4단계 자동 복구 체인이 동작합니다.

### 프로젝트 비전

이 파이프라인의 출력물(사업계획서/R&D 제안서)은 이후 AI 에이전트들이 실제 프로젝트를 구현해 나가는 **입력 SPEC**으로 활용됩니다.

```
[agent-compare 파이프라인]              [AI 에이전트 구현]
 주제 입력 --> 5단계 AI 협업 -->  문서.md  -->  프로젝트 빌드
              (ChatGPT/Claude/           (문서를 SPEC으로 삼아
               Gemini/Perplexity)         AI가 실제 구현)
```

---

## AI 에이전트 배치

4개 AI 에이전트 각각의 강점에 기반한 역할 분배입니다. 4개 AI의 교차검증을 통해 확정되었습니다 ([상세 근거](./final-summary.md)).

| AI | 역할 | 담당 단계 | 핵심 강점 |
|:---:|---|:---:|---|
| **ChatGPT** | 발상가 / 프레임워크 장인 | 1-A, 3-A, 4(보조) | 창의적 브레인스토밍, o3 추론, Canvas 편집 |
| **Claude** | 설계자 / 집필자 | 1-B, 3-B, **4(메인)**, 5 | 200K+ 컨텍스트, 논리적 일관성, 전문 문체 |
| **Gemini** | 리서치 군단 / 협업 허브 | **2(메인)**, 4(보조), 5(보조) | Deep Research, 1M+ 컨텍스트, Workspace 통합 |
| **Perplexity** | 팩트 라이브러리 | 2(보조), **5(메인)** | 실시간 웹 검색, 인용 정확도 90%+, 빠른 응답 |

---

## 파이프라인 동작 흐름

```
[사용자 입력: 사업 주제]
       |
       v
 --- Phase 1: 개념 프레이밍 (순차) -------------------
 |  1-A. ChatGPT  -> 아이디어 발산, BM 캔버스         |
 |  1-B. Claude   -> 후보 압축, 논리/리스크 검증       |
 -------------------------------------------------------
       |  결과 요약 -> 다음 단계 컨텍스트로 전달
       v
 --- Phase 2: 심층 리서치 (병렬) ---------------------
 |  Gemini DR     -> 100+ 소스, 범위 확장             |
 |  Perplexity DR -> 인용 정확, 핵심 수치 검증    [동시]|
 -------------------------------------------------------
       |  연구 결과 병합 -> 다음 단계 컨텍스트로 전달
       v
 --- Phase 3: 전략/로드맵 설계 (순차) ----------------
 |  3-A. ChatGPT  -> SWOT, PESTEL, 재무 시나리오      |
 |  3-B. Claude   -> 모순 제거, 서사 통합, KPI 정렬    |
 -------------------------------------------------------
       |  전략 결과 -> 다음 단계 컨텍스트로 전달
       v
 --- Phase 4: 계획서 초안 작성 (순차+병렬) -----------
 |  Claude (메인) -> 장문 계획서 본문 집필             |
 |  ChatGPT(보조) -> 투자자 요약, 피치덱              |
 |  Gemini (보조) -> 표, 그래프, 타임라인              |
 -------------------------------------------------------
       |  초안 전문 -> 다음 단계 검증 대상으로 전달
       v
 --- Phase 5: 팩트체크/최종 검수 (병렬) --------------
 |  Perplexity    -> 주장/수치/출처 인용 감사          |
 |  Claude        -> 오류 반영, 전체 재정렬       [동시]|
 |  Gemini        -> Workspace 버전관리/공유           |
 -------------------------------------------------------
       |
       v
 [완성된 문서 -> output/{session-id}/final/business_plan.md]
```

### 모드별 Phase 차이 (`--type`)

동일한 5단계 구조에서 `--type`에 따라 각 Phase의 작업 내용이 분기됩니다.

| Phase | bizplan (사업계획서) | rd (연구개발제안서) |
|:---:|---|---|
| 1 | BM 캔버스, USP, 페르소나 | 기술 과제 정의, 연구 범위, 선행 연구 |
| 2 | 시장/경쟁사/규제 조사 | 기술 문헌, 특허, 기술 동향 |
| 3 | SWOT, PESTEL, 재무 시나리오 | 기술 타당성, 연구 방법론, TRL 평가 |
| 4 | 사업 전략 서사, 투자 피치 | 연구 계획, 기대 성과, 활용 방안 |
| 5 | 시장 데이터 팩트체크 | 기술 주장 검증, 논문 인용 확인 |

### 핵심 메커니즘

| 메커니즘 | 설명 |
|---------|------|
| **Playwright 직접 접근** | Playwright 영구 프로필로 AI 웹 서비스에 직접 접근. API 키 불필요 (구독형 세션 기반) |
| **컨텍스트 체인** | 각 단계 결과가 요약되어 다음 단계 입력으로 누적 전달 (Phase 1 -> 2 -> 3 -> 4 -> 5) |
| **4단계 자동 복구** | 세션 만료 시: 리프레시 -> 재로그인(일시정지) -> 지정 폴백 -> Claude 최종 안전망 |
| **상태 저장/재개** | 매 단계 완료 시 상태를 JSON으로 저장. 실패 시 `resume` 명령으로 마지막 성공 지점부터 재개 |
| **병렬 실행** | Phase 2, 5에서 asyncio.gather()를 통한 동시 AI 호출로 실행 시간 단축 |

---

## 언어 처리 흐름

사용자는 한국어 또는 영어로 주제를 입력할 수 있습니다. 파이프라인 내부에서는 안정성을 위해 **영어**로 처리하고, 최종 출력은 사용자가 지정한 언어로 변환합니다.

> AI 웹 인터페이스 DOM 처리 시 한국어 인코딩 이슈가 확인되어, AI 프롬프트는 영어로 구성합니다.

```
[사용자 입력]                    [파이프라인 내부]                [최종 출력]

 한국어 입력                      영어로 처리                     한국어 출력
 "AI SaaS 플랫폼"  ---변환(1)--> "AI SaaS Platform" ---변환(2)--> 한국어 계획서
                                  Phase 1~5 전체 영어

 영어 입력                        영어로 처리                     영어 출력
 "AI SaaS Platform" --그대로-->  "AI SaaS Platform" --그대로-->  영어 계획서
```

### 단계별 언어 상세

| 구간 | 한국어 입력 시 | 영어 입력 시 | 이유 |
|------|:---:|:---:|---|
| 사용자 입력 | KO | EN | 사용자 편의 |
| 프롬프트 생성 (Jinja2) | **EN** (자동 변환) | EN (그대로) | DOM 인코딩 이슈 회피 |
| Phase 1~5 AI 처리 | **EN** | EN | AI 응답 안정성 |
| 컨텍스트 체인 (단계 간 전달) | **EN** | EN | 일관성 유지 |
| 최종 사업 계획서 | **KO** (변환 출력) | EN (그대로) | `--lang` 설정에 따름 |
| CLI 메시지 | KO | KO | 사용성 요구사항 |

### 언어 변환 포인트

파이프라인에서 언어 변환이 일어나는 지점은 **2곳**입니다:

```
       변환점 (1)                          변환점 (2)
          |                                   |
KO 입력 --+-- EN 프롬프트 --- EN 처리 (AI) ---+-- KO 출력
          |   Jinja2 템플릿    Phase 1~5      |   출력 템플릿
     topic 번역                         계획서 번역
```

| 변환점 | 위치 | 방향 | 방식 |
|--------|------|:---:|---|
| **(1)** | 프롬프트 생성 시 | KO -> EN | Jinja2 템플릿 내 topic 변환 |
| **(2)** | 최종 출력 시 | EN -> KO | 출력 템플릿의 번역 지시 |

---

## CLI 사용법

### 기본 명령

```bash
# 사업계획서 생성 (기본 모드)
agent-compare run --topic "AI SaaS 플랫폼"

# R&D 제안서 생성
agent-compare run --type rd --topic "양자 컴퓨팅 응용 연구"

# 템플릿 지정 (startup / rd / strategy)
agent-compare run --topic "친환경 물류" --template startup

# 출력 언어 지정
agent-compare run --topic "Fintech App" --lang en

# 특정 단계부터 재개
agent-compare run --topic "AI SaaS" --from-phase 3
```

### 유틸리티 명령

```bash
# 최초 설정: 각 AI 서비스 로그인
agent-compare setup

# Playwright 브라우저 및 AI 세션 상태 확인
agent-compare check

# 만료된 세션 재로그인
agent-compare relogin [chatgpt|claude|gemini|perplexity]

# 중단된 파이프라인 재개
agent-compare resume <session-id>

# 실행 상태 조회
agent-compare status <session-id>

# 설정 조회/변경
agent-compare config show
agent-compare config set language en
```

### CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--topic` | 사업 주제 (필수, 10자 이상) | - |
| `--type` | 문서 유형 (`bizplan` / `rd`) | `bizplan` |
| `--template` | 프롬프트 템플릿 | `default` |
| `--from-phase` | 재개 시작 단계 (1-5) | 1 |
| `--lang` | 출력 언어 | `ko` |
| `--output-dir` | 출력 디렉토리 | `output/` |

---

## 출력 결과물

```
output/<session-id>/
├── phase1/results.json          # Phase 1 개념 프레이밍 결과
├── phase2/results.json          # Phase 2 심층 리서치 결과
├── phase3/results.json          # Phase 3 전략/로드맵 결과
├── phase4/results.json          # Phase 4 초안 작성 결과
├── phase5/results.json          # Phase 5 최종 검증 결과
├── final/
│   └── business_plan.md         # 최종 사업 계획서
├── pipeline_state.json          # 파이프라인 상태 (resume용)
└── metadata.json                # 세션 메타데이터
```

---

## 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.13+ |
| CLI | Typer + Rich | 0.12+ / 13.0+ |
| AI 게이트웨이 | Playwright | 1.49+ |
| 데이터 검증 | Pydantic | 2.9+ |
| 프롬프트 템플릿 | Jinja2 | 3.1+ |
| 로깅 | structlog | 24.0+ |
| 테스트 | pytest + pytest-asyncio | 8.0+ / 0.23+ |
| 패키지 관리 | uv | latest |

---

## 시스템 요구사항

| 항목 | 요구사항 |
|------|----------|
| OS | Windows 10/11 (MINGW64 호환) |
| Python | 3.13 이상 |
| Playwright | `playwright install chromium` 으로 자동 설치 |
| 네트워크 | AI 서비스 웹사이트 접근 필요 |
| AI 구독 | ChatGPT, Claude, Gemini, Perplexity 구독 및 웹 로그인 |

---

## 프로젝트 구조

```
agent-compare/
├── src/                            # Python 코어 파이프라인
│   ├── main.py                     # CLI 진입점 (Typer)
│   ├── pipeline/                   # 5단계 파이프라인
│   │   ├── orchestrator.py         # 상태 머신 + 이벤트
│   │   ├── state.py                # PipelineState, PhaseResult
│   │   └── phase1~5_*.py           # 각 단계 모듈
│   ├── agents/                     # AI 에이전트 라우팅
│   │   ├── base.py                 # AsyncAgent Protocol
│   │   └── router.py              # (단계, 작업) -> AI 매핑
│   ├── gateway/                    # Playwright AI Gateway
│   │   ├── base.py                # BaseProvider 추상 인터페이스
│   │   ├── session.py             # SessionManager (4단계 복구 체인)
│   │   └── {provider}.py          # 서비스별 Provider 어댑터
│   ├── core/                       # 설정, 이벤트, 예외, 로깅
│   ├── templates/                  # Jinja2 프롬프트 + 출력 템플릿
│   └── output/                     # 포매팅 + 파일 내보내기
├── tests/                          # 테스트 스위트
├── docs/plans/                     # 설계 문서
├── .moai/
│   ├── specs/SPEC-PIPELINE-001/    # SPEC 문서
│   └── project/                    # 프로젝트 설계 문서
└── final-summary.md                # 4개 AI 교차검증 최종안
```

---

## 핵심 운용 원칙

| # | 원칙 | 근거 |
|:---:|---|---|
| 1 | **멀티에이전트 필수** | 단일 AI의 편향과 실패 모드를 상쇄 (4/4 AI 합의) |
| 2 | **발산 =/= 구조화** | ChatGPT=발산/프레임워크, Claude=구조화/논리/서사 (역할 분리) |
| 3 | **리서치 이중화** | 커버리지(Gemini) x 정밀도(Perplexity) 병렬로 재현성 확보 |
| 4 | **검증 가능한 형식 강제** | 모든 주장에 인용/증거 포함, 미확인 항목 명시적 표시 |

---

## 검증 기록

### 아키텍처 진화 기록

**Phase 1: Proxima 기반 검증 (2026-02-15)**
- Proxima(Electron) + 쿠키 임포트로 3-AI 영어 테스트 성공 (Perplexity 8.9s, ChatGPT 4.7s, Gemini 5.4s)
- 문제 발견: 쿠키 만료 시 수동 갱신 필요 → 자동화 파이프라인과 모순

**Phase 2: Playwright 전환 결정 (2026-02-15)**
- Proxima 제거, Playwright 영구 프로필 기반으로 전환
- 4단계 세션 자동 복구 체인 설계 (리프레시 → 재로그인 → 폴백 → Claude 안전망)
- 상세 설계: `docs/plans/2026-02-15-playwright-gateway-design.md`

**Phase 3: Playwright PoC 4개 AI 전체 검증 (2026-02-15)**
- 4개 AI 프로필 셋업 → 세션 유지 → 메시지 전송 → 응답 캡처 전과정 성공
- 검증 결과:

| AI | 계정 | 셋업 | 세션 | 전송 | 응답 | 입력 셀렉터 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Perplexity | Pro | ✅ | ✅ | ✅ | ✅ | `[role=textbox]` |
| ChatGPT 5.2 | Pro | ✅ | ✅ | ✅ | ✅ | `#prompt-textarea` |
| Gemini 3 | PRO | ✅ | ✅ | ✅ | ✅ | `.ql-editor` |
| Claude | Opus 4.6 | ✅ | ✅ | ✅ | ✅ | `[contenteditable]` |

- Cloudflare 대응: Playwright 번들 Chromium → PC 설치 Chrome (`channel="chrome"`) 전환으로 CAPTCHA 회피
- Headed 모드 필수: headless 시 Cloudflare 차단 확인 → headed + 최소화 방식 채택
- PoC 코드: `tests/poc_playwright.py`

### 알려진 제한사항

- Cloudflare가 headless 브라우저 차단 → headed 모드(+최소화)로 운영 필요
- AI 웹 인터페이스 DOM 스크래핑 시 한국어 인코딩 이슈 → AI 프롬프트는 영어 사용
- AI 서비스 DOM 구조 변경 시 셀렉터 업데이트 필요 (외부 설정 파일로 분리)
- 응답 캡처 시 UI 메뉴 텍스트 혼입 → 셀렉터 정밀화 필요

---

## 프로젝트 상태

- [x] 4개 AI 교차검증 완료 (final-summary.md)
- [x] Proxima 연동 검증 → 쿠키 만료 문제 확인 → Playwright 전환 결정
- [x] SPEC 문서 작성 완료 (SPEC-PIPELINE-001, Playwright 기반으로 업데이트)
- [x] Playwright Gateway 설계 문서 완료
- [x] Playwright PoC 검증 완료 (4개 AI 프로필/세션/전송/응답 전과정 성공)
- [ ] 코어 파이프라인 구현 (L0~L8)
- [ ] CLI 인터페이스 구현 (L8)
- [ ] 테스트 스위트 작성 (L9)
- [ ] 사용자 가이드 문서화

---

## 라이선스

Apache-2.0
