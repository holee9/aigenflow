# Architect Agent Memory - AigenFlow Project

## Project Context
- Project: AigenFlow - Multi-AI Pipeline CLI Tool
- SPEC: SPEC-PIPELINE-001 (9-layer architecture)
- Goal: Automated business plan generation using 4 AI providers

## Architecture Analysis (2026-02-16)

### Existing Patterns Identified

1. **Pydantic-Based Data Models**
   - All models use Pydantic BaseModel for validation
   - Field validators for input checking
   - model_dump() for JSON serialization
   - Location: `src/core/models.py`

2. **Event System**
   - EventBus with subscriber pattern
   - Event types: PipelineStarted, PhaseStarted, AgentCalled, etc.
   - Global event bus singleton via get_event_bus()
   - Location: `src/core/events.py`

3. **Async/Await Patterns**
   - BaseProvider uses abstract async methods
   - AsyncAgent protocol for agent implementations
   - SessionManager has async check operations
   - Locations: `src/gateway/base.py`, `src/agents/base.py`

4. **ABC/Protocol Patterns**
   - BaseProvider: ABC with send_message, check_session, login_flow, save_session, load_session
   - AsyncAgent: ABC with execute method
   - Consistent interface contracts across providers

5. **Structured Logging**
   - structlog with secret redaction
   - redact_secrets() function for sensitive data masking
   - LogContext for context-bound logging
   - Location: `src/core/logger.py`

6. **Settings Management**
   - Pydantic Settings with BaseSettings
   - Environment variable support with AC_ prefix
   - Field validation for directory creation
   - Location: `src/core/config.py`

7. **Custom Exceptions**
   - Hierarchical exception classes (AigenFlowException base)
   - Domain-specific: PipelineException, GatewayException, AgentException, etc.
   - ErrorCode enum for standardized error codes
   - Location: `src/core/exceptions.py`

### Implementation Gaps

1. **Playwright Integration**
   - BaseProvider methods are stubs, need actual browser automation
   - Need browser context management
   - Need DOM selector implementations

2. **4-Stage Recovery Chain**
   - SessionManager has basic structure
   - Missing: refresh, relogin, fallback, claude-safety-net implementation

3. **Phase Implementations**
   - Orchestrator skeleton exists
   - Individual phase modules missing
   - Context chain not implemented

4. **CLI Commands**
   - main.py is minimal greeting
   - Need full Typer command set: run, check, setup, relogin, status, resume, config

5. **Fallback Logic**
   - AgentRouter has basic mapping
   - Missing fallback execution logic

6. **Context Compression**
   - PhaseResult.summary field exists
   - No token counting or compression logic

7. **Prompt Templates**
   - TemplateManager exists with Jinja2
   - 12 template files exist but likely need content
   - No template validation

### Dependencies Between Layers

```
L0 (Foundation) -> All layers
L1 (Gateway) -> L3 (Agents)
L2 (Models) -> L3, L5, L6
L3 (Agents) -> L5 (Phases)
L4 (Templates) -> L5 (Phases)
L5 (Phases) -> L6 (Orchestrator)
L6 (Orchestrator) -> L8 (CLI)
L7 (Output) -> L6, L8
```

## Design Decisions Made

### DDR-001: State Persistence
- JSON files with atomic writes
- Rationale: No DB dependency, human-readable, Git-friendly

### DDR-002: Context Compression
- Summary-based with token counting
- Trigger at 80% token limit

### DDR-003: Fallback Mapping
- Bidirectional pairs: ChatGPT<->Claude, Gemini<->Perplexity

### DDR-004: Template Variables
- 3 scopes: Static, Dynamic, Cumulative

### DDR-005: Error Recovery
- Request-level (retry 2x -> fallback)
- Phase-level (state persistence -> resume)

## File Structure Reference

```
src/
├── core/
│   ├── config.py      [COMPLETE] Pydantic Settings
│   ├── events.py      [COMPLETE] EventBus
│   ├── exceptions.py  [COMPLETE] Custom exceptions
│   ├── logger.py      [COMPLETE] structlog
│   └── models.py      [COMPLETE] Data models
├── gateway/
│   ├── base.py        [PARTIAL] ABC interface
│   ├── session.py     [PARTIAL] SessionManager
│   ├── models.py      [COMPLETE] GatewayRequest/Response
│   ├── chatgpt_provider.py  [NEEDS IMPLEMENTATION]
│   ├── claude_provider.py   [NEEDS IMPLEMENTATION]
│   ├── gemini_provider.py   [NEEDS IMPLEMENTATION]
│   └── perplexity_provider.py [NEEDS IMPLEMENTATION]
├── agents/
│   ├── base.py        [PARTIAL] AsyncAgent ABC
│   ├── router.py      [PARTIAL] Basic routing
│   └── *_agent.py     [NEEDS IMPLEMENTATION]
├── templates/
│   ├── manager.py     [COMPLETE] Jinja2 TemplateManager
│   └── prompts/       [PARTIAL] Template files exist
├── pipeline/
│   ├── orchestrator.py [PARTIAL] Basic flow
│   └── state.py       [COMPLETE] State enum
├── output/
│   └── formatter.py   [PARTIAL] Basic save
└── main.py            [MINIMAL] Only greeting
```

## Key Integration Points

1. GatewayResponse -> AgentResponse conversion in AsyncAgent.validate_response()
2. AgentRouter.execute() -> AsyncAgent.execute() -> GatewayProvider.send_message()
3. TemplateManager.render_prompt() -> Phase execution
4. EventBus.publish() throughout pipeline state changes

## Risk Areas

1. Playwright browser automation complexity
2. DOM selector fragility (AI websites change)
3. Session management across providers
4. Context window overflow in long pipelines
5. Error recovery edge cases
