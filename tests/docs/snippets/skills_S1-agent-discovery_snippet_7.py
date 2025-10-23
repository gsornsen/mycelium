# Source: skills/S1-agent-discovery.md
# Line: 221
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Find specialists for different aspects
backend_agents = await discover_agents("backend API development")
frontend_agents = await discover_agents("React frontend development")
database_agents = await discover_agents("database design and optimization")

# Combine into workflow team
team = []
if backend_agents["agents"]:
    team.append(backend_agents["agents"][0])
if frontend_agents["agents"]:
    team.append(frontend_agents["agents"][0])
if database_agents["agents"]:
    team.append(database_agents["agents"][0])

# Get detailed info for each team member
for agent in team:
    details = await get_agent_details(agent["id"])
    # Plan workflow based on capabilities