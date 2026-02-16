"""
Stats command following SPEC-ENHANCE-004 US-3 requirements.

Provides:
- aigenflow stats: Show token usage and cost statistics
- Provider-wise breakdown
- Cost estimation
- Budget alerts
- Cache statistics integration

Reference: SPEC-ENHANCE-004 US-3, US-4
"""

from enum import StrEnum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cache import CacheManager
from monitoring.stats import Period, StatsCollector

app = typer.Typer(help="Show usage statistics and costs")
console = Console()


class StatsFormat(StrEnum):
    """Output format for statistics."""

    TABLE = "table"
    JSON = "json"
    CSV = "csv"


@app.command("stats")
def show_stats(
    period: Period = typer.Option(
        Period.ALL,
        "--period",
        "-p",
        help="Time period for statistics (daily, weekly, monthly, all)",
    ),
    format: StatsFormat = typer.Option(
        StatsFormat.TABLE,
        "--format",
        "-f",
        help="Output format (table, json, csv)",
    ),
    include_cache: bool = typer.Option(
        False,
        "--cache",
        "-c",
        help="Include cache statistics",
    ),
) -> None:
    """
    Show token usage and cost statistics.

    Displays:
    - Total tokens used
    - Total cost in USD
    - Breakdown by provider (Claude, ChatGPT, Gemini, Perplexity)
    - Breakdown by pipeline phase
    - Budget alerts if applicable
    - Cache statistics (optional)
    """
    collector = StatsCollector()
    summary = collector.get_summary(period=period)

    # Output based on format
    if format == StatsFormat.JSON:
        _output_json(summary, include_cache)
    elif format == StatsFormat.CSV:
        _output_csv(summary, include_cache)
    else:  # TABLE
        _output_table(summary, period, include_cache)


def _output_table(summary, period: Period, include_cache: bool) -> None:
    """Output statistics as a formatted table."""
    # Header
    console.print()
    console.print(
        Panel(
            f"[bold cyan]Token Usage Statistics[/bold cyan]\n"
            f"Period: {summary.period.value} "
            f"({summary.start_date.strftime('%Y-%m-%d')} to "
            f"{summary.end_date.strftime('%Y-%m-%d')})",
            title="AigenFlow Stats",
            border_style="cyan",
        )
    )

    # Summary table
    summary_table = Table(show_header=False, box=None, pad_edge=False)
    summary_table.add_column("Metric", style="cyan", width=20)
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Tokens", f"{summary.total_tokens:,}")
    summary_table.add_row("Total Cost", f"${summary.total_cost:.4f}")
    summary_table.add_row("Total Requests", f"{summary.request_count:,}")

    if summary.request_count > 0:
        avg_tokens = summary.total_tokens / summary.request_count
        avg_cost = summary.total_cost / summary.request_count
        summary_table.add_row("Avg Tokens/Request", f"{avg_tokens:,.0f}")
        summary_table.add_row("Avg Cost/Request", f"${avg_cost:.4f}")

    console.print(summary_table)
    console.print()

    # Provider breakdown
    if summary.by_provider:
        provider_table = Table(title="By Provider")
        provider_table.add_column("Provider", style="cyan")
        provider_table.add_column("Tokens", style="green", justify="right")
        provider_table.add_column("Cost ($)", style="yellow", justify="right")
        provider_table.add_column("Share", style="magenta", justify="right")

        for provider, tokens in sorted(
            summary.by_provider.items(), key=lambda x: x[1], reverse=True
        ):
            # Estimate cost (rough approximation)
            if provider == "claude":
                cost_per_m = 10.0  # Average
            elif provider == "chatgpt":
                cost_per_m = 20.0
            elif provider == "gemini":
                cost_per_m = 3.0
            elif provider == "perplexity":
                cost_per_m = 1.0
            else:
                cost_per_m = 5.0

            cost = (tokens / 1_000_000) * cost_per_m
            share = (tokens / summary.total_tokens) * 100 if summary.total_tokens > 0 else 0

            provider_table.add_row(
                provider.capitalize(),
                f"{tokens:,}",
                f"${cost:.4f}",
                f"{share:.1f}%",
            )

        console.print(provider_table)
        console.print()

    # Phase breakdown
    if summary.by_phase:
        phase_table = Table(title="By Pipeline Phase")
        phase_table.add_column("Phase", style="cyan")
        phase_table.add_column("Tokens", style="green", justify="right")
        phase_table.add_column("Share", style="magenta", justify="right")

        for phase, tokens in sorted(summary.by_phase.items()):
            share = (tokens / summary.total_tokens) * 100 if summary.total_tokens > 0 else 0
            phase_name = _get_phase_name(phase)
            phase_table.add_row(phase_name, f"{tokens:,}", f"{share:.1f}%")

        console.print(phase_table)
        console.print()

    # Budget alerts
    _show_budget_alerts(summary.total_cost)

    # Cache statistics
    if include_cache:
        _show_cache_stats()


def _output_json(summary, include_cache: bool) -> None:
    """Output statistics as JSON."""
    import json

    data = {
        "period": summary.period.value,
        "start_date": summary.start_date.isoformat(),
        "end_date": summary.end_date.isoformat(),
        "total_tokens": summary.total_tokens,
        "total_cost": summary.total_cost,
        "request_count": summary.request_count,
        "by_provider": summary.by_provider,
        "by_phase": summary.by_phase,
    }

    if include_cache:
        cache_mgr = CacheManager()
        cache_stats = cache_mgr.get_stats()
        data["cache"] = {
            "total_entries": cache_stats.total_entries,
            "total_size_mb": cache_stats.total_size_mb,
            "hit_rate": cache_stats.hit_rate,
            "hit_count": cache_stats.hit_count,
            "miss_count": cache_stats.miss_count,
        }

    console.print(json.dumps(data, indent=2))


def _output_csv(summary, include_cache: bool) -> None:
    """Output statistics as CSV."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Summary section
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Period", summary.period.value])
    writer.writerow(["Start Date", summary.start_date.strftime("%Y-%m-%d")])
    writer.writerow(["End Date", summary.end_date.strftime("%Y-%m-%d")])
    writer.writerow(["Total Tokens", summary.total_tokens])
    writer.writerow(["Total Cost", f"${summary.total_cost:.4f}"])
    writer.writerow(["Total Requests", summary.request_count])

    # Provider section
    writer.writerow([])
    writer.writerow(["Provider", "Tokens"])
    for provider, tokens in sorted(summary.by_provider.items()):
        writer.writerow([provider, tokens])

    # Phase section
    writer.writerow([])
    writer.writerow(["Phase", "Tokens"])
    for phase, tokens in sorted(summary.by_phase.items()):
        writer.writerow([phase, tokens])

    console.print(output.getvalue())


def _show_budget_alerts(total_cost: float) -> None:
    """Show budget alerts if applicable."""
    # Budget thresholds (can be configured later)
    budgets = {
        "daily": 10.0,
        "weekly": 50.0,
        "monthly": 200.0,
    }

    alerts = []

    for period, budget in budgets.items():
        percentage = (total_cost / budget) * 100 if budget > 0 else 0

        if percentage >= 100:
            alerts.append(f"[red]✗ {period.capitalize()} budget exceeded ({percentage:.0f}%)[/red]")
        elif percentage >= 90:
            alerts.append(f"[red]⚠ {period.capitalize()} budget at {percentage:.0f}%[/red]")
        elif percentage >= 75:
            alerts.append(f"[yellow]⚠ {period.capitalize()} budget at {percentage:.0f}%[/yellow]")
        elif percentage >= 50:
            alerts.append(f"[yellow]◉ {period.capitalize()} budget at {percentage:.0f}%[/yellow]")

    if alerts:
        console.print(Panel("\n".join(alerts), title="[bold]Budget Alerts[/bold]", border_style="yellow"))
        console.print()


def _show_cache_stats() -> None:
    """Show cache statistics."""
    try:
        cache_mgr = CacheManager()
        stats = cache_mgr.get_stats()

        cache_table = Table(title="Cache Statistics")
        cache_table.add_column("Metric", style="cyan")
        cache_table.add_column("Value", style="green")

        cache_table.add_row("Total Entries", str(stats.total_entries))
        cache_table.add_row("Total Size", f"{stats.total_size_mb:.2f} MB")
        cache_table.add_row("Hit Count", str(stats.hit_count))
        cache_table.add_row("Miss Count", str(stats.miss_count))

        # Color code hit rate
        hit_rate = stats.hit_rate
        if hit_rate >= 0.3:
            hit_rate_style = "green"
        elif hit_rate >= 0.15:
            hit_rate_style = "yellow"
        else:
            hit_rate_style = "red"

        cache_table.add_row(
            "Hit Rate",
            f"[{hit_rate_style}]{hit_rate:.1%}[/{hit_rate_style}]",
        )

        console.print(cache_table)
        console.print()
    except Exception as e:
        console.print(f"[yellow]Cache statistics unavailable: {e}[/yellow]")


def _get_phase_name(phase: int) -> str:
    """Get human-readable phase name."""
    phase_names = {
        1: "Phase 1: Framing",
        2: "Phase 2: Research",
        3: "Phase 3: Strategy",
        4: "Phase 4: Writing",
        5: "Phase 5: Review",
    }
    return phase_names.get(phase, f"Phase {phase}")
