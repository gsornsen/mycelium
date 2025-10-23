# Source: api/registry-api.md
# Line: 563
# Valid syntax: True
# Has imports: False
# Has assignments: False

try:
    await registry.create_agent(...)
except AgentAlreadyExistsError as e:
    print(f"Agent already exists: {e}")
