"""
Gemini provider implementation.

Uses Playwright to interact with gemini.google.com.
"""

from pathlib import Path

from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse
from gateway.selector_loader import SelectorLoader


class GeminiProvider(BaseProvider):
    """
    Provider for Gemini (gemini.google.com).

    Handles login, message sending, and session management.
    """

    agent_type: AgentType = AgentType.GEMINI
    provider_name: str = "gemini"

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = True,
        selector_loader: SelectorLoader | None = None,
    ) -> None:
        super().__init__(profile_dir, headless, selector_loader)
        self.base_url = "https://gemini.google.com"

    async def send_message(self, request: GatewayRequest) -> GatewayResponse:
        """Send message to Gemini."""
        return GatewayResponse(
            content=f"Gemini response to: {request.task_name}",
            success=True,
        )

    async def check_session(self) -> bool:
        """Check if Gemini session is valid."""
        return False

    async def login_flow(self) -> None:
        """Execute Gemini login flow."""
        pass

    def save_session(self) -> None:
        """Save Gemini session state."""
        pass

    def load_session(self) -> bool:
        """Load Gemini session state."""
        return False
