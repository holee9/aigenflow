# SPEC-PACKAGING-001: pip install aigenflow - Global Installation Package

## Overview

| Field | Value |
|-------|-------|
| SPEC ID | SPEC-PACKAGING-001 |
| Title | pip install aigenflow 전역 설치용 패키지 개선 |
| Status | Completed |
| Created | 2026-02-15 |
| Completed | 2026-02-15 |
| Methodology | Hybrid (TDD for new + DDD for legacy) |

## Problem Statement

현재 AigenFlow 프로젝트는 `git clone` 후 `pip install -e .`로만 실행 가능하며, 패키지 이름이 `aigenflow`로 되어 있어 `pip install aigenflow`로 전역 설치할 수 없다. 사용자가 어디서든 `aigenflow run --topic "..."` 명령으로 파이프라인을 실행할 수 있도록 PyPI 배포 가능한 패키지로 개선한다.

## Current State Analysis

### Critical Issues (Researcher Findings)

| Issue | Severity | Description |
|-------|----------|-------------|
| Missing `[build-system]` | HIGH | pyproject.toml에 빌드 시스템 미설정 |
| `aigenflow/` submodule 충돌 | HIGH | git submodule로 Electron 앱이 이미 존재 |
| 32개 `from src.` imports | HIGH | 모든 소스 파일이 `src.` prefix 사용 |
| 10개 `sys.path` hack | MEDIUM | main.py, conftest.py 등 경로 조작 |
| 템플릿 경로 하드코딩 | HIGH | `Path("src/templates/prompts")` CWD 기반 |
| 잘못된 `[project.scripts]` | HIGH | shell 명령 형식 (Python entry point 아님) |
| 테스트 import 혼재 | MEDIUM | bare import + `from src.` 두 가지 패턴 |

### File Impact Summary

- **소스 파일 수정**: 18개 (import 변경)
- **테스트 파일 수정**: ~25개 (import 변경)
- **sys.path 제거**: 10개 위치
- **새 파일 생성**: 2개 (`__main__.py`, `py.typed`)
- **설정 파일 수정**: 1개 (`pyproject.toml`)

## Requirements (EARS Format)

### Functional Requirements

**FR-1: Package Installation**
- When a user runs `pip install aigenflow`, the system shall install the aigenflow package and all runtime dependencies (playwright, typer, pydantic, pydantic-settings, jinja2, rich, structlog).
- Acceptance: `import aigenflow` succeeds; `aigenflow --help` prints usage.

**FR-2: CLI Entry Point**
- When the user runs `aigenflow run --topic "AI SaaS"`, the system shall execute the 5-phase pipeline.
- When the user runs `aigenflow setup`, `aigenflow check`, `aigenflow relogin`, `aigenflow resume`, `aigenflow status`, `aigenflow config`, the system shall execute the respective utility commands.
- Acceptance: All CLI commands from README work after pip install.

**FR-3: python -m Support**
- When the user runs `python -m aigenflow`, the system shall behave identically to the `aigenflow` CLI entry point.
- Acceptance: `python -m aigenflow run --topic "test"` works.

**FR-4: Template Data Files**
- While the package is installed, all 12 Jinja2 templates shall be included as package data.
- Where the TemplateManager loads templates, it shall resolve paths relative to the installed package (not CWD).
- Acceptance: `aigenflow run` works from any directory; templates render correctly.

**FR-5: Editable Install**
- When a developer runs `pip install -e .` from the repository root, the system shall install in editable mode.
- Acceptance: Code changes reflected without reinstallation.

**FR-6: pipx Support**
- When a user runs `pipx install aigenflow`, the system shall install and make the `aigenflow` command globally available.
- Acceptance: `pipx install aigenflow && aigenflow --help` works.

**FR-7: Playwright Browser Check**
- While Playwright browsers are not installed, the system shall display a clear error message with install instructions.
- Acceptance: Helpful error on missing browsers; no silent failures.

**FR-8: Cross-Platform**
- Where the platform is Windows, macOS, or Linux, the system shall function correctly.
- Acceptance: Install and run on all three platforms.

### Non-Functional Requirements

**NFR-1**: CLI startup time under 2 seconds (lazy imports already implemented).
**NFR-2**: Package size under 500KB sdist (excluding Playwright browsers).
**NFR-3**: No secrets in package distribution (.env, session tokens excluded).
**NFR-4**: `pip install` completes in under 60 seconds (excluding Playwright browsers).

## Technical Design

### Architecture Decision: src Layout

**Decision**: `src/aigenflow/` (src layout)

**Rationale**:
1. `aigenflow/` 디렉토리가 git submodule (Electron 앱)로 이미 존재하여 flat layout 불가
2. src layout은 미설치 코드의 우발적 import를 방지하는 Python packaging 모범 사례
3. 현재 코드가 이미 `src/`에 있어 자연스러운 전환 (rename만 필요)

### Build Backend: hatchling

**Decision**: hatchling

**Rationale**:
- src layout 네이티브 지원 (`packages = ["src/aigenflow"]`)
- 패키지 데이터 자동 포함 (non-Python 파일 기본 포함)
- Dynamic version 내장 지원 (`__init__.py`에서 읽기)
- 빠르고 현대적인 PEP 517/518 준수

### Target Directory Structure

```
aigenflow/
├── pyproject.toml                 # Updated: build-system, scripts, version
├── src/
│   └── aigenflow/                 # Renamed from src/ flat structure
│       ├── __init__.py            # Package root (version, lazy imports)
│       ├── __main__.py            # NEW: python -m aigenflow support
│       ├── py.typed               # NEW: PEP 561 type marker
│       ├── main.py                # CLI entry point (sys.path hack removed)
│       ├── core/                  # config, events, exceptions, logger, models
│       ├── agents/                # base, router, 4 AI agents
│       ├── gateway/               # base, session, models, 4 providers
│       ├── pipeline/              # orchestrator, state
│       ├── output/                # formatter
│       └── templates/
│           ├── __init__.py
│           ├── manager.py         # Fixed: __file__-relative path
│           └── prompts/           # 12 Jinja2 template data files
├── tests/                         # Updated imports
├── aigenflow/                     # Git submodule (untouched)
└── output/                        # Runtime output
```

### pyproject.toml Target Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "aigenflow"
dynamic = ["version"]
description = "Multi-AI Pipeline CLI Tool for Automated Business Plan Generation"
requires-python = ">=3.13"
license = {text = "Apache-2.0"}
dependencies = [
    "playwright>=1.49.0",
    "typer>=0.12.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "jinja2>=3.1.0",
    "rich>=13.0.0",
    "structlog>=24.0.0",
]

[project.scripts]
aigenflow = "aigenflow.main:main"

[tool.hatch.version]
path = "src/aigenflow/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["src/aigenflow"]
```

### Version Management

**Decision**: Single source of truth in `src/aigenflow/__init__.py`
- `pyproject.toml`에서 `dynamic = ["version"]` 선언
- `hatch.version`이 `__init__.py`의 `__version__`에서 읽기

## Implementation Plan

### Phase 1: Directory Restructure (DDD - PRESERVE)

| Step | Action | Files |
|------|--------|-------|
| 1.1 | `src/aigenflow/` 디렉토리 생성 | New directory |
| 1.2 | `src/*.py` → `src/aigenflow/` 이동 | `__init__.py`, `main.py` |
| 1.3 | `src/core/` → `src/aigenflow/core/` 이동 | 6 files |
| 1.4 | `src/agents/` → `src/aigenflow/agents/` 이동 | 7 files |
| 1.5 | `src/gateway/` → `src/aigenflow/gateway/` 이동 | 8 files |
| 1.6 | `src/pipeline/` → `src/aigenflow/pipeline/` 이동 | 3 files |
| 1.7 | `src/output/` → `src/aigenflow/output/` 이동 | 2 files |
| 1.8 | `src/templates/` → `src/aigenflow/templates/` 이동 | manager.py + 12 templates |
| 1.9 | `src/aigenflow/__main__.py` 생성 | New file |
| 1.10 | `src/aigenflow/py.typed` 생성 | New file |

### Phase 2: Import Refactoring (DDD - IMPROVE)

| Step | Action | Scope |
|------|--------|-------|
| 2.1 | `from src.` → `from aigenflow.` 전체 치환 | 18 source files (32 occurrences) |
| 2.2 | 테스트 import 통일 (`from aigenflow.`) | ~25 test files |
| 2.3 | `sys.path` hack 제거 | 10 locations |
| 2.4 | `conftest.py` sys.path 제거 | tests/conftest.py |

### Phase 3: Path Resolution Fix (DDD - IMPROVE)

| Step | Action | File |
|------|--------|------|
| 3.1 | TemplateManager: `Path(__file__).parent / "prompts"` | templates/manager.py |
| 3.2 | config.py templates_dir 기본값 수정 | core/config.py |
| 3.3 | main.py sys.path hack 제거 | main.py |

### Phase 4: pyproject.toml Update (TDD - NEW)

| Step | Action |
|------|--------|
| 4.1 | `[build-system]` 추가 (hatchling) |
| 4.2 | `[project]` name → "aigenflow", dynamic version |
| 4.3 | `[project.scripts]` → `aigenflow = "aigenflow.main:main"` |
| 4.4 | `[tool.hatch]` 설정 추가 |
| 4.5 | 잘못된 scripts 항목 제거 |
| 4.6 | ruff/pytest 경로 업데이트 |

### Phase 5: Configuration Update (DDD - IMPROVE)

| Step | Action |
|------|--------|
| 5.1 | `AgentCompareSettings` → `AigenFlowSettings` 리네이밍 |
| 5.2 | app_name 기본값 → "aigenflow" |
| 5.3 | profiles_dir 기본값 → `~/.aigenflow/profiles` |
| 5.4 | 하위 호환성 고려 (기존 profiles 마이그레이션 안내) |

### Phase 6: Validation (TDD)

| Step | Action |
|------|--------|
| 6.1 | `pip install -e .` 성공 확인 |
| 6.2 | `import aigenflow` 성공 확인 |
| 6.3 | `aigenflow --help` 동작 확인 |
| 6.4 | `python -m aigenflow` 동작 확인 |
| 6.5 | TemplateManager 임의 디렉토리에서 동작 확인 |
| 6.6 | 전체 테스트 스위트 통과 확인 |

## Edge Cases

| ID | Case | Mitigation |
|----|------|------------|
| EC-1 | aigenflow/ submodule과 패키지 이름 충돌 | src layout으로 완전 회피 |
| EC-2 | 기존 `~/.aigenflow/profiles` 디렉토리 | 마이그레이션 가이드 + fallback 로직 |
| EC-3 | PyPI 이름 'aigenflow' 사용 가능 여부 | 배포 전 확인 필수 |
| EC-4 | Playwright 미설치 시 cryptic error | 시작 시 브라우저 체크 + 안내 메시지 |
| EC-5 | CWD 기반 output_dir | 정상 동작 (문서화) |
| EC-6 | 버전 이중 관리 | hatch dynamic version으로 단일화 |

## Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-1 | 32개 import 리팩토링 오류 | HIGH | 기계적 치환 + 전체 테스트 |
| R-2 | 템플릿 경로 미포함 (wheel) | HIGH | hatchling 자동 포함 + 설치 후 검증 |
| R-3 | PyPI 이름 충돌 | MEDIUM | 사전 확인 (pypi.org/project/aigenflow) |
| R-4 | Playwright UX 혼란 | MEDIUM | startup guard + 문서화 |
| R-5 | 테스트 import 깨짐 | MEDIUM | import 리팩토링과 동시 수정 |

## Acceptance Criteria

- [x] `pip install -e .` 성공
- [x] `import aigenflow` 성공
- [x] `aigenflow.__version__` 올바른 버전 반환
- [x] `aigenflow --help` 사용법 출력
- [x] `python -m aigenflow --help` 동일 동작
- [x] `from aigenflow.core import get_settings` 동작
- [x] TemplateManager가 임의 디렉토리에서 템플릿 찾기 성공
- [x] `sys.path` hack 0개
- [x] `from src.` import 0개
