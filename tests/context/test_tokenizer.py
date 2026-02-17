"""
Tests for TokenCounter.

Tests follow TDD principles: written before implementation.
"""


from src.context.tokenizer import (
    ModelLimits,
    TokenCounter,
    TokenCountResult,
)


class TestModelLimits:
    """Test suite for ModelLimits."""

    def test_claude_limit(self) -> None:
        """Test Claude token limit."""
        limits = ModelLimits()
        assert limits.get_limit("claude") == 200000

    def test_gemini_limit(self) -> None:
        """Test Gemini token limit."""
        limits = ModelLimits()
        assert limits.get_limit("gemini") == 1000000

    def test_chatgpt_limit(self) -> None:
        """Test ChatGPT token limit."""
        limits = ModelLimits()
        assert limits.get_limit("chatgpt") == 128000

    def test_perplexity_limit(self) -> None:
        """Test Perplexity token limit."""
        limits = ModelLimits()
        assert limits.get_limit("perplexity") == 128000

    def test_unknown_provider_default(self) -> None:
        """Test default limit for unknown provider."""
        limits = ModelLimits()
        assert limits.get_limit("unknown") == 100000


class TestTokenCountResult:
    """Test suite for TokenCountResult."""

    def test_create_result(self) -> None:
        """Test creating a token count result."""
        result = TokenCountResult(
            total_tokens=1000,
            estimated=True,
            model_name="claude",
        )
        assert result.total_tokens == 1000
        assert result.estimated is True
        assert result.model_name == "claude"

    def test_percentage_used(self) -> None:
        """Test percentage calculation."""
        result = TokenCountResult(
            total_tokens=100000,
            estimated=True,
            model_name="claude",
        )
        # Claude limit is 200000
        assert result.get_percentage_used("claude") == 50.0

    def test_is_near_limit(self) -> None:
        """Test near limit detection."""
        result = TokenCountResult(
            total_tokens=180000,
            estimated=True,
            model_name="claude",
        )
        # 180000/200000 = 90% which is >= 80%
        assert result.is_near_limit("claude", threshold=0.8) is True

    def test_is_not_near_limit(self) -> None:
        """Test not near limit."""
        result = TokenCountResult(
            total_tokens=50000,
            estimated=True,
            model_name="claude",
        )
        # 50000/200000 = 25% which is < 80%
        assert result.is_near_limit("claude", threshold=0.8) is False


class TestTokenCounter:
    """Test suite for TokenCounter."""

    def test_count_empty_string(self) -> None:
        """Test counting empty string."""
        counter = TokenCounter()
        result = counter.count("", model_name="claude")
        assert result.total_tokens == 0

    def test_count_simple_text(self) -> None:
        """Test counting simple text."""
        counter = TokenCounter()
        # Approximate: ~4 characters per token
        text = "This is a simple test with some words."
        result = counter.count(text, model_name="claude")
        assert result.total_tokens > 0

    def test_count_with_model_specific(self) -> None:
        """Test counting with different models."""
        counter = TokenCounter()
        text = "Hello world! This is a test."

        claude_result = counter.count(text, model_name="claude")
        gemini_result = counter.count(text, model_name="gemini")

        # Results should be similar (same text)
        assert abs(claude_result.total_tokens - gemini_result.total_tokens) <= 1

    def test_count_markdown(self) -> None:
        """Test counting markdown text."""
        counter = TokenCounter()
        markdown = """
# Title

This is a paragraph.

## Subtitle

- Item 1
- Item 2

**Bold text** and *italic text*.
"""
        result = counter.count(markdown, model_name="claude")
        assert result.total_tokens > 0

    def test_count_dict(self) -> None:
        """Test counting dictionary (JSON-like)."""
        counter = TokenCounter()
        data = {
            "title": "Test",
            "content": "Some content here",
            "items": ["one", "two", "three"],
        }
        result = counter.count_dict(data, model_name="claude")
        assert result.total_tokens > 0

    def test_estimate_mode(self) -> None:
        """Test estimation mode when tiktoken not available."""
        counter = TokenCounter()
        text = "Some text for testing estimation."
        result = counter.count(text, model_name="claude", estimate_only=True)
        assert result.estimated is True

    def test_count_large_text(self) -> None:
        """Test counting large text."""
        counter = TokenCounter()
        # Create text ~50000 characters (12500 tokens at 4 chars/token)
        large_text = "word " * 10000  # 50000 chars = ~12500 tokens
        result = counter.count(large_text, model_name="claude")
        # Should count ~10000-12500 tokens
        assert result.total_tokens > 8000


class TestTokenCounterThreshold:
    """Test suite for threshold checking."""

    def test_should_summarize_true(self) -> None:
        """Test should_summarize returns True when near limit."""
        counter = TokenCounter()
        # Text that would be ~160000 tokens (80% of Claude's 200K)
        # At 4 chars/token, need ~640000 characters
        large_text = "word " * 128000  # 640000 chars = ~160000 tokens

        result = counter.count(large_text, model_name="claude")
        assert counter.should_summarize(result, provider="claude") is True

    def test_should_summarize_false(self) -> None:
        """Test should_summarize returns False when not near limit."""
        counter = TokenCounter()
        small_text = "Small text"
        result = counter.count(small_text, model_name="claude")
        assert counter.should_summarize(result, provider="claude") is False

    def test_custom_threshold(self) -> None:
        """Test custom threshold."""
        counter = TokenCounter()
        text = "word " * 10000  # ~50K chars

        result = counter.count(text, model_name="claude")
        # With 90% threshold, should not summarize yet
        assert counter.should_summarize(result, provider="claude", threshold=0.9) is False
