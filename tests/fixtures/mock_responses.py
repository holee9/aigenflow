"""
Mock response builders for AI agent testing.

Provides pre-configured mock responses for different phases and scenarios.
"""

from datetime import datetime

from src.core.models import AgentResponse, AgentType, PhaseResult, PhaseStatus


class MockResponseBuilder:
    """
    Builder for creating mock AI responses.

    Provides fluent interface for building test responses.
    """

    def __init__(self):
        """Initialize builder with defaults."""
        self._agent_type = AgentType.CLAUDE
        self._task_name = "mock_task"
        self._content = "Mock response content"
        self._success = True
        self._tokens_used = 100
        self._response_time = 1.0
        self._error = None

    def with_agent(self, agent_type: AgentType) -> "MockResponseBuilder":
        """Set agent type."""
        self._agent_type = agent_type
        return self

    def with_task(self, task_name: str) -> "MockResponseBuilder":
        """Set task name."""
        self._task_name = task_name
        return self

    def with_content(self, content: str) -> "MockResponseBuilder":
        """Set response content."""
        self._content = content
        return self

    def with_success(self, success: bool = True) -> "MockResponseBuilder":
        """Set success status."""
        self._success = success
        return self

    def with_tokens(self, tokens: int) -> "MockResponseBuilder":
        """Set tokens used."""
        self._tokens_used = tokens
        return self

    def with_response_time(self, time: float) -> "MockResponseBuilder":
        """Set response time."""
        self._response_time = time
        return self

    def with_error(self, error: str) -> "MockResponseBuilder":
        """Set error message."""
        self._error = error
        self._success = False
        return self

    def build(self) -> AgentResponse:
        """Build the AgentResponse."""
        return AgentResponse(
            agent_name=self._agent_type,
            task_name=self._task_name,
            content=self._content,
            tokens_used=self._tokens_used,
            response_time=self._response_time,
            success=self._success,
            error=self._error,
        )


def create_mock_success_response(
    agent_type: AgentType,
    task_name: str,
    content: str = "Mock success response",
) -> AgentResponse:
    """
    Create a mock success response.

    Args:
        agent_type: Type of agent
        task_name: Name of task
        content: Response content

    Returns:
        Mock AgentResponse with success=True
    """
    return (
        MockResponseBuilder()
        .with_agent(agent_type)
        .with_task(task_name)
        .with_content(content)
        .with_success(True)
        .build()
    )


def create_mock_failure_response(
    agent_type: AgentType,
    task_name: str,
    error: str = "Mock failure",
) -> AgentResponse:
    """
    Create a mock failure response.

    Args:
        agent_type: Type of agent
        task_name: Name of task
        error: Error message

    Returns:
        Mock AgentResponse with success=False
    """
    return (
        MockResponseBuilder()
        .with_agent(agent_type)
        .with_task(task_name)
        .with_error(error)
        .build()
    )


def create_phase_responses(
    phase_number: int,
    content_prefix: str = "Phase",
) -> list[AgentResponse]:
    """
    Create mock responses for a complete phase.

    Args:
        phase_number: Phase number (1-5)
        content_prefix: Prefix for response content

    Returns:
        List of mock AgentResponse objects for the phase
    """
    # Define expected tasks per phase
    phase_tasks = {
        1: [
            (AgentType.CHATGPT, "brainstorm_chatgpt"),
            (AgentType.CLAUDE, "validate_claude"),
        ],
        2: [
            (AgentType.GEMINI, "deep_search_gemini"),
            (AgentType.PERPLEXITY, "fact_check_perplexity"),
        ],
        3: [
            (AgentType.CHATGPT, "swot_chatgpt"),
            (AgentType.CLAUDE, "narrative_claude"),
        ],
        4: [
            (AgentType.CLAUDE, "business_plan_claude"),
            (AgentType.CHATGPT, "outline_chatgpt"),
            (AgentType.GEMINI, "charts_gemini"),
        ],
        5: [
            (AgentType.PERPLEXITY, "verify_perplexity"),
            (AgentType.CLAUDE, "final_review_claude"),
            (AgentType.CLAUDE, "polish_claude"),
        ],
    }

    tasks = phase_tasks.get(phase_number, [])

    responses = []
    for agent_type, task_name in tasks:
        response = create_mock_success_response(
            agent_type=agent_type,
            task_name=task_name,
            content=f"{content_prefix} {phase_number} - {task_name} response",
        )
        responses.append(response)

    return responses


def create_mock_phase_result(
    phase_number: int,
    status: PhaseStatus = PhaseStatus.COMPLETED,
) -> PhaseResult:
    """
    Create a mock PhaseResult.

    Args:
        phase_number: Phase number (1-5)
        status: Phase status

    Returns:
        Mock PhaseResult
    """
    phase_names = {
        1: "Phase 1: Framing",
        2: "Phase 2: Research",
        3: "Phase 3: Strategy",
        4: "Phase 4: Writing",
        5: "Phase 5: Review",
    }

    responses = []
    if status == PhaseStatus.COMPLETED:
        responses = create_phase_responses(phase_number)
    elif status == PhaseStatus.FAILED:
        responses = [create_mock_failure_response(AgentType.CLAUDE, "test_task")]

    return PhaseResult(
        phase_number=phase_number,
        phase_name=phase_names.get(phase_number, f"Phase {phase_number}"),
        status=status,
        ai_responses=responses,
        summary=f"Summary for Phase {phase_number}",
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )
