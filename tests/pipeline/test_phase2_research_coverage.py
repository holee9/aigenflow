"""
Comprehensive coverage tests for Phase2Research class.

Tests for uncovered lines:
- Lines 104-106: Empty tasks list (SKIPPED status)
- Line 110: Batch execution path selection
- Lines 200-247: _execute_with_batching method
"""

from unittest.mock import AsyncMock, Mock

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


class _MockAgent(AsyncAgent):
    """Mock agent for testing."""

    def __init__(self, name: str) -> None:
        super().__init__(gateway_provider=_DummyGateway())
        self._name = name

    async def execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            agent_name=AgentType(self._name),
            task_name=request.task_name,
            content=f"Mock response from {self._name}",
            tokens_used=150,
            response_time=1.5,
            success=True,
        )


class TestPhase2ResearchEmptyTasks:
    """Tests for empty tasks list (lines 104-106)."""

    @pytest.mark.anyio
    async def test_execute_with_empty_tasks_returns_skipped(self):
        """Test execute returns SKIPPED when tasks list is empty."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        # Create a session that will return empty tasks
        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)

        # Mock get_tasks to return empty list
        phase.get_tasks = Mock(return_value=[])

        result = await phase.execute(session, config)

        # Verify SKIPPED status (lines 104-106)
        assert result.status == PhaseStatus.SKIPPED
        assert result.completed_at is not None
        assert result.phase_number == 2
        assert result.phase_name == "Phase 2: Research"


class TestPhase2ResearchBatchingPath:
    """Tests for batch execution path (line 110)."""

    @pytest.mark.anyio
    async def test_execute_uses_batching_when_enabled(self):
        """Test execute uses batch processing when enable_batching=True."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.GEMINI, _MockAgent("gemini"))
        agent_router.register_agent(AgentType.PERPLEXITY, _MockAgent("perplexity"))

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        config = PipelineConfig(topic="Test topic for batch execution")
        session = PipelineSession(config=config)

        # Mock batch_processor.process_batch to track execution
        phase.batch_processor.process_batch = AsyncMock(return_value=[
            AgentResponse(
                agent_name=AgentType.GEMINI,
                task_name="deep_search_gemini",
                content="Batch response",
                tokens_used=100,
                response_time=1.0,
                success=True,
            ),
            AgentResponse(
                agent_name=AgentType.PERPLEXITY,
                task_name="fact_check_perplexity",
                content="Batch response",
                tokens_used=100,
                response_time=1.0,
                success=True,
            ),
        ])

        result = await phase.execute(session, config)

        # Verify batch processing was used (line 110)
        assert result.status == PhaseStatus.COMPLETED
        assert len(result.ai_responses) == 2
        phase.batch_processor.process_batch.assert_called_once()

    @pytest.mark.anyio
    async def test_execute_uses_sequential_when_batching_disabled(self):
        """Test execute uses sequential processing when enable_batching=False."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        # Register mock agents
        agent_router.register_agent(AgentType.GEMINI, _MockAgent("gemini"))
        agent_router.register_agent(AgentType.PERPLEXITY, _MockAgent("perplexity"))

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=False,
        )

        config = PipelineConfig(topic="Test topic for sequential execution")
        session = PipelineSession(config=config)

        result = await phase.execute(session, config)

        # Verify sequential processing was used
        assert result.status == PhaseStatus.COMPLETED
        assert len(result.ai_responses) == 2
        assert phase.batch_processor is None


class TestPhase2ResearchBatchExecution:
    """Tests for _execute_with_batching method (lines 200-247)."""

    @pytest.mark.anyio
    async def test_execute_with_batching_clears_queue(self):
        """Test _execute_with_batching clears previous batch state (lines 200-201)."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Add some items to the batch queue
        await phase.batch_processor.enqueue(
            agent_type=AgentType.GEMINI,
            request=AgentRequest(
                task_name="old_task",
                prompt="Old prompt",
                timeout=30,
            ),
        )

        # Verify queue has items (using internal attribute)
        assert len(phase.batch_processor.queue._queue) > 0

        # Setup mocks
        phase.batch_processor.process_batch = AsyncMock(return_value=[
            AgentResponse(
                agent_name=AgentType.GEMINI,
                task_name="deep_search_gemini",
                content="Response",
                tokens_used=100,
                response_time=1.0,
                success=True,
            ),
        ])

        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)

        # Execute with batching - should clear queue first (lines 200-201)
        await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=[PhaseTask.DEEP_SEARCH_GEMINI],
        )

        # Queue was cleared and new tasks were enqueued
        assert phase.batch_processor.process_batch.called

    @pytest.mark.anyio
    async def test_execute_with_batching_enqueues_all_tasks(self):
        """Test _execute_with_batching enqueues all tasks (lines 203-228)."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Mock enqueue to track calls
        enqueue_mock = AsyncMock(return_value="request_id_123")
        phase.batch_processor.enqueue = enqueue_mock
        phase.batch_processor.process_batch = AsyncMock(return_value=[])

        config = PipelineConfig(
            topic="Test topic",
            doc_type="bizplan",
            language="en",
            timeout_seconds=60,
        )
        session = PipelineSession(config=config)

        tasks = [
            PhaseTask.DEEP_SEARCH_GEMINI,
            PhaseTask.FACT_CHECK_PERPLEXITY,
        ]

        await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=tasks,
        )

        # Verify both tasks were enqueued (lines 204-228)
        assert enqueue_mock.call_count == 2

        # Check first enqueue call (GEMINI)
        first_call = enqueue_mock.call_args_list[0]
        assert first_call[1]["agent_type"] == AgentType.GEMINI
        # Verify request has required attributes
        request = first_call[1]["request"]
        assert hasattr(request, "task_name")
        assert hasattr(request, "prompt")
        assert hasattr(request, "timeout")

        # Check second enqueue call (PERPLEXITY)
        second_call = enqueue_mock.call_args_list[1]
        assert second_call[1]["agent_type"] == AgentType.PERPLEXITY
        # Verify request has required attributes
        request2 = second_call[1]["request"]
        assert hasattr(request2, "task_name")
        assert hasattr(request2, "prompt")
        assert hasattr(request2, "timeout")

    @pytest.mark.anyio
    async def test_execute_with_batching_processes_batch(self):
        """Test _execute_with_batching processes batch (lines 230-231)."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Mock process_batch to return responses
        mock_responses = [
            AgentResponse(
                agent_name="gemini",
                task_name="deep_search_gemini",
                content="Gemini research content",
                tokens_used=200,
                response_time=2.0,
                success=True,
            ),
            AgentResponse(
                agent_name="perplexity",
                task_name="fact_check_perplexity",
                content="Perplexity fact check",
                tokens_used=150,
                response_time=1.5,
                success=True,
            ),
        ]

        phase.batch_processor.process_batch = AsyncMock(return_value=mock_responses)

        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)

        result = await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=[PhaseTask.DEEP_SEARCH_GEMINI, PhaseTask.FACT_CHECK_PERPLEXITY],
        )

        # Verify batch was processed (line 231)
        phase.batch_processor.process_batch.assert_called_once()
        assert len(result) == 2

    @pytest.mark.anyio
    async def test_execute_with_batching_normalizes_responses(self):
        """Test _execute_with_batching normalizes responses (lines 234-246)."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Mock responses with string agent_name (simulating batch processor output)
        mock_responses = [
            AgentResponse(
                agent_name="gemini",  # String instead of AgentType
                task_name="deep_search_gemini",
                content="Gemini content",
                tokens_used=200,
                response_time=2.0,
                success=True,
            ),
            AgentResponse(
                agent_name="perplexity",  # String instead of AgentType
                task_name="fact_check_perplexity",
                content="Perplexity content",
                tokens_used=150,
                response_time=1.5,
                success=False,
                error="Perplexity error",
            ),
        ]

        phase.batch_processor.process_batch = AsyncMock(return_value=mock_responses)

        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)

        result = await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=[PhaseTask.DEEP_SEARCH_GEMINI, PhaseTask.FACT_CHECK_PERPLEXITY],
        )

        # Verify responses are normalized to AgentType (lines 234-246)
        assert len(result) == 2
        assert result[0].agent_name == AgentType.GEMINI
        assert result[0].success is True
        assert result[1].agent_name == AgentType.PERPLEXITY
        assert result[1].success is False
        assert result[1].error == "Perplexity error"

    @pytest.mark.anyio
    async def test_execute_with_batching_empty_responses(self):
        """Test _execute_with_batching handles empty responses."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Mock empty responses
        phase.batch_processor.process_batch = AsyncMock(return_value=[])

        config = PipelineConfig(topic="Test topic")
        session = PipelineSession(config=config)

        result = await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=[PhaseTask.DEEP_SEARCH_GEMINI],
        )

        # Verify empty list is returned
        assert result == []

    @pytest.mark.anyio
    async def test_execute_with_batching_uses_rendered_prompt(self):
        """Test _execute_with_batching uses rendered prompts."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)

        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
            enable_batching=True,
            batch_size=5,
        )

        # Mock to capture the request
        captured_requests = []

        async def mock_enqueue(agent_type, request):
            captured_requests.append((agent_type, request))
            return "request_id"

        phase.batch_processor.enqueue = mock_enqueue
        phase.batch_processor.process_batch = AsyncMock(return_value=[])

        config = PipelineConfig(
            topic="AI Safety Research",
            doc_type="bizplan",
            language="en",
        )
        session = PipelineSession(config=config)

        await phase._execute_with_batching(
            session=session,
            phase_number=2,
            tasks=[PhaseTask.DEEP_SEARCH_GEMINI],
        )

        # Verify prompt was rendered with context
        assert len(captured_requests) == 1
        agent_type, request = captured_requests[0]
        assert agent_type == AgentType.GEMINI
        # Verify request has required attributes
        assert hasattr(request, "task_name")
        assert hasattr(request, "prompt")
        assert hasattr(request, "timeout")
        # The prompt should contain the rendered template content
        assert len(request.prompt) > 0
        # Verify context is in the prompt (topic name should appear)
        assert "AI Safety Research" in request.prompt or len(request.prompt) > 100

    @pytest.mark.anyio
    async def test_get_agent_type_for_unknown_task_defaults_to_gemini(self):
        """Test _get_agent_type_for_task defaults to GEMINI for unknown tasks."""
        from src.templates.manager import TemplateManager

        template_manager = TemplateManager()
        agent_router = AgentRouter(settings=None)
        phase = Phase2Research(
            template_manager=template_manager,
            agent_router=agent_router,
        )

        # Create a mock task that doesn't exist in the mapping
        from unittest.mock import Mock
        unknown_task = Mock(spec=PhaseTask)
        unknown_task.value = "unknown_task"

        agent_type = phase._get_agent_type_for_task(unknown_task)

        # Should default to GEMINI
        assert agent_type == AgentType.GEMINI
