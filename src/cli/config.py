"""
Config command for AigenFlow CLI.

Manages configuration settings.
"""

import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core import get_settings

console = Console()


app = typer.Typer(help="Configuration management")


@app.command()
def config(
    action: str = typer.Argument(..., help="Action: show, set, or list"),
    key: str | None = typer.Option(None, help="Configuration key"),
    value: str | None = typer.Option(None, help="Configuration value"),
) -> None:
    """
    Manage AigenFlow configuration.

    Examples:
        aigenflow config show
        aigenflow config list
        aigenflow config set playwright_headless false
    """
    settings = get_settings()

    if action == "show":
        # Show all configuration
        console.print(Panel.fit(
            "[bold]AigenFlow Configuration[/bold]\n\n"
            f"[bold]Playwright Headless:[/bold] {settings.playwright_headless}\n"
            f"[bold]Profile Directory:[/bold] {settings.profile_dir}\n"
            f"[bold]Debug Mode:[/bold] {getattr(settings, 'debug', False)}",
            title="[bold]Current Settings[/bold]",
            border_style="cyan"
        ))

    elif action == "list":
        # List all configuration keys
        table = Table(title="Configuration Keys", show_header=True)
        table.add_column("Key", style="cyan", width=30)
        table.add_column("Value", style="green", width=30)
        table.add_column("Description", style="blue", width=40)

        # Add configuration items
        table.add_row("playwright_headless", str(settings.playwright_headless), "Run browser in headless mode")
        table.add_row("profile_dir", str(settings.profile_dir), "Browser profile directory")
        table.add_row("debug", str(getattr(settings, 'debug', False)), "Enable debug mode")

        console.print(table)

    elif action == "set":
        if not key or not value:
            console.print("[red]✗ Error: set requires both key and value[/red]")
            console.print("\n[bold]Usage:[/bold]")
            console.print("  aigenflow config set <key> <value>")
            console.print("\n[bold]Example:[/bold]")
            console.print("  aigenflow config set playwright_headless false")
            sys.exit(1)

        # Convert value to appropriate type
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)

        # NOTE: Config setting via CLI is intentionally not implemented.
        # Users should edit .env file directly for permanent configuration changes.
        # This keeps the configuration source of truth simple and explicit.
        console.print("[yellow]Config set functionality is under development[/yellow]")
        console.print(f"[yellow]Would set: {key} = {value}[/yellow]")
        console.print("\n[yellow]To permanently set configuration, edit .env file[/yellow]")

    else:
        console.print(f"[red]✗ Unknown action: {action}[/red]")
        console.print("[yellow]Valid actions: show, list, set[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    typer.run(app)
