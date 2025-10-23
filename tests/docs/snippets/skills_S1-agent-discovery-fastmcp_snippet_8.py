# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 658
# Valid syntax: True
# Has imports: False
# Has assignments: True

async def find_security_agents(task: str) -> List[AgentMatch]:
    """Find security-focused agents."""
    request = DiscoverAgentsRequest(
        query=task,
        limit=5,
        threshold=0.6,
        category_filter=AgentCategory.SECURITY
    )

    response = await discover_agents(request)
    return response.agents

# Usage
security_experts = await find_security_agents("authentication audit")