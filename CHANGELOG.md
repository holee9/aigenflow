# Changelog

All notable changes to the AigenFlow project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - SPEC-ENHANCE-004: AI Cost Optimization (Complete)
- Caching system for AI responses to reduce redundant API calls
  - SHA-256 based cache key generation with normalization
  - File system based cache storage with LRU eviction
  - Configurable TTL (default: 24 hours) and max size (default: 500MB)
  - Cache statistics tracking (hit rate, size, entries)
- Batch processing for AI requests to reduce overhead
  - Request queue with configurable max batch size (default: 5)
  - Provider-based grouping for efficient parallel processing
  - Automatic fallback to individual processing on batch failure
- Token monitoring and cost tracking
  - Real-time token usage tracking by provider and phase
  - Cost calculation with provider-specific pricing (Claude, ChatGPT, Gemini, Perplexity)
  - Budget alerts at thresholds (50%, 75%, 90%, 100%)
  - Usage statistics with daily, weekly, monthly, and all-time periods
- CLI commands for cost management
  - `aigenflow stats`: Show token usage and cost statistics
  - `aigenflow cache list`: List cached entries
  - `aigenflow cache clear`: Clear all cache
  - `aigenflow cache stats`: Show cache statistics
- 65 comprehensive tests (85%+ coverage)
  - 26 cache system tests
  - 12 batch processing tests
  - 13 monitoring tests
  - 14 integration tests

### Performance Improvements
- Target: 25-40% cost reduction through caching and batching
- Cache hit rate target: 20%+ (achievable with 24h TTL)
- Batch processing overhead: <5% (within NFR requirements)

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
