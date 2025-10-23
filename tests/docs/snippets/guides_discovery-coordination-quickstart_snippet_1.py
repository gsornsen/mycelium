# Source: guides/discovery-coordination-quickstart.md
# Line: 59
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.mcp.tools.discovery_tools import discover_agents

# Natural language query
result = discover_agents(
    query="optimize slow API performance and reduce latency",
    limit=5
)

# View results
for agent in result["agents"]:
    print(f"{agent['name']} (confidence: {agent['confidence']})")
    print(f"  → {agent['reason']}")
    print()

# Example output:
# Performance Engineer (confidence: 0.94)
#   → Matches keywords: API, performance, latency
#
# API Designer (confidence: 0.89)
#   → Matches keywords: API, optimization
#
# Backend Developer (confidence: 0.82)
#   → Matches keywords: API