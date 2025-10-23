# Source: skills/S1-agent-discovery.md
# Line: 413
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check API health
from plugins.mycelium_core.mcp.tools.discovery_tools import check_discovery_health

health = await check_discovery_health()
print(f"Status: {health['status']}")
print(f"Agents: {health['agent_count']}")

# Test with broad query
result = await discover_agents("development", limit=20, threshold=0.3)
print(f"Found {result['total_count']} agents")

# Verify specific agent exists
try:
    details = await get_agent_details("backend-developer")
    print(f"Agent found: {details['agent']['name']}")
except DiscoveryAPIError:
    print("Agent not in registry")
