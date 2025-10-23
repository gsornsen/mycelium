# Source: api/registry-api.md
# Line: 459
# Valid syntax: True
# Has imports: False
# Has assignments: True

agents_to_insert = [
    {
        "agent_id": "agent-1",
        "agent_type": "type-1",
        "name": "Agent 1",
        "display_name": "Agent 1",
        "category": "Test",
        "description": "Test agent 1",
        "file_path": "/path/to/agent1.md",
    },
    # ... more agents
]

count = await registry.bulk_insert_agents(agents_to_insert)
print(f"Inserted {count} agents")
