# Source: api/registry-api.md
# Line: 176
# Valid syntax: True
# Has imports: False
# Has assignments: True

agent = await registry.get_agent_by_id("01-core-backend-developer")
print(f"Agent: {agent['name']}")
print(f"Description: {agent['description']}")
print(f"Capabilities: {agent['capabilities']}")