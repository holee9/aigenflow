"""
Tests for FallbackChain.

Tests follow TDD principles: written before implementation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import GatewayException
from src.core.models import AgentType
from src.gateway.base import GatewayRequest, GatewayResponse
from src.resilience.fallback_chain import (
    FallbackChain,
    FallbackConfig,
    FallbackContext,
    FallbackDecision,
    FallbackReason,
)


class TestFallbackConfig:
    """Test suite for FallbackConfig Pydantic model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = FallbackConfig()
        assert config.max_retries == 2
        assert config.max_fallbacks == 3
        assert config.enable_circuit_breaker is True
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout_ms == 60000

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = FallbackConfig(
            max_retries=3,
            max_fallbacks=5,
            enable_circuit_breaker=False,
            circuit_breaker_threshold=10,
        )
        assert config.max_retries == 3
        assert config.max_fallbacks == 5
        assert config.enable_circuit_breaker is False
        assert config.circuit_breaker_threshold == 10

    def test_fallback_order(self) -> None:
        """Test default fallback order."""
        config = FallbackConfig()
        assert config.fallback_order == [
            AgentType.CLAUDE,
            AgentType.GEMINI,
            AgentType.CHATGPT,
            AgentType.PERPLEXITY,
        ]

    def test_custom_fallback_order(self) -> None:
        """Test custom fallback order."""
        config = FallbackConfig(
            fallback_order=[
                AgentType.GEMINI,
                AgentType.CLAUDE,
                AgentType.CHATGPT,
            ]
        )
        assert len(config.fallback_order) == 3
        assert config.fallback_order[0] == AgentType.GEMINI


class TestFallbackContext:
    """Test suite for FallbackContext."""

    def test_create_context(self) -> None:
        """Test creating a fallback context."""
        request = GatewayRequest(task_name="test", prompt="Hello")
        context = FallbackContext(
            request=request,
            current_provider=AgentType.CLAUDE,
            attempt_number=1,
        )

        assert context.request == request
        assert context.current_provider == AgentType.CLAUDE
        assert context.attempt_number == 1
        assert context.previous_errors == []

    def test_add_error(self) -> None:
        """Test adding error to context."""
        context = FallbackContext(
            request=GatewayRequest(task_name="test", prompt="Hello"),
            current_provider=AgentType.CLAUDE,
            attempt_number=1,
        )

        error = GatewayException("Test error")
        context.add_error(error)

        assert len(context.previous_errors) == 1
        assert context.previous_errors[0] == error

    def test_should_retry_with_limit(self) -> None:
        """Test should_retry respects max_retries."""
        context = FallbackContext(
            request=GatewayRequest(task_name="test", prompt="Hello"),
            current_provider=AgentType.CLAUDE,
            attempt_number=1,
        )

        config = FallbackConfig(max_retries=2)

        # Should retry when under limit
        assert context.should_retry(config) is True

        # Should not retry when at limit
        context.attempt_number = 3
        assert context.should_retry(config) is False

    def test_get_next_provider(self) -> None:
        """Test getting next provider in fallback chain."""
        config = FallbackConfig(
            fallback_order=[
                AgentType.CLAUDE,
                AgentType.GEMINI,
                AgentType.CHATGPT,
            ]
        )

        context = FallbackContext(
            request=GatewayRequest(task_name="test", prompt="Hello"),
            current_provider=AgentType.CLAUDE,
            attempt_number=1,
        )

        # Next after Claude should be Gemini
        next_provider = context.get_next_provider(config)
        assert next_provider == AgentType.GEMINI

        # Next after Gemini should be ChatGPT
        context.current_provider = AgentType.GEMINI
        next_provider = context.get_next_provider(config)
        assert next_provider == AgentType.CHATGPT

        # Next after ChatGPT should be None (end of chain)
        context.current_provider = AgentType.CHATGPT
        next_provider = context.get_next_provider(config)
        assert next_provider is None


class TestFallbackDecision:
    """Test suite for FallbackDecision."""

    def test_retry_decision(self) -> None:
        """Test RETRY decision."""
        decision = FallbackDecision(action=FallbackDecision.Action.RETRY)
        assert decision.action == FallbackDecision.Action.RETRY
        assert decision.next_provider is None

    def test_fallback_decision(self) -> None:
        """Test FALLBACK decision."""
        decision = FallbackDecision(
            action=FallbackDecision.Action.FALLBACK,
            next_provider=AgentType.GEMINI,
        )
        assert decision.action == FallbackDecision.Action.FALLBACK
        assert decision.next_provider == AgentType.GEMINI

    def test_fail_decision(self) -> None:
        """Test FAIL decision."""
        decision = FallbackDecision(action=FallbackDecision.Action.FAIL)
        assert decision.action == FallbackDecision.Action.FAIL
        assert decision.next_provider is None


class TestFallbackReason:
    """Test suite for FallbackReason."""

    def test_timeout_reason(self) -> None:
        """Test TIMEOUT reason."""
        reason = FallbackReason(FallbackReason.Type.TIMEOUT, "Request timed out after 120s")
        assert reason.type == FallbackReason.Type.TIMEOUT
        assert reason.message == "Request timed out after 120s"

    def test_connection_error_reason(self) -> None:
        """Test CONNECTION_ERROR reason."""
        reason = FallbackReason(
            FallbackReason.Type.CONNECTION_ERROR,
            "Failed to connect to provider",
        )
        assert reason.type == FallbackReason.Type.CONNECTION_ERROR

    def test_rate_limit_reason(self) -> None:
        """Test RATE_LIMIT reason."""
        reason = FallbackReason(
            FallbackReason.Type.RATE_LIMIT,
            "Rate limit exceeded",
        )
        assert reason.type == FallbackReason.Type.RATE_LIMIT

    def test_response_error_reason(self) -> None:
        """Test RESPONSE_ERROR reason."""
        reason = FallbackReason(
            FallbackReason.Type.RESPONSE_ERROR,
            "Invalid response format",
        )
        assert reason.type == FallbackReason.Type.RESPONSE_ERROR


class TestFallbackChain:
    """Test suite for FallbackChain."""

    @pytest.fixture
    def config(self) -> FallbackConfig:
        """Create test fallback config."""
        return FallbackConfig(
            max_retries=2,
            max_fallbacks=3,
            fallback_order=[
                AgentType.CLAUDE,
                AgentType.GEMINI,
                AgentType.CHATGPT,
            ],
        )

    @pytest.fixture
    def mock_providers(self) -> dict[AgentType, MagicMock]:
        """Create mock providers."""
        providers = {
            AgentType.CLAUDE: MagicMock(),
            AgentType.GEMINI: MagicMock(),
            AgentType.CHATGPT: MagicMock(),
        }
        return providers

    def test_initialization(self, config: FallbackConfig) -> None:
        """Test FallbackChain initialization."""
        chain = FallbackChain(config)
        assert chain.config == config

    @pytest.mark.asyncio
    async def test_successful_request_no_fallback(
        self,
        config: FallbackConfig,
        mock_providers: dict[AgentType, MagicMock],
    ) -> None:
        """Test successful request without fallback."""
        # Setup mock to return success
        mock_response = GatewayResponse(
            content="Success",
            success=True,
        )
        mock_providers[AgentType.CLAUDE].send_message = AsyncMock(return_value=mock_response)

        chain = FallbackChain(config)
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            mock_providers,
        )

        assert response.success is True
        assert response.content == "Success"
        mock_providers[AgentType.CLAUDE].send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_failure(
        self,
        config: FallbackConfig,
        mock_providers: dict[AgentType, MagicMock],
    ) -> None:
        """Test retry on failure."""
        # Setup mock to fail first, then succeed
        mock_providers[AgentType.CLAUDE].send_message = AsyncMock(
            side_effect=[
                GatewayResponse(content="Error", success=False, error="Temporary error"),
                GatewayResponse(content="Success", success=True),
            ]
        )

        chain = FallbackChain(config)
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            mock_providers,
        )

        assert response.success is True
        assert mock_providers[AgentType.CLAUDE].send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_on_exhausted_retries(
        self,
        config: FallbackConfig,
        mock_providers: dict[AgentType, MagicMock],
    ) -> None:
        """Test fallback after retries exhausted."""
        # Claude fails, Gemini succeeds
        mock_providers[AgentType.CLAUDE].send_message = AsyncMock(
            return_value=GatewayResponse(content="Error", success=False, error="Claude error")
        )
        mock_providers[AgentType.GEMINI].send_message = AsyncMock(
            return_value=GatewayResponse(content="Gemini Success", success=True)
        )

        chain = FallbackChain(config)
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            mock_providers,
        )

        assert response.success is True
        assert response.content == "Gemini Success"

    @pytest.mark.asyncio
    async def test_fail_after_all_providers_exhausted(
        self,
        config: FallbackConfig,
        mock_providers: dict[AgentType, MagicMock],
    ) -> None:
        """Test fail after all providers exhausted."""
        # All providers fail
        for provider in mock_providers.values():
            provider.send_message = AsyncMock(
                return_value=GatewayResponse(content="Error", success=False, error="Provider error")
            )

        chain = FallbackChain(config)
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            mock_providers,
        )

        assert response.success is False
        assert "All providers exhausted" in response.error or "Failed" in response.error

    @pytest.mark.asyncio
    async def test_context_metadata_preserved(
        self,
        config: FallbackConfig,
        mock_providers: dict[AgentType, MagicMock],
    ) -> None:
        """Test that metadata is preserved through fallback chain."""
        gemini_response = GatewayResponse(
            content="Gemini Success",
            success=True,
            metadata={"provider": "gemini", "fallback_used": True},
        )
        mock_providers[AgentType.CLAUDE].send_message = AsyncMock(
            return_value=GatewayResponse(content="Error", success=False)
        )
        mock_providers[AgentType.GEMINI].send_message = AsyncMock(
            return_value=gemini_response
        )

        chain = FallbackChain(config)
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            mock_providers,
        )

        assert response.metadata.get("fallback_used") is True
        assert response.metadata.get("original_provider") == AgentType.CLAUDE
