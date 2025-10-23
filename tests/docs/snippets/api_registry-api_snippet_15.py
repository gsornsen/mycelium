# Source: api/registry-api.md
# Line: 309
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get all agents
all_agents = await registry.list_agents()

# Get agents in specific category
core_agents = await registry.list_agents(category="Core Development")

# Get paginated results
page1 = await registry.list_agents(limit=20, offset=0)
page2 = await registry.list_agents(limit=20, offset=20)