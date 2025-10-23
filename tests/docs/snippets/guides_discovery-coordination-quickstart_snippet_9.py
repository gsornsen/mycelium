# Source: guides/discovery-coordination-quickstart.md
# Line: 366
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Problem: Empty results
result = discover_agents("very specific niche task")
# result["agents"] == []

# Solution 1: Broaden query
result = discover_agents("general category task")

# Solution 2: Lower threshold
result = discover_agents("specific task", threshold=0.4)

# Solution 3: Check all categories
result = discover_agents("task", limit=20)