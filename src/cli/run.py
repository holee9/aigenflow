"""
Run command for AigenFlow CLI.

Execute pipeline and generate business plan or R&D proposal documents.
"""

import asyncio
import warnings
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
from core.logger import get_logger
from core.models import AgentType, DocumentType, PipelineConfig, TemplateType
from gateway.session import SessionManager
from pipeline.orchestrator import PipelineOrchestrator
from templates.manager import TemplateManager

console = Console()
logger = get_logger(__name__)

app = typer.Typer(help="Execute pipeline and generate document")

# Suppress GC warnings from subprocess transport cleanup on Windows
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed transport")


def _validate_topic(topic: str) -> str:
    """
    Validate topic input.

    Args:
        topic: Topic string to validate

    Returns:
        Validated topic string

    Raises:
        typer.Exit: If topic is invalid
    """
    if not topic or not topic.strip():
        console.print("[red]Error: --topic is required[/red]")
        console.print("\n[dim]Usage: aigenflow run --topic 'your topic' --type bizplan[/dim]")
        raise typer.Exit(code=1)

    stripped = topic.strip()
    if len(stripped) < 10:
        console.print(
            f"[red]Error: Topic must be at least 10 characters. "
            f"Provided: {len(stripped)} characters[/red]"
        )
        raise typer.Exit(code=1)

    return stripped


async def _check_session_availability_async(headless: bool | None = None) -> bool:
    """
    Check if valid AI sessions are available (async version).

    Args:
        headless: Override headless setting from settings

    Returns:
        True if at least one valid session exists, False otherwise
    """
    try:
        settings = get_settings()
        session_manager = SessionManager(settings)

        # Register all providers
        from pathlib import Path

        from gateway.chatgpt_provider import ChatGPTProvider
        from gateway.claude_provider import ClaudeProvider
        from gateway.gemini_provider import GeminiProvider
        from gateway.perplexity_provider import PerplexityProvider
        from gateway.selector_loader import SelectorLoader

        # Get profiles directory and headless setting
        profiles_dir = settings.profiles_dir
        # Use override if provided, otherwise use settings
        if headless is None:
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

        if not valid_sessions:
            console.print("[red]Error: No valid AI sessions found.[/red]")
            console.print("[yellow]Please run 'aigenflow setup' to configure sessions.[/yellow]")
            return False

        # Optionally show valid sessions
        if len(valid_sessions) < len(session_status):
            console.print(f"[yellow]Warning: Only {len(valid_sessions)}/{len(session_status)} sessions are valid[/yellow]")

        return True

    except Exception as exc:
        console.print(f"[red]Error checking sessions: {exc}[/red]")
        console.print("[yellow]Please run 'aigenflow setup' to configure sessions.[/yellow]")
        return False


def _check_session_availability(headless: bool | None = None) -> bool:
    """
    Check if valid AI sessions are available.

    Args:
        headless: Override headless setting from settings

    Returns:
        True if at least one valid session exists, False otherwise
    """
    try:
        return asyncio.run(_check_session_availability_async(headless))
    except RuntimeError:
        # Handle case where event loop is already running
        import inspect
        if inspect.iscoroutinefunction(_check_session_availability_async):
            # Create new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_check_session_availability_async())
            finally:
                loop.close()
        return False


def _map_doc_type_to_template(doc_type: DocumentType) -> TemplateType:
    """
    Map document type to appropriate template.

    Args:
        doc_type: Document type (bizplan or rd)

    Returns:
        Corresponding template type
    """
    if doc_type == DocumentType.RD:
        return TemplateType.RD
    return TemplateType.DEFAULT


@app.command()
def run(
    topic: Annotated[str, typer.Option("--topic", "-t", help="Document topic (minimum 10 characters)", show_default=False)] = None,
    doc_type: Annotated[
        DocumentType,
        typer.Option("--type", "-y", help="Document type", case_sensitive=False)
    ] = DocumentType.BIZPLAN,
    language: Annotated[
        str,
        typer.Option("--language", "-l", help="Output language", show_default="ko")
    ] = "ko",
    template: Annotated[
        str,
        typer.Option("--template", help="Template name", show_default="default")
    ] = "default",
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output directory override", show_default="output/")
    ] = None,
    headed: Annotated[
        bool,
        typer.Option("--headed/--headless", help="Show browser window for debugging (default: headless)")
    ] = False,  # Changed: Always headless by default for background execution
) -> None:
    """
    Execute pipeline and generate business plan or R&D proposal document.

    Examples:
        aigenflow run --topic "AI-powered sustainable agriculture" --type bizplan
        aigenflow run -t "Quantum computing for drug discovery" -y rd --language en
        aigenflow run --topic "Your topic" --type bizplan --output ./my_output
    """
    # Validate topic
    if topic is None:
        console.print("[red]Error: --topic is required[/red]")
        console.print("\n[dim]Usage: aigenflow run --topic 'your topic' --type bizplan[/dim]")
        raise typer.Exit(code=1)

    validated_topic = _validate_topic(topic)

    # Check session availability (pass headless setting from command line flag)
    if not _check_session_availability(headless=not headed):
        console.print(
            "[red]Error: No valid AI sessions found.[/red]\n"
            "[yellow]Please run 'aigenflow setup' to configure sessions.[/yellow]"
        )
        raise typer.Exit(code=1)

    # Map document type to template
    template_type = _map_doc_type_to_template(doc_type)
    if template != "default":
        # Use explicit template if provided
        template_type = TemplateType(template)

    # Create pipeline config
    settings = get_settings()
    output_dir = Path(output) if output else Path(settings.output_dir)

    config = PipelineConfig(
        topic=validated_topic,
        doc_type=doc_type,
        template=template_type,
        language=language,
        output_dir=output_dir,
    )

    # Display startup message
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Starting AigenFlow Pipeline[/bold cyan]\n"
        f"[dim]Topic:[/dim] {validated_topic}\n"
        f"[dim]Type:[/dim] {doc_type.value}\n"
        f"[dim]Language:[/dim] {language}\n"
        f"[dim]Template:[/dim] {template_type.value}",
        title="[bold]Run[/bold]",
        border_style="cyan"
    ))
    console.print()

    # Create orchestrator and run pipeline
    try:
        template_manager = TemplateManager()
        session_manager = SessionManager(settings)

        # Get profiles directory and headless setting
        profiles_dir = settings.profiles_dir
        # Command-line flag takes precedence over settings
        headless = not headed  # headed=True means headless=False

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

        # Run the async pipeline with explicit cleanup
        import asyncio

        # Use explicit event loop for proper BrowserPool cleanup
        logger.debug("[run] Creating new event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("[run] Event loop created and set")

        # IMPORTANT: Reset BrowserPool singleton when creating new event loop
        # Playwright contexts are bound to their original event loop and cannot
        # be used in a different loop. The session check happens in the default
        # loop, so we need to reset the pool for the pipeline.
        try:
            from gateway.browser_pool import BrowserPool
            if BrowserPool._instance:
                logger.debug("[run] Resetting BrowserPool for new event loop")
                loop.run_until_complete(BrowserPool._instance.close_all())
            BrowserPool._instance = None
            BrowserPool._lock = asyncio.Lock()
            logger.debug("[run] BrowserPool reset completed")
        except Exception as e:
            logger.warning(f"[run] BrowserPool reset warning: {e}")

        try:
            logger.debug("[run] Starting pipeline execution")
            session = loop.run_until_complete(orchestrator.run_pipeline(config))
            logger.debug("[run] Pipeline execution completed")
        finally:
            logger.debug("[run] Starting cleanup in finally block")

            # Clean up all pending tasks
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            logger.debug(f"[run] Found {len(pending)} pending tasks")
            for task in pending:
                task.cancel()
            if pending:
                logger.debug(f"[run] Gathering {len(pending)} cancelled tasks")
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                logger.debug("[run] Pending tasks gathered")

            # NOTE: Skip BrowserPool cleanup to avoid event loop state issues
            # After task cancellation, the event loop cannot reliably execute new coroutines.
            # OS automatically terminates child processes when parent exits.
            logger.debug("[run] Skipping BrowserPool cleanup (OS will handle)")
            try:
                from gateway.browser_pool import BrowserPool
                if BrowserPool._instance:
                    logger.debug("[run] BrowserPool instance exists, deferring cleanup to OS")
            except Exception as e:
                logger.warning(f"[run] BrowserPool check warning: {e}")

            logger.debug("[run] Closing event loop")
            loop.close()
            logger.debug("[run] Event loop closed")
            logger.debug("[run] Setting event loop to None")
            asyncio.set_event_loop(None)
            logger.debug("[run] Event loop set to None, cleanup complete")

        # Display completion message
        console.print()
        # Handle both string and enum state values
        state_value = session.state.value if hasattr(session.state, 'value') else session.state
        if state_value == "completed":
            console.print(Panel.fit(
                f"[bold green]✓ Pipeline Completed Successfully[/bold green]\n\n"
                f"[dim]Session ID:[/dim] {session.session_id}\n"
                f"[dim]Output Directory:[/dim] {output_dir / session.session_id}\n"
                f"[dim]Phases Completed:[/dim] {session.current_phase}",
                title="[bold]Success[/bold]",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold yellow]⚠ Pipeline Ended with State:[/bold yellow] {state_value}\n\n"
                f"[dim]Session ID:[/dim] {session.session_id}\n"
                f"[dim]You can try to resume with:[/dim]\n"
                f"[dim]  aigenflow resume {session.session_id}[/dim]",
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
    app()
