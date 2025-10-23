# Source: guides/discovery-coordination-quickstart.md
# Line: 313
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Generic search
agents = discover_agents("your task description")

# Category-specific search
agents = discover_agents(
    "database optimization",
    category_filter="infrastructure"
)

# High-confidence matches only
agents = discover_agents(
    "security audit",
    threshold=0.8,
    limit=3
)