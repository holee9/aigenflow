"""
Integration tests for SPEC-ENHANCE-004 cost optimization features.

Tests the complete integration of:
- Cache system
- Batch processing
- Token monitoring
- CLI commands
- End-to-end pipeline

Reference: SPEC-ENHANCE-004 Phase 4
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.cache import CacheManager
from src.batch import BatchQueue
from src.monitoring import TokenTracker, TokenUsage, CostCalculator, StatsCollector
from src.gateway.models import GatewayResponse


class TestCacheIntegration:
    """Test cache system integration."""

    @pytest.fixture
    def cache_manager(self, tmp_path):
        """Create a cache manager for testing."""
        return CacheManager(cache_dir=tmp_path / "cache")

    @pytest.mark.asyncio
    async def test_cache_write_read_cycle(self, cache_manager):
        """Test complete cache write and read cycle."""
        from src.core.models import AgentType

        # Create mock response
        response = GatewayResponse(
            content="Test response content",
            success=True,
            tokens_used=150,
            metadata={"phase": 1, "provider": "claude", "model": "claude-3-opus-20240229"},
        )

        # Generate cache key and save
        key = cache_manager.key_generator.generate(
            prompt="Test prompt",
            context={"context": "context123"},
            agent_type=AgentType.CLAUDE,
            phase=1,
        )

        await cache_manager.set(key, response, ttl_hours=24)

        # Retrieve from cache
        cached_response = await cache_manager.get(key)

        assert cached_response is not None
        assert cached_response.content == "Test response content"
        assert cached_response.tokens_used == 150

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache_manager):
        """Test cache miss returns None."""
        response = await cache_manager.get("nonexistent_key")
        assert response is None


class TestBatchIntegration:
    """Test batch processing integration."""

    @pytest.fixture
    def batch_queue(self):
        """Create a batch queue for testing."""
        return BatchQueue(max_batch_size=5)

    def test_enqueue_single_request(self, batch_queue):
        """Test enqueuing a single request."""
        from src.core.models import AgentType

        request = MagicMock()
        request.request_id = "test-001"

        request_id = batch_queue.enqueue(AgentType.GEMINI, request)
        assert request_id  # Should return a valid UUID
        assert batch_queue.size() == 1

    def test_enqueue_multiple_requests(self, batch_queue):
        """Test enqueuing multiple requests."""
        from src.core.models import AgentType

        for i in range(3):
            request = MagicMock()
            request.request_id = f"test-{i:03d}"
            batch_queue.enqueue(AgentType.PERPLEXITY, request)

        assert batch_queue.size() == 3

    def test_max_batch_size_limit(self, batch_queue):
        """Test batch size limit enforcement."""
        from src.core.models import AgentType

        # Try to add more than max_batch_size
        enqueued = 0
        for i in range(10):
            request = MagicMock()
            request.request_id = f"test-{i:03d}"
            request_id = batch_queue.enqueue(AgentType.GEMINI, request)
            if request_id:  # Only count if enqueue was successful
                enqueued += 1

        # Should be capped at max_batch_size
        assert enqueued == 5
        assert batch_queue.size() == 5


class TestMonitoringIntegration:
    """Test monitoring system integration."""

    @pytest.fixture
    def tracker(self):
        """Create a token tracker for testing."""
        return TokenTracker()

    def test_track_single_usage(self, tracker):
        """Test tracking a single usage event."""
        from src.monitoring.tracker import AgentType

        usage = TokenUsage(
            provider=AgentType.CLAUDE,
            input_tokens=1000,
            output_tokens=500,
            timestamp=datetime.now(),
            phase=1,
            task="test_task",
        )

        tracker.track(usage)

        assert len(tracker._usage_records) == 1
        assert tracker._usage_records[0].total_tokens == 1500

    def test_track_multiple_usage_events(self, tracker):
        """Test tracking multiple usage events."""
        from src.monitoring.tracker import AgentType

        for i in range(5):
            usage = TokenUsage(
                provider=AgentType.GEMINI,
                input_tokens=500,
                output_tokens=250,
                timestamp=datetime.now(),
                phase=2,
                task=f"task_{i}",
            )
            tracker.track(usage)

        assert len(tracker._usage_records) == 5


class TestStatsCollectorIntegration:
    """Test stats collector integration."""

    @pytest.fixture
    def collector(self):
        """Create a stats collector for testing."""
        return StatsCollector()

    def test_get_empty_summary(self, collector):
        """Test getting summary with no data."""
        from src.monitoring.stats import Period

        summary = collector.get_summary(Period.DAILY)

        assert summary.total_tokens == 0
        assert summary.total_cost == 0.0
        assert summary.request_count == 0

    def test_get_summary_with_data(self, collector):
        """Test getting summary with tracked data."""
        from src.monitoring.tracker import AgentType
        from src.monitoring.stats import Period

        # Track some usage
        usage = TokenUsage(
            provider=AgentType.CLAUDE,
            input_tokens=1000,
            output_tokens=500,
            timestamp=datetime.now(),
            phase=1,
            task="test",
        )

        collector.track(usage)

        # Get summary
        summary = collector.get_summary(Period.ALL)

        assert summary.total_tokens == 1500
        assert summary.total_cost > 0  # Cost is calculated automatically
        assert summary.request_count == 1
        assert "claude" in summary.by_provider


class TestCostCalculatorIntegration:
    """Test cost calculator integration."""

    @pytest.fixture
    def calculator(self):
        """Create a cost calculator for testing."""
        return CostCalculator()

    def test_calculate_claude_cost(self, calculator):
        """Test cost calculation for Claude."""
        from src.monitoring.tracker import AgentType

        cost = calculator.calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            provider=AgentType.CLAUDE,
        )

        # Claude: $3/M input, $15/M output
        # (1000 * 3 / 1M) + (500 * 15 / 1M) = 0.003 + 0.0075 = 0.0105
        assert cost == pytest.approx(0.0105, rel=0.01)

    def test_calculate_gemini_cost(self, calculator):
        """Test cost calculation for Gemini."""
        from src.monitoring.tracker import AgentType

        cost = calculator.calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            provider=AgentType.GEMINI,
        )

        # Gemini: $1.25/M input, $5/M output
        # (1000 * 1.25 / 1M) + (500 * 5 / 1M) = 0.00125 + 0.0025 = 0.00375
        assert cost == pytest.approx(0.00375, rel=0.01)


class TestEndToEndPipeline:
    """Test end-to-end pipeline with cost optimization."""

    @pytest.mark.asyncio
    async def test_cache_hit_saves_api_call(self, tmp_path):
        """Test that cache hit saves an API call."""
        from src.core.models import AgentType

        cache_mgr = CacheManager(cache_dir=tmp_path / "cache_test")

        # Mock response
        response = GatewayResponse(
            content="Cached response",
            success=True,
            tokens_used=150,
            metadata={"provider": "claude"},
        )

        # First call - cache miss
        key = cache_mgr.key_generator.generate(
            prompt="Test prompt",
            context={"context": "ctx123"},
            agent_type=AgentType.CLAUDE,
            phase=1,
        )

        cached = await cache_mgr.get(key)
        assert cached is None

        # Save to cache
        await cache_mgr.set(key, response)

        # Second call - cache hit
        cached = await cache_mgr.get(key)
        assert cached is not None
        assert cached.content == "Cached response"

        # Verify stats updated
        stats = cache_mgr.get_stats()
        assert stats.hit_count == 1
        assert stats.miss_count == 1

    def test_token_tracking_across_pipeline(self):
        """Test token tracking across all pipeline phases."""
        tracker = TokenTracker()
        from src.monitoring.tracker import AgentType

        # Simulate pipeline execution
        phases = [
            (1, AgentType.CLAUDE, 1500),
            (2, AgentType.GEMINI, 800),
            (2, AgentType.PERPLEXITY, 600),
            (3, AgentType.CLAUDE, 2000),
            (4, AgentType.CHATGPT, 1200),
            (5, AgentType.CLAUDE, 500),
        ]

        for phase, provider, total_tokens in phases:
            # Calculate input/output split (60/40)
            input_tokens = int(total_tokens * 0.6)
            output_tokens = int(total_tokens * 0.4)

            usage = TokenUsage(
                provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                timestamp=datetime.now(),
                phase=phase,
                task=f"phase_{phase}",
            )
            tracker.track(usage)

        # Get summary
        summary = tracker.get_summary()

        # Verify totals (get_summary returns a dict)
        assert summary["total_tokens"] == 6600
        assert summary["total_cost"] > 0

        # Verify provider breakdown (by_provider contains nested dicts)
        assert summary["by_provider"]["claude"]["total_tokens"] == 4000
        assert summary["by_provider"]["gemini"]["total_tokens"] == 800
        assert summary["by_provider"]["perplexity"]["total_tokens"] == 600
        assert summary["by_provider"]["chatgpt"]["total_tokens"] == 1200


class TestBudgetAlerts:
    """Test budget alert system."""

    def test_no_alerts_under_budget(self):
        """Test no alerts when under budget."""
        tracker = TokenTracker()
        from src.monitoring.tracker import AgentType

        # Add usage well under budget (small cost)
        usage = TokenUsage(
            provider=AgentType.CLAUDE,
            input_tokens=100,
            output_tokens=50,
            timestamp=datetime.now(),
            phase=1,
            task="test",
        )

        tracker.track(usage)
        alerts = tracker.check_budget()

        # Should have no alerts for small usage
        assert len(alerts) == 0
