#!/usr/bin/env python3
"""Health check report for mycelium performance analytics.

Displays real-time performance dashboard with agent discovery, cache, and
token usage metrics. Provides instant visibility into mycelium's performance.

Usage:
    uv run python scripts/health_check.py
    uv run python scripts/health_check.py --days 30

Author: @cli-developer
Phase: 2 Performance Analytics - Day 2
Date: 2025-10-18
"""

import argparse
from datetime import datetime, timezone

from mycelium_analytics import EventStorage, MetricsAnalyzer


def format_duration(ms: float) -> str:
    """Format duration for display.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted string (e.g., "0.05ms", "1.5ms", "1.50s")

    Example:
        >>> format_duration(0.05)
        '0.05ms'
        >>> format_duration(1500)
        '1.50s'
    """
    if ms < 1:
        return f"{ms:.2f}ms"
    if ms < 1000:
        return f"{ms:.1f}ms"
    return f"{ms / 1000:.2f}s"


def status_icon(value: float, target: float, lower_is_better: bool = True) -> str:
    """Get status icon based on value vs target.

    Args:
        value: Actual value
        target: Target value
        lower_is_better: If True, lower values are better (e.g., latency)

    Returns:
        Status icon: check mark (pass), warning (warn), or X (fail)

    Example:
        >>> status_icon(5, 10, lower_is_better=True)
        '✅'
        >>> status_icon(85, 80, lower_is_better=False)
        '✅'
    """
    if lower_is_better:
        if value < target:
            return "✅"
        if value < target * 1.5:
            return "⚠️"
        return "❌"
    if value > target:
        return "✅"
    if value > target * 0.75:
        return "⚠️"
    return "❌"


def generate_health_report(days: int = 7) -> str:
    """Generate health check report.

    Args:
        days: Number of days to analyze (default: 7)

    Returns:
        Formatted health report string with ASCII box drawing

    Example:
        >>> report = generate_health_report(days=7)
        >>> "Mycelium Performance Health Check" in report
        True
        >>> "AGENT DISCOVERY PERFORMANCE" in report
        True
    """
    storage = EventStorage()
    analyzer = MetricsAnalyzer(storage)

    # Get metrics
    discovery = analyzer.get_discovery_stats(days)
    tokens = analyzer.get_token_savings(days)
    cache = analyzer.get_cache_performance(days)
    trends = analyzer.get_performance_trends(days)
    storage_stats = storage.get_storage_stats()

    # Build report
    lines = []

    # Header
    lines.append("╔═══════════════════════════════════════════════════════════╗")
    lines.append("║        🔍 Mycelium Performance Health Check               ║")
    lines.append(f"║        Last {days} Days{' ' * (45 - len(str(days)))}║")
    lines.append("╚═══════════════════════════════════════════════════════════╝")
    lines.append("")

    # Discovery Performance
    lines.append("📊 AGENT DISCOVERY PERFORMANCE")
    lines.append("━" * 63)

    if discovery.get("by_operation"):
        # Column headers
        col_headers = f"{'Operation':<15} {'Count':>6}   {'p50':>8}  {'p95':>8}  {'p99':>8}  {'Target':>8}  Status"
        lines.append(col_headers)

        targets = {"list_agents": 20, "get_agent": 5, "search": 10}

        for op, stats in discovery["by_operation"].items():
            target = targets.get(op, 10)
            p95 = stats["p95_ms"]
            status = status_icon(p95, target)

            lines.append(
                f"{op:<15} {stats['count']:>6,}   "
                f"{format_duration(stats['p50_ms']):>8}  "
                f"{format_duration(stats['p95_ms']):>8}  "
                f"{format_duration(stats['p99_ms']):>8}  "
                f"<{target}ms{' ' * (8 - len(str(target)) - 3)}  {status}"
            )

        lines.append("")
        overall_p95 = discovery["overall"].get("p95_ms", 0)
        overall_status = status_icon(overall_p95, 10)
        lines.append(
            f"Overall: {discovery['total_operations']:,} operations, "
            f"p95 = {format_duration(overall_p95)} {overall_status}"
        )
    else:
        lines.append("No discovery data available")

    lines.append("")

    # Cache Performance
    lines.append("⚡ CACHE PERFORMANCE")
    lines.append("━" * 63)

    if cache["total_lookups"] > 0:
        hit_rate = cache["hit_rate_percentage"]
        hit_status = status_icon(hit_rate, 80, lower_is_better=False)

        speedup = cache["avg_miss_latency_ms"] / cache["avg_hit_latency_ms"] if cache["avg_hit_latency_ms"] > 0 else 0

        lines.append(f"Hit Rate:       {hit_rate:.1f}% {hit_status} (target: >80%)")
        lines.append(
            f"Cache Hits:     {cache['cache_hits']:,} operations (avg: {format_duration(cache['avg_hit_latency_ms'])})"
        )
        lines.append(
            f"Cache Misses:   {cache['cache_misses']:,} operations "
            f"(avg: {format_duration(cache['avg_miss_latency_ms'])})"
        )
        lines.append(f"Speedup:        {speedup:.1f}x faster on cache hits")
    else:
        lines.append("No cache data available")

    lines.append("")

    # Token Savings
    lines.append("💾 TOKEN SAVINGS (Phase 1 Impact)")
    lines.append("━" * 63)

    if tokens["total_agents_loaded"] > 0:
        pct_loaded = (tokens["total_agents_loaded"] / 119) * 100
        savings_status = status_icon(tokens["savings_percentage"], 40, lower_is_better=False)

        agents_line = f"Agents Loaded:       {tokens['total_agents_loaded']} / 119 ({pct_loaded:.1f}%)"
        lines.append(agents_line)
        lines.append(f"Tokens Loaded:       {tokens['total_tokens_loaded']:,} tokens")
        baseline_line = (
            f"Baseline (pre-P1):   {tokens['estimated_baseline_tokens']:,} tokens (all 119 agents @ 450 tokens)"
        )
        lines.append(baseline_line)
        savings_line = (
            f"Savings:             "
            f"{tokens['estimated_savings_tokens']:,} tokens "
            f"({tokens['savings_percentage']:.1f}% reduction) "
            f"{savings_status}"
        )
        lines.append(savings_line)
    else:
        lines.append("No token data available")

    lines.append("")

    # Performance Trend
    lines.append("📈 PERFORMANCE TREND")
    lines.append("━" * 63)

    trend = trends.get("trend", "stable").upper()
    trend_icon_val = "✅" if trend == "IMPROVING" else "⚠️" if trend == "STABLE" else "❌"
    trend_desc = "decreasing" if trend == "IMPROVING" else "stable" if trend == "STABLE" else "increasing"
    lines.append(f"Trend: {trend} {trend_icon_val} (latency {trend_desc} over time)")

    lines.append("")

    # Storage Health
    lines.append("🗄️  STORAGE HEALTH")
    lines.append("━" * 63)

    file_count = storage_stats["file_count"]
    file_word = "file" if file_count == 1 else "files"
    lines.append(f"Event Files:    {file_count} {file_word}")
    lines.append(f"Total Events:   {storage_stats['total_events']:,} events")
    size_kb = storage_stats["total_size_bytes"] / 1024
    lines.append(f"Storage Size:   {size_kb:.0f} KB")

    if storage_stats.get("latest_event_time"):
        latest = datetime.fromisoformat(storage_stats["latest_event_time"])
        now = datetime.now(timezone.utc)
        time_ago = now - latest

        if time_ago.total_seconds() < 60:
            time_ago_str = f"{int(time_ago.total_seconds())} seconds ago"
        elif time_ago.total_seconds() < 3600:
            time_ago_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
        else:
            hours = int(time_ago.total_seconds() / 3600)
            time_ago_str = f"{hours} hours ago"

        event_time_str = latest.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Latest Event:   {event_time_str} ({time_ago_str})")
    else:
        lines.append("Latest Event:   No events recorded")

    lines.append("")
    lines.append("━" * 63)

    # Overall status
    all_good = (
        discovery.get("overall", {}).get("p95_ms", 0) < 10
        and cache.get("hit_rate_percentage", 0) > 80
        and tokens.get("savings_percentage", 0) > 40
    )

    if all_good:
        lines.append("✅ All Systems Operational - Performance Excellent")
    else:
        lines.append("⚠️  Some Metrics Below Target - Review Recommended")

    lines.append("━" * 63)
    lines.append("")

    # Tips
    lines.append("💡 Tips:")
    if cache.get("hit_rate_percentage", 0) > 80:
        hit_pct = cache["hit_rate_percentage"]
        lines.append(f"  • Cache hit rate is excellent ({hit_pct:.1f}%)")
    if tokens.get("savings_percentage", 0) > 40:
        savings_pct = tokens["savings_percentage"]
        tip_line = f"  • Phase 1 lazy loading saving {savings_pct:.1f}% of tokens"
        lines.append(tip_line)
    if discovery.get("overall", {}).get("p95_ms", 0) < 10:
        lines.append("  • All operations meeting performance targets")

    lines.append("")
    report_cmd = "Run `uv run python -m mycelium_analytics report` for details."
    lines.append(report_cmd)

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for health check."""
    parser = argparse.ArgumentParser(
        description="Display Mycelium performance health check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )

    args = parser.parse_args()

    print(generate_health_report(days=args.days))


if __name__ == "__main__":
    main()
