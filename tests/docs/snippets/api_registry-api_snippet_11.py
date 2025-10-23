# Source: api/registry-api.md
# Line: 253
# Valid syntax: True
# Has imports: False
# Has assignments: False

await registry.update_agent(
    "01-core-backend-developer",
    description="Updated description",
    capabilities=["api-development", "microservices", "database-design"],
    metadata={"version": "2.0", "updated": True}
)