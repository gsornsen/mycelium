"""Unit tests for the Agent Registry module.

This test suite validates all CRUD operations, search functionality,
and edge cases for the agent registry.
"""

import contextlib
import json
import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from registry import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    AgentRegistry,
    AgentRegistryError,
    load_agents_from_index,
)

# Test Configuration
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://mycelium:mycelium_dev_password@localhost:5432/mycelium_registry",
)

# Sample test data
SAMPLE_AGENT = {
    "agent_id": "test-backend-developer",
    "agent_type": "backend-developer",
    "name": "backend-developer",
    "display_name": "Backend Developer",
    "category": "Core Development",
    "description": "Senior backend engineer for scalable API development",
    "file_path": "/test/backend-developer.md",
    "capabilities": ["api-development", "database-design", "microservices"],
    "tools": ["Bash", "Docker", "PostgreSQL"],
    "keywords": ["backend", "api", "database", "microservices"],
    "estimated_tokens": 1200,
    "metadata": {"test": True},
}

SAMPLE_EMBEDDING = [0.1] * 384  # 384-dimensional test embedding


@pytest.fixture(scope="session")
async def db_pool():
    """Create a database pool for testing."""
    # Create the test database if it doesn't exist
    try:
        conn = await asyncpg.connect("postgresql://localhost:5432/postgres")
        try:
            await conn.execute("CREATE DATABASE mycelium_test")
        except asyncpg.DuplicateDatabaseError:
            pass
        finally:
            await conn.close()
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL: {e}")

    pool = await asyncpg.create_pool(TEST_DB_URL)
    yield pool
    await pool.close()


@pytest.fixture(scope="session")
async def schema_setup(db_pool):
    """Set up the database schema using Alembic migrations."""
    # Set DATABASE_URL for Alembic
    os.environ["DATABASE_URL"] = TEST_DB_URL

    try:
        # Run Alembic migrations to create all tables
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stderr and "error" in result.stderr.lower():
            pytest.skip(f"Failed to run migrations: {result.stderr}")
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Failed to run migrations: {e.stderr}")
    except FileNotFoundError:
        pytest.skip("Alembic not found - ensure it's installed")

    yield

    # Cleanup after all tests - drop all tables
    async with db_pool.acquire() as conn:
        # Get all table names
        tables = await conn.fetch(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'alembic_version'
            """
        )

        # Drop all tables (except alembic_version)
        for table in tables:
            await conn.execute(f"DROP TABLE IF EXISTS {table['tablename']} CASCADE")

        # Optionally, run downgrade to base (cleaner approach)
        with contextlib.suppress(Exception):
            subprocess.run(
                ["alembic", "downgrade", "base"],
                capture_output=True,
                text=True,
                check=False,  # Don't fail if downgrade has issues
            )


@pytest.fixture
async def registry(db_pool, schema_setup) -> AsyncGenerator[AgentRegistry, None]:
    """Create a clean agent registry for each test."""
    reg = AgentRegistry(pool=db_pool)
    await reg.initialize()

    yield reg

    # Clean up agents table after each test
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE agents CASCADE")


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentRegistry:
    """Test suite for Agent Registry operations."""

    async def test_create_agent(self, registry: AgentRegistry):
        """Test creating a new agent."""
        agent_id = await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)
        assert agent_id is not None
        assert isinstance(agent_id, UUID)

    async def test_create_duplicate_agent(self, registry: AgentRegistry):
        """Test that creating a duplicate agent raises an error."""
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

        with pytest.raises(AgentAlreadyExistsError):
            await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

    async def test_get_agent(self, registry: AgentRegistry):
        """Test retrieving an agent by ID."""
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

        agent = await registry.get_agent("test-backend-developer")
        assert agent is not None
        assert agent["agent_id"] == "test-backend-developer"
        assert agent["name"] == "backend-developer"
        assert agent["category"] == "Core Development"

    async def test_get_nonexistent_agent(self, registry: AgentRegistry):
        """Test that getting a non-existent agent raises an error."""
        with pytest.raises(AgentNotFoundError):
            await registry.get_agent("nonexistent-agent")

    async def test_update_agent(self, registry: AgentRegistry):
        """Test updating an existing agent."""
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

        updated_data = SAMPLE_AGENT.copy()
        updated_data["description"] = "Updated description"
        updated_data["capabilities"] = ["new-capability"]

        await registry.update_agent("test-backend-developer", updated_data)

        agent = await registry.get_agent("test-backend-developer")
        assert agent["description"] == "Updated description"
        assert "new-capability" in agent["capabilities"]

    async def test_update_nonexistent_agent(self, registry: AgentRegistry):
        """Test that updating a non-existent agent raises an error."""
        with pytest.raises(AgentNotFoundError):
            await registry.update_agent("nonexistent-agent", SAMPLE_AGENT)

    async def test_delete_agent(self, registry: AgentRegistry):
        """Test deleting an agent."""
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)
        await registry.delete_agent("test-backend-developer")

        with pytest.raises(AgentNotFoundError):
            await registry.get_agent("test-backend-developer")

    async def test_delete_nonexistent_agent(self, registry: AgentRegistry):
        """Test that deleting a non-existent agent raises an error."""
        with pytest.raises(AgentNotFoundError):
            await registry.delete_agent("nonexistent-agent")

    async def test_list_agents(self, registry: AgentRegistry):
        """Test listing all agents."""
        # Create multiple agents
        agents_data = [{**SAMPLE_AGENT, "agent_id": f"test-agent-{i}", "name": f"agent-{i}"} for i in range(3)]

        for agent_data in agents_data:
            await registry.create_agent(agent_data=agent_data, embedding=SAMPLE_EMBEDDING)

        agents = await registry.list_agents()
        assert len(agents) == 3
        assert all(a["agent_id"].startswith("test-agent-") for a in agents)

    async def test_search_agents_by_text(self, registry: AgentRegistry):
        """Test searching agents by text query."""
        # Create agents with different descriptions
        agent1 = {
            **SAMPLE_AGENT,
            "agent_id": "python-expert",
            "description": "Expert in Python programming and Django framework",
        }
        agent2 = {
            **SAMPLE_AGENT,
            "agent_id": "js-expert",
            "description": "Expert in JavaScript and React development",
        }

        await registry.create_agent(agent_data=agent1, embedding=SAMPLE_EMBEDDING)
        await registry.create_agent(agent_data=agent2, embedding=SAMPLE_EMBEDDING)

        # Search for Python-related agents
        results = await registry.search_agents(query="Python Django", limit=10)
        assert len(results) > 0
        assert results[0]["agent_id"] == "python-expert"

    async def test_search_agents_by_category(self, registry: AgentRegistry):
        """Test filtering agents by category."""
        # Create agents with different categories
        agent1 = {**SAMPLE_AGENT, "agent_id": "backend-dev", "category": "Backend"}
        agent2 = {**SAMPLE_AGENT, "agent_id": "frontend-dev", "category": "Frontend"}

        await registry.create_agent(agent_data=agent1, embedding=SAMPLE_EMBEDDING)
        await registry.create_agent(agent_data=agent2, embedding=SAMPLE_EMBEDDING)

        # Filter by category
        results = await registry.search_agents(category="Backend", limit=10)
        assert len(results) == 1
        assert results[0]["agent_id"] == "backend-dev"

    async def test_search_agents_by_capabilities(self, registry: AgentRegistry):
        """Test filtering agents by capabilities."""
        # Create agents with different capabilities
        agent1 = {
            **SAMPLE_AGENT,
            "agent_id": "api-dev",
            "capabilities": ["api-development", "rest", "graphql"],
        }
        agent2 = {
            **SAMPLE_AGENT,
            "agent_id": "data-eng",
            "capabilities": ["data-pipeline", "etl", "spark"],
        }

        await registry.create_agent(agent_data=agent1, embedding=SAMPLE_EMBEDDING)
        await registry.create_agent(agent_data=agent2, embedding=SAMPLE_EMBEDDING)

        # Search by capabilities
        results = await registry.search_agents(capabilities=["api-development"], limit=10)
        assert len(results) == 1
        assert results[0]["agent_id"] == "api-dev"

    async def test_search_agents_combined_filters(self, registry: AgentRegistry):
        """Test combining multiple search filters."""
        # Create diverse agents
        agents = [
            {
                **SAMPLE_AGENT,
                "agent_id": "backend-python",
                "category": "Backend",
                "capabilities": ["python", "django"],
                "description": "Backend developer specializing in Python",
            },
            {
                **SAMPLE_AGENT,
                "agent_id": "backend-java",
                "category": "Backend",
                "capabilities": ["java", "spring"],
                "description": "Backend developer specializing in Java",
            },
            {
                **SAMPLE_AGENT,
                "agent_id": "frontend-react",
                "category": "Frontend",
                "capabilities": ["javascript", "react"],
                "description": "Frontend developer specializing in React",
            },
        ]

        for agent in agents:
            await registry.create_agent(agent_data=agent, embedding=SAMPLE_EMBEDDING)

        # Search with multiple filters
        results = await registry.search_agents(query="Python", category="Backend", capabilities=["python"], limit=10)
        assert len(results) == 1
        assert results[0]["agent_id"] == "backend-python"

    async def test_update_agent_usage(self, registry: AgentRegistry):
        """Test updating agent usage statistics."""
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

        # Update usage statistics
        await registry.update_agent_usage("test-backend-developer", response_time_ms=150, success=True)

        agent = await registry.get_agent("test-backend-developer")
        assert agent["usage_count"] == 1
        assert agent["avg_response_time_ms"] == 150
        assert agent["success_rate"] == 100.0

        # Update with more usage
        await registry.update_agent_usage("test-backend-developer", response_time_ms=250, success=False)

        agent = await registry.get_agent("test-backend-developer")
        assert agent["usage_count"] == 2
        assert agent["avg_response_time_ms"] == 200  # (150 + 250) / 2
        assert agent["success_rate"] == 50.0  # 1 success out of 2

    async def test_bulk_create_agents(self, registry: AgentRegistry):
        """Test creating multiple agents in bulk."""
        agents_data = [{**SAMPLE_AGENT, "agent_id": f"bulk-agent-{i}", "name": f"bulk-{i}"} for i in range(5)]

        agent_ids = await registry.bulk_create_agents(agents_data=agents_data, embeddings=[SAMPLE_EMBEDDING] * 5)

        assert len(agent_ids) == 5
        assert all(isinstance(aid, UUID) for aid in agent_ids)

        # Verify all agents were created
        agents = await registry.list_agents()
        assert len(agents) == 5

    async def test_get_agent_dependencies(self, registry: AgentRegistry):
        """Test retrieving agent dependencies."""
        # Create agents
        await registry.create_agent(agent_data=SAMPLE_AGENT, embedding=SAMPLE_EMBEDDING)

        dep_agent = {
            **SAMPLE_AGENT,
            "agent_id": "dependency-agent",
            "name": "dependency",
        }
        await registry.create_agent(agent_data=dep_agent, embedding=SAMPLE_EMBEDDING)

        # Add dependency
        await registry.add_agent_dependency("test-backend-developer", "dependency-agent", "required")

        # Get dependencies
        deps = await registry.get_agent_dependencies("test-backend-developer")
        assert len(deps) == 1
        assert deps[0]["depends_on_agent_id"] == "dependency-agent"
        assert deps[0]["dependency_type"] == "required"

    async def test_load_agents_from_index(self, registry: AgentRegistry):
        """Test loading agents from index JSON file."""
        # Create a temporary index file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            index_data = {"agents": [SAMPLE_AGENT]}
            json.dump(index_data, f)
            index_path = f.name

        try:
            # Load agents from index
            agents = load_agents_from_index(index_path)
            assert len(agents) == 1
            assert agents[0]["agent_id"] == "test-backend-developer"
        finally:
            # Clean up
            Path(index_path).unlink()

    async def test_concurrent_operations(self, registry: AgentRegistry):
        """Test concurrent registry operations."""
        import asyncio

        # Create multiple agents concurrently
        tasks = [
            registry.create_agent(
                agent_data={**SAMPLE_AGENT, "agent_id": f"concurrent-{i}", "name": f"concurrent-{i}"},
                embedding=SAMPLE_EMBEDDING,
            )
            for i in range(10)
        ]
        agent_ids = await asyncio.gather(*tasks)
        assert len(agent_ids) == 10

        # Verify all were created
        agents = await registry.list_agents()
        assert len(agents) == 10

    async def test_transaction_rollback(self, registry: AgentRegistry):
        """Test that failed operations are rolled back."""
        # Try to create an agent with invalid data (missing required field)
        invalid_agent = SAMPLE_AGENT.copy()
        del invalid_agent["name"]  # Remove required field

        with pytest.raises((AgentRegistryError, KeyError)):
            await registry.create_agent(agent_data=invalid_agent, embedding=SAMPLE_EMBEDDING)

        # Verify no partial data was saved
        agents = await registry.list_agents()
        assert len(agents) == 0

    async def test_search_with_pagination(self, registry: AgentRegistry):
        """Test paginated search results."""
        # Create many agents
        for i in range(20):
            agent_data = {**SAMPLE_AGENT, "agent_id": f"page-agent-{i}", "name": f"page-{i}"}
            await registry.create_agent(agent_data=agent_data, embedding=SAMPLE_EMBEDDING)

        # Get first page
        page1 = await registry.search_agents(limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await registry.search_agents(limit=5, offset=5)
        assert len(page2) == 5

        # Verify different results
        page1_ids = {a["agent_id"] for a in page1}
        page2_ids = {a["agent_id"] for a in page2}
        assert page1_ids.isdisjoint(page2_ids)  # No overlap

    async def test_vector_similarity_search(self, registry: AgentRegistry):
        """Test vector similarity search using embeddings."""
        # Create agents with different embeddings
        embedding1 = [1.0] * 384
        embedding2 = [0.5] * 384
        embedding3 = [0.0] * 384

        agent1 = {**SAMPLE_AGENT, "agent_id": "similar-1", "name": "similar-1"}
        agent2 = {**SAMPLE_AGENT, "agent_id": "similar-2", "name": "similar-2"}
        agent3 = {**SAMPLE_AGENT, "agent_id": "different", "name": "different"}

        await registry.create_agent(agent_data=agent1, embedding=embedding1)
        await registry.create_agent(agent_data=agent2, embedding=embedding2)
        await registry.create_agent(agent_data=agent3, embedding=embedding3)

        # Search by similarity to embedding1
        results = await registry.search_by_embedding(embedding=embedding1, limit=3)
        assert len(results) == 3
        # Most similar should be agent1 itself
        assert results[0]["agent_id"] == "similar-1"
        # Next should be agent2 (closer to agent1 than agent3)
        assert results[1]["agent_id"] == "similar-2"
        # Least similar should be agent3
        assert results[2]["agent_id"] == "different"
