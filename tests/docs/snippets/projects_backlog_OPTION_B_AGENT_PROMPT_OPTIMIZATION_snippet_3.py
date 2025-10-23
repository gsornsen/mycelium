# Source: projects/backlog/OPTION_B_AGENT_PROMPT_OPTIMIZATION.md
# Line: 1239
# Valid syntax: True
# Has imports: True
# Has assignments: True

#!/usr/bin/env python3
"""CLI tool for agent prompt optimization.

Usage:
    # Analyze single agent
    python scripts/optimize_agent.py analyze agents/01-api-designer.md

    # Batch analyze category
    python scripts/optimize_agent.py batch-analyze --category core-development

    # Optimize single agent
    python scripts/optimize_agent.py optimize agents/01-api-designer.md --output agents/01-api-designer-v2.md

    # Batch optimize (lowest scores first)
    python scripts/optimize_agent.py batch-optimize --min-score 70 --dry-run

Author: @claude-code-developer + @documentation-engineer
Date: 2025-10-18
"""

import argparse
from pathlib import Path

from scripts.prompt_analyzer import PromptAnalyzer
from scripts.prompt_optimizer import PromptOptimizer

from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer
from scripts.agent_discovery import AgentDiscovery


def cmd_analyze(args):
    """Analyze single agent prompt."""
    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage()) if args.include_analytics else None
    )

    result = analyzer.analyze_prompt(
        Path(args.agent_path),
        agent_id=args.agent_id
    )

    print(f"\n=== Analysis: {args.agent_path} ===\n")
    print(f"Total Score: {result['total_score']:.1f}/100  (Grade: {result['grade']})")
    print(f"Token Count: {result['token_count']}")
    print()

    print("Criterion Scores:")
    for criterion, data in result['criteria_scores'].items():
        print(f"  {criterion.capitalize():15s}: {data['score']:5.1f}/100")
    print()

    if result['suggestions']:
        print("Suggestions for Improvement:")
        for suggestion in result['suggestions']:
            print(f"  - {suggestion}")
        print()


def cmd_batch_analyze(args):
    """Batch analyze agents by category."""
    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)

    # Get agents in category
    agents = discovery.list_agents(category=args.category)

    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage()) if args.include_analytics else None
    )

    print(f"\n=== Batch Analysis: {args.category} ===\n")
    print(f"Analyzing {len(agents)} agents...\n")

    results = []
    for agent in agents:
        agent_path = Path(agent['file_path'])
        result = analyzer.analyze_prompt(agent_path, agent_id=agent['id'])
        results.append({
            'agent_id': agent['id'],
            'score': result['total_score'],
            'grade': result['grade'],
            'token_count': result['token_count'],
        })

    # Sort by score (lowest first)
    results.sort(key=lambda x: x['score'])

    # Print summary
    for r in results:
        print(f"{r['agent_id']:40s}  {r['score']:5.1f}  ({r['grade']})  {r['token_count']} tokens")

    print()
    avg_score = sum(r['score'] for r in results) / len(results)
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Agents below 70: {sum(1 for r in results if r['score'] < 70)}")


def cmd_optimize(args):
    """Optimize single agent."""
    optimizer = PromptOptimizer(
        analyzer=PromptAnalyzer(usage_analyzer=UsageAnalyzer(EventStorage()))
    )

    suggestions = optimizer.suggest_improvements(
        Path(args.agent_path)
    )

    print(f"\n=== Optimization Suggestions: {args.agent_path} ===\n")

    for s in suggestions:
        print(f"[{s['priority'].upper()}] {s['category'].capitalize()}")
        print(f"  Issue: {s['issue']}")
        print(f"  Suggestion: {s['suggestion']}")
        print(f"  Estimated Impact: {s['estimated_impact']}")
        print()

    if args.apply:
        print("Applying template...")
        optimized = optimizer.apply_template(Path(args.agent_path))

        output_path = Path(args.output) if args.output else Path(args.agent_path).with_suffix('.optimized.md')
        output_path.write_text(optimized, encoding='utf-8')
        print(f"Optimized prompt written to: {output_path}")


def cmd_batch_optimize(args):
    """Batch optimize agents below score threshold."""
    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)

    analyzer = PromptAnalyzer(
        usage_analyzer=UsageAnalyzer(EventStorage())
    )
    optimizer = PromptOptimizer(analyzer=analyzer)

    # Analyze all agents
    all_agents = discovery.list_agents()
    candidates = []

    for agent in all_agents:
        agent_path = Path(agent['file_path'])
        result = analyzer.analyze_prompt(agent_path, agent_id=agent['id'])

        if result['total_score'] < args.min_score:
            candidates.append({
                'agent_id': agent['id'],
                'path': agent_path,
                'score': result['total_score'],
            })

    # Sort by score (lowest first)
    candidates.sort(key=lambda x: x['score'])

    print("\n=== Batch Optimization ===\n")
    print(f"Found {len(candidates)} agents below {args.min_score}/100\n")

    for candidate in candidates[:args.limit]:
        print(f"Optimizing: {candidate['agent_id']} ({candidate['score']:.1f}/100)")

        if not args.dry_run:
            suggestions = optimizer.suggest_improvements(candidate['path'])
            # TODO: Apply optimizations
            print(f"  - {len(suggestions)} improvements suggested")
        else:
            print("  [DRY RUN - skipped]")


def main():
    parser = argparse.ArgumentParser(description="Agent prompt optimization CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze single agent")
    analyze_parser.add_argument("agent_path", help="Path to agent markdown file")
    analyze_parser.add_argument("--agent-id", help="Agent ID for analytics lookup")
    analyze_parser.add_argument("--include-analytics", action="store_true", help="Include effectiveness metrics")

    # Batch analyze command
    batch_analyze_parser = subparsers.add_parser("batch-analyze", help="Analyze category")
    batch_analyze_parser.add_argument("--category", required=True, help="Agent category")
    batch_analyze_parser.add_argument("--include-analytics", action="store_true")

    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize single agent")
    optimize_parser.add_argument("agent_path", help="Path to agent markdown file")
    optimize_parser.add_argument("--output", help="Output path for optimized version")
    optimize_parser.add_argument("--apply", action="store_true", help="Apply template")

    # Batch optimize command
    batch_optimize_parser = subparsers.add_parser("batch-optimize", help="Batch optimize low-scoring agents")
    batch_optimize_parser.add_argument("--min-score", type=float, default=70, help="Min acceptable score")
    batch_optimize_parser.add_argument("--limit", type=int, default=10, help="Max agents to optimize")
    batch_optimize_parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "batch-analyze":
        cmd_batch_analyze(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "batch-optimize":
        cmd_batch_optimize(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
