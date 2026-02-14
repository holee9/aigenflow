# Multi-AI Pipeline BizPlan

4개 AI(ChatGPT, Claude, Gemini, Perplexity)를 교차 활용하여 사업계획서와 R&D 계획서를 자동 생성하는 MoAI-ADK 스킬입니다.

## 개요

단일 AI의 한계를 넘어, 각 AI의 강점을 단계별로 조합하는 멀티에이전트 파이프라인입니다.

| AI | 역할 | 강점 |
|:---:|---|---|
| **ChatGPT** | 발상가 / 프레임워크 장인 | 창의적 발산, SWOT/PESTEL 분석, 편집 |
| **Claude** | 설계자 / 집필자 | 논리적 수렴, 장문 일관성, 전문 문체 |
| **Gemini** | 리서치 군단 | Deep Research, 100+ 소스, 표/그래프 |
| **Perplexity** | 팩트 라이브러리 | 실시간 검색, 자동 인용, 팩트체크 |

## 파이프라인 구조

```
[아이디어 입력]
    │
    ▼
Phase 1: 컨셉 프레이밍
    ChatGPT(발산) → Claude(수렴/검증)
    │
    ▼
Phase 2: 심층 리서치 (병렬)
    Gemini(범위) + Perplexity(정확도) → Claude(교차검증)
    │
    ▼
Phase 3: 전략 설계
    ChatGPT(SWOT/PESTEL) → Claude(서사 통합)
    │
    ▼
Phase 4: 계획서 초안
    Claude(본문 집필) + ChatGPT(요약) + Gemini(시각자료)
    │
    ▼
Phase 5: 최종 검수
    Perplexity(팩트체크) → Claude(오류 반영)
    │
    ▼
[완성된 계획서]
```

각 Phase 사이에 사용자 검토/수정이 가능합니다.

## 아키텍처

- **마스터 스킬**: `moai-pipeline-bizplan` - `/bizplan` 커맨드로 실행
- **MCP 서버 3개**: 외부 AI를 MCP 프로토콜로 래핑
  - `mcp-openai` - ChatGPT API
  - `mcp-gemini` - Gemini API
  - `mcp-perplexity` - Perplexity API
- **상태 저장**: `.moai/pipeline/{session-id}/`에 Phase별 결과 저장

## 사용 방법

### 사전 준비

1. API 키를 환경 변수로 설정:

```bash
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
export PERPLEXITY_API_KEY="pplx-..."
```

2. MCP 서버 설치:

```bash
cd mcp-servers/mcp-openai && npm install
cd mcp-servers/mcp-gemini && npm install
cd mcp-servers/mcp-perplexity && npm install
```

### 실행

Claude Code에서:

```
/bizplan "AI 기반 헬스케어 플랫폼 사업계획서"
```

Phase별로 결과가 생성되며, 각 단계에서 검토/수정할 수 있습니다.

### 중단 후 재개

```
/bizplan resume bizplan-20260215-143022
```

### API 키 없이 사용

API 키가 설정되지 않은 AI는 Claude가 대신 처리합니다. 모든 API 키 없이도 Claude 단독으로 전체 파이프라인 실행이 가능합니다 (교차검증 이점은 감소).

## 출력물

| 파일 | 내용 |
|------|------|
| `phase1-concept.md` | 컨셉 프레이밍 (BM 캔버스, 후보 분석) |
| `phase2-research.md` | 심층 리서치 (시장/기술/경쟁사/규제) |
| `phase3-strategy.md` | 전략 설계 (SWOT, PESTEL, 재무, KPI) |
| `phase4-draft.md` | 계획서 초안 (본문 + 요약 + 시각자료) |
| `final-bizplan.md` | 팩트체크 완료된 최종 계획서 |

## 프로젝트 구조

```
agent-compare/
├── mcp-servers/
│   ├── mcp-openai/          # ChatGPT MCP 서버
│   ├── mcp-gemini/          # Gemini MCP 서버
│   └── mcp-perplexity/      # Perplexity MCP 서버
├── .claude/skills/moai-pipeline-bizplan/
│   └── SKILL.md             # 마스터 스킬 정의
├── docs/plans/              # 설계 문서
├── final-summary.md         # 4개 AI 교차검증 최종안
└── .moai/pipeline/          # 파이프라인 실행 상태
```

## 교차검증 근거

이 파이프라인 설계는 Claude, ChatGPT, Gemini, Perplexity 4개 AI에게 각각 최적의 워크플로우를 물어본 뒤 교차 대조하여 확정한 것입니다. 자세한 내용은 [`final-summary.md`](./final-summary.md)를 참조하세요.

## 라이선스

Apache-2.0
