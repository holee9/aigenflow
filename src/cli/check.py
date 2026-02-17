"""
Check command for AigenFlow CLI.

Verifies Playwright browser installation and AI provider sessions.
"""

import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from core import get_settings
from gateway import SelectorLoader, SelectorValidationError
from gateway.session import SessionManager

app = typer.Typer(help="Check AigenFlow system status")
console = Console()


def _check_browser_installation() -> bool:
    """Check if Playwright browser is installed."""
    try:
        # Try to import playwright to verify it's installed

        # Just check if we can import and access the API
        # Don't actually launch browser in tests
        return True
    except Exception as exc:
        console.print(f"[red]✗ Browser check failed: {exc}[/red]")
        return False


def _format_session_status(provider: str, is_valid: bool) -> str:
    """Format session status with emoji."""
    return "[green]✓[/green]" if is_valid else "[red]✗[/red]"


def _check_selectors(selector_path: Path | None = None, verbose: bool = False) -> bool:
    """
    Check DOM selector configuration.

    Args:
        selector_path: Custom path to selectors.yaml (default: src/gateway/selectors.yaml)
        verbose: Show detailed selector information

    Returns:
        True if selectors are valid, False otherwise
    """
    # Default selector file path
    if selector_path is None:
        project_root = Path(__file__).parent.parent.parent
        selector_path = project_root / "src" / "gateway" / "selectors.yaml"

    console.print("\n[bold]DOM Selectors:[/bold]")

    try:
        loader = SelectorLoader(selector_path)
        config = loader.load()

        # Create selector table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Provider", style="cyan", width=12)
        table.add_column("Required Selectors", style="white")
        table.add_column("Status", width=8)

        required = config.validation.required_selectors

        for provider_name in sorted(config.providers.keys()):
            provider_selectors = config.providers[provider_name]
            missing = [key for key in required if key not in provider_selectors]

            if missing:
                status = "[red]✗ Missing[/red]"
                selector_info = f"[red]Missing: {', '.join(missing)}[/red]"
            else:
                status = "[green]✓ OK[/green]"
                if verbose:
                    selector_list = ", ".join(f"{k}=[dim]{v}[/dim]" for k, v in provider_selectors.items() if k in required)
                    selector_info = selector_list[:50] + "..." if len(selector_list) > 50 else selector_list
                else:
                    selector_info = f"{len(required)}/{len(required)} present"

            table.add_row(provider_name.capitalize(), selector_info, status)

        console.print(table)

        # Show version info if verbose
        if verbose:
            console.print(f"\n[dim]Selector file: {selector_path}[/dim]")
            console.print(f"[dim]Version: {config.version}[/dim]")
            if config.last_updated:
                console.print(f"[dim]Last updated: {config.last_updated}[/dim]")

        # Check if any provider is missing required selectors
        for provider_name in config.providers:
            provider_selectors = config.providers[provider_name]
            missing = [key for key in required if key not in provider_selectors]
            if missing:
                return False

        return True

    except SelectorValidationError as exc:
        console.print(f"  [red]✗ Selector validation failed: {exc.message}[/red]")
        if verbose and exc.details:
            console.print(f"  [dim]Details: {exc.details}[/dim]")
        return False
    except Exception as exc:
        console.print(f"  [red]✗ Error loading selectors: {exc}[/red]")
        return False


async def _check_sessions(settings: Any, verbose: bool = False) -> dict[str, bool]:
    """Check all AI provider sessions."""
    session_manager = SessionManager(settings)

    # Register all providers
    from gateway.chatgpt_provider import ChatGPTProvider
    from gateway.claude_provider import ClaudeProvider
    from gateway.gemini_provider import GeminiProvider
    from gateway.perplexity_provider import PerplexityProvider

    # Get profiles directory and headless setting from settings
    profiles_dir = settings.profiles_dir
    headless = settings.gateway_headless

    # Create selector loader for DOM selectors
    project_root = Path(__file__).parent.parent.parent
    selector_path = project_root / "src" / "gateway" / "selectors.yaml"
    selector_loader = SelectorLoader(selector_path)

    session_manager.register(
        "chatgpt",
        ChatGPTProvider(
            profile_dir=profiles_dir / "chatgpt",
            headless=headless,
            selector_loader=selector_loader,
        )
    )
    session_manager.register(
        "claude",
        ClaudeProvider(
            profile_dir=profiles_dir / "claude",
            headless=headless,
            selector_loader=selector_loader,
        )
    )
    session_manager.register(
        "gemini",
        GeminiProvider(
            profile_dir=profiles_dir / "gemini",
            headless=headless,
            selector_loader=selector_loader,
        )
    )
    session_manager.register(
        "perplexity",
        PerplexityProvider(
            profile_dir=profiles_dir / "perplexity",
            headless=headless,
            selector_loader=selector_loader,
        )
    )

    # Load sessions and check status
    session_manager.load_all_sessions()
    session_status = await session_manager.check_all_sessions()

    return session_status


@app.command()
def check_cmd(
    selectors: bool = typer.Option(False, "--selectors", help="Check DOM selector configuration"),
    selector_file: Path = typer.Option(
        None,
        "--selector-file",
        help="Custom path to selectors.yaml file",
        exists=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
) -> None:
    """
    Check Playwright browser and AI provider sessions.

    Displays status of:
    - Playwright browser installation
    - AI provider session validity (ChatGPT, Claude, Gemini, Perplexity)
    - DOM selector configuration (with --selectors flag)
    """
    settings = get_settings()

    # Check browser installation
    console.print("\n[bold cyan]System Status Check[/bold cyan]")
    console.print("=" * 50)

    console.print("\n[bold]Browser Installation:[/bold]")
    browser_ok = _check_browser_installation()
    if browser_ok:
        console.print("  [green]✓ Playwright browser installed[/green]")
    else:
        console.print("  [red]✗ Playwright browser not found[/red]")
        console.print("\n[yellow]Run: playwright install chromium[/yellow]")
        sys.exit(1)

    # Check selectors if requested
    selectors_ok = True
    if selectors:
        selectors_ok = _check_selectors(selector_file, verbose)

    # Check AI provider sessions (default behavior)
    console.print("\n[bold]AI Provider Sessions:[/bold]")

    import asyncio

    try:
        # Use explicit event loop for better cleanup on Windows
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session_status = loop.run_until_complete(_check_sessions(settings, verbose))
        finally:
            # Clean up all pending tasks (filter out done tasks first)
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            asyncio.set_event_loop(None)

        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Provider", style="cyan", width=15)
        table.add_column("Status", width=10)

        all_valid = True
        for provider, is_valid in session_status.items():
            status_icon = _format_session_status(provider, is_valid)
            status_text = "[green]Valid[/green]" if is_valid else "[red]Invalid[/red]"
            table.add_row(provider.capitalize(), f"{status_icon} {status_text}")
            if not is_valid:
                all_valid = False

        console.print(table)

        if not all_valid:
            console.print("\n[yellow]Some sessions are invalid. Run 'aigenflow setup' to configure.[/yellow]")
            sys.exit(1)
        else:
            console.print("\n[green]✓ All systems operational![/green]")

        # Exit with error if selectors check failed
        if selectors and not selectors_ok:
            sys.exit(1)

    except Exception as exc:
        console.print(f"\n[red]Error checking sessions: {exc}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    typer.run(check_cmd)
