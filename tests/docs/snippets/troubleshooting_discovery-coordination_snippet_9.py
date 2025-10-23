# Source: troubleshooting/discovery-coordination.md
# Line: 171
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Solution 1: More specific query
result = discover_agents(
    query="Python backend API development REST FastAPI",
    threshold=0.7  # Higher threshold filters out weak matches
)

# Solution 2: Category filtering
result = discover_agents(
    query="Python development",
    category_filter="backend"  # Limit to backend category
)

# Solution 3: Multi-stage discovery
# Stage 1: Find primary agent
primary = discover_agents("backend development", limit=1)

# Stage 2: Find complementary agents
details = get_agent_details(primary["agents"][0]["id"])
if "Python" in details["agent"]["capabilities"]:
    # This is right agent
    pass
else:
    # Try next agent
    pass
