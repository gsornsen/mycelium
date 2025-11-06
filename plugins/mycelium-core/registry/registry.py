"""Agent Registry implementation with PostgreSQL and pgvector support.

This module provides a centralized registry for managing agent metadata,
capabilities, and semantic search using vector embeddings.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import asyncpg
from asyncpg import Pool


class AgentRegistryError(Exception):
    """Base exception for agent registry errors."""

    pass


class AgentNotFoundError(AgentRegistryError):
    """Raised when an agent is not found in the registry."""

    pass


class AgentAlreadyExistsError(AgentRegistryError):
    """Raised when attempting to create an agent that already exists."""

    pass


class AgentRegistry:
    """Centralized agent registry with PostgreSQL backend and pgvector support.

    This class provides CRUD operations for agent metadata and supports
    semantic search using vector embeddings for capability matching.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        pool: Pool | None = None,
    ):
        """Initialize the agent registry.

        Args:
            connection_string: PostgreSQL connection string. If not provided,
                             uses DATABASE_URL environment variable.
            pool: Existing connection pool. If provided, connection_string is ignored.
        """
        if pool is not None:
            self._pool: Pool | None = pool
            self._owns_pool = False
        else:
            self._connection_string = connection_string or os.getenv(
                "DATABASE_URL", "postgresql://localhost:5432/mycelium_registry"
            )
            self._pool = None
            self._owns_pool = True

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if self._pool is None and self._owns_pool:
            self._pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool is not None and self._owns_pool:
            await self._pool.close()
            self._pool = None

    # CRUD Operations

    async def create_agent(
        self,
        agent_id: str,
        agent_type: str,
        name: str,
        display_name: str,
        category: str,
        description: str,
        file_path: str,
        capabilities: list[str] | None = None,
        tools: list[str] | None = None,
        keywords: list[str] | None = None,
        embedding: list[float] | None = None,
        estimated_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Create a new agent in the registry.

        Args:
            agent_id: Unique agent identifier (e.g., "01-core-backend-developer")
            agent_type: Agent type/name (e.g., "backend-developer")
            name: Agent name
            display_name: Display name for UI
            category: Agent category
            description: Agent description
            file_path: Path to agent definition file
            capabilities: List of agent capabilities
            tools: List of tools the agent can use
            keywords: Keywords for search
            embedding: Vector embedding for semantic search (384-dim)
            estimated_tokens: Estimated token count for agent description
            metadata: Additional metadata as JSON

        Returns:
            UUID: The created agent's UUID

        Raises:
            AgentAlreadyExistsError: If an agent with the same agent_id already exists
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO agents (
                        agent_id, agent_type, name, display_name, category,
                        description, file_path, capabilities, tools, keywords,
                        embedding, estimated_tokens, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id
                """

                result: UUID = await conn.fetchval(
                    query,
                    agent_id,
                    agent_type,
                    name,
                    display_name,
                    category,
                    description,
                    file_path,
                    capabilities or [],
                    tools or [],
                    keywords or [],
                    embedding,
                    estimated_tokens,
                    json.dumps(metadata or {}),
                )
                return result

            except asyncpg.UniqueViolationError as e:
                raise AgentAlreadyExistsError(
                    f"Agent with agent_id '{agent_id}' or agent_type '{agent_type}' already exists"
                ) from e

    async def get_agent_by_id(self, agent_id: str) -> dict[str, Any]:
        """Get an agent by its agent_id.

        Args:
            agent_id: The agent_id to search for

        Returns:
            Dict containing agent data

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = """
                SELECT
                    id, agent_id, agent_type, name, display_name, category,
                    description, capabilities, tools, keywords, file_path,
                    estimated_tokens, metadata, avg_response_time_ms,
                    success_rate, usage_count, created_at, updated_at, last_used_at
                FROM agents
                WHERE agent_id = $1
            """

            row = await conn.fetchrow(query, agent_id)
            if row is None:
                raise AgentNotFoundError(f"Agent with agent_id '{agent_id}' not found")

            return dict(row)

    async def get_agent_by_type(self, agent_type: str) -> dict[str, Any]:
        """Get an agent by its agent_type.

        Args:
            agent_type: The agent_type to search for

        Returns:
            Dict containing agent data

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = """
                SELECT
                    id, agent_id, agent_type, name, display_name, category,
                    description, capabilities, tools, keywords, file_path,
                    estimated_tokens, metadata, avg_response_time_ms,
                    success_rate, usage_count, created_at, updated_at, last_used_at
                FROM agents
                WHERE agent_type = $1
            """

            row = await conn.fetchrow(query, agent_type)
            if row is None:
                raise AgentNotFoundError(f"Agent with agent_type '{agent_type}' not found")

            return dict(row)

    async def get_agent_by_uuid(self, uuid: UUID) -> dict[str, Any]:
        """Get an agent by its UUID.

        Args:
            uuid: The agent's UUID

        Returns:
            Dict containing agent data

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = """
                SELECT
                    id, agent_id, agent_type, name, display_name, category,
                    description, capabilities, tools, keywords, file_path,
                    estimated_tokens, metadata, avg_response_time_ms,
                    success_rate, usage_count, created_at, updated_at, last_used_at
                FROM agents
                WHERE id = $1
            """

            row = await conn.fetchrow(query, uuid)
            if row is None:
                raise AgentNotFoundError(f"Agent with UUID '{uuid}' not found")

            return dict(row)

    async def update_agent(
        self,
        agent_id: str,
        **fields: Any,
    ) -> None:
        """Update an agent's fields.

        Args:
            agent_id: The agent_id to update
            **fields: Fields to update (any field from the agents table)

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if not fields:
            return

        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            param_idx = 1

            for field, value in fields.items():
                if field == "metadata" and isinstance(value, dict):
                    value = json.dumps(value)
                set_clauses.append(f"{field} = ${param_idx}")
                values.append(value)
                param_idx += 1

            values.append(agent_id)
            # Using parameterized queries with $ placeholders - safe from SQL injection
            query = f"""  # nosec B608 - Using parameterized queries with asyncpg $ placeholders
                UPDATE agents
                SET {", ".join(set_clauses)}
                WHERE agent_id = ${param_idx}
                RETURNING id
            """

            result = await conn.fetchval(query, *values)
            if result is None:
                raise AgentNotFoundError(f"Agent with agent_id '{agent_id}' not found")

    async def delete_agent(self, agent_id: str) -> None:
        """Delete an agent from the registry.

        Args:
            agent_id: The agent_id to delete

        Raises:
            AgentNotFoundError: If the agent is not found
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = "DELETE FROM agents WHERE agent_id = $1 RETURNING id"
            result = await conn.fetchval(query, agent_id)

            if result is None:
                raise AgentNotFoundError(f"Agent with agent_id '{agent_id}' not found")

    async def list_agents(
        self,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List agents with optional filtering.

        Args:
            category: Filter by category
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of agent dictionaries
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            if category:
                query = """
                    SELECT
                        id, agent_id, agent_type, name, display_name, category,
                        description, capabilities, tools, keywords, file_path,
                        estimated_tokens, metadata, avg_response_time_ms,
                        success_rate, usage_count, created_at, updated_at, last_used_at
                    FROM agents
                    WHERE category = $1
                    ORDER BY name
                    LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, category, limit, offset)
            else:
                query = """
                    SELECT
                        id, agent_id, agent_type, name, display_name, category,
                        description, capabilities, tools, keywords, file_path,
                        estimated_tokens, metadata, avg_response_time_ms,
                        success_rate, usage_count, created_at, updated_at, last_used_at
                    FROM agents
                    ORDER BY name
                    LIMIT $1 OFFSET $2
                """
                rows = await conn.fetch(query, limit, offset)

            return [dict(row) for row in rows]

    async def search_agents(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search agents using full-text search on description and keywords.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of agent dictionaries matching the query
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            sql = """
                SELECT
                    id, agent_id, agent_type, name, display_name, category,
                    description, capabilities, tools, keywords, file_path,
                    estimated_tokens, metadata, avg_response_time_ms,
                    success_rate, usage_count, created_at, updated_at, last_used_at
                FROM agents
                WHERE
                    description ILIKE $1
                    OR $1 = ANY(keywords)
                    OR agent_type ILIKE $1
                    OR name ILIKE $1
                ORDER BY
                    CASE
                        WHEN agent_type ILIKE $1 THEN 1
                        WHEN name ILIKE $1 THEN 2
                        WHEN $1 = ANY(keywords) THEN 3
                        ELSE 4
                    END,
                    name
                LIMIT $2
            """

            search_pattern = f"%{query}%"
            rows = await conn.fetch(sql, search_pattern, limit)
            return [dict(row) for row in rows]

    async def similarity_search(
        self,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search agents by embedding similarity using pgvector.

        Args:
            embedding: Query embedding vector (384-dim)
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of tuples (agent_dict, similarity_score) sorted by similarity
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = """
                SELECT
                    id, agent_id, agent_type, name, display_name, category,
                    description, capabilities, tools, keywords, file_path,
                    estimated_tokens, metadata, avg_response_time_ms,
                    success_rate, usage_count, created_at, updated_at, last_used_at,
                    1 - (embedding <=> $1::vector) as similarity
                FROM agents
                WHERE embedding IS NOT NULL
                    AND 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """

            rows = await conn.fetch(query, embedding, threshold, limit)

            results = []
            for row in rows:
                similarity = row["similarity"]
                agent_data = {k: v for k, v in dict(row).items() if k != "similarity"}
                results.append((agent_data, float(similarity)))

            return results

    async def get_agent_count(self, category: str | None = None) -> int:
        """Get the total number of agents in the registry.

        Args:
            category: Optional category filter

        Returns:
            Total agent count
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            if category:
                query = "SELECT COUNT(*) FROM agents WHERE category = $1"
                count: int = await conn.fetchval(query, category)
                return count
            query = "SELECT COUNT(*) FROM agents"
            result: int = await conn.fetchval(query)
            return result

    async def get_categories(self) -> list[str]:
        """Get all unique categories in the registry.

        Returns:
            List of category names
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            query = "SELECT DISTINCT category FROM agents ORDER BY category"
            rows = await conn.fetch(query)
            return [row["category"] for row in rows]

    # Bulk operations

    async def bulk_insert_agents(
        self,
        agents: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """Bulk insert agents into the registry.

        Args:
            agents: List of agent dictionaries
            batch_size: Number of agents to insert per batch

        Returns:
            Number of agents inserted
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        inserted = 0

        async with self._pool.acquire() as conn:
            for i in range(0, len(agents), batch_size):
                batch = agents[i : i + batch_size]

                async with conn.transaction():
                    for agent in batch:
                        try:
                            # Use direct insert within transaction instead of calling create_agent
                            # to avoid nested connection acquisition
                            query = """
                                INSERT INTO agents (
                                    agent_id, agent_type, name, display_name, category,
                                    description, file_path, capabilities, tools, keywords,
                                    embedding, estimated_tokens, metadata
                                )
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            """
                            await conn.execute(
                                query,
                                agent["agent_id"],
                                agent["agent_type"],
                                agent["name"],
                                agent["display_name"],
                                agent["category"],
                                agent["description"],
                                agent["file_path"],
                                agent.get("capabilities", []),
                                agent.get("tools", []),
                                agent.get("keywords", []),
                                agent.get("embedding"),
                                agent.get("estimated_tokens"),
                                json.dumps(agent.get("metadata", {})),
                            )
                            inserted += 1
                        except asyncpg.UniqueViolationError:
                            # Skip duplicates
                            continue

        return inserted

    # Utility methods

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on the registry.

        Returns:
            Dictionary with health check results
        """
        if self._pool is None:
            raise AgentRegistryError("Registry not initialized. Call initialize() first.")

        async with self._pool.acquire() as conn:
            try:
                # Test basic connectivity
                await conn.fetchval("SELECT 1")

                # Check pgvector extension
                pgvector_installed = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                # Get agent count - use a separate connection acquisition
                agent_count = await self.get_agent_count()

                # Get database size
                db_size = await conn.fetchval("SELECT pg_size_pretty(pg_database_size(current_database()))")

                return {
                    "status": "healthy",
                    "pgvector_installed": pgvector_installed,
                    "agent_count": agent_count,
                    "database_size": db_size,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

    async def __aenter__(self) -> "AgentRegistry":
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


async def load_agents_from_index(
    index_path: str | Path,
    registry: AgentRegistry,
) -> int:
    """Load agents from index.json file into the registry.

    Args:
        index_path: Path to the index.json file
        registry: AgentRegistry instance

    Returns:
        Number of agents loaded
    """
    index_path = Path(index_path)

    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    with Path(index_path).open(encoding="utf-8") as f:
        data = json.load(f)

    agents_data = []
    for agent in data.get("agents", []):
        agent_data = {
            "agent_id": agent["id"],
            "agent_type": agent["name"],
            "name": agent["name"],
            "display_name": agent.get("display_name", agent["name"]),
            "category": agent.get("category", "Uncategorized"),
            "description": agent.get("description", ""),
            "file_path": agent.get("file_path", ""),
            "capabilities": agent.get("capabilities", []),
            "tools": agent.get("tools", []),
            "keywords": agent.get("keywords", []),
            "estimated_tokens": agent.get("estimated_tokens"),
            "metadata": {
                "version": data.get("version"),
                "generated": data.get("generated"),
            },
        }
        agents_data.append(agent_data)

    return await registry.bulk_insert_agents(agents_data)
