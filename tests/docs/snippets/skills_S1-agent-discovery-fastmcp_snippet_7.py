# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 632
# Valid syntax: True
# Has imports: True
# Has assignments: True


async def find_best_agent(task: str) -> Optional[AgentMatch]:
    """Find best agent for task with type safety."""
    request = DiscoverAgentsRequest(
        query=task,
        limit=1,
        threshold=0.8
    )

    response: DiscoverAgentsResponse = await discover_agents(request)

    if response.agents:
        return response.agents[0]
    return None

# Usage
best_agent = await find_best_agent("database performance optimization")
if best_agent:
    print(f"Using: {best_agent.name}")
