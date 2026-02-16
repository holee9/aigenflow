# Changelog

All notable changes to the AigenFlow project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - SPEC-ENHANCE-003 Phase 5: Logging Structure (Complete)
- Environment-specific logging profiles with structlog
  - Development: DEBUG level, console + file output
  - Testing: INFO level, file only
  - Production: WARNING level, file only with JSON format
- CLI log control options
  - `--log-level`: Set logging level (debug, info, warning, error)
  - `--environment`: Set logging environment (development, testing, production)
- Log file rotation (10MB max, 5 backup files)
- Sensitive data redaction in logs (API keys, tokens, passwords)
- 78 comprehensive tests (95% coverage for logging module)

### Added - SPEC-ENHANCE-003 Phases 1-4
- DOM selector externalization with `selectors.yaml`
- Fallback AI chain for automatic error recovery
- Multiple output formats (DOCX, PDF)
- Context optimization with automatic summarization

### Changed
- Refactored `orchestrator.py` to use Phase classes while maintaining 100% backward compatibility
- Updated `main.py` to integrate all CLI commands with Typer app
- Fixed import inconsistency in `gateway/base.py`

### Changed
- Refactored `orchestrator.py` to use Phase classes while maintaining 100% backward compatibility
- Updated `main.py` to integrate all CLI commands with Typer app
- Fixed import inconsistency in `gateway/base.py`

### Fixed
- Session manager status checking
- Phase module dependencies and imports

## [2.0.0] - 2026-02-15

### Added
- Multi-AI pipeline orchestration with 5 phases
- Playwright-based AI gateway with 4 providers (ChatGPT, Claude, Gemini, Perplexity)
- 12 Jinja2 prompt templates for all pipeline phases
- Session management with 4-stage auto-recovery chain
- Pipeline state persistence and resume functionality
- Template manager with multiple output formats

### Changed
- Migrated from agent-compare to aigenflow project structure

[Unreleased]: https://github.com/yourusername/aigenflow/compare/v2.0.0...HEAD
[v2.0.0]: https://github.com/yourusername/aigenflow/releases/tag/v2.0.0
