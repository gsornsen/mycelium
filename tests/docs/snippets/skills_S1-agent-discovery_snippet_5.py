# Source: skills/S1-agent-discovery.md
# Line: 171
# Valid syntax: True
# Has imports: False
# Has assignments: True

# 1. Discover agents for the task
result = await discover_agents(
    query="optimize slow PostgreSQL queries",
    limit=3,
    threshold=0.7
)

# 2. Review top matches
for agent in result["agents"]:
    print(f"{agent['name']} (confidence: {agent['confidence']})")
    print(f"  Reason: {agent['match_reason']}")
    print(f"  Capabilities: {', '.join(agent['capabilities'])}")

# 3. Get detailed information about top choice
if result["agents"]:
    top_agent = result["agents"][0]
    details = await get_agent_details(top_agent["id"])
    # Use agent based on detailed capabilities
