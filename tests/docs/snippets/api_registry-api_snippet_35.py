# Source: api/registry-api.md
# Line: 697
# Valid syntax: True
# Has imports: False
# Has assignments: True

# For high-concurrency workloads
pool = await asyncpg.create_pool(
    connection_string,
    min_size=10,
    max_size=50,
    command_timeout=30,
)
registry = AgentRegistry(pool=pool)