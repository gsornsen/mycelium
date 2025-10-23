# Source: api/registry-api.md
# Line: 729
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Increase pool size or timeout
pool = await asyncpg.create_pool(
    connection_string,
    max_size=20,
    command_timeout=120
)
