"""FastMCP server for Mycelium agent discovery and execution.

Exposes tools via MCP:
- discover_agents: Natural language search
- get_agent_details: Get full agent metadata
- list_categories: List agent categories
- invoke_agent: Execute an agent on a task
- get_workflow_status: Check workflow execution status

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


@mcp.tool()
def invoke_agent(agent_name: str, task_description: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Invoke an agent to execute a task via MCP.

    This tool delegates work to specialist agents. For high-risk
    agents (those with Bash(*) or Write(*) permissions), the user
    will be prompted for consent via CLI.

    Security features:
    - User consent required for dangerous tools
    - Environment isolation (sensitive vars blocked)
    - Output sanitization (credentials redacted)
    - Checksum-based re-consent on agent changes

    Args:
        agent_name: Name of the agent to invoke (e.g., "python-pro")
        task_description: Description of the task to execute
        context: Optional context dict (files, project info, etc.)

    Returns:
        Dictionary with workflow_id, status, and details

    Examples:
        >>> invoke_agent("python-pro", "Implement user authentication")
        {
            "workflow_id": "wf_abc123",
            "status": "started",
            "agent_name": "python-pro",
            "message": "Agent started successfully"
        }
    """
    return _tools.invoke_agent(agent_name, task_description, context)


@mcp.tool()
def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get the status of a running agent workflow.

    Use this to check on agent execution progress and get results.

    Args:
        workflow_id: Workflow identifier from invoke_agent

    Returns:
        Dictionary with status, agent info, and results

    Examples:
        >>> get_workflow_status("wf_abc123")
        {
            "workflow_id": "wf_abc123",
            "status": "running",
            "agent_name": "python-pro",
            "started_at": "2025-11-30T12:00:00Z"
        }
    """
    return _tools.get_workflow_status(workflow_id)


def main() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
