"""
Tests for Phase5Review class.

Uses TDD approach: tests written before implementation.
"""


import pytest

from agents.base import AgentRequest, AsyncAgent
from src.agents.router import AgentRouter, PhaseTask
from src.core.models import (
    AgentResponse,
    AgentType,
    PhaseStatus,
    PipelineConfig,
    PipelineSession,
)
from src.pipeline.phase5_review import Phase5Review


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


class _FailingAgent(AsyncAgent):
    """Mock failing agent for testing."""

    def __init__(self, error: str) -> None:
        super().__init__(gateway_provider=_DummyGateway())
        self._error = error

    async def execute(self, request: AgentRequest) -> AgentResponse:
        raise RuntimeError(self._error)


class TestPhase5Review:
    """Test suite for Phase5Review class."""

    def test_init(self):
        """Test Phase5Review initialization."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase is not None
        assert phase.template_manager == template_manager
        assert phase.agent_router == agent_router

    def test_get_phase_number(self):
        """Test get_phase_number returns 5."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase.get_phase_number() == 5

    def test_get_tasks_returns_phase5_tasks(self):
        """Test get_tasks returns Phase 5 specific tasks."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for phase 5")
        session = PipelineSession(config=config)

        tasks = phase.get_tasks(session)

        assert isinstance(tasks, list)
        assert len(tasks) == 3
        assert PhaseTask.VERIFY_PERPLEXITY in tasks
        assert PhaseTask.FINAL_REVIEW_CLAUDE in tasks
        assert PhaseTask.POLISH_CLAUDE in tasks

    @pytest.mark.anyio
    async def test_execute_completed_successfully(self):
        """Test execute completes successfully with mock agents."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))
        agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))

        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for successful phase 5 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 5
        assert result.phase_name == "Phase 5: Review"
        assert len(result.ai_responses) == 3
        assert result.completed_at is not None

    @pytest.mark.anyio
    async def test_execute_failure_when_agent_fails(self):
        """Test execute fails when one agent fails."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register success agents and one failing agent
        agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))
        agent_router.register_agent(AgentType.CLAUDE, _FailingAgent("Claude failed"))

        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for failed phase 5 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.FAILED
        assert len(result.ai_responses) == 3
        # At least one response should be unsuccessful
        assert any(not response.success for response in result.ai_responses)

    def test_validate_result_returns_true_for_completed(self):
        """Test validate_result returns True for completed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(5, "Phase 5: Review")
        result.status = PhaseStatus.COMPLETED

        assert phase.validate_result(result) is True

    def test_validate_result_returns_false_for_failed(self):
        """Test validate_result returns False for failed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase5Review(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(5, "Phase 5: Review")
        result.status = PhaseStatus.FAILED

        assert phase.validate_result(result) is False

    def test_build_template_name(self):
        """Test _build_template_name creates correct template path."""
        assert (
            Phase5Review._build_template_name(5, PhaseTask.VERIFY_PERPLEXITY)
            == "phase_5/verify_perplexity"
        )
        assert (
            Phase5Review._build_template_name(5, PhaseTask.FINAL_REVIEW_CLAUDE)
            == "phase_5/final_review_claude"
        )
        assert (
            Phase5Review._build_template_name(5, PhaseTask.POLISH_CLAUDE)
            == "phase_5/polish_claude"
        )
