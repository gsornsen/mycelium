"""MCP (Model Context Protocol) tools for Mycelium.

This package provides MCP tool wrappers that expose Mycelium's
functionality to Claude Code through the MCP protocol.
"""

from .tools.discovery_tools import (
    DiscoveryAPIError,
    DiscoveryTimeoutError,
    DiscoveryToolError,
    check_discovery_health,
    close_http_client,
    discover_agents,
    get_agent_details,
    mcp,
)

__all__ = [
    "discover_agents",
    "get_agent_details",
    "check_discovery_health",
    "close_http_client",
    "mcp",
    "DiscoveryToolError",
    "DiscoveryAPIError",
    "DiscoveryTimeoutError",
]
