# Source: skills/S1-agent-discovery.md
# Line: 86
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Basic discovery
result = await discover_agents("I need help with Python development")

# Specific requirements with higher confidence
result = await discover_agents(
    query="PostgreSQL performance tuning and query optimization",
    limit=3,
    threshold=0.8
)

# Broad search for multiple options
result = await discover_agents(
    query="frontend development",
    limit=10,
    threshold=0.5
)
