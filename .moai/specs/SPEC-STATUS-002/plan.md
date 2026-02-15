# SPEC-STATUS-002: 구현 계획

## 1. 개요

본 문서는 AigenFlow 프로젝트의 현황 분석 결과를 바탕으로 한 구현 계획을 기술한다. 프로젝트는 현재 약 80% 완료되어 있으며, 본 계획에서는 남은 20%를 완료하고 품질을 개선하는 데 중점을 둔다.

## 2. 구현 전략

### 2.1 3-Phase 접근법

```
Phase 1: CLI 명령 완성 (P0 - Critical)
    └── aigenflow check, setup, relogin, status, resume, config

Phase 2: Phase 모듈 분리 (P0 - Critical)
    └── BasePattern 추상화 + 개별 Phase 파일 분리

Phase 3: UI/UX 개선 (P1 - High)
    └── Rich 라이브러리 기반 진행 상황 시각화
```

### 2.2 우선순위 매트릭스

| 우선순위 | 항목 | 이유 | 예상 공수 |
|---------|------|------|-----------|
| P0 | CLI 명령 완성 | 사용자가 핵심 기능을 사용할 수 없음 | 5일 |
| P0 | Phase 모듈 분리 | 코드 유지보수성 및 테스트 가능성 | 3일 |
| P1 | Rich UI 개선 | 사용자 경험 향상 | 2일 |
| P2 | 선택자 외부화 | DOM 변경 대응 | 1일 |
| P2 | DOCX/PDF 출력 | 출력 형식 다양화 | 3일 |

## 3. Phase 1: CLI 명령 완성

### 3.1 명령별 구현 계획

#### 3.1.1 `aigenflow check`

**목표**: Playwright 브라우저 및 AI 세션 상태 확인

**구현**:
```python
# cli/check.py
from typer import Typer
from rich.table import Table
from rich.console import Console

app = Typer()
console = Console()

@app.command()
def check():
    """Check Playwright browser and AI session status."""
    table = Table(title="AigenFlow System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    # Playwright 브라우저 확인
    browser_status = check_playwright()
    table.add_row("Playwright Browser", browser_status, "Chromium")

    # AI 세션 확인
    for provider in ["chatgpt", "claude", "gemini", "perplexity"]:
        status = session_manager.check_session(provider)
        table.add_row(f"{provider.title()} Session", status, "Last login: ...")

    console.print(table)
```

**파일**: `src/cli/check.py`

#### 3.1.2 `aigenflow setup`

**목표**: 최초 설정 마법사 (대화형)

**구현**:
```python
# cli/setup.py
from typer import Typer, prompt
from playwright.sync_api import sync_playwright

@app.command()
def setup():
    """Initial setup wizard for AigenFlow."""
    console.print("[bold blue]AigenFlow Setup Wizard[/bold blue]")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for provider in ["chatgpt", "claude", "gemini", "perplexity"]:
            console.print(f"\n[ yellow]Setting up {provider}...[/yellow]")
            login_url = get_login_url(provider)
            page.goto(login_url)
            console.print("Please complete login in the browser...")
            prompt("Press Enter when login is complete")

            # 프로필 저장
            save_profile(page, provider)

        browser.close()
```

**파일**: `src/cli/setup.py`

#### 3.1.3 `aigenflow relogin [PROVIDER]`

**목표**: 만료된 세션 재로그인

**구현**:
```python
# cli/relogin.py
@app.command()
def relogin(provider: str = typer.Argument(None)):
    """Re-login to specified AI provider."""
    if provider is None:
        provider = prompt("Which provider?", type=Choice(["chatgpt", "claude", "gemini", "perplexity"]))

    gateway_provider = get_provider(provider)
    gateway_provider.login_flow()  # headed 모드
```

**파일**: `src/cli/relogin.py`

#### 3.1.4 `aigenflow status [SESSION_ID]`

**목표**: 파이프라인 실행 상태 조회

**구현**:
```python
# cli/status.py
@app.command()
def status(session_id: str = typer.Argument(None)):
    """Show pipeline execution status."""
    if session_id is None:
        # 최근 세션 표시
        sessions = list_sessions()
        table = Table(title="Recent Pipeline Sessions")
        for session in sessions[-5:]:
            table.add_row(session.id, session.state, session.topic)
    else:
        # 특정 세션 상세
        session = load_session(session_id)
        console.print(f"State: {session.state}")
        for result in session.results:
            console.print(f"Phase {result.phase_number}: {result.status}")
```

**파일**: `src/cli/status.py`

#### 3.1.5 `aigenflow resume SESSION_ID`

**목표**: 중단된 파이프라인 재개

**구현**:
```python
# cli/resume.py
@app.command()
def resume(session_id: str, from_phase: int = typer.Option(None, "--from-phase")):
    """Resume interrupted pipeline."""
    session = load_session(session_id)

    orchestrator = PipelineOrchestrator()
    orchestrator.current_session = session

    if from_phase:
        orchestrator.run_from_phase(from_phase)
    else:
        orchestrator.run_from_session(session)
```

**파일**: `src/cli/resume.py`

#### 3.1.6 `aigenflow config show|set`

**목표**: 설정 조회/변경

**구현**:
```python
# cli/config.py
@app.command()
def config():
    """Configuration management."""
    pass

@config.command()
def show():
    """Show current configuration."""
    settings = get_settings()
    console.print(settings.model_dump_yaml())

@config.command()
def set(key: str, value: str):
    """Set configuration value."""
    settings = get_settings()
    setattr(settings, key, parse_value(value))
    save_settings(settings)
```

**파일**: `src/cli/config.py`

### 3.2 main.py 명령 등록

```python
# main.py
from cli import check, setup, relogin, status, resume, config

app = Typer()

app.command()(run)
app.add_typer(check.app, name="check")
app.add_typer(setup.app, name="setup")
app.add_typer(relogin.app, name="relogin")
app.add_typer(status.app, name="status")
app.add_typer(resume.app, name="resume")
app.add_typer(config.app, name="config")
```

## 4. Phase 2: Phase 모듈 분리

### 4.1 BasePhase 추상 클래스

**파일**: `src/pipeline/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any
from src.core.models import PhaseResult, PipelineConfig

class BasePhase(ABC):
    """Base class for all pipeline phases."""

    def __init__(self, phase_number: int, name: str, config: PipelineConfig):
        self.phase_number = phase_number
        self.name = name
        self.config = config

    @abstractmethod
    def get_tasks(self) -> list[tuple[str, str]]:  # (task_name, agent_type)
        """Return list of (task_name, agent_type) tuples for this phase."""
        pass

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> PhaseResult:
        """Execute phase logic and return result."""
        pass

    def validate_result(self, result: PhaseResult) -> bool:
        """Validate phase result before proceeding."""
        return result.status == "completed"
```

### 4.2 Phase 1-5 구체 클래스

**파일 구조**:
```
src/pipeline/
├── phase1_framing.py   # FramingPhase
├── phase2_research.py  # ResearchPhase
├── phase3_strategy.py  # StrategyPhase
├── phase4_writing.py   # WritingPhase
└── phase5_review.py    # ReviewPhase
```

**예시**: `phase1_framing.py`

```python
from pipeline.base import BasePhase

class FramingPhase(BasePhase):
    """Phase 1: Concept Framing (ChatGPT + Claude)"""

    def get_tasks(self):
        return [
            ("brainstorm", "chatgpt"),
            ("validate", "claude"),
        ]

    async def execute(self, context):
        # 기존 Orchestrator의 Phase 1 로직 이동
        results = []
        for task_name, agent_type in self.get_tasks():
            agent = self.agent_router.get_agent(agent_type)
            response = await agent.execute(task_name, context)
            results.append(response)

        return PhaseResult(
            phase_number=1,
            phase_name="Framing",
            status="completed",
            ai_responses=results,
            summary=self._summarize(results),
        )
```

### 4.3 Orchestrator 리팩토링

**변경 전**: Phase 로직이 인라인으로 포함됨

**변경 후**: Phase 조정만 담당

```python
# orchestrator.py (리팩토링 후)
class PipelineOrchestrator:
    def __init__(self, ...):
        self.phases = [
            FramingPhase(1, "Framing", config),
            ResearchPhase(2, "Research", config),
            StrategyPhase(3, "Strategy", config),
            WritingPhase(4, "Writing", config),
            ReviewPhase(5, "Review", config),
        ]

    async def run(self):
        context = {}
        for phase in self.phases:
            result = await phase.execute(context)
            context[f"phase_{phase.phase_number}"] = result
```

## 5. Phase 3: UI/UX 개선

### 5.1 Rich Progress 컴포넌트

**파일**: `src/ui/progress.py`

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console

class PipelineProgress:
    def __init__(self, total_phases: int = 5):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

    def start_phase(self, phase_number: int, phase_name: str, agent: str):
        self.progress.add_task(
            f"Phase {phase_number}: {phase_name} ({agent})",
            total=100
        )
```

### 5.2 실시간 로그 스트림

**파일**: `src/ui/logger.py`

```python
from rich.panel import Panel
from rich.text import Text

class LogStream:
    def __init__(self):
        self.console = Console()
        self.logs = []

    def append(self, level: str, message: str):
        text = Text()
        text.append(f"[{level}] ", style=f"{'red' if level == 'ERROR' else 'green'}")
        text.append(message)
        self.console.print(Panel(text))
```

### 5.3 Orchestrator 통합

```python
# orchestrator.py
from ui.progress import PipelineProgress

class PipelineOrchestrator:
    async def run(self):
        progress = PipelineProgress(total_phases=5)

        for i, phase in enumerate(self.phases):
            progress.start_phase(i + 1, phase.name, agent)
            result = await phase.execute(context)
            progress.complete_phase(i + 1)
```

## 6. 의존성 그래프

```
Phase 1 (CLI 완성)
    ├── check.py → SessionManager
    ├── setup.py → Playwright, Provider.login_flow()
    ├── relogin.py → Provider.login_flow()
    ├── status.py → PipelineSession
    ├── resume.py → Orchestrator
    └── config.py → Settings

Phase 2 (모듈 분리)
    ├── BasePhase (ABC)
    ├── Phase1-5 → BasePhase
    └── Orchestrator → Phase1-5

Phase 3 (UI 개선)
    ├── Progress → Rich
    ├── LogStream → Rich
    └── Orchestrator → Progress, LogStream
```

## 7. 검증 전략

### 7.1 단위 테스트

각 CLI 명령과 Phase 클래스에 대한 단위 테스트:

```python
# tests/cli/test_check.py
def test_check_command():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Playwright Browser" in result.stdout

# tests/pipeline/test_phase1.py
async def test_framing_phase():
    phase = FramingPhase(1, "Framing", config)
    result = await phase.execute({})
    assert result.status == "completed"
```

### 7.2 통합 테스트

전체 CLI 명령 시퀀스 테스트:

```bash
# setup → check → run → status → resume → config
aigenflow setup
aigenflow check
aigenflow run --topic "Test"
aigenflow status <session_id>
aigenflow config show
```

## 8. 롤백 계획

| 단계 | 롤백 기준 | 복구 방법 |
|------|-----------|-----------|
| CLI 완성 | 명령 실행 실패 | Git revert로 이전 커밋 복원 |
| 모듈 분리 | Phase 동작 변경 | 인라인 버전 코드 브랜치 보존 |
| UI 개선 | 성능 저하 | Progress 컴포넌트 제거 |

---

**작성자**: MoAI Plan Team
**최종 업데이트**: 2026-02-16
