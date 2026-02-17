"""
Integration tests for Orchestrator UI components.

Tests that UI components integrate correctly with orchestrator.
"""

import pytest

from agents.base import AgentRequest, AsyncAgent
from src.core.models import (
    AgentResponse,
    AgentType,
    PipelineConfig,
    PipelineState,
)
from src.pipeline.orchestrator import PipelineOrchestrator


class _DummyGateway:
    """Dummy gateway for testing."""
    pass


class _SuccessAgent(AsyncAgent):
    """Mock successful agent for testing."""

    def __init__(self, name: str) -> None:
        super().__init__(gateway_provider=_DummyGateway())
        self._name = name

    async def execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            agent_name=AgentType(self._name),
            task_name=request.task_name,
            content="Success response",
            tokens_used=100,
            response_time=1.0,
            success=True,
        )


class TestOrchestratorUI:
    """Test suite for orchestrator UI integration."""

    def test_init_without_ui(self):
        """Test orchestrator initializes without UI by default."""
        orchestrator = PipelineOrchestrator(settings=None)

        assert orchestrator.enable_ui is False
        assert orchestrator.ui_progress is None
        assert orchestrator.ui_logger is None
        assert orchestrator.ui_summary is None

    def test_init_with_ui_enabled(self):
        """Test orchestrator initializes UI when enable_ui=True."""
        orchestrator = PipelineOrchestrator(settings=None, enable_ui=True)

        assert orchestrator.enable_ui is True
        assert orchestrator.ui_progress is not None
        assert orchestrator.ui_logger is not None
        assert orchestrator.ui_summary is not None

    @pytest.mark.anyio
    async def test_run_pipeline_with_ui_enabled(self):
        """Test run_pipeline with UI enabled."""
        orchestrator = PipelineOrchestrator(settings=None, enable_ui=True)

        # Register mock agents
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))
        orchestrator.agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        orchestrator.agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))

        config = PipelineConfig(topic="Test topic for UI enabled pipeline execution")
        session = await orchestrator.run_pipeline(config)

        assert session.state == PipelineState.COMPLETED
        assert len(session.results) == 5
        assert orchestrator.ui_logger.get_log_count() > 0

    @pytest.mark.anyio
    async def test_run_pipeline_without_ui(self):
        """Test run_pipeline without UI (default behavior)."""
        orchestrator = PipelineOrchestrator(settings=None, enable_ui=False)

        # Register mock agents
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))
        orchestrator.agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        orchestrator.agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))

        config = PipelineConfig(topic="Test topic for UI disabled pipeline execution")
        session = await orchestrator.run_pipeline(config)

        assert session.state == PipelineState.COMPLETED
        assert len(session.results) == 5
        assert orchestrator.ui_logger is None

    @pytest.mark.anyio
    async def test_execute_phase_with_ui_enabled(self):
        """Test execute_phase with UI enabled."""
        orchestrator = PipelineOrchestrator(settings=None, enable_ui=True)

        # Register mock agents
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))

        config = PipelineConfig(topic="Test topic for phase UI execution")
        session = orchestrator.create_session(config=config)

        result = await orchestrator.execute_phase(session, 1)

        assert result.phase_number == 1
        assert orchestrator.ui_logger.get_log_count() > 0

    @pytest.mark.anyio
    async def test_execute_phase_without_ui(self):
        """Test execute_phase without UI (default behavior)."""
        orchestrator = PipelineOrchestrator(settings=None, enable_ui=False)

        # Register mock agents
        orchestrator.agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        orchestrator.agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))

        config = PipelineConfig(topic="Test topic for phase execution without UI")
        session = orchestrator.create_session(config=config)

        result = await orchestrator.execute_phase(session, 1)

        assert result.phase_number == 1
        assert orchestrator.ui_logger is None

    def test_backward_compatibility_default_behavior(self):
        """Test that default behavior preserves backward compatibility."""
        # Create orchestrator without enable_ui parameter
        orchestrator = PipelineOrchestrator(settings=None)

        # UI should be disabled by default
        assert orchestrator.enable_ui is False
        assert orchestrator.ui_progress is None
        assert orchestrator.ui_logger is None
        assert orchestrator.ui_summary is None

        # Existing behavior should be preserved
        config = PipelineConfig(topic="Test backward compatibility")
        session = orchestrator.create_session(config)
        assert session is not None
