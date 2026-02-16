"""
Main CLI entry point for AigenFlow.

Provides unified CLI interface for all commands.
"""

import typer
from rich.console import Console

# Import CLI command apps and individual commands
from cli.cache import app as cache_app
from cli.check import check_cmd
from cli.config import app as config_app
from cli.relogin import relogin as relogin_command
from cli.resume import app as resume_app
from cli.run import run as run_command
from cli.setup import setup as setup_command
from cli.stats import app as stats_app
from cli.status import status as status_command
from config import LogEnvironment, configure_logging

console = Console()

# Create main Typer app
app = typer.Typer(
    help="AigenFlow - Multi-AI Pipeline CLI Tool for Automated Business Plan Generation",
    no_args_is_help=True,
    add_completion=False,
)


# Preserve existing run command behavior
def _preserve_run_command():
    """Preserve the original run command for backward compatibility."""
    console.print("[bold green]aigenflow v0.1.0[/bold green]")
    console.print("Multi-AI Pipeline CLI Tool for Automated Business Plan Generation")
    console.print("")
    console.print("[dim]Usage:[/dim]")
    console.print("[dim]  aigenflow run --topic \"Your topic here\"[/dim]")
    console.print("")
    console.print("[bold cyan]Available Commands:[/bold cyan]")
    console.print("  run        Execute pipeline and generate document")
    console.print("  setup       Interactive setup wizard for first-time configuration")
    console.print("  check       Check Playwright browser and AI provider sessions")
    console.print("  status      Display pipeline execution status")
    console.print("  resume      Resume interrupted pipeline execution")
    console.print("  config      Manage configuration settings")
    console.print("  cache       Manage AI response cache")
    console.print("  stats       Show token usage and cost statistics")
    console.print("")
    console.print("[bold cyan]Run Command Options:[/bold cyan]")
    console.print("  --topic     Document topic (required, min 10 characters)")
    console.print("  --type      Document type: bizplan or rd (default: bizplan)")
    console.print("  --language  Output language: ko or en (default: ko)")
    console.print("  --template  Template name (default: default)")
    console.print("  --output    Output directory override (default: output/)")
    console.print("")


# Main command (default when no subcommand is provided)
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
    log_level: str = typer.Option(
        "warning",
        "--log-level",
        help="Set logging level (debug, info, warning, error)",
    ),
    environment: str = typer.Option(
        "production",
        "--environment",
        "-e",
        help="Set logging environment (development, testing, production)",
    ),
) -> None:
    """
    AigenFlow CLI main entry point.
    """
    if version:
        console.print("[bold green]aigenflow v0.1.0[/bold green]")
        raise typer.Exit()

    # Configure logging based on environment and log level
    try:
        env = LogEnvironment(environment.lower())
    except ValueError:
        console.print(
            f"[red]Invalid environment: '{environment}'. "
            f"Valid options: development, testing, production[/red]"
        )
        raise typer.Exit(code=1)

    try:
        configure_logging(environment=env, log_level=log_level)
    except ValueError as e:
        console.print(f"[red]Invalid log level: {e}[/red]")
        raise typer.Exit(code=1)

    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        _preserve_run_command()


# Register all CLI commands as subcommands
app.add_typer(cache_app, name="cache", help="Manage AI response cache")
app.command()(check_cmd)  # Register check directly
app.command()(setup_command)  # Register setup directly
app.command()(relogin_command)  # Register relogin directly
app.command()(run_command)  # Register run directly
app.command()(status_command)  # Register status directly
app.add_typer(resume_app, name="resume", help="Resume interrupted pipeline execution")
app.add_typer(config_app, name="config", help="Manage configuration settings")
app.add_typer(stats_app, name="stats", help="Show token usage and cost statistics")


if __name__ == "__main__":
    app()
