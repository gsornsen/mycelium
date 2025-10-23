# Source: api/registry-api.md
# Line: 576
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio

from plugins.mycelium_core.registry import AgentRegistry, load_agents_from_index


async def main():
    # Initialize registry
    async with AgentRegistry() as registry:
        # Load agents from index.json
        count = await load_agents_from_index(
            "plugins/mycelium-core/agents/index.json",
            registry
        )
        print(f"Loaded {count} agents")

        # Get agent count by category
        categories = await registry.get_categories()
        for category in categories:
            count = await registry.get_agent_count(category=category)
            print(f"{category}: {count} agents")

        # Search for agents
        results = await registry.search_agents("backend development")
        print(f"\nFound {len(results)} agents matching 'backend development':")
        for agent in results[:5]:
            print(f"  - {agent['name']}: {agent['description']}")

        # Get specific agent
        agent = await registry.get_agent_by_type("backend-developer")
        print("\nAgent details:")
        print(f"  Name: {agent['display_name']}")
        print(f"  Category: {agent['category']}")
        print(f"  Tools: {', '.join(agent['tools'])}")
        print(f"  Usage count: {agent['usage_count']}")

asyncio.run(main())
