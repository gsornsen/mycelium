#!/usr/bin/env python3
"""Populate the agent registry from index.json.

This script loads agents from the index.json file and populates
the PostgreSQL registry with the metadata.
"""

import asyncio
import sys
from pathlib import Path

from registry import AgentRegistry, load_agents_from_index


async def main() -> int:
    """Main entry point."""
    # Default paths
    project_root = Path(__file__).parent.parent.parent.parent
    index_path = project_root / "plugins/mycelium-core/agents/index.json"

    # Allow custom index path from command line
    if len(sys.argv) > 1:
        index_path = Path(sys.argv[1])

    if not index_path.exists():
        print(f"Error: Index file not found: {index_path}", file=sys.stderr)
        return 1

    print(f"Loading agents from: {index_path}")

    try:
        async with AgentRegistry() as registry:
            # Perform health check
            print("Performing health check...")
            health = await registry.health_check()

            if health["status"] != "healthy":
                print(f"Error: Registry is unhealthy: {health}", file=sys.stderr)
                return 1

            print(f"  Status: {health['status']}")
            print(f"  pgvector installed: {health['pgvector_installed']}")
            print(f"  Current agent count: {health['agent_count']}")
            print(f"  Database size: {health['database_size']}")

            # Load agents
            print(f"\nLoading agents from index.json...")
            count = await load_agents_from_index(index_path, registry)

            print(f"\nSuccessfully loaded {count} agents")

            # Show summary by category
            print("\nAgents by category:")
            categories = await registry.get_categories()
            for category in sorted(categories):
                cat_count = await registry.get_agent_count(category=category)
                print(f"  {category}: {cat_count}")

            # Final stats
            total = await registry.get_agent_count()
            print(f"\nTotal agents in registry: {total}")

            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
