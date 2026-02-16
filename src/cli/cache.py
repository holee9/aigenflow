"""
Cache management CLI commands following US-5 requirements.

Provides commands for:
- aigenflow cache list: List cached entries
- aigenflow cache clear: Clear cache
- aigenflow cache stats: Show cache statistics

Reference: SPEC-ENHANCE-004 US-5
"""


import typer
from rich.console import Console
from rich.table import Table

from cache import CacheManager

app = typer.Typer(help="Cache management commands")
console = Console()


@app.command("list")
def list_cache(
    limit: int = typer.Option(10, help="Maximum number of entries to show"),
) -> None:
    """
    List cached entries.

    Shows cache keys with metadata including creation time, access count, and size.
    """
    manager = CacheManager()

    entries = manager.storage.list()

    if not entries:
        console.print("[yellow]No cached entries found.[/yellow]")
        raise typer.Exit()

    # Create table
    table = Table(title=f"Cache Entries (showing {min(limit, len(entries))} of {len(entries)})")

    table.add_column("Key", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Created", style="green")
    table.add_column("Expires", style="yellow")
    table.add_column("Access Count", style="magenta")
    table.add_column("Size", style="blue")

    for entry in entries[:limit]:
        # Truncate key for display
        display_key = entry.key[:16] + "..." if len(entry.key) > 16 else entry.key

        size_kb = entry.size_bytes / 1024
        size_str = f"{size_kb:.1f} KB"

        table.add_row(
            display_key,
            entry.created_at.strftime("%Y-%m-%d %H:%M"),
            entry.expires_at.strftime("%Y-%m-%d %H:%M"),
            str(entry.access_count),
            size_str,
        )

    console.print(table)


@app.command("clear")
def clear_cache(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """
    Clear all cached entries.

    Deletes all cache files and resets statistics.
    """
    manager = CacheManager()

    # Get current stats
    stats = manager.get_stats()

    if stats.total_entries == 0:
        console.print("[yellow]Cache is already empty.[/yellow]")
        raise typer.Exit()

    # Show what will be cleared
    console.print("[bold]Cache Statistics:[/bold]")
    console.print(f"  Total entries: [cyan]{stats.total_entries}[/cyan]")
    console.print(f"  Total size: [cyan]{stats.total_size_mb:.2f} MB[/cyan]")
    console.print(f"  Hit rate: [cyan]{stats.hit_rate:.1%}[/cyan]")

    # Confirm
    if not confirm:
        confirm_clear = typer.confirm("\nDo you want to clear all cache entries?")
        if not confirm_clear:
            console.print("[yellow]Cache clear cancelled.[/yellow]")
            raise typer.Exit()

    # Clear cache
    import asyncio

    cleared_count = asyncio.run(manager.clear())

    console.print(f"[green]Successfully cleared {cleared_count} cache entries.[/green]")


@app.command("stats")
def show_stats() -> None:
    """
    Show cache statistics.

    Displays hit rate, total entries, cache size, and other metrics.
    """
    manager = CacheManager()
    stats = manager.get_stats()

    # Create stats table
    table = Table(title="Cache Statistics")

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Add rows
    table.add_row("Total Entries", str(stats.total_entries))
    table.add_row("Total Size", f"{stats.total_size_mb:.2f} MB")
    table.add_row("Hit Count", str(stats.hit_count))
    table.add_row("Miss Count", str(stats.miss_count))

    # Color code hit rate
    hit_rate = stats.hit_rate
    if hit_rate >= 0.3:  # 30%+ is good
        hit_rate_style = "green"
    elif hit_rate >= 0.15:  # 15-30% is okay
        hit_rate_style = "yellow"
    else:  # Below 15% is poor
        hit_rate_style = "red"

    table.add_row("Hit Rate", f"[{hit_rate_style}]{hit_rate:.1%}[/{hit_rate_style}]")

    # Add performance indicators
    if stats.total_entries > 0:
        avg_size_kb = (stats.total_size_bytes / stats.total_entries) / 1024
        table.add_row("Avg Entry Size", f"{avg_size_kb:.1f} KB")

    console.print(table)

    # Show recommendations
    console.print("\n[bold]Recommendations:[/bold]")

    if stats.total_entries == 0:
        console.print("[dim]  - Cache is empty. Stats will populate after pipeline runs.[/dim]")
    elif hit_rate < 0.15:
        console.print(
            "[yellow]  - Hit rate is below 15%. Consider:[/yellow]"
            "\n    - Increasing cache TTL (default: 24h)"
            "\n    - Checking if prompts are too variable"
        )
    elif hit_rate >= 0.3:
        console.print(
            "[green]  - Hit rate is excellent (>=30%)! Caching is working well.[/green]"
        )
    else:
        console.print(
            "[cyan]  - Hit rate is within target range (15-30%).[/cyan]"
        )

    if stats.total_size_mb > 400:
        console.print(
            "[yellow]  - Cache size is large. Consider clearing old entries.[/yellow]"
        )
