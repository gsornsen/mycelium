# Source: projects/backlog/OPTION_C_SMART_AGENT_SUGGESTIONS.md
# Line: 781
# Valid syntax: True
# Has imports: True
# Has assignments: True

#!/usr/bin/env python3
"""CLI tool for smart agent suggestions.

Usage:
    # Auto-detect context from working directory
    mycelium suggest

    # Manual query
    mycelium suggest "help with react components"

    # Suggest within category
    mycelium suggest "api design" --category core-development

    # Explain why agent was suggested
    mycelium suggest --explain react-tanstack-developer --query "react frontend"

Author: @claude-code-developer
Date: 2025-10-18
"""

import argparse
import subprocess
from pathlib import Path
from mycelium_recommender.context_extractor import ContextExtractor
from mycelium_recommender.recommender import AgentRecommender
from scripts.agent_discovery import AgentDiscovery


def auto_detect_files() -> list[Path]:
    """Auto-detect recently modified files in working directory.

    Returns:
        List of recently modified file paths (last 10)
    """
    try:
        # Get recently modified files (git-aware)
        result = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if result:
            return [Path(p) for p in result.split('\n')[:10]]
        else:
            # Fallback: list files in current directory
            return list(Path.cwd().rglob("*.py"))[:10]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo - use current directory
        return list(Path.cwd().rglob("*.*"))[:10]


def cmd_suggest(args):
    """Suggest agents based on context."""
    # Initialize components
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery, use_redis=True)
    extractor = ContextExtractor()

    # Extract context
    if args.query:
        # Manual query
        context = extractor.extract_from_query(args.query)
    else:
        # Auto-detect from environment
        file_paths = auto_detect_files()
        context = extractor.extract_full_context(
            file_paths=file_paths,
            include_git=True
        )

    print(f"\n=== Agent Suggestions ===\n")
    print(f"Context: {context}\n")

    # Get suggestions
    if args.category:
        suggestions = recommender.suggest_by_category(
            context,
            category=args.category,
            top_k=args.top_k
        )
    else:
        suggestions = recommender.suggest(
            context,
            top_k=args.top_k,
            usage_boost=args.use_analytics
        )

    if not suggestions:
        print("No suggestions found. Try a different query or context.")
        return

    # Display suggestions
    for i, (agent_id, score, metadata) in enumerate(suggestions, 1):
        percentage = int(score * 100)
        print(f"{i}. {agent_id}")
        print(f"   Match: {percentage}%")
        print(f"   Category: {metadata.get('category', 'unknown')}")
        print(f"   Description: {metadata.get('description', '')[:80]}...")
        print()

    # Show how to invoke
    top_agent = suggestions[0][0]
    print(f"To use top suggestion: claude --agents {top_agent}")


def cmd_explain(args):
    """Explain why agent was suggested."""
    index_path = Path("plugins/mycelium-core/agents/index.json")
    discovery = AgentDiscovery(index_path)
    recommender = AgentRecommender(discovery)
    extractor = ContextExtractor()

    # Extract context
    context = extractor.extract_from_query(args.query)

    # Get explanation
    explanation = recommender.explain_suggestion(args.agent_id, context)

    print(f"\n=== Explanation: {args.agent_id} ===\n")
    print(f"Similarity Score: {explanation['similarity_score']:.2%}")
    print(f"\nMatched Keywords:")
    for keyword in explanation['matched_keywords']:
        print(f"  - {keyword}")
    print(f"\nTop Features:")
    for feature, weight in explanation['top_features']:
        print(f"  - {feature}: {weight:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Smart agent suggestions")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest agents")
    suggest_parser.add_argument("query", nargs="?", help="Optional query (auto-detect if omitted)")
    suggest_parser.add_argument("--category", help="Filter by category")
    suggest_parser.add_argument("--top-k", type=int, default=5, help="Number of suggestions")
    suggest_parser.add_argument("--use-analytics", action="store_true", help="Boost with usage data")

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain suggestion")
    explain_parser.add_argument("--agent-id", required=True, help="Agent ID to explain")
    explain_parser.add_argument("--query", required=True, help="Query context")

    args = parser.parse_args()

    if args.command == "suggest" or args.command is None:
        # Default to suggest if no command
        if not hasattr(args, 'query'):
            args.query = None
            args.category = None
            args.top_k = 5
            args.use_analytics = False
        cmd_suggest(args)
    elif args.command == "explain":
        cmd_explain(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()