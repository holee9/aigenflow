"""
Claude provider implementation.

Uses Playwright to interact with claude.ai.
"""

from pathlib import Path

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.selector_loader import SelectorLoader


class ClaudeProvider(BaseProvider):
    """
    Provider for Claude (claude.ai).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.CLAUDE
    provider_name: str = "claude"

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://claude.ai"

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """Send message to Claude."""
        # TODO: Implement Playwright interaction
        return GatewayResponse(
            content=f"Claude response to: {request.task_name}",
            success=True,
        )

    async def check_session(self) -> bool:
        """Check if Claude session is valid."""
        return False

    async def login_flow(self) -> None:
        """Execute Claude login flow."""
        pass

    def save_session(self) -> None:
        """Save Claude session state."""
        pass

    def load_session(self) -> bool:
        """Load Claude session state."""
        return False
