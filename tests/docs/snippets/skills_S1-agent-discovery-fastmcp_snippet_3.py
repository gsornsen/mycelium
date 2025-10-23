# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 254
# Valid syntax: True
# Has imports: True
# Has assignments: True

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Mycelium Agent Discovery")


@mcp.tool()
async def discover_agents(
    request: DiscoverAgentsRequest
) -> DiscoverAgentsResponse:
    """
    Discover agents using natural language query.

    This tool enables Claude Code to find appropriate agents based on
    task descriptions, capabilities, or domain expertise.

    Args:
        request: Discovery request with query and filters

    Returns:
        Matching agents with confidence scores

    Example:
        >>> request = DiscoverAgentsRequest(
        ...     query="Python backend development",
        ...     limit=5,
        ...     threshold=0.7
        ... )
        >>> response = await discover_agents(request)
        >>> print(response.agents[0].name)
        "Backend Developer"
    """
    import time

    from mycelium_core.agent_discovery import AgentDiscoveryService

    start_time = time.perf_counter()

    # Initialize discovery service
    service = AgentDiscoveryService()

    # Execute search
    matches = await service.search(
        query=request.query,
        limit=request.limit,
        threshold=request.threshold,
        category_filter=request.category_filter.value if request.category_filter else None
    )

    # Convert to response model
    agents = [
        AgentMatch(
            id=match["id"],
            type=match["type"],
            name=match["name"],
            display_name=match["display_name"],
            category=match["category"],
            description=match["description"],
            capabilities=match.get("capabilities", []),
            tools=match.get("tools", []),
            keywords=match.get("keywords", []),
            confidence=match["confidence"],
            match_reason=match["match_reason"],
            estimated_tokens=match.get("estimated_tokens", 0),
            avg_response_time_ms=match.get("avg_response_time_ms", 0.0)
        )
        for match in matches
    ]

    processing_time_ms = (time.perf_counter() - start_time) * 1000

    return DiscoverAgentsResponse(
        success=True,
        query=request.query,
        agents=agents,
        total_count=len(agents),
        processing_time_ms=processing_time_ms
    )


@mcp.tool()
async def get_agent_details(
    request: GetAgentDetailsRequest
) -> GetAgentDetailsResponse:
    """
    Get detailed information about a specific agent.

    This tool retrieves comprehensive metadata about an agent including
    capabilities, performance metrics, and usage statistics.

    Args:
        request: Request with agent_id

    Returns:
        Detailed agent information

    Example:
        >>> request = GetAgentDetailsRequest(agent_id="backend-developer")
        >>> response = await get_agent_details(request)
        >>> print(response.agent.description)
        "Expert in full-stack backend development..."
    """
    from mycelium_core.agent_discovery import AgentDiscoveryService

    service = AgentDiscoveryService()

    # Fetch agent details
    details = await service.get_details(request.agent_id)

    if not details:
        raise ValueError(f"Agent not found: {request.agent_id}")

    # Convert to response model
    agent = AgentDetails(
        id=details["id"],
        type=details["type"],
        name=details["name"],
        display_name=details["display_name"],
        category=details["category"],
        description=details["description"],
        capabilities=details.get("capabilities", []),
        tools=details.get("tools", []),
        keywords=details.get("keywords", []),
        file_path=details["file_path"],
        estimated_tokens=details.get("estimated_tokens", 0),
        avg_response_time_ms=details.get("avg_response_time_ms", 0.0),
        success_rate=details.get("success_rate", 0.95),
        usage_count=details.get("usage_count", 0),
        created_at=details.get("created_at", datetime.now()),
        updated_at=details.get("updated_at", datetime.now()),
        last_used_at=details.get("last_used_at")
    )

    metadata = AgentDetailsMetadata(
        dependencies=details.get("dependencies", []),
        examples=details.get("examples", []),
        tags=details.get("tags", [])
    )

    return GetAgentDetailsResponse(
        success=True,
        agent=agent,
        metadata=metadata
    )


# Error handling middleware
@mcp.error_handler()
async def handle_discovery_error(error: Exception) -> Dict[str, Any]:
    """Handle discovery errors gracefully."""
    import logging

    logger = logging.getLogger("mycelium.discovery")
    logger.error(f"Discovery error: {error}", exc_info=True)

    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__
    }
