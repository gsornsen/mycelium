"""CLI entry point for analytics reports.

Provides command-line interface for generating performance analytics reports
from collected telemetry data.

Usage:
    uv run python -m mycelium_analytics report --days=7
    uv run python -m mycelium_analytics report --days=30 --format=json

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import argparse
import json

from mycelium_analytics import EventStorage, MetricsAnalyzer


def main() -> None:
    """Generate analytics report."""
    parser = argparse.ArgumentParser(
        description="Mycelium Analytics Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 7-day report in text format
  uv run python -m mycelium_analytics report --days=7

  # Generate 30-day report in JSON format
  uv run python -m mycelium_analytics report --days=30 --format=json
        """,
    )
    parser.add_argument(
        "command",
        choices=["report"],
        help="Command to run",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    storage = EventStorage()
    analyzer = MetricsAnalyzer(storage)

    if args.command == "report":
        report = analyzer.get_summary_report(days=args.days)

        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            # Text format
            print(
                f"\n=== Mycelium Performance Analytics "
                f"({args.days} days) ===\n"
            )

            # Discovery Stats
            disc = report["discovery_stats"]
            print("Agent Discovery Performance:")
            print(f"  Total operations: {disc['total_operations']}")
            if disc.get("overall"):
                print(f"  Overall p95: {disc['overall']['p95_ms']:.2f}ms")
                print(f"  Overall avg: {disc['overall']['avg_ms']:.2f}ms")

            if disc.get("by_operation"):
                print("\n  By Operation:")
                for op_name, op_stats in disc["by_operation"].items():
                    print(f"    {op_name}:")
                    print(f"      Count: {op_stats['count']}")
                    print(f"      p95: {op_stats['p95_ms']:.2f}ms")
                    if "cache_hit_rate" in op_stats:
                        print(
                            f"      Cache hit rate: "
                            f"{op_stats['cache_hit_rate']:.2f}%"
                        )

            # Token Savings
            tokens = report["token_savings"]
            print("\nToken Consumption:")
            print(f"  Agents loaded: {tokens['total_agents_loaded']}")
            print(f"  Tokens loaded: {tokens['total_tokens_loaded']:,}")
            if tokens['total_agents_loaded'] > 0:
                print(
                    f"  Estimated savings: "
                    f"{tokens['estimated_savings_tokens']:,} tokens "
                    f"({tokens['savings_percentage']:.2f}%)"
                )

            # Cache Performance
            cache = report["cache_performance"]
            print("\nCache Performance:")
            if cache['total_lookups'] > 0:
                print(f"  Hit rate: {cache['hit_rate_percentage']:.2f}%")
                print(
                    f"  Avg hit latency: {cache['avg_hit_latency_ms']:.2f}ms"
                )
                print(
                    f"  Avg miss latency: "
                    f"{cache['avg_miss_latency_ms']:.2f}ms"
                )
            else:
                print("  No cache lookups recorded")

            # Trends
            trends = report["trends"]
            print(f"\nPerformance Trend: {trends['trend']}")
            if trends.get("daily_stats"):
                print(f"  Days with data: {len(trends['daily_stats'])}")

            print()


if __name__ == "__main__":
    main()
