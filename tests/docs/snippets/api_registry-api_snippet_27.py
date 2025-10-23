# Source: api/registry-api.md
# Line: 493
# Valid syntax: True
# Has imports: False
# Has assignments: True

health = await registry.health_check()
print(f"Status: {health['status']}")
print(f"pgvector installed: {health['pgvector_installed']}")
print(f"Agent count: {health['agent_count']}")
print(f"Database size: {health['database_size']}")