"""
Stats collector following SPEC-ENHANCE-004 US-3.

Provides statistics collection functionality:
- Period-based summaries (daily, weekly, monthly)
- Phase-based aggregation
- CLI-friendly output format
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from src.monitoring.tracker import TokenTracker, TokenUsage


class Period(str, Enum):
    """Time period for statistics."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL = "all"


@dataclass
class UsageSummary:
    """
    Summary of usage statistics.

    Attributes:
        period: Time period for this summary
        start_date: Start of period
        end_date: End of period
        total_tokens: Total tokens used
        total_cost: Total cost in USD
        by_provider: Token count by provider
        by_phase: Token count by phase
        request_count: Total number of requests
    """

    period: Period
    start_date: datetime
    end_date: datetime
    total_tokens: int
    total_cost: float
    by_provider: dict[str, int]  # provider_name -> token_count
    by_phase: dict[int, int]  # phase_number -> token_count
    request_count: int


class StatsCollector:
    """
    Collect and aggregate usage statistics.

    Responsibilities:
    - Track usage over time periods
    - Aggregate by provider and phase
    - Generate CLI-friendly summaries
    - Support period-based filtering

    Reference: SPEC-ENHANCE-004 US-3
    """

    def __init__(self) -> None:
        """Initialize stats collector."""
        self.tracker = TokenTracker()

    def track(self, usage: TokenUsage) -> None:
        """
        Record usage for statistics.

        Args:
            usage: Token usage record
        """
        self.tracker.track(usage)

    def get_summary(
        self,
        period: Period = Period.ALL,
    ) -> UsageSummary:
        """
        Get usage summary for time period.

        Args:
            period: Time period to summarize

        Returns:
            UsageSummary with aggregated statistics
        """
        # Calculate date range
        now = datetime.now()
        if period == Period.DAILY:
            start_date = now - timedelta(days=1)
        elif period == Period.WEEKLY:
            start_date = now - timedelta(weeks=1)
        elif period == Period.MONTHLY:
            start_date = now - timedelta(days=30)
        else:  # ALL
            start_date = datetime.min

        # Filter records by period
        filtered_records = [
            r
            for r in self.tracker._usage_records
            if r.timestamp >= start_date
        ]

        # Aggregate statistics
        total_tokens = sum(r.total_tokens for r in filtered_records)
        total_cost = sum(r.estimated_cost for r in filtered_records)

        # Group by provider
        by_provider: dict[str, int] = {}
        for record in filtered_records:
            provider_name = record.provider.value
            by_provider[provider_name] = (
                by_provider.get(provider_name, 0) + record.total_tokens
            )

        # Group by phase
        by_phase: dict[int, int] = {}
        for record in filtered_records:
            by_phase[record.phase] = (
                by_phase.get(record.phase, 0) + record.total_tokens
            )

        return UsageSummary(
            period=period,
            start_date=start_date,
            end_date=now,
            total_tokens=total_tokens,
            total_cost=total_cost,
            by_provider=by_provider,
            by_phase=by_phase,
            request_count=len(filtered_records),
        )

    def get_formatted_stats(self, period: Period = Period.ALL) -> str:
        """
        Get formatted statistics for CLI output.

        Args:
            period: Time period to summarize

        Returns:
            Formatted string with statistics
        """
        summary = self.get_summary(period=period)

        lines = [
            f"\n{'='*50}",
            f"Usage Statistics ({summary.period.value})",
            f"{'='*50}",
            f"Period: {summary.start_date.strftime('%Y-%m-%d')} to {summary.end_date.strftime('%Y-%m-%d')}",
            "",
            f"Total Tokens: {summary.total_tokens:,}",
            f"Total Cost: ${summary.total_cost:.4f}",
            f"Total Requests: {summary.request_count}",
            "",
            "By Provider:",
        ]

        for provider, tokens in sorted(summary.by_provider.items()):
            lines.append(f"  {provider}: {tokens:,} tokens")

        lines.append("")
        lines.append("By Phase:")

        for phase, tokens in sorted(summary.by_phase.items()):
            lines.append(f"  Phase {phase}: {tokens:,} tokens")

        lines.append("=" * 50)

        return "\n".join(lines)
