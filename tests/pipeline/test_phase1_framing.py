"""
Tests for Phase1Framing class.

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
from src.pipeline.phase1_framing import Phase1Framing


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


class TestPhase1Framing:
    """Test suite for Phase1Framing class."""

    def test_init(self):
        """Test Phase1Framing initialization."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase is not None
        assert phase.template_manager == template_manager
        assert phase.agent_router == agent_router

    def test_get_phase_number(self):
        """Test get_phase_number returns 1."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase.get_phase_number() == 1

    def test_get_tasks_returns_phase1_tasks(self):
        """Test get_tasks returns Phase 1 specific tasks."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for phase 1")
        session = PipelineSession(config=config)

        tasks = phase.get_tasks(session)

        assert isinstance(tasks, list)
        assert len(tasks) == 2
        assert PhaseTask.BRAINSTORM_CHATGPT in tasks
        assert PhaseTask.VALIDATE_CLAUDE in tasks

    @pytest.mark.anyio
    async def test_execute_completed_successfully(self):
        """Test execute completes successfully with mock agents."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))

        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for successful phase 1 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 1
        assert result.phase_name == "Phase 1: Framing"
        assert len(result.ai_responses) == 2
        assert result.completed_at is not None

    @pytest.mark.anyio
    async def test_execute_failure_when_agent_fails(self):
        """Test execute fails when one agent fails."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register one success and one failing agent
        agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        agent_router.register_agent(AgentType.CLAUDE, _FailingAgent("Claude failed"))

        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for failed phase 1 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.FAILED
        assert len(result.ai_responses) == 2
        # At least one response should be unsuccessful
        assert any(not response.success for response in result.ai_responses)

    def test_validate_result_returns_true_for_completed(self):
        """Test validate_result returns True for completed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(1, "Phase 1: Framing")
        result.status = PhaseStatus.COMPLETED

        assert phase.validate_result(result) is True

    def test_validate_result_returns_false_for_failed(self):
        """Test validate_result returns False for failed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase1Framing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(1, "Phase 1: Framing")
        result.status = PhaseStatus.FAILED

        assert phase.validate_result(result) is False

    def test_build_template_name(self):
        """Test _build_template_name creates correct template path."""
        assert (
            Phase1Framing._build_template_name(1, PhaseTask.BRAINSTORM_CHATGPT)
            == "phase_1/brainstorm_chatgpt"
        )
        assert (
            Phase1Framing._build_template_name(1, PhaseTask.VALIDATE_CLAUDE)
            == "phase_1/validate_claude"
        )
