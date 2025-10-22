"""FastMCP-based agent discovery tools.

This module provides MCP tools for agent discovery using FastMCP 2.0 SDK
with clean separation of concerns: Pydantic models for validation,
FastMCP for protocol handling, and focused business logic.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import FastMCP

from ..models import (
    AgentDetails,
    AgentMatch,
    DiscoverAgentsRequest,
    DiscoverAgentsResponse,
    GetAgentDetailsRequest,
    GetAgentDetailsResponse,
    HealthCheckResponse,
)

# Configuration
API_BASE_URL = os.getenv("DISCOVERY_API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 2


class DiscoveryToolError(Exception):
    """Base exception for discovery tool errors."""

    pass


class DiscoveryAPIError(DiscoveryToolError):
    """Raised when the Discovery API returns an error."""

    pass


class DiscoveryTimeoutError(DiscoveryToolError):
    """Raised when a discovery operation times out."""

    pass


# HTTP client management
_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def get_http_client():
    """Get or create the HTTP client with retry logic."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=DEFAULT_TIMEOUT,
        )
    try:
        yield _http_client
    except Exception:
        # Close and reset client on error
        if _http_client is not None:
            await _http_client.aclose()
            _http_client = None
        raise


async def close_http_client():
    """Close the HTTP client."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


# Core business logic functions
async def discover_agents(
    query: str,
    limit: int = 5,
    threshold: float = 0.6,
) -> DiscoverAgentsResponse:
    """Discover agents using natural language query.

    This tool enables Claude Code to discover relevant agents based on
    natural language task descriptions. It queries the Discovery API and
    returns ranked agent recommendations with confidence scores.

    Args:
        query: Natural language description of desired capabilities
        limit: Maximum number of agents to return (1-20)
        threshold: Minimum confidence threshold (0.0-1.0)

    Returns:
        Discovery response with matched agents and metadata

    Raises:
        DiscoveryAPIError: If the API returns an error
        DiscoveryTimeoutError: If the request times out
        DiscoveryToolError: For other errors
    """
    # Validate with Pydantic
    request = DiscoverAgentsRequest(query=query, limit=limit, threshold=threshold)

    # Execute with retry logic
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with get_http_client() as client:
                response = await client.post(
                    "/api/v1/agents/discover",
                    json=request.model_dump(),
                )

                # Handle error responses
                if response.status_code == 400:
                    error_data = response.json()
                    raise DiscoveryAPIError(
                        f"Invalid request: {error_data.get('message', 'Unknown error')}"
                    )
                if response.status_code == 404:
                    raise DiscoveryAPIError("Discovery API endpoint not found")
                if response.status_code == 500:
                    error_data = response.json()
                    raise DiscoveryAPIError(
                        f"Server error: {error_data.get('message', 'Unknown error')}"
                    )

                response.raise_for_status()

                # Parse and transform response
                data = response.json()
                agents = [
                    AgentMatch(
                        agent_id=match["agent"]["agent_id"],
                        agent_type=match["agent"]["agent_type"],
                        name=match["agent"]["name"],
                        display_name=match["agent"]["display_name"],
                        category=match["agent"]["category"],
                        description=match["agent"]["description"],
                        capabilities=match["agent"].get("capabilities", []),
                        tools=match["agent"].get("tools", []),
                        keywords=match["agent"].get("keywords", []),
                        confidence=match["confidence"],
                        match_reason=match.get("match_reason", ""),
                        estimated_tokens=match["agent"].get("estimated_tokens"),
                        avg_response_time_ms=match["agent"].get("avg_response_time_ms"),
                    )
                    for match in data.get("matches", [])
                ]

                return DiscoverAgentsResponse(
                    success=True,
                    query=data.get("query", query),
                    agents=agents,
                    total_count=data.get("total_count", len(agents)),
                    processing_time_ms=data.get("processing_time_ms", 0),
                )

        except httpx.TimeoutException:
            last_error = DiscoveryTimeoutError(
                f"Request timed out after {DEFAULT_TIMEOUT}s"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except httpx.HTTPError as e:
            last_error = DiscoveryAPIError(f"HTTP error: {str(e)}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except DiscoveryAPIError:
            raise  # Don't retry known API errors

    # All retries failed
    if last_error:
        raise last_error
    raise DiscoveryToolError("Unknown error occurred")


async def get_agent_details(agent_id: str) -> GetAgentDetailsResponse:
    """Get detailed information about a specific agent.

    This tool retrieves comprehensive metadata for a specific agent by ID.
    Useful for getting complete information about an agent after discovery.

    Args:
        agent_id: Agent ID (e.g., 'backend-developer') or agent type

    Returns:
        Agent details response with complete metadata

    Raises:
        DiscoveryAPIError: If the API returns an error or agent not found
        DiscoveryTimeoutError: If the request times out
        DiscoveryToolError: For other errors
    """
    # Validate with Pydantic
    request = GetAgentDetailsRequest(agent_id=agent_id)

    # Execute with retry logic
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with get_http_client() as client:
                response = await client.get(f"/api/v1/agents/{request.agent_id}")

                # Handle error responses
                if response.status_code == 404:
                    raise DiscoveryAPIError(
                        f"Agent '{agent_id}' not found. "
                        "Try using discover_agents to find available agents."
                    )
                if response.status_code == 400:
                    error_data = response.json()
                    raise DiscoveryAPIError(
                        f"Invalid request: {error_data.get('message', 'Unknown error')}"
                    )
                if response.status_code == 500:
                    error_data = response.json()
                    raise DiscoveryAPIError(
                        f"Server error: {error_data.get('message', 'Unknown error')}"
                    )

                response.raise_for_status()

                # Parse and transform response
                data = response.json()
                agent = data["agent"]

                return GetAgentDetailsResponse(
                    success=True,
                    agent=AgentDetails(
                        agent_id=agent["agent_id"],
                        agent_type=agent["agent_type"],
                        name=agent["name"],
                        display_name=agent["display_name"],
                        category=agent["category"],
                        description=agent["description"],
                        capabilities=agent.get("capabilities", []),
                        tools=agent.get("tools", []),
                        keywords=agent.get("keywords", []),
                        file_path=agent.get("file_path"),
                        estimated_tokens=agent.get("estimated_tokens"),
                        avg_response_time_ms=agent.get("avg_response_time_ms"),
                        success_rate=agent.get("success_rate"),
                        usage_count=agent.get("usage_count", 0),
                        created_at=agent.get("created_at"),
                        updated_at=agent.get("updated_at"),
                        last_used_at=agent.get("last_used_at"),
                    ),
                    metadata=data.get("metadata", {}),
                )

        except httpx.TimeoutException:
            last_error = DiscoveryTimeoutError(
                f"Request timed out after {DEFAULT_TIMEOUT}s"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except httpx.HTTPError as e:
            last_error = DiscoveryAPIError(f"HTTP error: {str(e)}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except DiscoveryAPIError:
            raise  # Don't retry known API errors

    # All retries failed
    if last_error:
        raise last_error
    raise DiscoveryToolError("Unknown error occurred")


async def check_discovery_health() -> HealthCheckResponse:
    """Check the health status of the Discovery API.

    This utility tool checks if the Discovery API is operational and
    returns health metrics.

    Returns:
        Health check response with status and metrics

    Raises:
        DiscoveryAPIError: If the API is unreachable
        DiscoveryTimeoutError: If the request times out
    """
    try:
        async with get_http_client() as client:
            response = await client.get("/api/v1/health")

            if response.status_code != 200:
                return HealthCheckResponse(
                    success=False,
                    status="unhealthy",
                    error=f"Status code: {response.status_code}",
                )

            data = response.json()
            return HealthCheckResponse(
                success=True,
                status=data.get("status", "unknown"),
                agent_count=data.get("agent_count", 0),
                database_size=data.get("database_size", 0),
                pgvector_installed=data.get("pgvector_installed", False),
                timestamp=data.get("timestamp"),
            )

    except httpx.TimeoutException:
        raise DiscoveryTimeoutError(
            f"Health check timed out after {DEFAULT_TIMEOUT}s"
        ) from None
    except httpx.HTTPError as e:
        raise DiscoveryAPIError(f"Health check failed: {str(e)}") from e
    except Exception as e:
        raise DiscoveryToolError(
            f"Unexpected error during health check: {str(e)}"
        ) from e


# FastMCP integration - register functions as MCP tools
mcp = FastMCP("Agent Discovery")


@mcp.tool()
async def mcp_discover_agents(
    query: str,
    limit: int = 5,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """Discover agents using natural language query (MCP wrapper)."""
    result = await discover_agents(query, limit, threshold)
    return result.model_dump()


@mcp.tool()
async def mcp_get_agent_details(agent_id: str) -> dict[str, Any]:
    """Get detailed information about a specific agent (MCP wrapper)."""
    result = await get_agent_details(agent_id)
    return result.model_dump()


@mcp.tool()
async def mcp_check_discovery_health() -> dict[str, Any]:
    """Check the health status of the Discovery API (MCP wrapper)."""
    result = await check_discovery_health()
    return result.model_dump()
