"""
Token counter for context size estimation.

Provides token counting and limit checking for AI provider context windows.
Uses tiktoken when available, falls back to character-based estimation.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from core.logger import get_logger

logger = get_logger(__name__)


class ModelLimits(BaseModel):
    """
    Token limits for different AI models.

    Limits are in tokens (not characters).
    """

    claude: int = 200000  # Claude 3 (200K context)
    gemini: int = 1000000  # Gemini 1.5 Pro (1M context)
    chatgpt: int = 128000  # GPT-4 (128K context)
    perplexity: int = 128000  # Perplexity (128K context)
    default: int = 100000  # Default fallback limit

    def get_limit(self, provider: str) -> int:
        """
        Get token limit for a provider.

        Args:
            provider: Provider name (claude, gemini, chatgpt, perplexity)

        Returns:
            Token limit for the provider
        """
        provider_lower = provider.lower()
        if hasattr(self, provider_lower):
            return getattr(self, provider_lower)
        return self.default


@dataclass
class TokenCountResult:
    """
    Result of token counting operation.

    Attributes:
        total_tokens: Total token count
        estimated: Whether count is estimated (vs. exact)
        model_name: Model used for counting
        breakdown: Optional breakdown by section
    """

    total_tokens: int
    estimated: bool
    model_name: str
    breakdown: dict[str, int] = field(default_factory=dict)

    def get_percentage_used(self, provider: str) -> float:
        """
        Get percentage of context limit used.

        Args:
            provider: Provider name

        Returns:
            Percentage (0-100)
        """
        limits = ModelLimits()
        limit = limits.get_limit(provider)
        return (self.total_tokens / limit) * 100 if limit > 0 else 0

    def is_near_limit(
        self,
        provider: str,
        threshold: float = 0.8,
    ) -> bool:
        """
        Check if token count is near the limit.

        Args:
            provider: Provider name
            threshold: Threshold percentage (default 0.8 = 80%)

        Returns:
            True if near or over limit
        """
        return self.get_percentage_used(provider) >= (threshold * 100)


class TokenCounter:
    """
    Counts tokens in text for context management.

    Uses tiktoken for exact counting when available,
    falls back to character-based estimation (1 token ≈ 4 characters).
    """

    # Character-based estimation: ~4 characters per token
    CHARS_PER_TOKEN = 4

    def __init__(self) -> None:
        """Initialize token counter."""
        self._tiktoken_available = self._check_tiktoken()
        if self._tiktoken_available:
            try:
                import importlib.util

                if importlib.util.find_spec("tiktoken") is not None:
                    import tiktoken

                    self._encoding = tiktoken.get_encoding("cl100k_base")
            except Exception as exc:
                logger.warning(f"tiktoken initialization failed: {exc}")
                self._tiktoken_available = False

    def _check_tiktoken(self) -> bool:
        """Check if tiktoken is available."""
        try:
            import importlib.util

            return importlib.util.find_spec("tiktoken") is not None
        except ImportError:
            return False

    def count(
        self,
        text: str,
        model_name: str = "claude",
        estimate_only: bool = False,
    ) -> TokenCountResult:
        """
        Count tokens in text.

        Args:
            text: Text to count
            model_name: Model name for counting
            estimate_only: Force character-based estimation

        Returns:
            TokenCountResult with count and metadata
        """
        if not text:
            return TokenCountResult(
                total_tokens=0,
                estimated=True,
                model_name=model_name,
            )

        if self._tiktoken_available and not estimate_only:
            try:
                tokens = self._encoding.encode(text)
                return TokenCountResult(
                    total_tokens=len(tokens),
                    estimated=False,
                    model_name=model_name,
                )
            except Exception as exc:
                logger.warning(f"tiktoken encoding failed: {exc}, falling back to estimation")

        # Character-based estimation
        estimated_tokens = max(1, len(text) // self.CHARS_PER_TOKEN)
        return TokenCountResult(
            total_tokens=estimated_tokens,
            estimated=True,
            model_name=model_name,
        )

    def count_dict(
        self,
        data: dict[str, Any],
        model_name: str = "claude",
    ) -> TokenCountResult:
        """
        Count tokens in dictionary (serialized as JSON).

        Args:
            data: Dictionary to count
            model_name: Model name for counting

        Returns:
            TokenCountResult with count
        """
        json_str = json.dumps(data, ensure_ascii=False)
        return self.count(json_str, model_name)

    def should_summarize(
        self,
        result: TokenCountResult,
        provider: str,
        threshold: float = 0.8,
    ) -> bool:
        """
        Check if context should be summarized based on token count.

        Args:
            result: Token count result
            provider: Provider name
            threshold: Threshold percentage (default 0.8 = 80%)

        Returns:
            True if summarization is recommended
        """
        return result.is_near_limit(provider, threshold)
