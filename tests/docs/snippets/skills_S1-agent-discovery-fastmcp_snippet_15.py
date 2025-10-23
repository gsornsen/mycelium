# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 935
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Before (Legacy)
from scripts.agent_discovery import AgentDiscovery

discovery = AgentDiscovery()
results = discovery.search("Python development")

# After (FastMCP)
from mycelium_core.mcp.tools.discovery_tools import (
    DiscoverAgentsRequest,
    discover_agents,
)

request = DiscoverAgentsRequest(query="Python development")
response = await discover_agents(request)
results = [agent.model_dump() for agent in response.agents]
