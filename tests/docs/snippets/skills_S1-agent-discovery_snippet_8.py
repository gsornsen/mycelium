# Source: skills/S1-agent-discovery.md
# Line: 276
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Discover agents for workflow steps
step1_agents = await discover_agents("data validation")
step2_agents = await discover_agents("database migration")
step3_agents = await discover_agents("API endpoint creation")

# Coordinate workflow (S2 skill)
await coordinate_workflow(
    steps=[
        {"agent": step1_agents["agents"][0]["id"], "task": "Validate data"},
        {"agent": step2_agents["agents"][0]["id"], "task": "Migrate schema"},
        {"agent": step3_agents["agents"][0]["id"], "task": "Create endpoints"},
    ]
)