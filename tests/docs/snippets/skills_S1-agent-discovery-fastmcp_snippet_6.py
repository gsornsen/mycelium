# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 610
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_core.mcp.tools.discovery_tools import (
    DiscoverAgentsRequest,
    discover_agents,
)

# Create request
request = DiscoverAgentsRequest(
    query="Python backend API development",
    limit=5,
    threshold=0.7
)

# Execute discovery
response = await discover_agents(request)

# Process results
print(f"Found {response.total_count} agents in {response.processing_time_ms}ms")
for agent in response.agents:
    print(f"{agent.name} (confidence: {agent.confidence:.2f})")
    print(f"  Reason: {agent.match_reason}")
