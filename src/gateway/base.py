"""
Base provider for AI gateway.

Defines BaseProvider interface and common functionality for all AI providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from aigenflow.core.models import AgentType


class GatewayRequest(BaseModel):
    """Request to send to AI provider."""

    task_name: str
    prompt: str
    max_tokens: int | None = None
    timeout: int = 120


class GatewayResponse(BaseModel):
    """Response from AI provider."""

    content: str
    success: bool
    error: str | None = None
    tokens_used: int = 0
    response_time: float = 0.0
    metadata: dict[str, Any] = {}


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.

    Each provider (ChatGPT, Claude, Gemini, Perplexity) inherits from this
    and implements the abstract methods.
    """

    agent_type: AgentType = None  # To be overridden by subclasses

    def __init__(self, profile_dir: Path, headless: bool = True) -> None:
        """Initialize provider with profile directory and headless mode."""
        self.profile_dir = profile_dir
        self.headless = headless

    @abstractmethod
    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """
        Send a message to the AI provider.

        Args:
            request: GatewayRequest with task_name and prompt

        Returns:
            GatewayResponse with content and metadata
        """
        raise NotImplementedError

    @abstractmethod
    async def check_session(self) -> bool:
        """
        Check if current session is valid (logged in).

        Returns:
            True if session is valid, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def login_flow(self) -> None:
        """
        Execute login flow if session is invalid.

        Should:
        1. Check if session exists
        2. If expired/missing, run login flow
        3. Save session state
        """
        raise NotImplementedError

    @abstractmethod
    def save_session(self) -> None:
        """
        Save current session state to disk.

        Sessions are persisted to allow resume functionality.
        """
        raise NotImplementedError

    @abstractmethod
    def load_session(self) -> bool:
        """
        Load session state from disk if available.

        Returns:
            True if session was loaded, False otherwise
        """
        raise NotImplementedError

    def get_profile_path(self) -> Path:
        """Get path to provider profile directory."""
        return self.profile_dir
