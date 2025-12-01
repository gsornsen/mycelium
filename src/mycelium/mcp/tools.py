"""MCP tool implementations for agent discovery.

Provides three core tools:
- discover_agents: Natural language search for agents
- get_agent_details: Get full metadata for a specific agent
- list_categories: List all available agent categories
"""

from pathlib import Path
from typing import Any

from mycelium.config.agent_loader import AgentConfig, AgentLoader


class AgentDiscoveryTools:
    """Agent discovery tools for MCP server."""

    def __init__(self, plugin_dir: Path | None = None) -> None:
        """Initialize discovery tools.

        Args:
            plugin_dir: Directory containing agent .md files.
                       Defaults to plugins/mycelium-core/agents/
        """
        if plugin_dir is None:
            # Default to mycelium-core plugin agents directory
            plugin_dir = Path(__file__).parent.parent.parent.parent / "plugins" / "mycelium-core" / "agents"

        self.loader = AgentLoader(plugin_dir)

    def discover_agents(self, query: str) -> list[dict[str, Any]]:
        """Search for agents using natural language query.

        Args:
            query: Natural language search query (e.g., "Python backend development")

        Returns:
            List of matching agents with name, category, and description
        """
        # Load all agents
        all_agents = self.loader.list_agents()

        # Simple keyword-based matching
        # TODO: In future, use sentence transformers for semantic search
        query_lower = query.lower()
        matches: list[AgentConfig] = []

        for agent in all_agents:
            # Search in name, description, and tools
            searchable_text = " ".join([
                agent.name,
                agent.description,
                agent.category,
                " ".join(agent.tools or []),
            ]).lower()

            if query_lower in searchable_text:
                matches.append(agent)

        # Convert to response format
        return [
            {
                "name": agent.name,
                "category": agent.category,
                "description": agent.description,
            }
            for agent in matches
        ]

    def get_agent_details(self, name: str) -> dict[str, Any] | None:
        """Get full metadata for a specific agent.

        Args:
            name: Agent name (e.g., "backend-developer")

        Returns:
            Full agent info including tools, description, category, or None if not found
        """
        agent = self.loader.load_agent(name)

        if not agent:
            return None

        return {
            "name": agent.name,
            "category": agent.category,
            "description": agent.description,
            "tools": agent.tools or [],
            "command": agent.command,
        }

    def list_categories(self) -> list[dict[str, Any]]:
        """List all available agent categories with counts.

        Returns:
            List of category names with agent counts
        """
        all_agents = self.loader.list_agents()

        # Count agents per category
        category_counts: dict[str, int] = {}
        for agent in all_agents:
            category_counts[agent.category] = category_counts.get(agent.category, 0) + 1

        # Convert to response format
        return [
            {
                "category": category,
                "count": count,
            }
            for category, count in sorted(category_counts.items())
        ]
