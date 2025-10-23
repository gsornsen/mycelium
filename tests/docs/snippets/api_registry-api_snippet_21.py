# Source: api/registry-api.md
# Line: 407
# Valid syntax: True
# Has imports: False
# Has assignments: True

total = await registry.get_agent_count()
print(f"Total agents: {total}")

core_count = await registry.get_agent_count(category="Core Development")
print(f"Core agents: {core_count}")