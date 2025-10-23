# Source: api/registry-api.md
# Line: 227
# Valid syntax: True
# Has imports: True
# Has assignments: True

from uuid import UUID

agent = await registry.get_agent_by_uuid(
    UUID("550e8400-e29b-41d4-a716-446655440000")
)
