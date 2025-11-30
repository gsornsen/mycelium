"""MCP (Model Context Protocol) integration for Mycelium.

This module provides:
- MCP server for agent discovery (server.py)
- Agent integrity verification (checksums.py)
- Tool permission analysis (permissions.py)
"""

from mycelium.mcp.checksums import (
    generate_agent_checksum,
    generate_all_checksums,
    load_checksums,
    save_checksums,
    verify_agent_checksum,
    verify_all_checksums,
)
from mycelium.mcp.permissions import (
    ToolPermission,
    analyze_tool_permissions,
    generate_permissions_report,
    get_agent_permissions,
    get_agent_risk_level,
    get_high_risk_agents,
    parse_agent_tools,
)

# Lazy import to avoid import errors during testing
# Users should import directly from mycelium.mcp.server if needed
__all__ = [
    # Checksums
    "generate_agent_checksum",
    "generate_all_checksums",
    "load_checksums",
    "save_checksums",
    "verify_agent_checksum",
    "verify_all_checksums",
    # Permissions
    "ToolPermission",
    "parse_agent_tools",
    "analyze_tool_permissions",
    "get_agent_risk_level",
    "generate_permissions_report",
    "get_high_risk_agents",
    "get_agent_permissions",
]
