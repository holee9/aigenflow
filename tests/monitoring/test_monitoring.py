"""
Tests for monitoring module following SPEC-ENHANCE-004 Phase 3 requirements.

This module tests:
- FR-4: Token usage tracking by provider
- FR-5: Cost calculation with provider pricing
- US-3: Real-time token monitoring
- US-4: Budget alerts
"""

from datetime import datetime

import pytest

from src.core.models import AgentType
from src.monitoring.calculator import CostCalculator, PricingConfig
from src.monitoring.stats import Period, StatsCollector, UsageSummary
from src.monitoring.tracker import BudgetAlert, BudgetConfig, TokenTracker, TokenUsage


class TestPricingConfig:
    """Test pricing configuration following FR-5."""

    def test_default_pricing(self):
        """Test default pricing configuration."""
        config = PricingConfig()

        # Check Claude pricing (2026 rates per SPEC)
        assert config.get_pricing(AgentType.CLAUDE, is_input=True) == 3.00
        assert config.get_pricing(AgentType.CLAUDE, is_input=False) == 15.00

        # Check ChatGPT pricing
        assert config.get_pricing(AgentType.CHATGPT, is_input=True) == 10.00
        assert config.get_pricing(AgentType.CHATGPT, is_input=False) == 30.00

        # Check Gemini pricing
        assert config.get_pricing(AgentType.GEMINI, is_input=True) == 1.25
        assert config.get_pricing(AgentType.GEMINI, is_input=False) == 5.00

        # Check Perplexity pricing
        assert config.get_pricing(AgentType.PERPLEXITY, is_input=True) == 1.00
        assert config.get_pricing(AgentType.PERPLEXITY, is_input=False) == 1.00

    def test_custom_pricing(self):
        """Test custom pricing configuration."""
        custom_pricing = {
            AgentType.CLAUDE: {"input": 5.00, "output": 20.00},
        }

        config = PricingConfig(custom_pricing=custom_pricing)

        assert config.get_pricing(AgentType.CLAUDE, is_input=True) == 5.00
        assert config.get_pricing(AgentType.CLAUDE, is_input=False) == 20.00

        # Other agents should use default pricing
        assert config.get_pricing(AgentType.GEMINI, is_input=True) == 1.25


class TestCostCalculator:
    """Test cost calculation following FR-5."""

    def test_calculate_cost_claude(self):
        """Test cost calculation for Claude."""
        calculator = CostCalculator()

        # 1000 input tokens, 500 output tokens
        cost = calculator.calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            provider=AgentType.CLAUDE,
        )

        # Expected: (1000 * 3.00 + 500 * 15.00) / 1,000,000
        expected = (1000 * 3.00 + 500 * 15.00) / 1_000_000
        assert cost == pytest.approx(expected)

    def test_calculate_cost_gemini(self):
        """Test cost calculation for Gemini."""
        calculator = CostCalculator()

        cost = calculator.calculate_cost(
            input_tokens=10000,
            output_tokens=2000,
            provider=AgentType.GEMINI,
        )

        # Expected: (10000 * 1.25 + 2000 * 5.00) / 1,000,000
        expected = (10000 * 1.25 + 2000 * 5.00) / 1_000_000
        assert cost == expected

    def test_estimate_cost_input_only(self):
        """Test cost estimation for input tokens only."""
        calculator = CostCalculator()

        cost = calculator.estimate_cost(
            tokens=5000,
            provider=AgentType.PERPLEXITY,
            is_input=True,
        )

        # Expected: 5000 * 1.00 / 1,000,000
        expected = (5000 * 1.00) / 1_000_000
        assert cost == expected


class TestTokenUsage:
    """Test TokenUsage model following FR-4."""

    def test_create_token_usage(self):
        """Test creating a token usage record."""
        usage = TokenUsage(
            provider=AgentType.CLAUDE,
            input_tokens=1000,
            output_tokens=500,
            phase=1,
            task="test_task",
        )

        assert usage.provider == AgentType.CLAUDE
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.total_tokens == 1500
        assert usage.phase == 1
        assert usage.task == "test_task"
        assert usage.estimated_cost > 0
        assert usage.timestamp is not None


class TestTokenTracker:
    """Test TokenTracker following FR-4 and US-3."""

    def test_track_usage(self):
        """Test tracking token usage."""
        tracker = TokenTracker()

        usage = TokenUsage(
            provider=AgentType.CLAUDE,
            input_tokens=1000,
            output_tokens=500,
            phase=1,
            task="test_task",
        )

        tracker.track(usage)

        # Check that usage was recorded
        assert len(tracker._usage_records) == 1
        assert tracker._usage_records[0] == usage

    def test_get_summary_by_provider(self):
        """Test getting usage summary by provider."""
        tracker = TokenTracker()

        # Track multiple usages
        tracker.track(
            TokenUsage(
                provider=AgentType.CLAUDE,
                input_tokens=1000,
                output_tokens=500,
                phase=1,
                task="task1",
            )
        )

        tracker.track(
            TokenUsage(
                provider=AgentType.GEMINI,
                input_tokens=2000,
                output_tokens=1000,
                phase=2,
                task="task2",
            )
        )

        summary = tracker.get_summary(provider=AgentType.CLAUDE)

        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        assert summary["total_tokens"] == 1500
        assert summary["total_cost"] > 0
        assert summary["request_count"] == 1

    def test_get_summary_all_providers(self):
        """Test getting summary for all providers."""
        tracker = TokenTracker()

        # Track usages for different providers
        for provider in [AgentType.CLAUDE, AgentType.GEMINI, AgentType.PERPLEXITY]:
            tracker.track(
                TokenUsage(
                    provider=provider,
                    input_tokens=1000,
                    output_tokens=500,
                    phase=1,
                    task="test",
                )
            )

        summary = tracker.get_summary()

        assert summary["total_input_tokens"] == 3000
        assert summary["total_output_tokens"] == 1500
        assert summary["total_tokens"] == 4500
        assert summary["request_count"] == 3

    def test_check_budget_no_alerts(self):
        """Test budget check with no alerts."""
        budget_config = BudgetConfig(
            daily_budget=10.0,  # $10 daily budget
            weekly_budget=50.0,
            monthly_budget=200.0,
        )

        tracker = TokenTracker(budget_config=budget_config)

        # Track small usage
        tracker.track(
            TokenUsage(
                provider=AgentType.CLAUDE,
                input_tokens=1000,
                output_tokens=500,
                phase=1,
                task="test",
            )
        )

        alerts = tracker.check_budget()

        # Should be no alerts (well below budget)
        assert len(alerts) == 0

    def test_check_budget_50_percent_alert(self):
        """Test budget check at 50% threshold."""
        budget_config = BudgetConfig(
            daily_budget=1.0,  # $1 daily budget
        )

        tracker = TokenTracker(budget_config=budget_config)

        # Track usage to reach ~50% of budget
        # Claude: (100000 * 3.00 + 50000 * 15.00) / 1M = ~0.00105
        # We need ~$0.50 to trigger 50% alert
        tracker.track(
            TokenUsage(
                provider=AgentType.CLAUDE,
                input_tokens=150000,
                output_tokens=20000,
                phase=1,
                task="test",
            )
        )

        alerts = tracker.check_budget()

        # Should have 50% alert
        assert len(alerts) >= 1
        assert any(alert.threshold == 50 for alert in alerts)


class TestStatsCollector:
    """Test StatsCollector following US-3."""

    def test_get_daily_summary(self):
        """Test getting daily usage summary."""
        collector = StatsCollector()

        # Track some usage
        collector.track(
            TokenUsage(
                provider=AgentType.CLAUDE,
                input_tokens=1000,
                output_tokens=500,
                phase=1,
                task="test",
            )
        )

        summary = collector.get_summary(period=Period.DAILY)

        assert isinstance(summary, UsageSummary)
        assert summary.total_tokens == 1500
        assert summary.total_cost > 0

    def test_get_summary_by_phase(self):
        """Test getting summary grouped by phase."""
        collector = StatsCollector()

        # Track usage for different phases
        collector.track(
            TokenUsage(
                provider=AgentType.CLAUDE,
                input_tokens=1000,
                output_tokens=500,
                phase=1,
                task="task1",
            )
        )

        collector.track(
            TokenUsage(
                provider=AgentType.GEMINI,
                input_tokens=2000,
                output_tokens=1000,
                phase=2,
                task="task2",
            )
        )

        summary = collector.get_summary(period=Period.DAILY)

        # Should have breakdown by phase
        assert len(summary.by_phase) == 2
        assert summary.by_phase[1] == 1500  # Phase 1 total tokens
        assert summary.by_phase[2] == 3000  # Phase 2 total tokens
