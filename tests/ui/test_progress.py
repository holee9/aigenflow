"""
Tests for PipelineProgress class.

Uses TDD approach: tests written before implementation.
"""

from rich.console import Console

from src.core.models import PipelineConfig, PipelineSession, PipelineState
from src.ui.progress import PipelineProgress


class TestPipelineProgress:
    """Test suite for PipelineProgress class."""

    def test_init_default_console(self):
        """Test PipelineProgress initializes with default console."""
        progress = PipelineProgress()

        assert progress.console is not None
        assert progress.task_id is None
        assert progress.current_phase == 0
        assert progress.total_phases == 5

    def test_init_custom_console(self):
        """Test PipelineProgress initializes with custom console."""
        console = Console()
        progress = PipelineProgress(console=console)

        assert progress.console == console
        assert progress.task_id is None

    def test_start_creates_task(self):
        """Test start creates a progress task."""
        progress = PipelineProgress()
        progress.start(total_phases=5)

        assert progress.task_id is not None
        assert progress.total_phases == 5

        progress.stop()

    def test_start_custom_phases(self):
        """Test start with custom phase count."""
        progress = PipelineProgress()
        progress.start(total_phases=3)

        assert progress.total_phases == 3

        progress.stop()

    def test_update_phase(self):
        """Test update_phase updates progress."""
        progress = PipelineProgress()
        progress.start(total_phases=5)

        progress.update_phase(
            phase_number=1,
            phase_name="Framing",
            agent_name="ChatGPT",
        )

        assert progress.current_phase == 1

        progress.stop()

    def test_complete_phase(self):
        """Test complete_phase marks phase as done."""
        progress = PipelineProgress()
        progress.start(total_phases=5)

        progress.complete_phase(phase_number=1)

        assert progress.current_phase == 0  # Not updated by complete_phase

        progress.stop()

    def test_stop(self):
        """Test stop stops progress display."""
        progress = PipelineProgress()
        progress.start(total_phases=5)

        progress.stop()

        # Should not raise any errors
        assert True

    def test_show_session_summary(self, capsys=None):
        """Test show_session_summary displays session info."""
        progress = PipelineProgress()
        config = PipelineConfig(
            topic="Test topic for session summary display",
            doc_type="bizplan",
            language="en",
        )
        session = PipelineSession(config=config)
        session.state = PipelineState.COMPLETED
        session.add_result(
            type("PhaseResult", (), {
                "phase_number": 1,
                "phase_name": "Phase 1",
                "status": "completed",
            })()
        )

        # Just verify it doesn't raise errors
        progress.show_session_summary(session)

        assert True

    def test_multiple_phases(self):
        """Test progress through multiple phases."""
        progress = PipelineProgress()
        progress.start(total_phases=5)

        for i in range(1, 6):
            progress.update_phase(
                phase_number=i,
                phase_name=f"Phase {i}",
                agent_name=f"Agent{i}",
            )
            assert progress.current_phase == i

        progress.stop()

    def test_update_without_start(self):
        """Test update_phase without start doesn't crash but doesn't update."""
        progress = PipelineProgress()

        # Should not crash, but won't update since task_id is None
        progress.update_phase(
            phase_number=1,
            phase_name="Framing",
            agent_name="ChatGPT",
        )

        # current_phase won't be updated because task_id is None
        assert progress.current_phase == 0

    def test_complete_without_start(self):
        """Test complete_phase without start doesn't crash."""
        progress = PipelineProgress()

        # Should not crash
        progress.complete_phase(phase_number=1)

        assert True
