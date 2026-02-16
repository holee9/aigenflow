"""
Tests for Phase2Research class.

Uses TDD approach: tests written before implementation.
"""

from datetime import datetime

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
from src.pipeline.phase2_research import Phase2Research


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


class TestPhase2Research:
    """Test suite for Phase2Research class."""

    def test_init(self):
        """Test Phase2Research initialization."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase is not None
        assert phase.template_manager == template_manager
        assert phase.agent_router == agent_router

    def test_get_phase_number(self):
        """Test get_phase_number returns 2."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        assert phase.get_phase_number() == 2

    def test_get_tasks_returns_phase2_tasks(self):
        """Test get_tasks returns Phase 2 specific tasks."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for phase 2")
        session = PipelineSession(config=config)

        tasks = phase.get_tasks(session)

        assert isinstance(tasks, list)
        assert len(tasks) == 2
        assert PhaseTask.DEEP_SEARCH_GEMINI in tasks
        assert PhaseTask.FACT_CHECK_PERPLEXITY in tasks

    @pytest.mark.anyio
    async def test_execute_completed_successfully(self):
        """Test execute completes successfully with mock agents."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        agent_router.register_agent(AgentType.PERPLEXITY, _SuccessAgent("perplexity"))

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for successful phase 2 execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        assert result.status == PhaseStatus.COMPLETED
        assert result.phase_number == 2
        assert result.phase_name == "Phase 2: Research"
        assert len(result.ai_responses) == 2
        assert result.completed_at is not None

    @pytest.mark.anyio
    async def test_execute_failure_when_agent_fails(self):
        """Test execute fails when one agent fails."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register one success and one failing agent
        agent_router.register_agent(AgentType.GEMINI, _SuccessAgent("gemini"))
        agent_router.register_agent(AgentType.PERPLEXITY, _FailingAgent("Perplexity failed"))

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        config = PipelineConfig(topic="Test topic for failed phase 2 execution")
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
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(2, "Phase 2: Research")
        result.status = PhaseStatus.COMPLETED

        assert phase.validate_result(result) is True

    def test_validate_result_returns_false_for_failed(self):
        """Test validate_result returns False for failed phase."""
        from src.core.models import create_phase_result
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        result = create_phase_result(2, "Phase 2: Research")
        result.status = PhaseStatus.FAILED

        assert phase.validate_result(result) is False

    def test_build_template_name(self):
        """Test _build_template_name creates correct template path."""
        assert (
            Phase2Research._build_template_name(2, PhaseTask.DEEP_SEARCH_GEMINI)
            == "phase_2/deep_search_gemini"
        )
        assert (
            Phase2Research._build_template_name(2, PhaseTask.FACT_CHECK_PERPLEXITY)
            == "phase_2/fact_check_perplexity"
        )


class TestPhase2ResearchBatchProcessing:
    """Tests for Phase2Research batch processing functionality."""

    def test_init_with_batching_enabled(self):
        """Test Phase2Research initialization with batching enabled."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        assert phase is not None
        assert phase.enable_batching is True
        assert phase.batch_processor is not None

    def test_init_with_batching_disabled(self):
        """Test Phase2Research initialization with batching disabled."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=False,
        )

        assert phase is not None
        assert phase.enable_batching is False
        assert phase.batch_processor is None

    def test_get_agent_type_for_task(self):
        """Test _get_agent_type_for_task returns correct mappings."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        gemini_agent = phase._get_agent_type_for_task(PhaseTask.DEEP_SEARCH_GEMINI)
        assert gemini_agent == AgentType.GEMINI

        perplexity_agent = phase._get_agent_type_for_task(PhaseTask.FACT_CHECK_PERPLEXITY)
        assert perplexity_agent == AgentType.PERPLEXITY
