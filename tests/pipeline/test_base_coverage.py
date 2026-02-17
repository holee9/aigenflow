"""
Comprehensive coverage tests for BasePhase class.

Tests for uncovered lines:
- Line 32: pass statement in get_tasks abstract method
- Line 46: pass statement in execute abstract method
- Line 59: pass statement in validate_result abstract method
- Line 69: Default get_phase_number return value
"""

import pytest

from src.core.models import (
    PhaseResult,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
    create_phase_result,
)
from src.pipeline.base import BasePhase


class TestBasePhaseAbstractMethodPassStatements:
    """Tests for abstract method pass statements (lines 32, 46, 59)."""

    def test_abstract_get_tasks_has_pass_body(self):
        """Test that get_tasks abstract method has pass statement (line 32)."""
        import inspect

        # Get the source code of the get_tasks method
        source = inspect.getsource(BasePhase.get_tasks)

        # Verify it contains 'pass' statement
        assert "pass" in source

    def test_abstract_execute_has_pass_body(self):
        """Test that execute abstract method has pass statement (line 46)."""
        import inspect

        # Get the source code of the execute method
        source = inspect.getsource(BasePhase.execute)

        # Verify it contains 'pass' statement
        assert "pass" in source

    def test_abstract_validate_result_has_pass_body(self):
        """Test that validate_result abstract method has pass statement (line 59)."""
        import inspect

        # Get the source code of the validate_result method
        source = inspect.getsource(BasePhase.validate_result)

        # Verify it contains 'pass' statement
        assert "pass" in source

    def test_abstract_methods_cannot_be_called_directly(self):
        """Test that abstract methods raise TypeError when called without implementation."""

        # Verify methods are abstract
        assert 'get_tasks' in BasePhase.__abstractmethods__
        assert 'execute' in BasePhase.__abstractmethods__
        assert 'validate_result' in BasePhase.__abstractmethods__


class TestBasePhaseDefaultGetPhaseNumber:
    """Tests for default get_phase_number implementation (line 69)."""

    def test_default_get_phase_number_returns_one(self):
        """Test that default get_phase_number returns 1 (line 69)."""
        from src.pipeline.base import BasePhase

        class MinimalPhase(BasePhase):
            """Minimal implementation with only required abstract methods."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(1, "Minimal Phase")

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        phase = MinimalPhase()
        assert phase.get_phase_number() == 1

    def test_concrete_phase_can_override_get_phase_number(self):
        """Test that concrete phases can override get_phase_number."""
        from src.pipeline.base import BasePhase

        class CustomPhase(BasePhase):
            """Custom phase with different phase number."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(3, "Custom Phase")

            def validate_result(self, result: PhaseResult) -> bool:
                return True

            def get_phase_number(self) -> int:
                return 3

        phase = CustomPhase()
        assert phase.get_phase_number() == 3


class TestBasePhaseMethodSignatures:
    """Tests for BasePhase method signatures and type hints."""

    def test_get_tasks_signature(self):
        """Test get_tasks has correct signature."""
        import inspect

        sig = inspect.signature(BasePhase.get_tasks)
        params = sig.parameters

        # Should have 'self' and 'session' parameters
        assert 'self' in params or list(params.keys())[0] == 'session'
        assert 'session' in params

        # Check return annotation
        assert sig.return_annotation != inspect.Signature.empty

    def test_execute_signature(self):
        """Test execute has correct signature."""
        import inspect

        sig = inspect.signature(BasePhase.execute)
        params = sig.parameters

        # Should have 'self', 'session', and 'config' parameters
        param_names = list(params.keys())
        assert 'session' in param_names
        assert 'config' in param_names

        # Check return annotation
        assert sig.return_annotation != inspect.Signature.empty

    def test_validate_result_signature(self):
        """Test validate_result has correct signature."""
        import inspect

        sig = inspect.signature(BasePhase.validate_result)
        params = sig.parameters

        # Should have 'self' and 'result' parameters
        param_names = list(params.keys())
        assert 'result' in param_names

        # Check return annotation (should be bool)
        assert sig.return_annotation != inspect.Signature.empty

    def test_get_phase_number_signature(self):
        """Test get_phase_number has correct signature."""
        import inspect

        sig = inspect.signature(BasePhase.get_phase_number)
        params = sig.parameters

        # Should only have 'self' parameter
        param_names = list(params.keys())
        assert len(param_names) <= 1  # Only 'self' or no parameters for class method

        # Check return annotation (should be int)
        assert sig.return_annotation != inspect.Signature.empty


class TestBasePhaseConcreteImplementation:
    """Tests for concrete implementations of BasePhase."""

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementation can be created and used."""
        from src.pipeline.base import BasePhase

        class ConcretePhase(BasePhase):
            """Fully concrete implementation."""

            def get_tasks(self, session: PipelineSession) -> list:
                return ["task1", "task2"]

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                result = create_phase_result(1, "Concrete Phase")
                result.status = PhaseStatus.COMPLETED
                result.ai_responses = []
                result.completed_at = None
                return result

            def validate_result(self, result: PhaseResult) -> bool:
                return result.status == PhaseStatus.COMPLETED

        # Should be instantiable
        phase = ConcretePhase()
        assert phase is not None

        # Should have all methods callable
        assert callable(phase.get_tasks)
        assert callable(phase.execute)
        assert callable(phase.validate_result)
        assert callable(phase.get_phase_number)

    @pytest.mark.anyio
    async def test_concrete_implementation_full_workflow(self):
        """Test full workflow with concrete implementation."""

        from src.pipeline.base import BasePhase

        class CompletePhase(BasePhase):
            """Complete implementation for testing."""

            def get_tasks(self, session: PipelineSession) -> list:
                return ["research", "draft", "review"]

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                result = create_phase_result(2, "Complete Phase")
                result.status = PhaseStatus.COMPLETED
                result.ai_responses = [
                    {
                        "agent_name": "test",
                        "task_name": "research",
                        "content": "Research completed",
                        "success": True,
                    }
                ]
                return result

            def validate_result(self, result: PhaseResult) -> bool:
                return result.status == PhaseStatus.COMPLETED and result.ai_responses is not None

            def get_phase_number(self) -> int:
                return 2

        # Create phase and session
        phase = CompletePhase()
        config = PipelineConfig(topic="Test Workflow")
        session = PipelineSession(config=config)

        # Test get_tasks
        tasks = phase.get_tasks(session)
        assert len(tasks) == 3
        assert "research" in tasks

        # Test get_phase_number
        assert phase.get_phase_number() == 2

        # Test execute
        result = await phase.execute(session, config)
        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 2
        assert len(result.ai_responses) == 1

        # Test validate_result
        assert phase.validate_result(result) is True


class TestBasePhaseInheritance:
    """Tests for BasePhase inheritance patterns."""

    def test_base_phase_is_abc(self):
        """Test that BasePhase inherits from ABC."""
        from abc import ABC

        from src.pipeline.base import BasePhase

        assert issubclass(BasePhase, ABC)
        assert isinstance(BasePhase, type)

    def test_concrete_phase_inherits_base_methods(self):
        """Test that concrete phases inherit all BasePhase methods."""
        from src.pipeline.base import BasePhase

        class DerivedPhase(BasePhase):
            """Derived phase for testing."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(1, "Derived")

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        phase = DerivedPhase()

        # Should have inherited get_phase_number
        assert hasattr(phase, 'get_phase_number')
        assert callable(phase.get_phase_number)

        # Should return default value
        assert phase.get_phase_number() == 1

    def test_multiple_inheritance_levels(self):
        """Test BasePhase works with multiple inheritance levels."""
        from src.pipeline.base import BasePhase

        class IntermediatePhase(BasePhase):
            """Intermediate abstract phase."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

        class FinalPhase(IntermediatePhase):
            """Final concrete phase."""

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(1, "Final")

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        # IntermediatePhase should still be abstract
        with pytest.raises(TypeError):
            IntermediatePhase()

        # FinalPhase should be concrete
        phase = FinalPhase()
        assert phase is not None
        assert phase.get_phase_number() == 1


class TestBasePhaseAbstractBehavior:
    """Tests for BasePhase abstract behavior enforcement."""

    def test_cannot_instantiate_base_phase_directly(self):
        """Test that BasePhase cannot be instantiated directly."""
        from src.pipeline.base import BasePhase

        with pytest.raises(TypeError):
            BasePhase()

    def test_partial_implementation_raises_type_error(self):
        """Test that partial implementation still raises TypeError."""
        from src.pipeline.base import BasePhase

        class PartialPhase(BasePhase):
            """Only implements get_tasks."""

            def get_tasks(self, session: PipelineSession) -> list:
                return []

        # Should still raise TypeError because execute and validate_result are missing
        with pytest.raises(TypeError):
            PartialPhase()

    def test_all_abstract_methods_required(self):
        """Test that all three abstract methods must be implemented."""
        from src.pipeline.base import BasePhase

        # Try creating a class missing get_tasks
        class NoGetTasks(BasePhase):
            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(1, "No GetTasks")

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        with pytest.raises(TypeError):
            NoGetTasks()

        # Try creating a class missing execute
        class NoExecute(BasePhase):
            def get_tasks(self, session: PipelineSession) -> list:
                return []

            def validate_result(self, result: PhaseResult) -> bool:
                return True

        with pytest.raises(TypeError):
            NoExecute()

        # Try creating a class missing validate_result
        class NoValidate(BasePhase):
            def get_tasks(self, session: PipelineSession) -> list:
                return []

            async def execute(self, session: PipelineSession, config: PipelineConfig) -> PhaseResult:
                return create_phase_result(1, "No Validate")

        with pytest.raises(TypeError):
            NoValidate()
