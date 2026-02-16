"""
Phase summary display using Rich Table.

Provides beautiful tables for phase completion with:
- Phase number and name
- Agents used
- Execution time
- Status indicators
"""


from rich.console import Console
from rich.table import Table

from core.models import PhaseResult, PhaseStatus, PipelineSession


class PhaseSummary:
    """
    Rich table for phase completion summary.

    Displays phase execution results in a formatted table.
    """

    def __init__(self, console: Console | None = None) -> None:
        """
        Initialize PhaseSummary.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()

    def show_session_phases(self, session: PipelineSession) -> None:
        """
        Display a summary table for all phases in a session.

        Args:
            session: Pipeline session with phase results
        """
        if not session.results:
            self.console.print("[yellow]No phase results to display[/yellow]")
            return

        table = Table(title=f"Phase Summary - {session.session_id[:8]}")

        table.add_column("Phase", style="cyan", width=12)
        table.add_column("Agents", style="yellow", width=30)
        table.add_column("Time", style="green", width=12)
        table.add_column("Status", width=10)

        for result in session.results:
            # Format phase name
            phase_name = f"Phase {result.phase_number}"

            # Format agents
            agents = self._format_agents(result)

            # Format time
            time_str = self._format_time(result)

            # Format status with color
            status_str = self._format_status(result.status)

            table.add_row(phase_name, agents, time_str, status_str)

        self.console.print(table)

    def show_single_phase(self, result: PhaseResult) -> None:
        """
        Display a summary for a single phase result.

        Args:
            result: Phase result to display
        """
        table = Table(title=f"Phase {result.phase_number} Details")

        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Phase Name", result.phase_name)
        table.add_row("Status", self._format_status(result.status))

        if result.started_at:
            table.add_row("Started", result.started_at.strftime("%Y-%m-%d %H:%M:%S"))
        if result.completed_at:
            table.add_row("Completed", result.completed_at.strftime("%Y-%m-%d %H:%M:%S"))

        if result.ai_responses:
            table.add_row("AI Responses", str(len(result.ai_responses)))
            for i, response in enumerate(result.ai_responses, 1):
                status = "[green]✓[/green]" if response.success else "[red]✗[/red]"
                table.add_row(
                    f"  Response {i}",
                    f"{status} {response.agent_name.value} - {response.task_name}",
                )

        self.console.print(table)

    def _format_agents(self, result: PhaseResult) -> str:
        """
        Format agent names from phase result.

        Args:
            result: Phase result with AI responses

        Returns:
            Comma-separated list of agent names
        """
        if not result.ai_responses:
            return "-"

        agents = [resp.agent_name.value for resp in result.ai_responses]
        return ", ".join(agents)

    def _format_time(self, result: PhaseResult) -> str:
        """
        Format execution time from phase result.

        Args:
            result: Phase result with timestamps

        Returns:
            Formatted time string or "-"
        """
        if result.started_at and result.completed_at:
            duration = (result.completed_at - result.started_at).total_seconds()
            return f"{duration:.1f}s"
        return "-"

    def _format_status(self, status: PhaseStatus) -> str:
        """
        Format status with color coding.

        Args:
            status: Phase status

        Returns:
            Colored status string
        """
        status_colors = {
            PhaseStatus.COMPLETED: "[green]✓ Completed[/green]",
            PhaseStatus.FAILED: "[red]✗ Failed[/red]",
            PhaseStatus.SKIPPED: "[dim]⊘ Skipped[/dim]",
            PhaseStatus.IN_PROGRESS: "[yellow]⟳ In Progress[/yellow]",
        }

        return status_colors.get(status, str(status.value))

    def show_progress_table(
        self,
        phase_number: int,
        phase_name: str,
        total_phases: int = 5,
    ) -> None:
        """
        Display a simple progress table.

        Args:
            phase_number: Current phase number
            phase_name: Current phase name
            total_phases: Total number of phases
        """
        table = Table(title="Pipeline Progress")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        # Calculate percentage
        percentage = (phase_number / total_phases) * 100

        table.add_row("Current Phase", f"Phase {phase_number}/{total_phases}")
        table.add_row("Phase Name", phase_name)
        table.add_row("Progress", f"{percentage:.0f}%")

        self.console.print(table)
