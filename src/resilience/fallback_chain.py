"""
Fallback chain for AI provider error recovery.

Implements automatic fallback between AI providers when failures occur.
Follows the chain: Claude -> Gemini -> ChatGPT -> Perplexity.
"""

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from core.exceptions import GatewayException
from core.logger import get_logger
from core.models import AgentType
from gateway.base import BaseProvider, GatewayRequest, GatewayResponse

logger = get_logger(__name__)


class FallbackConfig(BaseModel):
    """Configuration for fallback chain behavior."""

    max_retries: int = Field(default=2, description="Maximum retries per provider")
    max_fallbacks: int = Field(default=3, description="Maximum number of provider fallbacks")
    enable_circuit_breaker: bool = Field(default=True, description="Enable circuit breaker")
    circuit_breaker_threshold: int = Field(default=5, description="Failures before circuit opens")
    circuit_breaker_timeout_ms: int = Field(default=60000, description="Circuit open timeout in ms")
    fallback_order: list[AgentType] = Field(
        default_factory=lambda: [
            AgentType.CLAUDE,
            AgentType.GEMINI,
            AgentType.CHATGPT,
            AgentType.PERPLEXITY,
        ],
        description="Order of provider fallback",
    )


@dataclass
class FallbackReason:
    """Reason for fallback decision."""

    class Type(StrEnum):
        """Types of failure reasons."""
        TIMEOUT = "timeout"
        CONNECTION_ERROR = "connection_error"
        RATE_LIMIT = "rate_limit"
        RESPONSE_ERROR = "response_error"
        UNKNOWN = "unknown"

    type: Type
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackContext:
    """Context tracking fallback state."""

    request: GatewayRequest
    current_provider: AgentType
    attempt_number: int = 1
    previous_errors: list[Exception] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    fallback_count: int = 0

    def add_error(self, error: Exception) -> None:
        """Add an error to the context."""
        self.previous_errors.append(error)

    def should_retry(self, config: FallbackConfig) -> bool:
        """Check if retry should be attempted."""
        return self.attempt_number <= config.max_retries

    def get_next_provider(self, config: FallbackConfig) -> AgentType | None:
        """Get the next provider in the fallback chain."""
        try:
            current_index = config.fallback_order.index(self.current_provider)
            if current_index + 1 < len(config.fallback_order):
                return config.fallback_order[current_index + 1]
        except ValueError:
            pass
        return None


class FallbackDecision:
    """Decision made by fallback chain."""

    class Action(StrEnum):
        """Possible actions."""
        RETRY = "retry"
        FALLBACK = "fallback"
        FAIL = "fail"
        SUCCESS = "success"

    action: Action
    next_provider: AgentType | None = None
    reason: FallbackReason | None = None

    def __init__(
        self,
        action: Action,
        next_provider: AgentType | None = None,
        reason: FallbackReason | None = None,
    ) -> None:
        self.action = action
        self.next_provider = next_provider
        self.reason = reason


class FallbackChain:
    """
    Manages AI provider fallback chain.

    Automatically retries failed requests and falls back to alternative providers.
    """

    def __init__(self, config: FallbackConfig | None = None) -> None:
        """
        Initialize fallback chain.

        Args:
            config: Fallback configuration (uses defaults if None)
        """
        self.config = config or FallbackConfig()
        self._circuit_states: dict[AgentType, dict[str, Any]] = {}

    def _get_circuit_state(self, provider: AgentType) -> dict[str, Any]:
        """Get circuit state for a provider."""
        if provider not in self._circuit_states:
            self._circuit_states[provider] = {
                "state": "closed",  # closed, open, half_open
                "failures": 0,
                "last_failure_time": 0,
            }
        return self._circuit_states[provider]

    def _is_circuit_open(self, provider: AgentType) -> bool:
        """Check if circuit is open for a provider."""
        if not self.config.enable_circuit_breaker:
            return False

        state = self._get_circuit_state(provider)
        if state["state"] == "open":
            # Check if timeout has passed
            if time.time() - state["last_failure_time"] > (self.config.circuit_breaker_timeout_ms / 1000):
                state["state"] = "half_open"
                return False
            return True
        return False

    def _record_success(self, provider: AgentType) -> None:
        """Record successful request (reset circuit)."""
        state = self._get_circuit_state(provider)
        state["state"] = "closed"
        state["failures"] = 0

    def _record_failure(self, provider: AgentType) -> None:
        """Record failed request (may open circuit)."""
        if not self.config.enable_circuit_breaker:
            return

        state = self._get_circuit_state(provider)
        state["failures"] += 1
        state["last_failure_time"] = time.time()

        if state["failures"] >= self.config.circuit_breaker_threshold:
            state["state"] = "open"
            logger.warning(
                "Circuit breaker opened",
                provider=provider.value,
                failures=state["failures"],
            )

    def _classify_error(self, error: Exception) -> FallbackReason:
        """Classify error into fallback reason type."""
        error_type = FallbackReason.Type.UNKNOWN
        error_message = str(error)

        if isinstance(error, TimeoutError):
            error_type = FallbackReason.Type.TIMEOUT
        elif "connection" in error_message.lower():
            error_type = FallbackReason.Type.CONNECTION_ERROR
        elif "rate limit" in error_message.lower():
            error_type = FallbackReason.Type.RATE_LIMIT
        elif isinstance(error, GatewayException):
            error_type = FallbackReason.Type.RESPONSE_ERROR

        return FallbackReason(type=error_type, message=error_message)

    def _make_decision(
        self,
        response: GatewayResponse | None,
        error: Exception | None,
        context: FallbackContext,
    ) -> FallbackDecision:
        """
        Make fallback decision based on response/error.

        Args:
            response: Gateway response (None if error occurred)
            error: Exception that occurred (None if response received)
            context: Current fallback context

        Returns:
            FallbackDecision with next action
        """
        # Success case
        if response and response.success:
            return FallbackDecision(action=FallbackDecision.Action.SUCCESS)

        # Determine error reason
        reason: FallbackReason | None = None
        if error:
            reason = self._classify_error(error)
        elif response and response.error:
            reason = FallbackReason(type=FallbackReason.Type.RESPONSE_ERROR, message=response.error)

        # Check if we should retry
        if context.should_retry(self.config):
            return FallbackDecision(action=FallbackDecision.Action.RETRY, reason=reason)

        # Check if we should fallback
        next_provider = context.get_next_provider(self.config)
        if next_provider and context.fallback_count < self.config.max_fallbacks:
            return FallbackDecision(
                action=FallbackDecision.Action.FALLBACK,
                next_provider=next_provider,
                reason=reason,
            )

        # No more options, fail
        return FallbackDecision(action=FallbackDecision.Action.FAIL, reason=reason)

    async def execute(
        self,
        request: GatewayRequest,
        initial_provider: AgentType,
        providers: dict[AgentType, BaseProvider],
    ) -> GatewayResponse:
        """
        Execute request with fallback chain.

        Args:
            request: Gateway request to execute
            initial_provider: Starting provider for the request
            providers: Dictionary of available providers

        Returns:
            GatewayResponse from successful provider or error response

        Raises:
            GatewayException: If all providers are exhausted
        """
        context = FallbackContext(
            request=request,
            current_provider=initial_provider,
        )
        original_provider = initial_provider

        while True:
            # Check circuit breaker
            if self._is_circuit_open(context.current_provider):
                logger.info(
                    "Circuit breaker open, skipping provider",
                    provider=context.current_provider.value,
                )
                # Skip to next provider
                next_provider = context.get_next_provider(self.config)
                if next_provider:
                    context.current_provider = next_provider
                    context.fallback_count += 1
                    continue
                else:
                    break

            # Get provider
            provider = providers.get(context.current_provider)
            if not provider:
                error = GatewayException(f"Provider not found: {context.current_provider}")
                context.add_error(error)
                decision = self._make_decision(None, error, context)
            else:
                # Execute request
                try:
                    response = await provider.send_message(request)

                    if response.success:
                        # Record success and return
                        self._record_success(context.current_provider)
                        response.metadata = response.metadata or {}
                        if context.fallback_count > 0:
                            response.metadata["fallback_used"] = True
                            response.metadata["original_provider"] = original_provider.value
                            response.metadata["final_provider"] = context.current_provider.value
                        return response

                    # Non-success response
                    error = GatewayException(response.error or "Request failed")
                    context.add_error(error)
                    decision = self._make_decision(response, None, context)

                except Exception as e:
                    context.add_error(e)
                    decision = self._make_decision(None, e, context)

            # Handle decision
            if decision.action == FallbackDecision.Action.SUCCESS:
                return GatewayResponse(content="", success=True)

            elif decision.action == FallbackDecision.Action.RETRY:
                context.attempt_number += 1
                logger.info(
                    "Retrying request",
                    provider=context.current_provider.value,
                    attempt=context.attempt_number,
                )
                continue

            elif decision.action == FallbackDecision.Action.FALLBACK:
                self._record_failure(context.current_provider)
                context.current_provider = decision.next_provider
                context.fallback_count += 1
                context.attempt_number = 1

                logger.warning(
                    "Fallback triggered",
                    from_provider=providers.get(context.current_provider),
                    to_provider=decision.next_provider.value if decision.next_provider else None,
                    reason=decision.reason.message if decision.reason else "Unknown",
                )
                continue

            else:  # FAIL
                self._record_failure(context.current_provider)
                break

        # All providers exhausted
        error_messages = [str(e) for e in context.previous_errors]
        logger.error(
            "All providers exhausted",
            errors=error_messages,
            total_attempts=context.attempt_number + sum(
                1 for _ in range(context.fallback_count)
            ),
        )

        return GatewayResponse(
            content="",
            success=False,
            error=f"All providers exhausted. Errors: {'; '.join(error_messages[-3:])}",
            metadata={
                "original_provider": original_provider.value,
                "fallback_count": context.fallback_count,
                "total_attempts": context.attempt_number,
            },
        )
