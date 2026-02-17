"""
Relogin command for AigenFlow CLI.

Re-authenticate with AI providers.
"""

import sys

import typer
from rich.console import Console

from core import get_settings
from gateway.chatgpt_provider import ChatGPTProvider
from gateway.claude_provider import ClaudeProvider
from gateway.gemini_provider import GeminiProvider
from gateway.perplexity_provider import PerplexityProvider

console = Console()


def _validate_provider(provider: str) -> bool:
    """Validate provider name."""
    valid_providers = ["chatgpt", "claude", "gemini", "perplexity"]
    return provider.lower() in valid_providers


app = typer.Typer(help="Re-authenticate with providers")


@app.command()
def relogin(
    provider: str = typer.Argument(..., help="Provider name: chatgpt, claude, gemini, or perplexity"),
    headed: bool = typer.Option(False, "--headed", "-h", help="Use headed browser mode"),
) -> None:
    """
    Re-login to a specific AI provider.

    Examples:
        aigenflow relogin chatgpt
        aigenflow relogin claude --headed
    """
    # Validate provider
    if not _validate_provider(provider):
        console.print(f"[red]✗ Invalid provider: {provider}[/red]")
        console.print("[yellow]Valid providers: chatgpt, claude, gemini, perplexity[/yellow]")
        sys.exit(1)

    # Load settings
    settings = get_settings()

    # Override headless setting if --headed flag is provided
    if headed:
        settings.playwright_headless = False

    # Import asyncio
    import asyncio

    async def _run_relogin():
        """Run the relogin process."""
        # Provider class mapping
        provider_map = {
            "chatgpt": ChatGPTProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "perplexity": PerplexityProvider,
        }

        provider_class = provider_map.get(provider.lower())
        if not provider_class:
            console.print(f"[red]✗ Provider not found: {provider}[/red]")
            sys.exit(1)

        # Create provider instance
        provider_instance = provider_class(settings)

        # Check if session exists and is valid
        console.print(f"[bold]Checking {provider.capitalize()} session...[/bold]")
        is_valid = await provider_instance.check_session()

        if is_valid:
            console.print(f"[yellow]✓ {provider.capitalize()} session is already valid[/yellow]")
            console.print("[yellow]Use --force to re-login anyway[/yellow]")
            return

        # Run login flow
        console.print(f"[bold]Launching browser for {provider.capitalize()} login...[/bold]\n")
        console.print("[yellow]Please complete the login process in the browser.[/yellow]\n")

        try:
            await provider_instance.login_flow()
            provider_instance.save_session()
            console.print(f"[green]✓ {provider.capitalize()} login successful![/green]")
        except Exception as exc:
            console.print(f"\n[red]✗ {provider.capitalize()} login failed: {exc}[/red]")
            raise

    # Run the async relogin with proper cleanup
    try:
        # Use explicit event loop for proper BrowserPool cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_relogin())
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
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    typer.run(app)
