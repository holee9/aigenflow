"""
Tests for ContextSummary class.

Tests for context summarization functionality including threshold checking,
token counting, and summary generation.
"""

import pytest

from src.agents.router import AgentRouter
from src.context.summarizer import ContextSummary, SummaryConfig, SummaryResult
from src.core.models import AgentResponse, AgentType, PhaseResult, PhaseStatus


class TestSummaryConfig:
    """Tests for SummaryConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SummaryConfig()

        assert config.enabled is True
        assert config.target_reduction_ratio == 0.5
        assert config.agent_type == AgentType.CLAUDE
        assert config.max_retries == 2
        assert len(config.preserve_sections) == 3

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SummaryConfig(
            enabled=False,
            target_reduction_ratio=0.7,
            max_retries=5,
        )

        assert config.enabled is False
        assert config.target_reduction_ratio == 0.7
        assert config.max_retries == 5


class TestSummaryResult:
    """Tests for SummaryResult dataclass."""

    def test_create_summary_result(self):
        """Test creating a summary result."""
        result = SummaryResult(
            original_text="Original context text",
            summarized_text="Summarized text",
            tokens_original=1000,
            tokens_summary=500,
            reduction_ratio=0.5,
        )

        assert result.original_text == "Original context text"
        assert result.summarized_text == "Summarized text"
        assert result.tokens_original == 1000
        assert result.tokens_summary == 500
        assert result.reduction_ratio == 0.5
        assert result.success is True

    def test_get_summary_dict(self):
        """Test converting summary result to dictionary."""
        result = SummaryResult(
            original_text="Original",
            summarized_text="Summary",
            tokens_original=100,
            tokens_summary=50,
            reduction_ratio=0.5,
        )

        summary_dict = result.get_summary_dict()

        assert summary_dict["original_length"] == len("Original")
        assert summary_dict["summary_length"] == len("Summary")
        assert summary_dict["tokens_original"] == 100
        assert summary_dict["tokens_summary"] == 50
        assert summary_dict["reduction_ratio"] == 0.5
        assert summary_dict["success"] is True
        assert "timestamp" in summary_dict

    def test_failed_summary_result(self):
        """Test summary result with failure."""
        result = SummaryResult(
            original_text="",
            summarized_text="",
            tokens_original=0,
            tokens_summary=0,
            reduction_ratio=0.0,
            success=False,
            error="Summarization failed",
        )

        assert result.success is False
        assert result.error == "Summarization failed"


class TestContextSummary:
    """Tests for ContextSummary class."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        assert summary.agent_router is router
        assert summary.config is not None
        assert summary.config.enabled is True
        assert len(summary._summaries) == 0

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        router = AgentRouter(settings=None)
        config = SummaryConfig(enabled=False, target_reduction_ratio=0.7)
        summary = ContextSummary(agent_router=router, config=config)

        assert summary.config is config
        assert summary.config.enabled is False
        assert summary.config.target_reduction_ratio == 0.7

    def test_extract_context_from_results(self):
        """Test extracting context from phase results."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        # Create mock phase results
        result1 = PhaseResult(
            phase_number=1,
            phase_name="Phase 1",
            status=PhaseStatus.COMPLETED,
            ai_responses=[
                AgentResponse(
                    agent_name=AgentType.CLAUDE,
                    task_name="brainstorm",
                    content="Brainstorming content here",
                    success=True,
                )
            ],
            summary="Phase 1 summary",
        )

        result2 = PhaseResult(
            phase_number=2,
            phase_name="Phase 2",
            status=PhaseStatus.COMPLETED,
            ai_responses=[
                AgentResponse(
                    agent_name=AgentType.GEMINI,
                    task_name="research",
                    content="Research content here",
                    success=True,
                )
            ],
            summary="Phase 2 summary",
        )

        context = summary._extract_context_from_results([result1, result2])

        assert "Phase 1" in context
        assert "Phase 2" in context
        assert "Brainstorming content" in context
        assert "Research content" in context

    def test_extract_context_filters_failed_results(self):
        """Test that failed phases are excluded from context."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        result1 = PhaseResult(
            phase_number=1,
            phase_name="Phase 1",
            status=PhaseStatus.COMPLETED,
            ai_responses=[],
        )

        result2 = PhaseResult(
            phase_number=2,
            phase_name="Phase 2",
            status=PhaseStatus.FAILED,
            ai_responses=[],
        )

        context = summary._extract_context_from_results([result1, result2])

        assert "Phase 1" in context
        assert "Phase 2" not in context or "Status: failed" in context

    def test_build_summary_prompt(self):
        """Test building summary prompt."""
        router = AgentRouter(settings=None)
        config = SummaryConfig(target_reduction_ratio=0.6)
        summary = ContextSummary(agent_router=router, config=config)

        context = "This is the context to summarize"
        prompt = summary._build_summary_prompt(context, 3)

        assert "60%" in prompt
        assert context in prompt
        assert "key decisions" in prompt.lower()

    def test_should_summarize_before_phase_with_no_results(self):
        """Test should_summarize returns False with no results."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        result = summary.should_summarize_before_phase(
            session_results=[],
            current_phase=2,
            provider="claude",
            threshold=0.8,
        )

        assert result is False

    def test_should_summarize_below_threshold(self):
        """Test should_summarize returns False when below threshold."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        # Create minimal phase result
        result = PhaseResult(
            phase_number=1,
            phase_name="Phase 1",
            status=PhaseStatus.COMPLETED,
            ai_responses=[
                AgentResponse(
                    agent_name=AgentType.CLAUDE,
                    task_name="test",
                    content="Short content",
                    success=True,
                )
            ],
        )

        should_summarize = summary.should_summarize_before_phase(
            session_results=[result],
            current_phase=2,
            provider="claude",
            threshold=0.99,  # Very high threshold
        )

        # Short content should not trigger summarization at high threshold
        assert should_summarize is False

    def test_get_summary_returns_none_for_nonexistent_phase(self):
        """Test get_summary returns None for non-existent phase."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        result = summary.get_summary(1)
        assert result is None

    def test_get_all_summaries_returns_empty_dict_initially(self):
        """Test get_all_summaries returns empty dict initially."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        summaries = summary.get_all_summaries()
        assert summaries == {}

    def test_clear_summaries(self):
        """Test clearing all summaries."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        # Simulate storing a summary
        summary._summaries[1] = SummaryResult(
            original_text="test",
            summarized_text="test",
            tokens_original=10,
            tokens_summary=5,
            reduction_ratio=0.5,
        )

        assert len(summary._summaries) == 1

        summary.clear_summaries()

        assert len(summary._summaries) == 0

    @pytest.mark.anyio
    async def test_summarize_phase_context_with_disabled_config(self):
        """Test summarize_phase_context returns immediately when disabled."""
        router = AgentRouter(settings=None)
        config = SummaryConfig(enabled=False)
        summary = ContextSummary(agent_router=router, config=config)

        result = await summary.summarize_phase_context(
            session_results=[],
            current_phase=2,
        )

        assert result.success is False
        assert result.error == "Summarization disabled"

    @pytest.mark.anyio
    async def test_summarize_phase_context_with_no_previous_results(self):
        """Test summarize_phase_context with no previous results."""
        router = AgentRouter(settings=None)
        summary = ContextSummary(agent_router=router)

        # Create result for current phase (not previous)
        current_result = PhaseResult(
            phase_number=2,
            phase_name="Phase 2",
            status=PhaseStatus.PENDING,
            ai_responses=[],
        )

        result = await summary.summarize_phase_context(
            session_results=[current_result],
            current_phase=2,
        )

        assert result.success is True
        assert result.tokens_original == 0
        assert result.tokens_summary == 0
