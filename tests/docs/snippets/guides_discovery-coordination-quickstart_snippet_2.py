# Source: guides/discovery-coordination-quickstart.md
# Line: 87
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.mcp.tools.discovery_tools import get_agent_details

# Get full details on top match
agent_id = result["agents"][0]["id"]
details = get_agent_details(agent_id)

print(f"Agent: {details['agent']['name']}")
print(f"Capabilities: {', '.join(details['agent']['capabilities'])}")
print(f"Tools: {', '.join(details['agent']['tools'])}")
print(f"Success Rate: {details['agent']['success_rate']*100}%")

# Example output:
# Agent: Performance Engineer
# Capabilities: Performance profiling, Load testing, Query optimization
# Tools: pytest-benchmark, locust, py-spy
# Success Rate: 95%