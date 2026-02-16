"""
Pipeline progress display using Rich Progress.

Provides real-time progress tracking for pipeline execution with:
- Current phase indicator
- Agent being executed
- Progress percentage
- Time elapsed/remaining
"""


from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from core.models import PipelineSession


class PipelineProgress:
    """
    Rich progress bar for pipeline execution.

    Displays a beautiful progress bar with current phase,
    agent information, and timing details.
    """

    def __init__(self, console: Console | None = None) -> None:
        """
        Initialize PipelineProgress.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.task_id: TaskID | None = None
        self.current_phase = 0
        self.total_phases = 5

    def start(self, total_phases: int = 5) -> None:
        """
        Start the progress display.

        Args:
            total_phases: Total number of phases in pipeline
        """
        self.total_phases = total_phases
        self.progress.start()
        self.task_id = self.progress.add_task(
            "[cyan]Starting pipeline...",
            total=total_phases,
        )

    def update_phase(
        self,
        phase_number: int,
        phase_name: str,
        agent_name: str,
    ) -> None:
        """
        Update progress for current phase.

        Args:
            phase_number: Current phase number (1-5)
            phase_name: Name of the phase
            agent_name: Name of the agent being executed
        """
        if self.task_id is None:
            return

        self.current_phase = phase_number
        self.progress.update(
            self.task_id,
            description=f"[cyan]Phase {phase_number}: {phase_name}[/cyan] | [yellow]{agent_name}[/yellow]",
            completed=phase_number,
        )

    def complete_phase(self, phase_number: int) -> None:
        """
        Mark a phase as completed.

        Args:
            phase_number: Phase number to mark complete
        """
        if self.task_id is None:
            return

        self.progress.update(
            self.task_id,
            completed=phase_number,
        )

    def stop(self) -> None:
        """Stop the progress display."""
        if self.task_id is not None:
            self.progress.update(
                self.task_id,
                description="[green]Pipeline completed![/green]",
                completed=self.total_phases,
            )
        self.progress.stop()

    def show_session_summary(self, session: PipelineSession) -> None:
        """
        Display a summary table for the session.

        Args:
            session: Pipeline session to summarize
        """
        table = Table(title=f"Pipeline Summary - {session.session_id[:8]}")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Session ID", session.session_id[:16] + "...")
        table.add_row("Topic", session.config.topic[:40] + "...")
        table.add_row("Document Type", session.config.doc_type.value)
        table.add_row("Language", session.config.language)
        table.add_row("State", f"[{'green' if session.state.value == 'completed' else 'red'}]{session.state.value}[/]")
        table.add_row("Phases Completed", str(len(session.results)))

        table.add_row("Created", session.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Updated", session.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

        self.console.print(table)
