# Source: api/registry-api.md
# Line: 66
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.registry import AgentRegistry

# Initialize with connection string
registry = AgentRegistry(
    connection_string="postgresql://localhost:5432/mycelium_registry"
)
await registry.initialize()

# Initialize with existing pool
import asyncpg
pool = await asyncpg.create_pool(connection_string)
registry = AgentRegistry(pool=pool)
await registry.initialize()

# Use as context manager (recommended)
async with AgentRegistry(connection_string) as registry:
    # Use registry
    pass