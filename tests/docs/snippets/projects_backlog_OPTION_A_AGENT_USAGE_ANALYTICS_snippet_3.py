# Source: projects/backlog/OPTION_A_AGENT_USAGE_ANALYTICS.md
# Line: 614
# Valid syntax: True
# Has imports: True
# Has assignments: True

#!/usr/bin/env python3
"""CLI tool for viewing agent usage analytics.

Provides command-line interface to usage statistics including popularity
ranking, category breakdown, and unused agent detection.

Usage:
    # Show top 10 most used agents
    python scripts/agent_stats.py popularity --days 30 --limit 10

    # Show category breakdown
    python scripts/agent_stats.py categories --days 30

    # Find unused agents
    python scripts/agent_stats.py unused --days 30

    # Show usage heatmap
    python scripts/agent_stats.py heatmap --days 7

Author: @claude-code-developer
Date: 2025-10-18
"""

import argparse
from pathlib import Path
from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer
from scripts.agent_discovery import AgentDiscovery


def cmd_popularity(args):
    """Show popularity ranking."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    ranking = analyzer.get_popularity_ranking(
        days=args.days,
        min_usage=args.min_usage
    )

    print(f"\n=== Top {args.limit} Most Used Agents (Last {args.days} Days) ===\n")

    for i, agent in enumerate(ranking[:args.limit], 1):
        print(f"{i}. Agent {agent['agent_id_hash']}")
        print(f"   Category: {agent['category']}")
        print(f"   Usage: {agent['usage_count']} times")
        print(f"   Avg Session: {agent['avg_session_duration_seconds']:.1f}s")
        if agent['avg_effectiveness_score']:
            print(f"   Avg Rating: {agent['avg_effectiveness_score']:.1f}/5.0")
        print(f"   Last Used: {agent['last_used']}")
        print()


def cmd_categories(args):
    """Show category breakdown."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    breakdown = analyzer.get_category_breakdown(days=args.days)

    print(f"\n=== Usage by Category (Last {args.days} Days) ===\n")

    total = sum(breakdown.values())
    for category, count in breakdown.items():
        percentage = (count / total * 100) if total > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{category:30s} {count:4d} ({percentage:5.1f}%) {bar}")


def cmd_unused(args):
    """Find unused agents."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    if not index_path.exists():
        print(f"Error: Index not found at {index_path}")
        return

    discovery = AgentDiscovery(index_path)
    unused = analyzer.get_unused_agents(days=args.days, discovery=discovery)

    print(f"\n=== Unused Agents (Last {args.days} Days) ===\n")
    print(f"Found {len(unused)} agents with no recent usage\n")

    for agent in unused[:args.limit]:
        print(f"• {agent['agent_id']}")
        print(f"  Category: {agent['category']}")
        print(f"  Keywords: {', '.join(agent['keywords'][:5])}")
        days_since = agent['days_since_last_use']
        if days_since == float("inf"):
            print(f"  Status: Never used")
        else:
            print(f"  Last Used: {days_since} days ago")
        print()


def cmd_heatmap(args):
    """Show usage heatmap."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    heatmap = analyzer.get_usage_heatmap(days=args.days)

    print(f"\n=== Usage Heatmap (Last {args.days} Days) ===\n")
    print("Hour distribution by day of week:\n")

    # Print header
    print("Day       ", end="")
    for hour in [0, 6, 12, 18]:
        print(f"{hour:>4}h", end=" ")
    print()

    # Print heatmap rows
    for day, hours in heatmap.items():
        print(f"{day.capitalize():10s}", end="")
        for hour in [0, 6, 12, 18]:
            count = hours[hour]
            if count == 0:
                symbol = "·"
            elif count < 10:
                symbol = "░"
            elif count < 30:
                symbol = "▒"
            else:
                symbol = "█"
            print(f"  {symbol}  ", end=" ")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Agent usage analytics CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Popularity command
    pop_parser = subparsers.add_parser("popularity", help="Show popularity ranking")
    pop_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    pop_parser.add_argument("--limit", type=int, default=10, help="Number to show")
    pop_parser.add_argument("--min-usage", type=int, default=1, help="Min usage count")

    # Categories command
    cat_parser = subparsers.add_parser("categories", help="Show category breakdown")
    cat_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Unused command
    unused_parser = subparsers.add_parser("unused", help="Find unused agents")
    unused_parser.add_argument("--days", type=int, default=30, help="Days to check")
    unused_parser.add_argument("--limit", type=int, default=20, help="Max to show")

    # Heatmap command
    heat_parser = subparsers.add_parser("heatmap", help="Show usage heatmap")
    heat_parser.add_argument("--days", type=int, default=7, help="Days to analyze")

    args = parser.parse_args()

    if args.command == "popularity":
        cmd_popularity(args)
    elif args.command == "categories":
        cmd_categories(args)
    elif args.command == "unused":
        cmd_unused(args)
    elif args.command == "heatmap":
        cmd_heatmap(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()