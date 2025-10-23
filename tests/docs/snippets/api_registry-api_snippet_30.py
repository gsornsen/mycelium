# Source: api/registry-api.md
# Line: 551
# Valid syntax: True
# Has imports: False
# Has assignments: True

try:
    agent = await registry.get_agent_by_id("nonexistent")
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")