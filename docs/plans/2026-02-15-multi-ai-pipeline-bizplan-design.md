# Multi-AI Pipeline BizPlan - Design Document

> **Date**: 2026-02-15
> **Status**: Approved
> **Approach**: Single Orchestrator Skill + 3 MCP Servers

---

## 1. Overview

MoAI-ADK skill that automates the 5-phase multi-AI pipeline from `final-summary.md` to generate business plans and R&D proposals. Each external AI (ChatGPT, Gemini, Perplexity) is wrapped as an MCP server, with Claude as the primary orchestrator and writer.

### Key Decisions

- **Form**: MoAI-ADK skill (`/bizplan` command)
- **AI Integration**: MCP Server wrapping (mcp-openai, mcp-gemini, mcp-perplexity)
- **Output**: Business plans / R&D proposals (specialized)
- **Execution**: Phase-by-phase sequential with user review between phases
- **Architecture**: Single orchestrator skill (vs. per-phase skills or per-phase agents)

---

## 2. Architecture

### Components

1. **Master Skill** (`moai-pipeline-bizplan`): Controls 5-phase sequence, mediates user review between phases, stores intermediate results.

2. **MCP Servers** (3):
   - `mcp-openai`: OpenAI API wrapper (brainstorming, frameworks, editing)
   - `mcp-gemini`: Google Gemini API wrapper (deep research, visuals)
   - `mcp-perplexity`: Perplexity API wrapper (search with citations, fact-checking)

3. **State Store**: `.moai/pipeline/{session-id}/` with markdown files per phase. Supports pause/resume.

4. **Claude** (built-in): Main executor for convergence (1-B), narrative integration (3-B), and draft writing (4).

### Data Flow

```
User Input (idea)
  -> Phase 1: mcp-openai(brainstorm) -> Claude(converge) -> save
  -> Phase 2: mcp-gemini + mcp-perplexity (parallel research) -> save
  -> Phase 3: mcp-openai(framework) -> Claude(narrative) -> save
  -> Phase 4: Claude(draft) + mcp-openai(edit) + mcp-gemini(visuals) -> save
  -> Phase 5: mcp-perplexity(fact-check) -> Claude(apply fixes) -> final document
```

---

## 3. MCP Server Design

### Common Structure

- Language: TypeScript (MCP SDK)
- Registration: `.mcp.json`
- API Keys: Environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY`)
- Fallback: If API key is missing, Claude handles the task directly

### mcp-openai (ChatGPT Role)

| Tool | Purpose | Phase |
|------|---------|-------|
| `brainstorm` | Idea divergence, BM canvas, variant generation | 1-A |
| `framework_analysis` | SWOT, PESTEL, financial scenarios | 3-A |
| `edit_and_format` | Investor summary, pitch deck, document editing | 4 |

### mcp-gemini (Research/Collaboration Role)

| Tool | Purpose | Phase |
|------|---------|-------|
| `deep_research` | 100+ source deep research, subtopic decomposition | 2 |
| `generate_visuals` | Tables, graphs, timelines | 4 |

### mcp-perplexity (Fact-Check Role)

| Tool | Purpose | Phase |
|------|---------|-------|
| `search_with_citations` | Real-time web search + auto citations | 2 |
| `fact_check` | Claim/number/source verification, citation audit | 5 |

---

## 4. Master Skill Workflow

### Phase 1 - Concept Framing

1. Send user idea to `mcp-openai.brainstorm` -> BM canvas, 3-5 variants
2. Claude converges -> compress candidates, logic/risk verification, assumptions
3. Save: `.moai/pipeline/{id}/phase1-concept.md`
4. Present to user -> approve or request changes

### Phase 2 - Deep Research

1. Execute `mcp-gemini.deep_research` and `mcp-perplexity.search_with_citations` in **parallel**
2. Claude cross-validates Gemini (breadth) and Perplexity (accuracy) results
3. Save: `.moai/pipeline/{id}/phase2-research.md`
4. User review

### Phase 3 - Strategy Design

1. Send Phase 1+2 results to `mcp-openai.framework_analysis` -> SWOT, PESTEL, financials
2. Claude removes contradictions, integrates narrative, aligns KPIs
3. Save: `.moai/pipeline/{id}/phase3-strategy.md`
4. User review

### Phase 4 - Draft Writing

1. Claude writes full proposal based on Phase 1-3 context
2. `mcp-openai.edit_and_format` generates investor summary / pitch deck
3. `mcp-gemini.generate_visuals` generates tables / graphs
4. Save: `.moai/pipeline/{id}/phase4-draft.md`
5. User review

### Phase 5 - Final Review

1. `mcp-perplexity.fact_check` verifies all claims/numbers/sources
2. Claude applies corrections, realigns document
3. Save final: `.moai/pipeline/{id}/final-bizplan.md`
4. Present completed document to user

---

## 5. File Structure

```
agent-compare/
├── .mcp.json                          # MCP server registration
├── mcp-servers/
│   ├── mcp-openai/
│   │   ├── package.json
│   │   ├── src/index.ts               # MCP server entry point
│   │   └── src/tools/                 # brainstorm, framework_analysis, edit_and_format
│   ├── mcp-gemini/
│   │   ├── package.json
│   │   ├── src/index.ts
│   │   └── src/tools/                 # deep_research, generate_visuals
│   └── mcp-perplexity/
│       ├── package.json
│       ├── src/index.ts
│       └── src/tools/                 # search_with_citations, fact_check
├── .claude/skills/moai-pipeline-bizplan/
│   └── SKILL.md                       # Master skill definition
└── .moai/pipeline/                    # Pipeline execution state
    └── {session-id}/
        ├── config.yaml                # Session config (idea, options, current phase)
        ├── phase1-concept.md
        ├── phase2-research.md
        ├── phase3-strategy.md
        ├── phase4-draft.md
        └── final-bizplan.md
```

---

## 6. State Management

- Each phase completion records current phase number in `config.yaml`
- Resume after interruption: `/bizplan resume {session-id}`
- All outputs are markdown, editable by user between phases
- Session IDs use timestamp format: `bizplan-20260215-143022`

---

## 7. Error Handling & Fallback

### API Key Missing Fallback

| MCP Server | Fallback |
|------------|----------|
| `mcp-openai` missing | Claude handles brainstorming/framework analysis directly |
| `mcp-gemini` missing | Claude uses WebSearch + WebFetch for research |
| `mcp-perplexity` missing | Claude uses WebSearch for fact-checking |

Full pipeline runs with Claude alone if no external APIs configured. Cross-validation benefits are reduced.

### Phase Execution Errors

- API call failure: Max 2 retries, then switch to fallback
- Token limit exceeded: Save phase results, guide user to `/bizplan resume`
- User rejects phase: Re-execute with modification requests applied

### Quality Assurance

- Phase 2: When Gemini and Perplexity results conflict, Claude compares evidence and adopts the more credible source, reporting discrepancies to user
- Phase 5: Unverified claims tagged with `[unverified]` for user judgment

---

## 8. Implementation Priority

1. **Phase 1**: Master skill skeleton + state management
2. **Phase 2**: mcp-openai server (most phases depend on it)
3. **Phase 3**: mcp-perplexity server (research + fact-check)
4. **Phase 4**: mcp-gemini server (research + visuals)
5. **Phase 5**: Full integration testing

---

## 9. Future Considerations

- Template system for different document types (R&D, investor pitch, grant proposal)
- Export to Word/PDF via Pandoc integration
- Cost tracking per pipeline run (API usage)
- Pipeline history and comparison between runs
