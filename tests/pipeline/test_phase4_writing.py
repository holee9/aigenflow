"""
Tests for Phase4Writing class.

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
from src.pipeline.phase4_writing import Phase4Writing


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


class TestPhase4Writing:
    """Test suite for Phase4Writing class."""

    def test_init(self):
        """Test Phase4Writing initialization."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase is not None
        assert phase.template_manager == template_manager
        assert phase.agent_router == agent_router

    def test_get_phase_number(self):
        """Test get_phase_number returns 4."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase.get_phase_number() == 4

    def test_get_tasks_returns_phase4_tasks(self):
        """Test get_tasks returns Phase 4 specific tasks."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for phase 4")
        session = PipelineSession(config=config)

        tasks = phase.get_tasks(session)

        assert isinstance(tasks, list)
        assert len(tasks) == 3
        assert PhaseTask.BUSINESS_PLAN_CLAUDE in tasks
        assert PhaseTask.OUTLINE_CHATGPT in tasks
        assert PhaseTask.CHARTS_GEMINI in tasks

    @pytest.mark.anyio
    async def test_execute_completed_successfully(self):
        """Test execute completes successfully with mock agents."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))
        agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))

        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for successful phase 4 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 4
        assert result.phase_name == "Phase 4: Writing"
        assert len(result.ai_responses) == 3
        assert result.completed_at is not None

    @pytest.mark.anyio
    async def test_execute_failure_when_agent_fails(self):
        """Test execute fails when one agent fails."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register two success and one failing agent
        agent_router.register_agent(AgentType.CLAUDE, _SuccessAgent("claude"))
        agent_router.register_agent(AgentType.CHATGPT, _SuccessAgent("chatgpt"))
        agent_router.register_agent(AgentType.GEMINI, _FailingAgent("Gemini failed"))

        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for failed phase 4 execution")
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
        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(4, "Phase 4: Writing")
        result.status = PhaseStatus.COMPLETED

        assert phase.validate_result(result) is True

    def test_validate_result_returns_false_for_failed(self):
        """Test validate_result returns False for failed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase4Writing(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(4, "Phase 4: Writing")
        result.status = PhaseStatus.FAILED

        assert phase.validate_result(result) is False

    def test_build_template_name(self):
        """Test _build_template_name creates correct template path."""
        assert (
            Phase4Writing._build_template_name(4, PhaseTask.BUSINESS_PLAN_CLAUDE)
            == "phase_4/business_plan_claude"
        )
        assert (
            Phase4Writing._build_template_name(4, PhaseTask.OUTLINE_CHATGPT)
            == "phase_4/outline_chatgpt"
        )
        assert (
            Phase4Writing._build_template_name(4, PhaseTask.CHARTS_GEMINI)
            == "phase_4/charts_gemini"
        )
