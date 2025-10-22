"""MCP (Model Context Protocol) tools for Mycelium.

This package provides MCP tool wrappers that expose Mycelium's
functionality to Claude Code through the MCP protocol.
"""

from .tools.discovery_tools import (
    MCP_TOOLS,
    DiscoveryAPIError,
    DiscoveryTimeoutError,
    DiscoveryToolError,
    check_discovery_health,
    discover_agents,
    dispatch_tool,
    get_agent_details,
)

__all__ = [
    "discover_agents",
    "get_agent_details",
    "check_discovery_health",
    "dispatch_tool",
    "MCP_TOOLS",
    "DiscoveryToolError",
    "DiscoveryAPIError",
    "DiscoveryTimeoutError",
]
