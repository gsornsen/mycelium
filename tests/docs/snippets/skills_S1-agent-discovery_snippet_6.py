# Source: skills/S1-agent-discovery.md
# Line: 196
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Broad search to see available options
result = await discover_agents(
    query="web development",
    limit=10,
    threshold=0.5  # Lower threshold for exploration
)

# Review categories of agents found
categories = {}
for agent in result["agents"]:
    cat = agent["category"]
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(agent["name"])

# Examine specific agents of interest
for agent_id in interesting_agents:
    details = await get_agent_details(agent_id)