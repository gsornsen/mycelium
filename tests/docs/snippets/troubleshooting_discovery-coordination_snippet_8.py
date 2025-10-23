# Source: troubleshooting/discovery-coordination.md
# Line: 156
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Check match reasons
for agent in result["agents"]:
    print(f"{agent['name']}: {agent['match_reason']}")

# Example output:
# frontend-developer: Matches keyword 'development'
# data-scientist: Matches keyword 'Python'
# devops-engineer: Matches keyword 'backend'

# The matching is too broad!