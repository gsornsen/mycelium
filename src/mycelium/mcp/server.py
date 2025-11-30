"""FastMCP server for Mycelium agent discovery.

Exposes three tools via MCP:
- discover_agents: Natural language search
- get_agent_details: Get full agent metadata
- list_categories: List agent categories

Uses stdio transport (standard for MCP).
"""

from typing import Any

from fastmcp import FastMCP

from mycelium.mcp.tools import AgentDiscoveryTools

# Create FastMCP server instance
mcp = FastMCP("mycelium")

# Initialize discovery tools
_tools = AgentDiscoveryTools()


@mcp.tool()
def discover_agents(query: str) -> list[dict[str, Any]]:
    """Search for agents using natural language query.

    Use this tool to find agents that match your requirements.
    For example:
    - "Python backend development"
    - "React frontend"
    - "database optimization"
    - "API design"

    Args:
        query: Natural language search query describing what you need

    Returns:
        List of matching agents with name, category, and description
    """
    return _tools.discover_agents(query)


@mcp.tool()
def get_agent_details(name: str) -> dict[str, Any] | None:
    """Get full metadata for a specific agent.

    Use this tool to get complete information about an agent,
    including available tools, command, and full description.

    Args:
        name: Agent name (e.g., "backend-developer", "python-pro")

    Returns:
        Full agent information or None if not found
    """
    result = _tools.get_agent_details(name)
    if result is None:
        return {"error": f"Agent '{name}' not found"}
    return result


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """List all available agent categories with counts.

    Use this tool to explore the types of agents available.
    Categories typically include:
    - core: Core development agents
    - language: Language-specific specialists
    - data: Data and AI specialists
    - developer: Developer tools and workflow
    - specialized: Domain-specific experts
    - business: Business and content specialists

    Returns:
        List of categories with agent counts
    """
    return _tools.list_categories()


def main() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
