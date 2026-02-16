"""
ChatGPT agent implementation.
"""

from pathlib import Path

from agents.base import AgentRequest, AgentResponse, AsyncAgent
from gateway.chatgpt_provider import ChatGPTProvider
from gateway.models import GatewayRequest


class ChatGPTAgent(AsyncAgent):
    """Agent for ChatGPT."""

    def __init__(self, profile_dir: Path, headless: bool = True) -> None:
        provider = ChatGPTProvider(profile_dir=profile_dir, headless=headless)
        super().__init__(gateway_provider=provider)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute ChatGPT task."""
        # Convert AgentRequest to GatewayRequest
        gw_request = GatewayRequest(
            task_name=request.task_name,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )

        # Send via gateway
        gw_response = await self.gateway.send_message(gw_request)

        # Validate and convert response
        response = await self.validate_response(gw_response)
        response.task_name = request.task_name
        return response
