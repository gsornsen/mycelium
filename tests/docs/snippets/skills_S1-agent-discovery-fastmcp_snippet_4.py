# Source: skills/S1-agent-discovery-fastmcp.md
# Line: 423
# Valid syntax: True
# Has imports: True
# Has assignments: True

from typing import Any

from mycelium_core.matching import NLPMatcher
from mycelium_core.registry import AgentRegistry


class AgentDiscoveryService:
    """Agent discovery service with NLP matching."""

    def __init__(self):
        """Initialize discovery service."""
        self.registry = AgentRegistry()
        self.matcher = NLPMatcher()

    async def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.6,
        category_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for agents matching query.

        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum confidence
            category_filter: Optional category

        Returns:
            List of matching agents with scores
        """
        # Get all agents from registry
        agents = await self.registry.get_all_agents()

        # Filter by category if specified
        if category_filter:
            agents = [a for a in agents if a.get("category") == category_filter]

        # Generate embeddings and compute similarity
        matches = await self.matcher.match(
            query=query,
            candidates=agents,
            threshold=threshold
        )

        # Sort by confidence and limit results
        matches.sort(key=lambda m: m["confidence"], reverse=True)
        matches = matches[:limit]

        return matches

    async def get_details(self, agent_id: str) -> dict[str, Any] | None:
        """
        Get detailed agent information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent details or None if not found
        """
        return await self.registry.get_agent(agent_id)
