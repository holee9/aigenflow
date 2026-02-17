"""
Setup command for AigenFlow CLI.

Interactive wizard for first-time configuration and browser setup.
"""

import sys
import warnings

import typer
from rich.console import Console
from rich.panel import Panel

from core import get_settings
from gateway.session import SessionManager

console = Console()

# Suppress GC warnings from subprocess transport cleanup on Windows
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed transport")


app = typer.Typer(help="Setup AigenFlow configuration")


def _check_browser_installation() -> bool:
    """Check if Playwright browser is installed."""
    try:
        return True
    except Exception as exc:
        console.print(f"[red]✗ Browser check failed: {exc}[/red]")
        return False


def _show_setup_wizard() -> None:
    """Display interactive setup wizard."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]AigenFlow Setup Wizard[/bold cyan]\n\n"
        "This wizard will guide you through:\n"
        "1. Verifying Playwright browser installation\n"
        "2. Launching browser in headed mode\n"
        "3. Logging into AI providers (ChatGPT, Claude, Gemini, Perplexity)\n"
        "4. Saving session cookies for future use",
        title="[bold]Welcome[/bold]",
        border_style="cyan"
    ))
    console.print()


def _validate_provider(provider: str) -> bool:
    """Validate provider name."""
    valid_providers = ["chatgpt", "claude", "gemini", "perplexity", "all"]
    return provider.lower() in valid_providers


@app.command()
def setup(
    provider: str = typer.Option("all", "--provider", "-p", help="Specific provider to setup (chatgpt, claude, gemini, perplexity, all)"),
    headed: bool = typer.Option(False, "--headed", "-h", help="Use headed browser mode"),
) -> None:
    """
    Setup AigenFlow with interactive wizard.

    Examples:
        aigenflow setup              # Setup all providers
        aigenflow setup --provider claude   # Setup only Claude
        aigenflow setup --headed     # Use headed browser mode
    """
    # Validate provider
    if not _validate_provider(provider):
        console.print(f"[red]✗ Invalid provider: {provider}[/red]")
        console.print("[yellow]Valid providers: chatgpt, claude, gemini, perplexity, all[/yellow]")
        sys.exit(1)

    # Show welcome message
    _show_setup_wizard()

    # Check browser installation
    console.print("[bold]Step 1: Verifying Playwright browser...[/bold]")
    browser_ok = _check_browser_installation()
    if not browser_ok:
        console.print("\n[red]✗ Playwright browser not found[/red]")
        console.print("\n[yellow]Please install Playwright browser:[/yellow]")
        console.print("  playwright install chromium")
        sys.exit(1)
    console.print("[green]✓ Playwright browser installed[/green]\n")

    # Load settings
    settings = get_settings()

    # Setup always uses headed mode for user login interaction
    settings.gateway_headless = False

    # Import asyncio here to avoid issues with tests
    import asyncio

    async def _run_setup():
        """Run the setup process."""
        session_manager = SessionManager(settings)

        # Register all providers
        from pathlib import Path

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

        if provider.lower() == "all":
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
            console.print("[bold]Step 2: Launching browser and logging into all providers...[/bold]\n")
        else:
            provider_map = {
                "chatgpt": (ChatGPTProvider, "chatgpt"),
                "claude": (ClaudeProvider, "claude"),
                "gemini": (GeminiProvider, "gemini"),
                "perplexity": (PerplexityProvider, "perplexity"),
            }
            provider_info = provider_map.get(provider.lower())
            if provider_info:
                provider_class, provider_name = provider_info
                session_manager.register(
                    provider_name,
                    provider_class(
                        profile_dir=profiles_dir / provider_name,
                        headless=headless,
                        selector_loader=selector_loader,
                    )
                )
                console.print(f"[bold]Step 2: Launching browser and logging into {provider.capitalize()}...[/bold]\n")

        # Run login flow
        try:
            console.print("[yellow]Browser will open in headed mode for login...[/yellow]")
            console.print("[yellow]Please complete the login process in the browser.[/yellow]\n")

            await session_manager.login_all_expired()
            await session_manager.save_all_sessions()

            console.print("[green]✓ Setup completed successfully![/green]")
            console.print("\n[bold]Next steps:[/bold]")
            console.print("  Run 'aigenflow check' to verify your sessions")
            console.print("  Run 'aigenflow status' to see pipeline status")

        except Exception as exc:
            console.print(f"\n[red]✗ Setup failed: {exc}[/red]")
            raise

    # Run the async setup
    try:
        # Use explicit event loop for better cleanup on Windows
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_setup())
        finally:
            # Clean up all pending tasks (filter out done tasks first)
            pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            # FIX: Cleanup BrowserPool BEFORE closing loop (critical!)
            # This must happen while event loop is still running
            try:
                from gateway.browser_pool import BrowserPool

                if BrowserPool._instance:
                    loop.run_until_complete(BrowserPool._instance.close_all())
            except Exception as e:
                console.print(f"[yellow]BrowserPool cleanup warning: {e}[/yellow]")

            loop.close()

            # FIX: Set event loop to None BEFORE Python garbage collection
            # This prevents "Event loop is closed" errors from subprocess transports
            asyncio.set_event_loop(None)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    app()
