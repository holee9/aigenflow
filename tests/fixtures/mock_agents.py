"""
Mock agent implementations for offline testing.

Provides configurable mock agents that simulate AI provider behavior
without requiring actual API calls or browser automation.
"""

import asyncio
from typing import Any

from src.agents.base import AgentRequest, AgentResponse
from src.agents.router import AgentRouter
from src.core.models import AgentType


class _DummyGateway:
    """Dummy gateway provider for mock agents."""
    pass


class MockAgent:
    """
    Base mock agent with configurable behavior.

    Can be configured to succeed, fail, or timeout based on request patterns.
    """

    def __init__(
        self,
        agent_type: AgentType,
        always_succeed: bool = True,
        fail_on_tasks: list[str] | None = None,
        response_delay: float = 0.01,
        response_content: str | None = None,
    ):
        """
        Initialize mock agent.

        Args:
            agent_type: Type of agent (chatgpt, claude, gemini, perplexity)
            always_succeed: If True, all requests succeed (unless fail_on_tasks matches)
            fail_on_tasks: List of task names that should fail
            response_delay: Simulated response time in seconds
            response_content: Custom response content (default: auto-generated)
        """
        self.agent_type = agent_type
        self.always_succeed = always_succeed
        self.fail_on_tasks = fail_on_tasks or []
        self.response_delay = response_delay
        self.response_content = response_content
        self.call_count = 0
        self.last_request: AgentRequest | None = None

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute mock request with simulated behavior.

        Args:
            request: Agent request to execute

        Returns:
            Mock AgentResponse
        """
        self.call_count += 1
        self.last_request = request

        # Simulate network delay
        await asyncio.sleep(self.response_delay)

        # Check if this task should fail
        if request.task_name in self.fail_on_tasks or not self.always_succeed:
            return AgentResponse(
                agent_name=self.agent_type,
                task_name=request.task_name,
                content="",
                success=False,
                error=f"Mock failure for task: {request.task_name}",
                response_time=self.response_delay,
            )

        # Generate response content
        content = self.response_content or self._generate_content(request)

        return AgentResponse(
            agent_name=self.agent_type,
            task_name=request.task_name,
            content=content,
            success=True,
            response_time=self.response_delay,
            tokens_used=len(content.split()),
        )

    def _generate_content(self, request: AgentRequest) -> str:
        """Generate mock response content based on task."""
        return f"Mock {self.agent_type.value} response for {request.task_name}"


class MockSuccessAgent(MockAgent):
    """Mock agent that always succeeds."""

    def __init__(self, agent_type: AgentType, response_delay: float = 0.01):
        super().__init__(
            agent_type=agent_type,
            always_succeed=True,
            response_delay=response_delay,
        )


class MockFailingAgent(MockAgent):
    """Mock agent that always fails."""

    def __init__(self, agent_type: AgentType, error_message: str = "Mock agent failure"):
        super().__init__(
            agent_type=agent_type,
            always_succeed=False,
        )
        self.error_message = error_message

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Always return failure response."""
        return AgentResponse(
            agent_name=self.agent_type,
            task_name=request.task_name,
            content="",
            success=False,
            error=self.error_message,
        )


class MockTimeoutAgent(MockAgent):
    """Mock agent that simulates timeout."""

    def __init__(self, agent_type: AgentType, timeout_delay: float = 5.0):
        super().__init__(
            agent_type=agent_type,
            always_succeed=True,
            response_delay=timeout_delay,
        )


def create_mock_router_with_all_agents(settings: Any = None) -> AgentRouter:
    """
    Create an AgentRouter with all mock agents registered.

    Args:
        settings: Optional settings to pass to router

    Returns:
        AgentRouter with all 4 mock agents registered
    """
    router = AgentRouter(settings)

    # Register mock agents for all types
    router.register_agent(AgentType.CHATGPT, MockSuccessAgent(AgentType.CHATGPT))
    router.register_agent(AgentType.CLAUDE, MockSuccessAgent(AgentType.CLAUDE))
    router.register_agent(AgentType.GEMINI, MockSuccessAgent(AgentType.GEMINI))
    router.register_agent(AgentType.PERPLEXITY, MockSuccessAgent(AgentType.PERPLEXITY))

    return router


def create_mock_router_with_failing_agent(
    failing_agent: AgentType,
    settings: Any = None,
) -> AgentRouter:
    """
    Create an AgentRouter with one agent configured to fail.

    Args:
        failing_agent: Which agent type should fail
        settings: Optional settings to pass to router

    Returns:
        AgentRouter with one failing agent
    """
    router = AgentRouter(settings)

    # Register agents - one will fail
    for agent_type in AgentType:
        if agent_type == failing_agent:
            router.register_agent(agent_type, MockFailingAgent(agent_type))
        else:
            router.register_agent(agent_type, MockSuccessAgent(agent_type))

    return router
