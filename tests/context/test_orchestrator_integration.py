"""
Integration tests for context optimization in pipeline orchestrator.

Tests the integration of TokenCounter and ContextSummary with PipelineOrchestrator.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from same paths as orchestrator
from context.summarizer import ContextSummary
from context.tokenizer import TokenCounter
from src.core.models import AgentType, DocumentType, PhaseResult, PhaseStatus, PipelineConfig
from src.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.timeout_seconds = 120
    return settings


@pytest.fixture
def pipeline_config():
    """Create a pipeline configuration."""
    return PipelineConfig(
        topic="Test topic for context optimization integration",
        doc_type=DocumentType.BIZPLAN,
    )


class TestOrchestratorContextIntegration:
    """Tests for context optimization integration in orchestrator."""

    def test_orchestrator_initialization_with_summarization(self, mock_settings):
        """Test that orchestrator initializes with context optimization components."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
            summarization_threshold=0.8,
        )

        # Verify components are initialized
        assert orchestrator.enable_summarization is True
        assert orchestrator.summarization_threshold == 0.8
        assert isinstance(orchestrator.token_counter, TokenCounter)
        assert isinstance(orchestrator.context_summary, ContextSummary)

    def test_orchestrator_initialization_without_summarization(self, mock_settings):
        """Test that orchestrator can be initialized without summarization."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=False,
        )

        # Verify summarization is disabled
        assert orchestrator.enable_summarization is False
        assert orchestrator.context_summary is None
        # Token counter should still be available for checking
        assert isinstance(orchestrator.token_counter, TokenCounter)

    def test_custom_summarization_threshold(self, mock_settings):
        """Test custom summarization threshold."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
            summarization_threshold=0.7,
        )

        assert orchestrator.summarization_threshold == 0.7

    @pytest.mark.asyncio
    async def test_context_check_before_phase_execution(
        self, mock_settings, pipeline_config
    ):
        """Test that context is checked before phase execution."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
        )

        # Create a session with some previous results
        session = orchestrator.create_session(pipeline_config)

        # Add a mock phase result
        result = PhaseResult(
            phase_number=1,
            phase_name="Test Phase",
            status=PhaseStatus.COMPLETED,
        )
        result.ai_responses = [
            MagicMock(
                agent_name=AgentType.CLAUDE,
                task_name="test_task",
                content="Test content " * 1000,  # Long content
                tokens_used=5000,
            )
        ]
        session.add_result(result)

        # Mock the should_summarize check to avoid actual token counting
        with patch.object(
            orchestrator.context_summary,
            "should_summarize_before_phase",
            return_value=False,
        ):
            # This should not raise an error
            await orchestrator._check_and_summarize_context(session, 2)

    @pytest.mark.asyncio
    async def test_summarization_triggered_at_threshold(
        self, mock_settings, pipeline_config
    ):
        """Test that summarization is triggered when threshold is exceeded."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
            summarization_threshold=0.8,
        )

        # Create a session with large previous results
        session = orchestrator.create_session(pipeline_config)

        # Add a result that exceeds threshold
        result = PhaseResult(
            phase_number=1,
            phase_name="Large Phase",
            status=PhaseStatus.COMPLETED,
        )
        result.ai_responses = [
            MagicMock(
                agent_name=AgentType.CLAUDE,
                task_name="large_task",
                content="X" * 100000,  # Very large content
                tokens_used=200000,  # Exceeds 80% of Claude's 200K limit
            )
        ]
        session.add_result(result)

        # Mock the summarization to avoid actual API call
        mock_summary_result = MagicMock(
            success=True,
            tokens_original=200000,
            tokens_summary=50000,
            reduction_ratio=0.75,
            get_summary_dict=MagicMock(return_value={"test": "summary"}),
        )

        with patch.object(
            orchestrator.context_summary,
            "should_summarize_before_phase",
            return_value=True,
        ):
            with patch.object(
                orchestrator.context_summary,
                "summarize_phase_context",
                new=AsyncMock(return_value=mock_summary_result),
            ):
                await orchestrator._check_and_summarize_context(session, 2)

                # Verify summarization was called
                orchestrator.context_summary.summarize_phase_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarization_failure_does_not_break_pipeline(
        self, mock_settings, pipeline_config
    ):
        """Test that summarization failure doesn't break pipeline execution."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
        )

        session = orchestrator.create_session(pipeline_config)

        # Mock should_summarize to return True
        with patch.object(
            orchestrator.context_summary,
            "should_summarize_before_phase",
            return_value=True,
        ):
            # Mock summarize to fail
            with patch.object(
                orchestrator.context_summary,
                "summarize_phase_context",
                new=AsyncMock(
                    side_effect=Exception("Summarization API failed")
                ),
            ):
                # Should not raise exception
                await orchestrator._check_and_summarize_context(session, 2)

    def test_session_artifacts_include_summaries(self, mock_settings, pipeline_config):
        """Test that session artifacts store summary information."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
        )

        # Verify that artifacts dict is initialized in run_pipeline
        # (This is a basic test - full integration would require running the pipeline)
        assert hasattr(orchestrator, "context_summary")
        assert hasattr(orchestrator.context_summary, "get_all_summaries")


class TestTokenCounterIntegration:
    """Tests for TokenCounter integration with orchestrator."""

    def test_token_counter_available_in_orchestrator(self, mock_settings):
        """Test that TokenCounter is available in orchestrator."""
        orchestrator = PipelineOrchestrator(
            settings=mock_settings,
            enable_summarization=True,
        )

        assert isinstance(orchestrator.token_counter, TokenCounter)

    def test_token_counter_functionality(self):
        """Test that TokenCounter works as expected."""
        counter = TokenCounter()

        # Test basic counting
        result = counter.count("Hello, world!")
        assert result.total_tokens > 0

        # Test threshold checking
        large_text = "X" * 100000
        result = counter.count(large_text)
        # Should be near limit for claude (200K)
        percentage = result.get_percentage_used("claude")
        assert 0.0 <= percentage <= 100.0
