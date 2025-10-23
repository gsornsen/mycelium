# Source: api/registry-api.md
# Line: 139
# Valid syntax: True
# Has imports: False
# Has assignments: True

agent_uuid = await registry.create_agent(
    agent_id="01-core-backend-developer",
    agent_type="backend-developer",
    name="Backend Developer",
    display_name="Backend Developer",
    category="Core Development",
    description="Senior backend engineer for scalable API development",
    file_path="plugins/mycelium-core/agents/01-core-backend-developer.md",
    capabilities=["api-development", "database-design"],
    tools=["Bash", "Docker", "PostgreSQL"],
    keywords=["backend", "api", "database"],
    estimated_tokens=1200,
    metadata={"version": "1.0"}
)
