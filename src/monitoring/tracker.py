"""
Token tracker following SPEC-ENHANCE-004 FR-4 and US-4.

Provides token usage tracking functionality:
- Real-time token tracking by provider
- Session/phase-based aggregation
- Budget alerts at thresholds (50%, 75%, 90%, 100%)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.core.models import AgentType
from src.monitoring.calculator import CostCalculator


@dataclass
class TokenUsage:
    """
    Record of token usage for a single request.

    Attributes:
        provider: AI provider type
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total tokens (input + output)
        estimated_cost: Estimated cost in USD
        timestamp: When the request was made
        phase: Pipeline phase number
        task: Task identifier
    """

    provider: AgentType
    input_tokens: int
    output_tokens: int
    total_tokens: int = field(init=False)
    estimated_cost: float = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    phase: int = 1
    task: str = "unknown"

    def __post_init__(self):
        """Calculate derived fields."""
        self.total_tokens = self.input_tokens + self.output_tokens

        # Calculate estimated cost
        calculator = CostCalculator()
        self.estimated_cost = calculator.calculate_cost(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            provider=self.provider,
        )


@dataclass
class BudgetConfig:
    """
    Budget configuration for alerts.

    Attributes:
        daily_budget: Daily budget in USD
        weekly_budget: Weekly budget in USD
        monthly_budget: Monthly budget in USD
        alert_thresholds: Percentage thresholds for alerts (default: 50, 75, 90, 100)
    """

    daily_budget: float = 10.0
    weekly_budget: float = 50.0
    monthly_budget: float = 200.0
    alert_thresholds: list[int] = field(default_factory=lambda: [50, 75, 90, 100])


@dataclass
class BudgetAlert:
    """
    Budget alert notification.

    Attributes:
        threshold: Alert threshold percentage (50, 75, 90, 100)
        current_spending: Current spending in USD
        budget_limit: Budget limit in USD
        period: Budget period (daily, weekly, monthly)
        timestamp: When alert was generated
    """

    threshold: int
    current_spending: float
    budget_limit: float
    period: str  # "daily", "weekly", "monthly"
    timestamp: datetime = field(default_factory=datetime.now)


class TokenTracker:
    """
    Track token usage and costs.

    Responsibilities:
    - Record token usage for all requests
    - Aggregate usage by provider, phase, task
    - Calculate estimated costs
    - Check budget limits and generate alerts

    Reference: SPEC-ENHANCE-004 FR-4, US-4
    """

    def __init__(self, budget_config: BudgetConfig | None = None) -> None:
        """
        Initialize token tracker.

        Args:
            budget_config: Budget configuration for alerts
        """
        self.budget_config = budget_config or BudgetConfig()
        self._usage_records: list[TokenUsage] = []

    def track(self, usage: TokenUsage) -> None:
        """
        Record token usage.

        Args:
            usage: Token usage record
        """
        self._usage_records.append(usage)

    def get_summary(self, provider: AgentType | None = None) -> dict[str, Any]:
        """
        Get usage summary.

        Args:
            provider: Filter by provider (default: all providers)

        Returns:
            Dictionary with usage statistics
        """
        # Filter by provider if specified
        records = self._usage_records
        if provider:
            records = [r for r in records if r.provider == provider]

        if not records:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "request_count": 0,
                "by_provider": {},
                "by_phase": {},
            }

        # Aggregate statistics
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cost = sum(r.estimated_cost for r in records)

        # Group by provider
        by_provider: dict[AgentType, dict[str, Any]] = {}
        for record in records:
            if record.provider not in by_provider:
                by_provider[record.provider] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "request_count": 0,
                }
            by_provider[record.provider]["total_tokens"] += record.total_tokens
            by_provider[record.provider]["total_cost"] += record.estimated_cost
            by_provider[record.provider]["request_count"] += 1

        # Group by phase
        by_phase: dict[int, int] = {}
        for record in records:
            by_phase[record.phase] = by_phase.get(record.phase, 0) + record.total_tokens

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "request_count": len(records),
            "by_provider": {
                p.value: stats for p, stats in by_provider.items()
            },
            "by_phase": by_phase,
        }

    def check_budget(self) -> list[BudgetAlert]:
        """
        Check budget limits and generate alerts.

        Returns:
            List of budget alerts for triggered thresholds
        """
        alerts: list[BudgetAlert] = []

        # Get current spending
        summary = self.get_summary()
        current_cost = summary["total_cost"]

        # Check daily budget
        alerts.extend(
            self._check_budget_thresholds(
                current_cost=current_cost,
                budget_limit=self.budget_config.daily_budget,
                period="daily",
            )
        )

        # Check weekly budget (simplified - uses same current cost)
        alerts.extend(
            self._check_budget_thresholds(
                current_cost=current_cost,
                budget_limit=self.budget_config.weekly_budget,
                period="weekly",
            )
        )

        # Check monthly budget (simplified - uses same current cost)
        alerts.extend(
            self._check_budget_thresholds(
                current_cost=current_cost,
                budget_limit=self.budget_config.monthly_budget,
                period="monthly",
            )
        )

        return alerts

    def _check_budget_thresholds(
        self,
        current_cost: float,
        budget_limit: float,
        period: str,
    ) -> list[BudgetAlert]:
        """
        Check budget thresholds for a period.

        Args:
            current_cost: Current spending
            budget_limit: Budget limit
            period: Period name (daily, weekly, monthly)

        Returns:
            List of alerts for triggered thresholds
        """
        alerts: list[BudgetAlert] = []

        if budget_limit <= 0:
            return alerts

        usage_percentage = (current_cost / budget_limit) * 100

        # Check each threshold
        for threshold in self.budget_config.alert_thresholds:
            # Check if we've crossed this threshold
            if usage_percentage >= threshold:
                # Check if we haven't already alerted for this threshold
                # (In production, you'd track alerted thresholds)
                alerts.append(
                    BudgetAlert(
                        threshold=threshold,
                        current_spending=current_cost,
                        budget_limit=budget_limit,
                        period=period,
                    )
                )

        return alerts
