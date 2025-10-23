# Source: skills/S1-agent-discovery.md
# Line: 157
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get details by agent ID
result = await get_agent_details("backend-developer")

# Get details by agent type (file prefix)
result = await get_agent_details("01-core-backend-developer")
