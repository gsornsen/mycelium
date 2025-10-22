"""MCP tool wrapper for agent discovery functionality.

This module provides MCP tools that expose the agent discovery API to Claude Code,
enabling natural language agent discovery and metadata retrieval through MCP.
"""

import asyncio
import json
import os
from typing import Any

import httpx

# Configuration
API_BASE_URL = os.getenv("DISCOVERY_API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30.0  # seconds
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


async def discover_agents(
    query: str,
    limit: int = 5,
    threshold: float = 0.6,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Discover agents using natural language query.

    This MCP tool enables Claude Code to discover relevant agents based on
    natural language task descriptions. It queries the Discovery API and
    returns ranked agent recommendations with confidence scores.

    Args:
        query: Natural language description of desired capabilities or task
        limit: Maximum number of agents to return (1-20)
        threshold: Minimum confidence threshold (0.0-1.0)
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Dictionary containing:
            - query: The original query
            - agents: List of matching agents with metadata
            - total_count: Number of matches found
            - processing_time_ms: API processing time
            - success: Boolean indicating success

    Raises:
        DiscoveryAPIError: If the API returns an error
        DiscoveryTimeoutError: If the request times out
        DiscoveryToolError: For other errors

    Example:
        >>> result = await discover_agents(
        ...     "I need help with Python backend development",
        ...     limit=3
        ... )
        >>> for agent in result["agents"]:
        ...     print(f"{agent['name']}: {agent['confidence']}")
    """
    # Validate inputs
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if not 1 <= limit <= 20:
        raise ValueError("Limit must be between 1 and 20")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0.0 and 1.0")

    request_timeout = timeout or DEFAULT_TIMEOUT

    # Prepare request
    url = f"{API_BASE_URL}/api/v1/agents/discover"
    payload = {
        "query": query.strip(),
        "limit": limit,
        "threshold": threshold,
    }

    # Execute request with retries
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(url, json=payload)

                # Check for API errors
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
                if response.status_code == 404:
                    raise DiscoveryAPIError("Discovery API endpoint not found")
                if response.status_code != 200:
                    raise DiscoveryAPIError(
                        f"Unexpected status code: {response.status_code}"
                    )

                # Parse successful response
                data = response.json()

                # Format response for MCP
                agents = []
                for match in data.get("matches", []):
                    agent = match.get("agent", {})
                    agents.append(
                        {
                            "id": agent.get("agent_id"),
                            "type": agent.get("agent_type"),
                            "name": agent.get("name"),
                            "display_name": agent.get("display_name"),
                            "category": agent.get("category"),
                            "description": agent.get("description"),
                            "capabilities": agent.get("capabilities", []),
                            "tools": agent.get("tools", []),
                            "keywords": agent.get("keywords", []),
                            "confidence": match.get("confidence", 0.0),
                            "match_reason": match.get("match_reason", ""),
                            "estimated_tokens": agent.get("estimated_tokens"),
                            "avg_response_time_ms": agent.get("avg_response_time_ms"),
                        }
                    )

                return {
                    "success": True,
                    "query": data.get("query", query),
                    "agents": agents,
                    "total_count": data.get("total_count", len(agents)),
                    "processing_time_ms": data.get("processing_time_ms", 0),
                }

        except httpx.TimeoutException:
            last_error = DiscoveryTimeoutError(
                f"Request timed out after {request_timeout}s "
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
        except httpx.HTTPError as e:
            last_error = DiscoveryAPIError(
                f"HTTP error: {str(e)} (attempt {attempt + 1}/{MAX_RETRIES + 1})"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except json.JSONDecodeError as e:
            last_error = DiscoveryAPIError(f"Invalid JSON response: {str(e)}")
            break  # Don't retry JSON errors
        except DiscoveryAPIError:
            raise  # Don't retry known API errors
        except Exception as e:
            last_error = DiscoveryToolError(f"Unexpected error: {str(e)}")
            break

    # All retries failed
    if last_error:
        raise last_error
    raise DiscoveryToolError("Unknown error occurred")


async def get_agent_details(
    agent_id: str,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Get detailed information about a specific agent.

    This MCP tool retrieves comprehensive metadata for a specific agent by ID.
    Useful for getting complete information about an agent after discovery.

    Args:
        agent_id: Agent ID (e.g., 'backend-developer') or agent type
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Dictionary containing:
            - agent: Complete agent metadata
            - metadata: Additional metadata (dependencies, examples, etc.)
            - success: Boolean indicating success

    Raises:
        DiscoveryAPIError: If the API returns an error or agent not found
        DiscoveryTimeoutError: If the request times out
        DiscoveryToolError: For other errors

    Example:
        >>> result = await get_agent_details("backend-developer")
        >>> print(f"Agent: {result['agent']['display_name']}")
        >>> print(f"Capabilities: {result['agent']['capabilities']}")
    """
    # Validate input
    if not agent_id or not agent_id.strip():
        raise ValueError("Agent ID cannot be empty")

    request_timeout = timeout or DEFAULT_TIMEOUT

    # Prepare request
    url = f"{API_BASE_URL}/api/v1/agents/{agent_id.strip()}"

    # Execute request with retries
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.get(url)

                # Check for API errors
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
                if response.status_code != 200:
                    raise DiscoveryAPIError(
                        f"Unexpected status code: {response.status_code}"
                    )

                # Parse successful response
                data = response.json()
                agent = data.get("agent", {})

                return {
                    "success": True,
                    "agent": {
                        "id": agent.get("agent_id"),
                        "type": agent.get("agent_type"),
                        "name": agent.get("name"),
                        "display_name": agent.get("display_name"),
                        "category": agent.get("category"),
                        "description": agent.get("description"),
                        "capabilities": agent.get("capabilities", []),
                        "tools": agent.get("tools", []),
                        "keywords": agent.get("keywords", []),
                        "file_path": agent.get("file_path"),
                        "estimated_tokens": agent.get("estimated_tokens"),
                        "avg_response_time_ms": agent.get("avg_response_time_ms"),
                        "success_rate": agent.get("success_rate"),
                        "usage_count": agent.get("usage_count", 0),
                        "created_at": agent.get("created_at"),
                        "updated_at": agent.get("updated_at"),
                        "last_used_at": agent.get("last_used_at"),
                    },
                    "metadata": data.get("metadata", {}),
                }

        except httpx.TimeoutException:
            last_error = DiscoveryTimeoutError(
                f"Request timed out after {request_timeout}s (attempt {attempt + 1}/{MAX_RETRIES + 1})"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except httpx.HTTPError as e:
            last_error = DiscoveryAPIError(
                f"HTTP error: {str(e)} (attempt {attempt + 1}/{MAX_RETRIES + 1})"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
        except json.JSONDecodeError as e:
            last_error = DiscoveryAPIError(f"Invalid JSON response: {str(e)}")
            break
        except DiscoveryAPIError:
            raise  # Don't retry known API errors
        except Exception as e:
            last_error = DiscoveryToolError(f"Unexpected error: {str(e)}")
            break

    # All retries failed
    if last_error:
        raise last_error
    raise DiscoveryToolError("Unknown error occurred")


async def check_discovery_health(
    timeout: float | None = None,
) -> dict[str, Any]:
    """Check the health status of the Discovery API.

    This utility tool checks if the Discovery API is operational and
    returns health metrics.

    Args:
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        Dictionary containing:
            - status: Health status ("healthy" or "unhealthy")
            - agent_count: Number of agents in registry
            - database_size: Database size in bytes
            - success: Boolean indicating success

    Raises:
        DiscoveryAPIError: If the API is unreachable
        DiscoveryTimeoutError: If the request times out
    """
    request_timeout = timeout or DEFAULT_TIMEOUT
    url = f"{API_BASE_URL}/api/v1/health"

    try:
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()
            return {
                "success": True,
                "status": data.get("status", "unknown"),
                "agent_count": data.get("agent_count", 0),
                "database_size": data.get("database_size", 0),
                "pgvector_installed": data.get("pgvector_installed", False),
                "timestamp": data.get("timestamp"),
            }

    except httpx.TimeoutException:
        raise DiscoveryTimeoutError(f"Health check timed out after {request_timeout}s")
    except httpx.HTTPError as e:
        raise DiscoveryAPIError(f"Health check failed: {str(e)}")
    except Exception as e:
        raise DiscoveryToolError(f"Unexpected error during health check: {str(e)}")


# MCP tool definitions for registration
MCP_TOOLS = [
    {
        "name": "discover_agents",
        "description": (
            "Discover agents using natural language query. "
            "Returns ranked list of agents with confidence scores. "
            "Use this to find the right agent for a specific task or capability."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language description of desired capabilities "
                        "(e.g., 'Python backend development', 'database optimization')"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of agents to return (1-20)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
                },
                "threshold": {
                    "type": "number",
                    "description": "Minimum confidence threshold (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.6,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_agent_details",
        "description": (
            "Get detailed information about a specific agent by ID. "
            "Returns complete metadata including capabilities, tools, "
            "performance metrics, and usage statistics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": (
                        "Agent ID (e.g., 'backend-developer', 'python-pro') "
                        "or agent type"
                    ),
                },
            },
            "required": ["agent_id"],
        },
    },
]


# Tool dispatcher for MCP server
async def dispatch_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch MCP tool calls to appropriate handlers.

    This function is called by the MCP server to execute tool requests.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as dictionary

    Returns:
        Tool execution result

    Raises:
        ValueError: If tool name is unknown
        DiscoveryToolError: If tool execution fails
    """
    if tool_name == "discover_agents":
        return await discover_agents(
            query=arguments["query"],
            limit=arguments.get("limit", 5),
            threshold=arguments.get("threshold", 0.6),
        )
    if tool_name == "get_agent_details":
        return await get_agent_details(agent_id=arguments["agent_id"])
    raise ValueError(f"Unknown tool: {tool_name}")
