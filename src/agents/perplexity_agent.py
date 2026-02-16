"""
Perplexity agent implementation.
"""

from pathlib import Path

from agents.base import AgentRequest, AgentResponse, AsyncAgent
from gateway.models import GatewayRequest
from gateway.perplexity_provider import PerplexityProvider


class PerplexityAgent(AsyncAgent):
    """Agent for Perplexity."""

    def __init__(self, profile_dir: Path, headless: bool = True) -> None:
        provider = PerplexityProvider(profile_dir=profile_dir, headless=headless)
        super().__init__(gateway_provider=provider)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute Perplexity task."""
        gw_request = GatewayRequest(
            task_name=request.task_name,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )

        gw_response = await self.gateway.send_message(gw_request)

        response = await self.validate_response(gw_response)
        response.task_name = request.task_name
        return response
