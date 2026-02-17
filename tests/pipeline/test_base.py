"""
Tests for BasePhase abstract class.

Uses TDD approach: tests written before implementation.
"""


import pytest

from src.core.models import PhaseResult, PipelineConfig, PipelineSession


class TestBasePhase:
    """Test suite for BasePhase abstract class."""

    def test_base_phase_is_abstract(self):
        """Test that BasePhase cannot be instantiated."""
        from src.pipeline.base import BasePhase

        with pytest.raises(TypeError):
            BasePhase()

    def test_base_phase_has_abstract_methods(self):
        """Test that BasePhase defines required abstract methods."""

        from src.pipeline.base import BasePhase

        # Check that BasePhase has the required abstract methods
        assert hasattr(BasePhase, '__abstractmethods__')

        # Verify abstract methods exist by name
        abstract_methods = BasePhase.__abstractmethods__
        method_names = {method for method in abstract_methods}

        # Required abstract methods
        required_methods = {'get_tasks', 'execute', 'validate_result'}
        assert required_methods.issubset(method_names)

        # Verify methods are callable
        assert callable(BasePhase.get_tasks)
        assert callable(BasePhase.execute)
        assert callable(BasePhase.validate_result)

    def test_base_phase_concrete_implementation(self):
        """Test that concrete implementation can be created."""
        from src.pipeline.base import BasePhase

        class ConcretePhase(BasePhase):
            """Concrete implementation for testing."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                from src.core.models import create_phase_result
                return create_phase_result(1, "Test Phase")

            def validate_result(self, result: PhaseResult) -> bool:
                return result.status.value == "completed"

        # Should be instantiable
        phase = ConcretePhase()
        assert phase is not None
        assert phase.get_tasks(None) == []

        # Should have callable methods
        assert callable(phase.execute)
        assert callable(phase.validate_result)

    def test_base_phase_get_tasks_returns_list(self):
        """Test that get_tasks returns a list."""
        from src.core.models import PhaseStatus, PipelineSession
        from src.pipeline.base import BasePhase

        class TestPhase(BasePhase):
            def get_tasks(self, session: PipelineSession) -> list:
                return ["task1", "task2"]

            async def execute(self, session: PipelineSession, config) -> PhaseResult:
                from src.core.models import create_phase_result
                result = create_phase_result(1, "Test Phase")
                result.status = PhaseStatus.COMPLETED
                return result

            def validate_result(self, result: PhaseResult) -> bool:
                return result.status == PhaseStatus.COMPLETED

        # Create a mock session
        from src.core.models import PipelineConfig
        config = PipelineConfig(topic="Test topic for phase")
        session = PipelineSession(config=config)
        phase = TestPhase()

        tasks = phase.get_tasks(session)
        assert isinstance(tasks, list)
        assert len(tasks) == 2

    def test_base_phase_execute_returns_phase_result(self):
        """Test that execute returns PhaseResult."""
        from src.core.models import PhaseStatus, PipelineConfig, PipelineSession
        from src.pipeline.base import BasePhase

        class ExecutePhase(BasePhase):
            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                from src.core.models import create_phase_result
                result = create_phase_result(1, "Test Phase")
                result.status = PhaseStatus.COMPLETED
                return result

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        config = PipelineConfig(topic="Test topic for phase execution", doc_type="bizplan", language="en")
        session = PipelineSession(config=config)
        phase = ExecutePhase()

        # Execute the phase (in real test, would be async)
        import asyncio
        result = asyncio.run(phase.execute(session, config))

        assert result is not None
        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 1

    def test_base_phase_validate_result_returns_bool(self):
        """Test that validate_result returns boolean."""
        from src.core.models import PhaseResult, PhaseStatus, create_phase_result
        from src.pipeline.base import BasePhase

        class ValidatePhase(BasePhase):
            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                from src.core.models import create_phase_result
                return create_phase_result(1, "Test Phase")

            def validate_result(self, result: PhaseResult) -> bool:
                return result.status == PhaseStatus.COMPLETED

        phase = ValidatePhase()
        result = create_phase_result(1, "Test")
        result.status = PhaseStatus.COMPLETED

        assert phase.validate_result(result) is True

        result_failed = create_phase_result(1, "Test")
        result_failed.status = PhaseStatus.FAILED
        assert phase.validate_result(result_failed) is False
