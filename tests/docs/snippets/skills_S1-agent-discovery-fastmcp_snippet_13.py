# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 852
# Valid syntax: True
# Has imports: True
# Has assignments: True

async def batch_discover(
    queries: List[str],
    limit: int = 5
) -> List[DiscoverAgentsResponse]:
    """Batch process multiple discovery queries."""
    import asyncio

    requests = [
        DiscoverAgentsRequest(query=q, limit=limit)
        for q in queries
    ]

    # Process in parallel
    responses = await asyncio.gather(*[
        discover_agents(req) for req in requests
    ])

    return responses

# Usage
queries = ["Python dev", "database optimization", "security audit"]
results = await batch_discover(queries)
