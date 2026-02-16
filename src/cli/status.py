"""
Status command for AigenFlow CLI.

Display pipeline execution status.
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Sessions directory
SESSIONS_DIR = Path("output") / "sessions"


def _format_status(status: str) -> str:
    """Format status with emoji."""
    status_map = {
        "in_progress": "[yellow]⏳ In Progress[/yellow]",
        "completed": "[green]✓ Completed[/green]",
        "failed": "[red]✗ Failed[/red]",
        "paused": "[blue]⏸ Paused[/blue]",
    }
    return status_map.get(status, status)


def _format_phase(phase: str) -> str:
    """Format phase name for display."""
    phase_map = {
        "framing": "Phase 1: Framing",
        "research": "Phase 2: Research",
        "strategy": "Phase 3: Strategy",
        "writing": "Phase 4: Writing",
        "review": "Phase 5: Review",
    }
    return phase_map.get(phase, phase)


app = typer.Typer(help="Pipeline status")


@app.command()
def status(
    session_id: str | None = typer.Argument(None, help="Pipeline session ID"),
) -> None:
    """
    Display pipeline execution status.

    Examples:
        aigenflow status
        aigenflow status abc-123-def
    """
    # Ensure sessions directory exists
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # List all session files
    session_files = list(SESSIONS_DIR.glob("session_*.json"))

    if not session_files:
        console.print("[yellow]No pipeline sessions found[/yellow]")
        console.print("\n[bold]Start a new pipeline:[/bold]")
        console.print("  aigenflow run <prompt>")
        return

    # If session_id provided, show specific session
    if session_id:
        session_file = SESSIONS_DIR / f"session_{session_id}.json"
        if not session_file.exists():
            console.print(f"[red]✗ Session not found: {session_id}[/red]")
            console.print("\n[bold]Available sessions:[/bold]")
            for sf in session_files[:5]:
                sid = sf.stem.replace("session_", "")
                console.print(f"  - {sid}")
            return

        # Load and display session
        with open(session_file) as f:
            session_data = json.load(f)

        console.print(Panel.fit(
            f"[bold]Session:[/bold] {session_data['session_id']}\n"
            f"[bold]Phase:[/bold] {_format_phase(session_data['phase'])}\n"
            f"[bold]Status:[/bold] {_format_status(session_data['status'])}\n"
            f"[bold]Created:[/bold] {session_data['created_at']}\n"
            f"[bold]Updated:[/bold] {session_data['updated_at']}",
            title="[bold]Pipeline Session[/bold]",
            border_style="cyan"
        ))
        return

    # Show all sessions
    table = Table(title="Pipeline Sessions", show_header=True, header_style="bold magenta")
    table.add_column("Session ID", style="cyan", width=12)
    table.add_column("Phase", style="green", width=20)
    table.add_column("Status", width=15)
    table.add_column("Updated", style="blue", width=20)

    for session_file in sorted(session_files, key=lambda p: p.stat().st_mtime, reverse=True):
        with open(session_file) as f:
            session_data = json.load(f)

        table.add_row(
            session_data['session_id'],
            _format_phase(session_data['phase']),
            _format_status(session_data['status']),
            session_data['updated_at']
        )

    console.print(table)


if __name__ == "__main__":
    typer.run(app)
