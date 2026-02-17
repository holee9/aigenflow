"""
Tests for PhaseSummary class.

Uses TDD approach: tests written before implementation.
"""

from datetime import datetime, timedelta

from src.core.models import (
    AgentResponse,
    AgentType,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    create_phase_result,
)
from src.ui.summary import PhaseSummary


class TestPhaseSummary:
    """Test suite for PhaseSummary class."""

    def test_init_default_console(self):
        """Test PhaseSummary initializes with default console."""
        summary = PhaseSummary()

        assert summary.console is not None

    def test_init_custom_console(self):
        """Test PhaseSummary initializes with custom console."""
        from rich.console import Console

        console = Console()
        summary = PhaseSummary(console=console)

        assert summary.console == console

    def test_show_session_phases_with_no_results(self):
        """Test show_session_phases with empty results."""
        summary = PhaseSummary()
        config = PipelineConfig(topic="Test topic for empty session")
        session = PipelineSession(config=config)

        # Should not crash
        summary.show_session_phases(session)

        assert True

    def test_show_session_phases_with_results(self):
        """Test show_session_phases with phase results."""
        summary = PhaseSummary()
        config = PipelineConfig(topic="Test topic for session with results")
        session = PipelineSession(config=config)

        # Add a phase result
        result = create_phase_result(1, "Phase 1: Framing")
        result.status = PhaseStatus.COMPLETED
        result.started_at = datetime.now()
        result.completed_at = result.started_at + timedelta(seconds=10)
        session.add_result(result)

        # Should not crash
        summary.show_session_phases(session)

        assert True

    def test_show_single_phase(self):
        """Test show_single_phase displays phase details."""
        summary = PhaseSummary()

        result = create_phase_result(1, "Phase 1: Framing")
        result.status = PhaseStatus.COMPLETED
        result.started_at = datetime.now()
        result.completed_at = result.started_at + timedelta(seconds=10)

        # Should not crash
        summary.show_single_phase(result)

        assert True

    def test_show_single_phase_with_responses(self):
        """Test show_single_phase with AI responses."""
        summary = PhaseSummary()

        result = create_phase_result(1, "Phase 1: Framing")
        result.status = PhaseStatus.COMPLETED

        # Add AI responses
        response1 = AgentResponse(
            agent_name=AgentType.CHATGPT,
            task_name="brainstorm_chatgpt",
            content="Brainstorming content",
            tokens_used=100,
            response_time=1.5,
            success=True,
        )
        response2 = AgentResponse(
            agent_name=AgentType.CLAUDE,
            task_name="validate_claude",
            content="Validation content",
            tokens_used=150,
            response_time=2.0,
            success=True,
        )
        result.ai_responses = [response1, response2]

        # Should not crash
        summary.show_single_phase(result)

        assert True

    def test_format_agents(self):
        """Test _format_agents formats agent names correctly."""
        summary = PhaseSummary()

        result = create_phase_result(1, "Phase 1")

        # No agents
        agents = summary._format_agents(result)
        assert agents == "-"

        # With agents
        response1 = AgentResponse(
            agent_name=AgentType.CHATGPT,
            task_name="task1",
            content="",
            tokens_used=0,
            response_time=0,
            success=True,
        )
        response2 = AgentResponse(
            agent_name=AgentType.CLAUDE,
            task_name="task2",
            content="",
            tokens_used=0,
            response_time=0,
            success=True,
        )
        result.ai_responses = [response1, response2]

        agents = summary._format_agents(result)
        assert "chatgpt" in agents
        assert "claude" in agents

    def test_format_time(self):
        """Test _format_time formats duration correctly."""
        summary = PhaseSummary()

        result = create_phase_result(1, "Phase 1")

        # No timestamps
        time_str = summary._format_time(result)
        assert time_str == "-"

        # With timestamps
        result.started_at = datetime.now()
        result.completed_at = result.started_at + timedelta(seconds=10)

        time_str = summary._format_time(result)
        assert "10.0s" in time_str

    def test_format_status(self):
        """Test _format_status color codes statuses."""
        summary = PhaseSummary()

        # COMPLETED
        status_str = summary._format_status(PhaseStatus.COMPLETED)
        assert "✓" in status_str
        assert "[green]" in status_str

        # FAILED
        status_str = summary._format_status(PhaseStatus.FAILED)
        assert "✗" in status_str
        assert "[red]" in status_str

        # SKIPPED
        status_str = summary._format_status(PhaseStatus.SKIPPED)
        assert "⊘" in status_str
        assert "[dim]" in status_str

        # IN_PROGRESS
        status_str = summary._format_status(PhaseStatus.IN_PROGRESS)
        assert "⟳" in status_str
        assert "[yellow]" in status_str

    def test_show_progress_table(self):
        """Test show_progress_table displays progress."""
        summary = PhaseSummary()

        # Should not crash
        summary.show_progress_table(
            phase_number=2,
            phase_name="Phase 2: Research",
            total_phases=5,
        )

        assert True

    def test_show_session_phases_multiple_phases(self):
        """Test show_session_phases with multiple phase results."""
        summary = PhaseSummary()
        config = PipelineConfig(topic="Test topic for multi-phase session")
        session = PipelineSession(config=config)

        # Add multiple phase results
        for i in range(1, 4):
            result = create_phase_result(i, f"Phase {i}")
            result.status = PhaseStatus.COMPLETED
            result.started_at = datetime.now()
            result.completed_at = result.started_at + timedelta(seconds=i * 10)
            session.add_result(result)

        # Should not crash
        summary.show_session_phases(session)

        assert True
