# Source: api/registry-api.md
# Line: 342
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Search for backend-related agents
results = await registry.search_agents("backend api development")

for agent in results:
    print(f"{agent['name']}: {agent['description']}")
