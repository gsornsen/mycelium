# Source: guides/coordination-best-practices.md
# Line: 233
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Confidence-aware selection
agents = discover_agents("machine learning model deployment", limit=10)

# High-confidence agent for critical task
if agents["agents"][0]["confidence"] > 0.9:
    primary_agent = agents["agents"][0]
else:
    # Get human approval if no high-confidence match
    primary_agent = await get_human_selection(agents["agents"])

# Multiple agents for collaborative task
collaborators = [
    agent for agent in agents["agents"]
    if agent["confidence"] > 0.7
]

# ❌ BAD: Ignoring confidence scores
agents = discover_agents("some task")
chosen = agents["agents"][0]  # Blindly use first result