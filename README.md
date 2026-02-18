# AigenFlow

> 4개의 AI 에이전트(ChatGPT, Claude, Gemini, Perplexity)를 활용한 사업계획서/R&D 제안서 자동 생성 CLI 파이프라인

[![CI](https://github.com/holee9/aigenflow/workflows/CI/badge.svg)](https://github.com/holee9/aigenflow/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/aigenflow.svg)](https://badge.fury.io/py/aigenflow)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-73%25-yellow.svg)](https://github.com/holee9/aigenflow)

---

## 배포 상태 (Deployment Status)

| 항목 | 상태 | 비고 |
|------|------|------|
| **테스트 통과** | 866/873 (99.2%) | 핵심 기능 100% 통과 |
| **안정성 테스트** | 10/10 (100%) | BrowserPool 10회 반복 검증 |
| **코드 커버리지** | 73% | 핵심 모듈 97%+ |
| **DDD 성숙도** | 82/100 | 성숙단계 |
| **Lint 통과** | 0 errors | Ruff 검증 완료 |
| **구현 완료도** | 100% | 모든 핵심 기능 구현 |
| **PyPI 배포** | 준비 완료 | 배포 가능 |

---

## 최신 업데이트 (2026-02-18)

### 성능 최적화
- **BrowserPool 싱글톤 패턴**: 단일 브라우저 인스턴스 (~50-100MB)로 메모리 최적화
- **컨텍스트 격리**: 각 AI 프로바이더별 독립적 브라우저 컨텍스트 관리
- **지연 로딩**: 필요한 시점에 컨텍스트 생성으로 시작 시간 단축

### 안정성 개선
- **이벤트 루프 관리 강화**: 명시적 이벤트 루프 생성 및 정리
- **Windows 호환성**: 서브프로세스 정리 경고 억제
- **Graceful Shutdown**: 미완료 태스크 취소 및 정리

### 안정성 테스트 결과
- **10회 반복 테스트**: 성공률 100% (10/10)
- **평균 실행 시간**: 1.3초/회 (Mock Agent 기준)
- **결론**: BrowserPool 이벤트 루프 관리가 **안정적**임을 검증

---

## Quick Start (빠른 시작)

### 설치 (Installation)

```bash
# PyPI에서 설치 (권장)
pip install aigenflow

# 소스에서 설치 (개발용)
git clone https://github.com/holee9/aigenflow.git
cd aigenflow
pip install -e .
```

### 제거 (Uninstallation)

```bash
# 1. 패키지 제거
pip uninstall aigenflow

# 2. 생성된 문서 출력물 제거 (선택)
rm -rf output/

# 3. Playwright 브라우저 프로필 제거 (선택)
# Windows: %USERPROFILE%\.aigenflow\profiles\
# macOS/Linux: ~/.aigenflow/profiles/

# 4. 설정 파일 제거 (선택)
# Windows: %APPDATA%\aigenflow\
# macOS: ~/Library/Application Support/aigenflow/
# Linux: ~/.config/aigenflow/
```

### 사용법 (Usage)

```bash
# 1. 최초 설정 (AI 서비스 로그인)
aigenflow setup

# 2. 사업계획서 생성 (브라우저 표시됨)
aigenflow run --topic "AI 기반 스마트홈 서비스" --type bizplan --lang ko

# 3. R&D 제안서 생성 (백그라운드 실행)
aigenflow run --topic "양자 컴퓨팅 응용 연구" --type rd --lang ko --headless

# 4. 실행 상태 확인
aigenflow status
```

---

## AigenFlow란?

AigenFlow는 **하나의 CLI 명령**으로 4개의 AI 에이전트(ChatGPT, Claude, Gemini, Perplexity)가 협업하여 고품질의 사업계획서/R&D 제안서를 자동 생성하는 파이프라인 도구입니다.

### 핵심 기능

- **5단계 AI 협업 파이프라인**: 개념 프레이밍 → 심층 리서치 → 전략 설계 → 초안 작성 → 팩트체크
- **4개 AI 교차 검증**: 각 AI의 강점을 활용한 역할 분배로 신뢰도 높은 문서 생성
- **API 키 불필요**: Playwright 영구 프로필로 구독형 AI 서비스에 직접 접근
- **자동 복구 체인**: 4단계 세션 복구로 안정적인 실행 보장
- **상태 저장/재개**: 중단된 파이프라인을 마지막 성공 지점부터 재개

### 어떤 문서를 생성하나요?

| 모드 | 출력물 | 사용 사례 |
|------|--------|----------|
| `bizplan` | 사업계획서 | 스타트업 피치, 투자 유치, 사업 기획 |
| `rd` | R&D 제안서 | 연구 과제 신청, 기술 개발 계획 |

### 문서 생성 예시

```bash
aigenflow run --topic "AI 기반 스마트홈 서비스" --type bizplan --lang ko
```

위 명령 하나로:
1. ChatGPT가 아이디어를 발산하고 프레임워크를 설계
2. Gemini와 Perplexity가 병렬로 심층 리서치 수행
3. ChatGPT와 Claude가 전략과 로드맵을 설계
4. Claude가 장문의 사업계획서 본문 집필
5. Perplexity가 팩트체크하고 Claude가 최종 검증

**결과물**: `output/{session-id}/final/business_plan.md`

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

---

## CLI 사용법

### 기본 명령

```bash
# 사업계획서 생성 (기본 모드, 브라우저 표시)
aigenflow run --topic "AI SaaS 플랫폼"

# 백그라운드 실행 (브라우저 숨김)
aigenflow run --topic "AI SaaS 플랫폼" --headless

# R&D 제안서 생성
aigenflow run --type rd --topic "양자 컴퓨팅 응용 연구"

# 템플릿 지정 (startup / rd / strategy)
aigenflow run --topic "친환경 물류" --template startup

# 출력 언어 지정
aigenflow run --topic "Fintech App" --lang en

# 특정 단계부터 재개
aigenflow run --topic "AI SaaS" --from-phase 3
```

### 유틸리티 명령

```bash
# 최초 설정: 대화형 설정 마법사
aigenflow setup

# Playwright 브라우저 및 AI 세션 상태 확인
aigenflow check

# 특정 프로바이더 재로그인
aigenflow relogin claude
aigenflow relogin chatgpt
aigenflow relogin gemini
aigenflow relogin perplexity

# 실행 상태 조회
aigenflow status              # 최근 세션 목록
aigenflow status <session-id>   # 특정 세션 상세

# 중단된 파이프라인 재개
aigenflow resume <session-id>

# 설정 관리
aigenflow config show           # 설정 조회
aigenflow config list           # 설정 키 목록
aigenflow config set <key> <value>  # 설정 변경
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
| `--headed` | 브라우저 창 표시 | `true` |
| `--headless` | 백그라운드 실행 (브라우저 숨김) | `false` |

### 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `AC_DEBUG` | 디버그 모드 활성화 | `false` |
| `AC_LOG_LEVEL` | 로그 레벨 (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `AC_LOG_FORMAT` | 로그 형식 (json/pretty) | `pretty` |
| `AC_OUTPUT_DIR` | 출력 디렉토리 경로 | `output/` |
| `AC_PROFILES_DIR` | 브라우저 프로필 디렉토리 | `~/.aigenflow/profiles/` |
| `AC_GATEWAY_HEADLESS` | 브라우저 백그라운드 실행 | `false` |
| `AC_GATEWAY_TIMEOUT` | 브라우저 작업 타임아웃 (초) | `120` |
| `AC_ENABLE_PARALLEL_PHASES` | 병렬 Phase 실행 활성화 | `true` |
| `AC_ENABLE_SUMMARIZATION` | 컨텍스트 요약 활성화 | `true` |
| `AIGENFLOW_USE_BROWSER_POOL` | BrowserPool 싱글톤 사용 | `true` |

**예시:**
```bash
# BrowserPool 비활성화 (개발/디버깅용)
export AIGENFLOW_USE_BROWSER_POOL=false

# 백그라운드 실행 기본 설정
export AC_GATEWAY_HEADLESS=true

# 로그 레벨 변경
export AC_LOG_LEVEL=DEBUG
```

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

## 📊 종합 평가 결과 (2026-02-17)

### 코드 품질 평가

| 평가 차원 | 결과 | 등급 |
|-----------|------|------|
| 템플릿 일관성 | 100% | A+ ✅ |
| AI 응답 재현성 | 27.5% | D ⚠️ |
| 파이프라인 안정성 | 100% | A+ ✅ |
| **전체 등급** | **B+** | **우수** |

### DDD 성숙도 평가

| 평가 차원 | 점수 | 등급 |
|-----------|------|------|
| ANALYZE | 88/100 | 우수 |
| PRESERVE | 85/100 | 우수 |
| IMPROVE | 78/100 | 양호 |
| **전체 성숙도** | **82/100** | **성숙단계** |

### 테스트 커버리지

| 모듈 | 커버리지 | 상태 |
|------|----------|------|
| UI/모니터링/템플릿/출력 | 97-100% | 완벽 |
| 파이프라인/코어/게이트웨이 | 86-98% | 우수 |
| **전체 커버리지** | **73%** | **양호** |

**핵심 메시지**: AigenFlow는 안정적이고 신뢰할 수 있는 시스템입니다. AI 응답의 낮은 재현성은 창의적 문서 생성을 위한 설계 결정이며, 필요 시 Temperature=0 설정으로 재현성을 80%+ 향상시킬 수 있습니다.

[종합 평가 보고서 보기 →](./docs/AigenFlow-종합평가보고서.md) | [DDD 성숙도 평가 →](./.moai/docs/DDD-MATURITY-ASSESSMENT.md) | [테스트 전략 분석 →](./TEST_STRATEGY_ANALYSIS.md)

### 프로젝트 비전

이 파이프라인의 출력물(사업계획서/R&D 제안서)은 이후 AI 에이전트들이 실제 프로젝트를 구현해 나가는 **입력 SPEC**으로 활용됩니다.

```
[AigenFlow 파이프라인]              [AI 에이전트 구현]
 주제 입력 --> 5단계 AI 협업 -->  문서.md  -->  프로젝트 빌드
              (ChatGPT/Claude/           (문서를 SPEC으로 삼아
               Gemini/Perplexity)         AI가 실제 구현)
```

---

## 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.11+ |
| CLI | Typer + Rich | 0.12+ / 13.0+ |
| AI 게이트웨이 | Playwright (BrowserPool 싱글톤) | 1.49+ |
| 데이터 검증 | Pydantic | 2.9+ |
| 프롬프트 템플릿 | Jinja2 | 3.1+ |
| 로깅 | structlog | 24.0+ |
| 테스트 | pytest + pytest-asyncio | 8.0+ / 0.23+ |

### BrowserPool 아키텍처 (2026-02-18 개선)

- **메모리 최적화**: 단일 브라우저 인스턴스 (~50-100MB) 사용
- **컨텍스트 격리**: 각 AI 프로바이더별 독립적 브라우저 컨텍스트
- **라이프사이클 관리**: 명시적 초기화 및 정리
- **스레드 안전성**: asyncio.Lock으로 경쟁 조건 방지 |

---

## 시스템 요구사항

| 항목 | 요구사항 |
|------|----------|
| OS | Windows 10/11, macOS, Linux |
| Python | 3.11 이상 |
| 브라우저 | Chrome (Windows) 또는 Chromium (macOS/Linux) |
| AI 구독 | ChatGPT, Claude, Gemini, Perplexity 유료 구독 |

---

## 프로젝트 구조

```
AigenFlow/
├── src/                            # Python 코어 파이프라인
│   ├── main.py                     # CLI 진입점 (Typer)
│   ├── cli/                        # CLI 유틸리티 명령
│   ├── pipeline/                   # 5단계 파이프라인
│   ├── agents/                     # AI 에이전트 라우팅
│   ├── gateway/                    # Playwright AI Gateway
│   ├── core/                       # 설정, 이벤트, 예외, 로깅
│   ├── ui/                         # Rich UI 컴포넌트
│   ├── templates/                  # Jinja2 프롬프트 + 출력 템플릿
│   └── output/                     # 포매팅 + 파일 내보내기
├── tests/                          # 테스트 스위트
├── docs/                           # 문서 및 평가 보고서
└── .moai/                          # MoAI 설정 및 SPEC 문서
```

---

## 개발자를 위한 정보

### 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 확인
pytest tests/ --cov=src --cov-report=term-missing

# 특정 테스트만 실행
pytest tests/test_main.py -v
```

### 패키지 빌드

```bash
# 빌드
python -m build

# 배포 (PyPI)
twine upload dist/*
```

---

## 🗺️ 로드맵 (Roadmap)

AigenFlow는 현재 **안정화 단계**에 있으며, 다음과 같은 개선 계획을 가지고 있습니다.

### 현재 상태 (v0.1.0)
- ✅ 5단계 파이프라인 완전 구현
- ✅ 4개 AI 프로바이더 지원 (ChatGPT, Claude, Gemini, Perplexity)
- ✅ BrowserPool 싱글톤 메모리 최적화
- ✅ 이벤트 루프 라이프사이클 관리
- ✅ PyPI 배포 준비 완료

### Phase 1: 품질 기반 (1-2주) 🔴

**목표**: TRUST 5 품질 기준 충족 (커버리지 85%+)

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| 테스트 커버리지 향상 | agents/, gateway/, pipeline/ 모듈 테스트 추가 | 8-12시간 |
| Docstring 추가 | API 문서 기반 확보 | 4-6시간 |

### Phase 2: 문서화 강화 (2-3주) 🟡

**목표**: 사용자 및 개발자를 위한 포괄적인 문서 제공

| 작업 | 산출물 | 예상 시간 |
|------|--------|----------|
| API 문서 | docs/api/*.md (Sphinx/MkDocs) | 6-8시간 |
| 사용자 가이드 | docs/guides/*.md | 4-5시간 |
| 개발자 가이드 | docs/development/*.md | 4-5시간 |

### Phase 3: 확장성 개선 (3-4주) 🟢

**목표**: 플러그인 시스템과 커스터마이제이션 용이성 확보

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| Provider 레지스트리 | 플러그인 방식 AI 프로바이더 등록 | 8-10시간 |
| Phase 레지스트리 | 커스텀 파이프라인 단계 등록 | 8-10시간 |
| 플러그인 예제 | 커스텀 프로바이더/단계 작성 가이드 | 2-3시간 |

### Phase 4: UX/성능 (선택) ⚪

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| 설정 명령어 개선 | `aigenflow config set` 구현 | 3-4시간 |
| 오류 메시지 강화 | 상세 가이드 포함 예외 | 2-3시간 |
| 진행 상황 표시 개선 | Rich UI 컴포넌트 확장 | 2-3시간 |
| 병렬화 확장 | Phase 4/5 병렬 처리 | 4-6시간 |

### 장기 비전

- **다국어 지원**: 영어, 중국어, 일본어 템플릿
- **추가 AI 프로바이더**: Anthropic, Cohere, Local LLM
- **웹 UI**: 브라우저 기반 GUI
- **클라우드 배포**: AWS/GCP 컨테이너화

---

## 라이선스

Apache-2.0
