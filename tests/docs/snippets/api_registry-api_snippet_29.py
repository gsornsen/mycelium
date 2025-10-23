# Source: api/registry-api.md
# Line: 527
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.registry import load_agents_from_index

async with AgentRegistry(connection_string) as registry:
    count = await load_agents_from_index(
        "plugins/mycelium-core/agents/index.json",
        registry
    )
    print(f"Loaded {count} agents")
