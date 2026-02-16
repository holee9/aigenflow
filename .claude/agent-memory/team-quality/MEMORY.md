# Team Quality Agent Memory

## Project: AigenFlow

### Project Overview
- **Name**: AigenFlow
- **Description**: Multi-AI Pipeline CLI Tool for Automated Business Plan Generation
- **Python Version**: 3.13+
- **License**: Apache-2.0

### Codebase Structure
```
src/
├── gateway/           # AI provider integrations (Claude, Gemini, ChatGPT, Perplexity)
├── agents/            # Agent implementations
├── templates/         # Template management
├── pipeline/          # Pipeline phases and orchestrator
├── output/            # Output formatting
├── core/              # Core utilities (config, events, exceptions, logger, models)
├── cli/               # CLI commands
└── ui/                # UI components (progress, logger, summary)

tests/
├── agents/
├── cli/
├── core/
├── gateway/
├── integration/
├── output/
└── pipeline/
```

### Quality Tools Configuration

**Ruff (Linter & Formatter)**:
- Line length: 100
- Target version: py313
- Select: E, F, I, N, W, UP
- Ignore: E501

**MyPy (Type Checker)**:
- Python version: 3.13
- Strict mode enabled (disallow_untyped_defs: true)

**Pytest**:
- Options: -v --tb=short
- Async mode: auto

**Coverage Target**: 85%

### TRUST 5 Validation Framework

#### 1. TESTED
- All tests must pass: `pytest tests/`
- Coverage >= 85%: `pytest tests/ --cov=src --cov-report=term-missing`
- New code must have tests written before implementation (TDD for new files)

#### 2. READABLE
- Zero lint errors: `ruff check src/`
- Clear naming conventions (snake_case for functions/variables, PascalCase for classes)
- English comments only (per code_comments: en)
- Docstrings for all public functions/classes

#### 3. UNIFIED
- Consistent code style (ruff format)
- Follow existing patterns in codebase
- No duplicate code (DRY principle)

#### 4. SECURED
- OWASP compliance
- Input validation on all external inputs
- No secrets in code
- Sensitive data redaction in logs (see src/core/logger.py)

#### 5. TRACKABLE
- Conventional commit messages
- Issue references in commits
- Clear changelog entries

### SPEC-ENHANCE-003 Validation Checklist

#### Phase 1: Selector Externalization (TASK-001 to TASK-004)
- [ ] selectors.yaml exists at src/gateway/selectors.yaml
- [ ] SelectorLoader class implemented with YAML validation
- [ ] Provider classes refactored to use SelectorLoader
- [ ] `aigenflow check --selectors` command works

#### Phase 2: Error Recovery (TASK-005 to TASK-008)
- [ ] FallbackChain class implemented
- [ ] Fault detection mechanism working
- [ ] Transition logging implemented
- [ ] E2E fault injection tests passing

#### Phase 3: Output Formats (TASK-009 to TASK-012)
- [ ] OutputFormatter interface defined
- [ ] DocxFormatter implemented (python-docx)
- [ ] PdfFormatter implemented (reportbook/weasyprint)
- [ ] CLI --output-format option works

#### Phase 4: Context Optimization (TASK-013 to TASK-016)
- [ ] TokenCounter utility implemented
- [ ] ContextSummary class implemented
- [ ] Trigger integrated with Orchestrator
- [ ] Summary quality tests passing

#### Phase 5: Log Structure (TASK-017 to TASK-018)
- [ ] Logging profiles created (dev/test/prod)
- [ ] CLI --log-level option works
- [ ] Log rotation configured (max 10MB, 5 files)

### Quality Gates Commands

```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Lint check
ruff check src/

# Type check
mypy src/

# Format check
ruff format --check src/

# Security scan (if bandit installed)
bandit -r src/
```

### Common Patterns to Verify

1. **Pydantic models** for configuration and data validation
2. **Structlog** for logging with sensitive data redaction
3. **Pathlib** for all file path operations
4. **Type hints** on all functions (strict mypy)
5. **Async/await** for I/O operations
6. **Context managers** for resource management

### Baseline Quality Assessment (2026-02-16)

**Linter Status (ruff)**:
- 103 errors found in existing codebase
- 75 fixable with `--fix`
- Most are import sorting issues (I001)
- Some need `X | None` syntax instead of `Optional[X]`

**Test Status**:
- Collection errors in 4 test files
- test_selector_loader.py exists but selector_loader.py does not (TDD RED phase)

**Type Checker (mypy)**:
- Not available in current environment (command not found)

**Quality Gates Baseline**:
- Zero lint errors: FAIL (103 errors)
- Zero type errors: CANNOT CHECK
- Tests passing: FAIL (import errors)
- Coverage 85%: CANNOT CHECK

### Known Limitations & Considerations

- Selector YAML validation must handle provider-specific differences
- Fallback chain quality degradation must be monitored
- DOCX/PDF libraries may have version compatibility issues
- Context summary may lose some information (acceptable trade-off)
- Log rotation must prevent disk fill in production

### SPEC-ENHANCE-003 Status (2026-02-16)

**Completed**: 1/18 tasks
- TASK-001: selectors.yaml created

**In Progress**: 3 tasks
- TASK-002: SelectorLoader implementation (tests written, code pending)
- TASK-008: E2E tests (blocked by TASK-005, TASK-006, TASK-007)
- TASK-019: Quality validation (blocked by all implementation tasks)

**Pending**: 14 tasks
