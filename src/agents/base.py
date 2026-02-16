"""
Base agent protocol and utilities.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from core.models import AgentType
from gateway.models import GatewayResponse


class AgentRequest(BaseModel):
    """Request to send to AI agent."""

    task_name: str
    prompt: str
    max_tokens: int | None = None
    timeout: int = 120


class AgentResponse(BaseModel):
    """Response from AI agent."""

    agent_name: AgentType
    task_name: str
    content: str
    tokens_used: int = 0
    response_time: float = 0.0
    success: bool = True
    error: str | None = None


class AsyncAgent(ABC):
    """
    Abstract base class for all AI agents.

    Wraps gateway provider and adds agent-specific logic.
    """

    def __init__(self, gateway_provider) -> None:
        """Initialize agent with gateway provider."""
        self.gateway = gateway_provider

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute agent task.

        Args:
            request: AgentRequest with task_name and prompt

        Returns:
            AgentResponse with AI response
        """
        raise NotImplementedError

    async def validate_response(self, response: GatewayResponse) -> AgentResponse:
        """
        Validate and normalize gateway response.

        Args:
            response: Raw GatewayResponse

        Returns:
            AgentResponse with agent metadata
        """
        # Get agent type from gateway
        agent_type = self.gateway.agent_type if hasattr(self.gateway, "agent_type") else None

        # Validate response
        if not response.success:
            return AgentResponse(
                agent_name=agent_type if agent_type else AgentType.CHATGPT,
                task_name="unknown",
                content="",
                success=False,
                error=response.error or "Gateway returned failure",
            )

        # Convert to AgentResponse
        return AgentResponse(
            agent_name=agent_type if agent_type else AgentType.CHATGPT,
            task_name="unknown",  # Will be updated by caller
            content=response.content,
            tokens_used=response.tokens_used,
            response_time=response.response_time,
            success=response.success,
            error=response.error,
        )
