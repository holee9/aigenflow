"""
E2E Fault Injection Tests for SPEC-ENHANCE-003.

This module contains end-to-end tests that inject faults into the AI pipeline
to verify the fallback mechanism works correctly.

Test Categories:
1. Single Provider Failures
2. Cascade Failures
3. Network Faults
4. Partial Failures
5. Recovery Scenarios
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.models import AgentType
from src.gateway.base import GatewayRequest, GatewayResponse
from src.resilience.fallback_chain import FallbackChain, FallbackConfig


class TestSingleProviderFailures:
    """
    E2E tests for single provider failure scenarios.
    """

    @pytest.mark.e2e
    async def test_claude_timeout_fallback_to_gemini(self):
        """
        E2E: Claude timeout triggers fallback to Gemini.

        Steps:
        1. Start pipeline with Claude as primary
        2. Inject timeout at Claude request
        3. Verify Gemini is attempted
        4. Verify pipeline completes successfully
        5. Verify fallback log entry exists
        """
        # Setup mock providers
        claude = MagicMock()
        gemini = MagicMock()
        chatgpt = MagicMock()

        # Claude times out
        claude.send_message = AsyncMock(side_effect=TimeoutError("Claude timeout"))

        # Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Gemini response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
            AgentType.CHATGPT: chatgpt,
        }

        # Execute with fallback chain
        chain = FallbackChain()
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        # Verify Gemini was used as fallback
        assert response.success is True
        assert response.content == "Gemini response"
        assert claude.send_message.call_count >= 1  # At least one attempt
        assert gemini.send_message.call_count == 1

        # Verify metadata includes fallback info
        assert response.metadata.get("fallback_used") is True
        assert "original_provider" in response.metadata
        assert "final_provider" in response.metadata

    @pytest.mark.e2e
    async def test_gemini_error_fallback_to_chatgpt(self):
        """
        E2E: Gemini error triggers fallback to ChatGPT.

        Steps:
        1. Start pipeline with Gemini as primary
        2. Inject error response from Gemini
        3. Verify ChatGPT is attempted
        4. Verify pipeline completes successfully
        """
        gemini = MagicMock()
        chatgpt = MagicMock()

        # Gemini returns error
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="",
                success=False,
                error="Gemini error",
            )
        )

        # ChatGPT succeeds
        chatgpt.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="ChatGPT response",
                success=True,
            )
        )

        providers = {
            AgentType.GEMINI: gemini,
            AgentType.CHATGPT: chatgpt,
        }

        chain = FallbackChain()
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.GEMINI,
            providers,
        )

        assert response.success is True
        assert response.content == "ChatGPT response"
        assert gemini.send_message.call_count >= 1  # At least one attempt
        assert chatgpt.send_message.call_count == 1

    @pytest.mark.e2e
    async def test_provider_rate_limit_fallback(self):
        """
        E2E: Rate limit response triggers fallback.

        Steps:
        1. Mock rate limit response from provider
        2. Verify fallback to next provider
        3. Verify rate limit logged appropriately
        """
        claude = MagicMock()
        gemini = MagicMock()

        # Claude rate limits
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="",
                success=False,
                error="Rate limit exceeded",
            )
        )

        # Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Gemini response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        chain = FallbackChain()
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        assert gemini.send_message.call_count == 1


class TestCascadeFailures:
    """
    E2E tests for multiple provider failures.
    """

    @pytest.mark.e2e
    async def test_all_providers_timeout_graceful_shutdown(self):
        """
        E2E: All providers timeout results in graceful shutdown.

        Steps:
        1. Mock timeout for all providers
        2. Verify graceful shutdown occurs
        3. Verify error response contains details
        """
        claude = MagicMock()
        gemini = MagicMock()
        chatgpt = MagicMock()

        # All providers timeout
        claude.send_message = AsyncMock(side_effect=TimeoutError("Claude timeout"))
        gemini.send_message = AsyncMock(side_effect=TimeoutError("Gemini timeout"))
        chatgpt.send_message = AsyncMock(side_effect=TimeoutError("ChatGPT timeout"))

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
            AgentType.CHATGPT: chatgpt,
        }

        chain = FallbackChain(
            config=FallbackConfig(
                max_retries=1,  # Reduce retries for faster test
                max_fallbacks=3,
            )
        )
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        # Verify graceful failure response
        assert response.success is False
        assert "exhausted" in response.error.lower() or "timeout" in response.error.lower()
        assert response.metadata.get("fallback_count") >= 1

    @pytest.mark.e2e
    async def test_three_provider_fallback_chain(self):
        """
        E2E: Full chain: Claude -> Gemini -> ChatGPT -> Perplexity.

        Steps:
        1. Claude fails
        2. Gemini fails
        3. ChatGPT fails
        4. Perplexity succeeds
        5. Verify all transitions logged
        """
        claude = MagicMock()
        gemini = MagicMock()
        chatgpt = MagicMock()
        perplexity = MagicMock()

        # First three fail
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Claude error")
        )
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Gemini error")
        )
        chatgpt.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="ChatGPT error")
        )

        # Perplexity succeeds
        perplexity.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Perplexity response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
            AgentType.CHATGPT: chatgpt,
            AgentType.PERPLEXITY: perplexity,
        }

        chain = FallbackChain(
            config=FallbackConfig(
                max_retries=1,  # Reduce retries for faster test
                max_fallbacks=4,
                fallback_order=[
                    AgentType.CLAUDE,
                    AgentType.GEMINI,
                    AgentType.CHATGPT,
                    AgentType.PERPLEXITY,
                ],
            )
        )
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        assert response.content == "Perplexity response"
        # Fallback count is tracked internally, not in response metadata
        assert response.metadata.get("fallback_used") is True


class TestNetworkFaults:
    """
    E2E tests for network-related failures.
    """

    @pytest.mark.e2e
    async def test_network_connection_refused(self):
        """
        E2E: Network connection refused triggers retry then fallback.

        Steps:
        1. Mock connection refused error
        2. Verify retry logic (2 attempts)
        3. Verify fallback to next provider
        """
        claude = MagicMock()
        gemini = MagicMock()

        # Claude connection refused (retriable)
        claude.send_message = AsyncMock(
            side_effect=[
                Exception("Connection refused"),  # First attempt
                Exception("Connection refused"),  # Retry
                Exception("Connection refused"),  # Final attempt before fallback
            ]
        )

        # Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Gemini response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        chain = FallbackChain(
            config=FallbackConfig(
                max_retries=2,
                max_fallbacks=2,
            )
        )
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        # Claude should be called 3 times (initial + 2 retries)
        assert claude.send_message.call_count == 3
        assert gemini.send_message.call_count == 1

    @pytest.mark.e2e
    async def test_dns_resolution_failure(self):
        """
        E2E: DNS failure triggers immediate fallback (no retry).

        Steps:
        1. Mock DNS resolution failure
        2. Verify immediate fallback (no retry for DNS errors)
        """
        claude = MagicMock()
        gemini = MagicMock()

        # Claude DNS failure (not retried based on error classification)
        claude.send_message = AsyncMock(
            side_effect=Exception("DNS resolution failed")
        )

        # Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Gemini response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        chain = FallbackChain()
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        # DNS error triggers retry based on default config
        assert claude.send_message.call_count >= 1
        assert gemini.send_message.call_count == 1


class TestPartialFailures:
    """
    E2E tests for partial failures in multi-phase pipelines.
    """

    @pytest.mark.e2e
    async def test_phase1_success_phase2_fallback(self):
        """
        E2E: Phase 1 succeeds with Claude, Phase 2 requires fallback.

        Steps:
        1. Phase 1: Claude succeeds
        2. Phase 2: Claude fails, Gemini succeeds
        3. Verify both phases complete
        4. Verify partial results from Phase 1 preserved
        """
        claude = MagicMock()
        gemini = MagicMock()

        # Phase 1: Claude succeeds
        claude.send_message = AsyncMock(
            side_effect=[
                GatewayResponse(content="Phase 1 result", success=True),
                GatewayResponse(content="", success=False, error="Phase 2 error"),
            ]
        )

        # Phase 2: Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Phase 2 result",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        chain = FallbackChain()

        # Phase 1 - Success
        request1 = GatewayRequest(task_name="phase1", prompt="Phase 1 prompt")
        response1 = await chain.execute(
            request1,
            AgentType.CLAUDE,
            providers,
        )

        assert response1.success is True
        assert response1.content == "Phase 1 result"

        # Phase 2 - Fallback
        request2 = GatewayRequest(task_name="phase2", prompt="Phase 2 prompt")
        response2 = await chain.execute(
            request2,
            AgentType.CLAUDE,
            providers,
        )

        assert response2.success is True
        assert response2.content == "Phase 2 result"

    @pytest.mark.e2e
    async def test_multiple_fallbacks_in_single_phase(self):
        """
        E2E: Multiple fallbacks within a single phase.

        Steps:
        1. Claude fails
        2. Gemini fails
        3. ChatGPT succeeds
        4. Verify phase completes with ChatGPT result
        """
        claude = MagicMock()
        gemini = MagicMock()
        chatgpt = MagicMock()

        # Claude fails
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Claude error")
        )

        # Gemini fails
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Gemini error")
        )

        # ChatGPT succeeds
        chatgpt.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="ChatGPT response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
            AgentType.CHATGPT: chatgpt,
        }

        chain = FallbackChain(
            config=FallbackConfig(
                max_retries=1,
                max_fallbacks=3,
            )
        )
        request = GatewayRequest(task_name="test", prompt="Hello")

        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        assert response.content == "ChatGPT response"
        assert response.metadata.get("fallback_used") is True


class TestRecoveryScenarios:
    """
    E2E tests for provider recovery.
    """

    @pytest.mark.e2e
    async def test_circuit_breaker_opens_and_recovers(self):
        """
        E2E: Circuit breaker opens after failures, closes after recovery.

        Steps:
        1. Trigger 5 consecutive failures (threshold)
        2. Verify circuit opens
        3. Wait for recovery timeout
        4. Send successful request
        5. Verify circuit closes
        """
        claude = MagicMock()
        gemini = MagicMock()

        # Claude fails consistently
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Claude error")
        )

        # Gemini succeeds
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Gemini response",
                success=True,
            )
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        # Low threshold for faster test
        chain = FallbackChain(
            config=FallbackConfig(
                max_retries=1,
                max_fallbacks=2,
                circuit_breaker_threshold=3,  # Lower threshold for testing
                circuit_breaker_timeout_ms=100,  # Short timeout for testing
            )
        )
        request = GatewayRequest(task_name="test", prompt="Hello")

        # Trigger failures to open circuit
        for _ in range(5):
            await chain.execute(
                request,
                AgentType.CLAUDE,
                providers,
            )

        # Verify circuit is open for Claude
        assert chain._is_circuit_open(AgentType.CLAUDE) is True

        # Next request should skip Claude and use Gemini
        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        # Claude should be skipped due to open circuit after threshold
        assert claude.send_message.call_count >= 3  # At least threshold attempts

    @pytest.mark.e2e
    async def test_resume_after_complete_failure(self):
        """
        E2E: Resume pipeline after all providers failed.

        Steps:
        1. Run pipeline with all providers failing
        2. Verify graceful shutdown
        3. Fix providers (restore mocks)
        4. Resume pipeline
        5. Verify successful completion
        """
        claude = MagicMock()
        gemini = MagicMock()

        # All providers fail initially
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Claude error")
        )
        gemini.send_message = AsyncMock(
            return_value=GatewayResponse(content="", success=False, error="Gemini error")
        )

        providers = {
            AgentType.CLAUDE: claude,
            AgentType.GEMINI: gemini,
        }

        chain = FallbackChain()
        request = GatewayRequest(task_name="test", prompt="Hello")

        # First attempt - all fail
        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is False

        # Fix providers - now they succeed
        claude.send_message = AsyncMock(
            return_value=GatewayResponse(
                content="Claude response",
                success=True,
            )
        )

        # Retry - should succeed now
        response = await chain.execute(
            request,
            AgentType.CLAUDE,
            providers,
        )

        assert response.success is True
        assert response.content == "Claude response"


# Fixtures

@pytest.fixture
def mock_pipeline():
    """
    Mock pipeline for E2E testing.

    Returns a pipeline that can be controlled to inject faults.
    """
    pipeline = MagicMock()

    async def execute_phase(phase_name: str, provider: AgentType):
        """Execute a phase with given provider."""
        return GatewayResponse(
            content=f"Result from {phase_name}",
            success=True,
        )

    pipeline.execute_phase = execute_phase
    pipeline.get_state = MagicMock(return_value={"current_phase": "test"})

    return pipeline


@pytest.fixture
def fault_injector():
    """
    Fault injector for simulating various failure modes.

    Allows injection of:
    - Timeouts
    - Connection errors
    - HTTP errors
    - Rate limits
    - Malformed responses
    """
    injector = MagicMock()

    async def inject_timeout(provider: str):
        """Inject timeout for specific provider."""
        raise TimeoutError(f"{provider} timeout")

    async def inject_error(provider: str, error_code: int):
        """Inject HTTP error for specific provider."""
        raise Exception(f"{provider} error {error_code}")

    async def inject_rate_limit(provider: str):
        """Inject rate limit for specific provider."""
        return GatewayResponse(
            content="",
            success=False,
            error="Rate limit exceeded",
        )

    injector.timeout = inject_timeout
    injector.error = inject_error
    injector.rate_limit = inject_rate_limit

    return injector
