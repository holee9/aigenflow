"""
Resume command for AigenFlow CLI.

Resume interrupted pipeline execution.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from agents.chatgpt_agent import ChatGPTAgent
from agents.claude_agent import ClaudeAgent
from agents.gemini_agent import GeminiAgent
from agents.perplexity_agent import PerplexityAgent
from core import get_settings
from core.models import (
    AgentType,
    DocumentType,
    PipelineConfig,
    PipelineSession,
    PipelineState,
    TemplateType,
)
from gateway.session import SessionManager
from pipeline.orchestrator import TOTAL_PHASES, PipelineOrchestrator
from templates.manager import TemplateManager

console = Console()

# Output directory
OUTPUT_DIR = Path("output")

app = typer.Typer(help="Resume pipeline")


def _find_session_dir(session_id: str) -> Path | None:
    """
    Find session directory by session ID.

    Args:
        session_id: Session ID to find

    Returns:
        Path to session directory if found, None otherwise
    """
    session_dir = OUTPUT_DIR / session_id
    if session_dir.exists() and (session_dir / "pipeline_state.json").exists():
        return session_dir
    return None


def _list_available_sessions() -> list[dict[str, any]]:
    """
    List all available sessions in output directory.

    Returns:
        List of session info dictionaries
    """
    sessions = []
    if not OUTPUT_DIR.exists():
        return sessions

    for session_dir in OUTPUT_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        state_file = session_dir / "pipeline_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state_data = json.load(f)
                    sessions.append({
                        "id": state_data.get("session_id", session_dir.name),
                        "topic": state_data.get("config", {}).get("topic", "Unknown"),
                        "state": state_data.get("state", "unknown"),
                        "current_phase": state_data.get("current_phase", 0),
                    })
            except (OSError, json.JSONDecodeError):
                continue

    # Sort by updated_at (most recent first)
    return sorted(sessions, key=lambda x: x["id"], reverse=True)


def _get_resume_phase(session: PipelineSession) -> int:
    """
    Determine which phase to resume from.

    Args:
        session: Pipeline session to check

    Returns:
        Phase number to resume from (1-5), or None if completed
    """
    if session.state == PipelineState.COMPLETED:
        return -1  # Already completed

    # Resume from next phase after current completed phase
    return session.current_phase + 1


async def _check_session_availability_async() -> bool:
    """
    Check if valid AI sessions are available (async version).

    Returns:
        True if at least one valid session exists, False otherwise
    """
    try:
        settings = get_settings()
        session_manager = SessionManager(settings)

        # Register all providers
        from gateway.chatgpt_provider import ChatGPTProvider
        from gateway.claude_provider import ClaudeProvider
        from gateway.gemini_provider import GeminiProvider
        from gateway.perplexity_provider import PerplexityProvider
        from gateway.selector_loader import SelectorLoader

        # Get profiles directory and headless setting from settings
        profiles_dir = settings.profiles_dir
        headless = settings.gateway_headless

        # Create selector loader for DOM selectors
        project_root = Path(__file__).parent.parent.parent
        selector_path = project_root / "src" / "gateway" / "selectors.yaml"
        selector_loader = SelectorLoader(selector_path)

        session_manager.register("chatgpt", ChatGPTProvider(
            profile_dir=profiles_dir / "chatgpt",
            headless=headless,
            selector_loader=selector_loader,
        ))
        session_manager.register("claude", ClaudeProvider(
            profile_dir=profiles_dir / "claude",
            headless=headless,
            selector_loader=selector_loader,
        ))
        session_manager.register("gemini", GeminiProvider(
            profile_dir=profiles_dir / "gemini",
            headless=headless,
            selector_loader=selector_loader,
        ))
        session_manager.register("perplexity", PerplexityProvider(
            profile_dir=profiles_dir / "perplexity",
            headless=headless,
            selector_loader=selector_loader,
        ))

        # Load sessions and check status
        session_manager.load_all_sessions()
        session_status = await session_manager.check_all_sessions()

        # Check if at least one session is valid
        valid_sessions = [provider for provider, is_valid in session_status.items() if is_valid]
        return len(valid_sessions) > 0

    except Exception:
        return False


def _check_session_availability() -> bool:
    """
    Check if valid AI sessions are available.

    Returns:
        True if at least one valid session exists, False otherwise
    """
    try:
        return asyncio.run(_check_session_availability_async())
    except RuntimeError:
        # Handle case where event loop is already running
        import inspect
        if inspect.iscoroutinefunction(_check_session_availability_async):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_check_session_availability_async())
            finally:
                loop.close()
        return False


@app.command()
def resume(
    session_id: Annotated[str, typer.Argument(..., help="Pipeline session ID to resume")],
) -> None:
    """
    Resume an interrupted pipeline execution.

    Examples:
        aigenflow resume abc-123-def
    """
    # Find session directory
    session_dir = _find_session_dir(session_id)
    if not session_dir:
        console.print(f"[red]✗ Session not found: {session_id}[/red]")
        console.print("\n[bold]Available sessions:[/bold]")

        sessions = _list_available_sessions()
        if sessions:
            for s in sessions[:10]:
                status_color = "green" if s["state"] == "completed" else "yellow"
                console.print(
                    f"  [{status_color}]{s['id']}[/{status_color}] - "
                    f"{s['topic'][:50]}... (Phase {s['current_phase']}/5)"
                )
        else:
            console.print("  No sessions available")
        sys.exit(1)

    # Load session state
    state_file = session_dir / "pipeline_state.json"
    with open(state_file) as f:
        state_data = json.load(f)

    # Recreate session from saved state
    config_dict = state_data["config"]
    config_dict["output_dir"] = Path(config_dict.get("output_dir", "output"))

    # Recreate PipelineConfig
    config = PipelineConfig(
        topic=config_dict["topic"],
        doc_type=DocumentType(config_dict.get("doc_type", "bizplan")),
        template=TemplateType(config_dict.get("template", "default")),
        language=config_dict.get("language", "ko"),
        output_dir=config_dict["output_dir"],
        max_retries=config_dict.get("max_retries", 2),
        timeout_seconds=config_dict.get("timeout_seconds", 120),
    )

    # Recreate PipelineSession
    session = PipelineSession(**state_data)

    # Determine resume phase
    resume_phase = _get_resume_phase(session)

    # Display session info
    state_value = session.state.value if hasattr(session.state, "value") else session.state
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Resuming Pipeline Session[/bold cyan]\n"
        f"[dim]Session ID:[/dim] {session_id}\n"
        f"[dim]Topic:[/dim] {config.topic}\n"
        f"[dim]Current State:[/dim] {state_value}\n"
        f"[dim]Current Phase:[/dim] {session.current_phase}/5",
        title="[bold]Resume[/bold]",
        border_style="cyan"
    ))

    # Check if already completed
    if resume_phase == -1:
        console.print(Panel.fit(
            "[bold green]✓ This pipeline is already completed[/bold green]\n"
            "[dim]All 5 phases have been successfully executed.[/dim]",
            title="[bold]Info[/bold]",
            border_style="green"
        ))
        console.print(f"\n[dim]Output directory: {session_dir}[/dim]")
        sys.exit(0)

    # Check if resume phase is beyond total phases
    if resume_phase > TOTAL_PHASES:
        console.print(Panel.fit(
            "[bold green]✓ All phases completed[/bold green]\n"
            "[dim]No more phases to execute.[/dim]",
            title="[bold]Info[/bold]",
            border_style="green"
        ))
        sys.exit(0)

    # Check session availability
    if not _check_session_availability():
        console.print(
            "[red]Error: No valid AI sessions found.[/red]\n"
            "[yellow]Please run 'aigenflow setup' to configure sessions.[/yellow]"
        )
        sys.exit(1)

    # Display resume info
    console.print()
    console.print(f"[bold yellow]Resuming from Phase {resume_phase}...[/bold yellow]")
    console.print(f"[dim]Phases 1-{session.current_phase} already completed, skipping.[/dim]\n")

    # Set the from_phase in config
    config.from_phase = resume_phase

    # Create orchestrator and run pipeline
    try:
        settings = get_settings()
        template_manager = TemplateManager()
        session_manager = SessionManager(settings)

        # Get profiles directory and headless setting
        profiles_dir = settings.profiles_dir
        headless = settings.gateway_headless

        orchestrator = PipelineOrchestrator(
            settings=settings,
            template_manager=template_manager,
            session_manager=session_manager,
            enable_ui=True,
            enable_summarization=settings.enable_summarization,
            summarization_threshold=settings.summarization_threshold,
        )

        # Register agents with the router
        orchestrator.agent_router.register_agent(
            AgentType.CHATGPT,
            ChatGPTAgent(profile_dir=profiles_dir / "chatgpt", headless=headless)
        )
        orchestrator.agent_router.register_agent(
            AgentType.CLAUDE,
            ClaudeAgent(profile_dir=profiles_dir / "claude", headless=headless)
        )
        orchestrator.agent_router.register_agent(
            AgentType.GEMINI,
            GeminiAgent(profile_dir=profiles_dir / "gemini", headless=headless)
        )
        orchestrator.agent_router.register_agent(
            AgentType.PERPLEXITY,
            PerplexityAgent(profile_dir=profiles_dir / "perplexity", headless=headless)
        )

        # Load existing session into orchestrator
        orchestrator.current_session = session

        # Run the async pipeline with explicit cleanup
        import asyncio

        # Use explicit event loop for proper BrowserPool cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            updated_session = loop.run_until_complete(orchestrator.run_pipeline(config))
        finally:
            # Clean up all pending tasks
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            # FIX: Cleanup BrowserPool BEFORE closing loop
            try:
                from gateway.browser_pool import BrowserPool

                if BrowserPool._instance:
                    loop.run_until_complete(BrowserPool._instance.close_all())
            except Exception:
                pass  # Ignore cleanup errors during shutdown

            loop.close()
            asyncio.set_event_loop(None)

        # Display completion message
        console.print()
        final_state = updated_session.state.value if hasattr(updated_session.state, "value") else updated_session.state
        if final_state == "completed":
            console.print(Panel.fit(
                f"[bold green]✓ Pipeline Resumed and Completed Successfully[/bold green]\n\n"
                f"[dim]Session ID:[/dim] {session_id}\n"
                f"[dim]Output Directory:[/dim] {session_dir}\n"
                f"[dim]Phases Completed:[/dim] {updated_session.current_phase}",
                title="[bold]Success[/bold]",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold yellow]⚠ Pipeline Ended with State:[/bold yellow] {final_state}\n\n"
                f"[dim]Session ID:[/dim] {session_id}\n"
                f"[dim]You can try to resume again with:[/dim]\n"
                f"[dim]  aigenflow resume {session_id}[/dim]",
                title="[bold]Warning[/bold]",
                border_style="yellow"
            ))
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Pipeline interrupted by user.[/yellow]")
        console.print("[yellow]Session state has been saved. You can resume with 'aigenflow resume'.[/yellow]")
        raise typer.Exit(code=130)

    except Exception as exc:
        console.print()
        console.print(Panel.fit(
            f"[bold red]✗ Pipeline Failed[/bold red]\n\n"
            f"[dim]Error:[/dim] {exc}",
            title="[bold]Error[/bold]",
            border_style="red"
        ))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(app)
