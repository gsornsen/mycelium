"""Unit tests for the Agent Registry module.

This test suite validates all CRUD operations, search functionality,
and edge cases for the agent registry.
"""

import json
import os
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
    """Set up the database schema once for all tests."""
    schema_path = (
        Path(__file__).parent.parent.parent
        / "plugins/mycelium-core/registry/schema.sql"
    )

    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")

    async with db_pool.acquire() as conn:
        with open(schema_path) as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)

    yield

    # Cleanup after all tests
    async with db_pool.acquire() as conn:
        await conn.execute("DROP SCHEMA public CASCADE")
        await conn.execute("CREATE SCHEMA public")


@pytest.fixture
async def registry(db_pool, schema_setup) -> AsyncGenerator[AgentRegistry, None]:
    """Create a clean agent registry for each test."""
    reg = AgentRegistry(pool=db_pool)
    await reg.initialize()

    yield reg

    # Clean up agents table after each test
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE agents CASCADE")

    await reg.close()


@pytest.mark.asyncio
class TestAgentRegistryInitialization:
    """Test registry initialization and connection management."""

    async def test_initialize_with_connection_string(self):
        """Test registry initialization with connection string."""
        registry = AgentRegistry(connection_string=TEST_DB_URL)
        await registry.initialize()
        assert registry._pool is not None
        await registry.close()

    async def test_initialize_with_pool(self, db_pool):
        """Test registry initialization with existing pool."""
        registry = AgentRegistry(pool=db_pool)
        await registry.initialize()
        assert registry._pool is not None
        await registry.close()

    async def test_context_manager(self, db_pool):
        """Test registry as async context manager."""
        async with AgentRegistry(pool=db_pool) as registry:
            assert registry._pool is not None

    async def test_get_connection_before_init(self):
        """Test that getting connection before init raises error."""
        registry = AgentRegistry(connection_string=TEST_DB_URL)
        with pytest.raises(AgentRegistryError):
            await registry._get_connection()


@pytest.mark.asyncio
class TestAgentCRUD:
    """Test CRUD operations for agents."""

    async def test_create_agent(self, registry):
        """Test creating a new agent."""
        agent_uuid = await registry.create_agent(**SAMPLE_AGENT)
        assert isinstance(agent_uuid, UUID)

    async def test_create_duplicate_agent(self, registry):
        """Test that creating duplicate agent raises error."""
        await registry.create_agent(**SAMPLE_AGENT)

        with pytest.raises(AgentAlreadyExistsError):
            await registry.create_agent(**SAMPLE_AGENT)

    async def test_create_agent_with_embedding(self, registry):
        """Test creating agent with vector embedding."""
        agent_data = {**SAMPLE_AGENT}
        agent_data["agent_id"] = "test-ai-engineer"
        agent_data["agent_type"] = "ai-engineer"
        agent_data["embedding"] = SAMPLE_EMBEDDING

        agent_uuid = await registry.create_agent(**agent_data)
        assert isinstance(agent_uuid, UUID)

    async def test_get_agent_by_id(self, registry):
        """Test retrieving agent by agent_id."""
        await registry.create_agent(**SAMPLE_AGENT)
        agent = await registry.get_agent_by_id(SAMPLE_AGENT["agent_id"])

        assert agent["agent_id"] == SAMPLE_AGENT["agent_id"]
        assert agent["agent_type"] == SAMPLE_AGENT["agent_type"]
        assert agent["name"] == SAMPLE_AGENT["name"]
        assert agent["description"] == SAMPLE_AGENT["description"]

    async def test_get_agent_by_type(self, registry):
        """Test retrieving agent by agent_type."""
        await registry.create_agent(**SAMPLE_AGENT)
        agent = await registry.get_agent_by_type(SAMPLE_AGENT["agent_type"])

        assert agent["agent_type"] == SAMPLE_AGENT["agent_type"]

    async def test_get_agent_by_uuid(self, registry):
        """Test retrieving agent by UUID."""
        agent_uuid = await registry.create_agent(**SAMPLE_AGENT)
        agent = await registry.get_agent_by_uuid(agent_uuid)

        assert agent["id"] == agent_uuid
        assert agent["agent_id"] == SAMPLE_AGENT["agent_id"]

    async def test_get_nonexistent_agent(self, registry):
        """Test that getting nonexistent agent raises error."""
        with pytest.raises(AgentNotFoundError):
            await registry.get_agent_by_id("nonexistent-agent")

    async def test_update_agent(self, registry):
        """Test updating an agent."""
        await registry.create_agent(**SAMPLE_AGENT)

        new_description = "Updated description"
        await registry.update_agent(
            SAMPLE_AGENT["agent_id"], description=new_description
        )

        agent = await registry.get_agent_by_id(SAMPLE_AGENT["agent_id"])
        assert agent["description"] == new_description

    async def test_update_agent_metadata(self, registry):
        """Test updating agent metadata."""
        await registry.create_agent(**SAMPLE_AGENT)

        new_metadata = {"version": "2.0", "updated": True}
        await registry.update_agent(SAMPLE_AGENT["agent_id"], metadata=new_metadata)

        agent = await registry.get_agent_by_id(SAMPLE_AGENT["agent_id"])
        assert json.loads(agent["metadata"]) == new_metadata

    async def test_update_nonexistent_agent(self, registry):
        """Test that updating nonexistent agent raises error."""
        with pytest.raises(AgentNotFoundError):
            await registry.update_agent("nonexistent-agent", description="test")

    async def test_delete_agent(self, registry):
        """Test deleting an agent."""
        await registry.create_agent(**SAMPLE_AGENT)
        await registry.delete_agent(SAMPLE_AGENT["agent_id"])

        with pytest.raises(AgentNotFoundError):
            await registry.get_agent_by_id(SAMPLE_AGENT["agent_id"])

    async def test_delete_nonexistent_agent(self, registry):
        """Test that deleting nonexistent agent raises error."""
        with pytest.raises(AgentNotFoundError):
            await registry.delete_agent("nonexistent-agent")


@pytest.mark.asyncio
class TestAgentQueries:
    """Test query operations for agents."""

    async def test_list_agents(self, registry):
        """Test listing all agents."""
        # Create multiple agents
        for i in range(5):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            await registry.create_agent(**agent_data)

        agents = await registry.list_agents()
        assert len(agents) == 5

    async def test_list_agents_with_category_filter(self, registry):
        """Test listing agents filtered by category."""
        # Create agents in different categories
        for i in range(3):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-core-{i}"
            agent_data["agent_type"] = f"core-{i}"
            agent_data["category"] = "Core Development"
            await registry.create_agent(**agent_data)

        for i in range(2):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-data-{i}"
            agent_data["agent_type"] = f"data-{i}"
            agent_data["category"] = "Data & AI"
            await registry.create_agent(**agent_data)

        core_agents = await registry.list_agents(category="Core Development")
        assert len(core_agents) == 3

        data_agents = await registry.list_agents(category="Data & AI")
        assert len(data_agents) == 2

    async def test_list_agents_pagination(self, registry):
        """Test pagination in list_agents."""
        # Create 10 agents
        for i in range(10):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            await registry.create_agent(**agent_data)

        # Get first page
        page1 = await registry.list_agents(limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await registry.list_agents(limit=5, offset=5)
        assert len(page2) == 5

        # Ensure different agents
        page1_ids = {a["agent_id"] for a in page1}
        page2_ids = {a["agent_id"] for a in page2}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_search_agents(self, registry):
        """Test full-text search for agents."""
        # Create agents with different descriptions
        agent1 = {**SAMPLE_AGENT}
        agent1["agent_id"] = "backend-dev"
        agent1["agent_type"] = "backend-developer"
        agent1["description"] = "Backend development specialist"
        await registry.create_agent(**agent1)

        agent2 = {**SAMPLE_AGENT}
        agent2["agent_id"] = "frontend-dev"
        agent2["agent_type"] = "frontend-developer"
        agent2["description"] = "Frontend UI development expert"
        await registry.create_agent(**agent2)

        # Search for backend
        results = await registry.search_agents("backend")
        assert len(results) >= 1
        assert any("backend" in r["agent_type"].lower() for r in results)

    async def test_search_agents_by_keyword(self, registry):
        """Test searching agents by keyword."""
        agent_data = {**SAMPLE_AGENT}
        agent_data["keywords"] = ["api", "rest", "graphql"]
        await registry.create_agent(**agent_data)

        results = await registry.search_agents("api")
        assert len(results) >= 1

    async def test_get_agent_count(self, registry):
        """Test getting total agent count."""
        # Create 3 agents
        for i in range(3):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            await registry.create_agent(**agent_data)

        count = await registry.get_agent_count()
        assert count == 3

    async def test_get_agent_count_by_category(self, registry):
        """Test getting agent count filtered by category."""
        # Create agents in different categories
        for i in range(2):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-core-{i}"
            agent_data["agent_type"] = f"core-{i}"
            agent_data["category"] = "Core Development"
            await registry.create_agent(**agent_data)

        count = await registry.get_agent_count(category="Core Development")
        assert count == 2

    async def test_get_categories(self, registry):
        """Test getting all unique categories."""
        # Create agents in different categories
        categories = ["Core Development", "Data & AI", "Infrastructure"]

        for i, category in enumerate(categories):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            agent_data["category"] = category
            await registry.create_agent(**agent_data)

        result = await registry.get_categories()
        assert set(result) == set(categories)


@pytest.mark.asyncio
class TestVectorSearch:
    """Test vector similarity search operations."""

    async def test_similarity_search(self, registry):
        """Test semantic similarity search with embeddings."""
        # Create agents with embeddings
        for i in range(3):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            # Create slightly different embeddings
            agent_data["embedding"] = [0.1 + i * 0.01] * 384
            await registry.create_agent(**agent_data)

        # Search with similar embedding
        query_embedding = [0.11] * 384
        results = await registry.similarity_search(
            query_embedding, limit=3, threshold=0.5
        )

        assert len(results) > 0
        # Results should be tuples of (agent_dict, similarity_score)
        for agent_dict, similarity in results:
            assert isinstance(agent_dict, dict)
            assert isinstance(similarity, float)
            assert 0.0 <= similarity <= 1.0

    async def test_similarity_search_with_threshold(self, registry):
        """Test similarity search respects threshold parameter."""
        # Create agent with embedding
        agent_data = {**SAMPLE_AGENT}
        agent_data["embedding"] = [0.5] * 384
        await registry.create_agent(**agent_data)

        # Search with very different embedding and high threshold
        query_embedding = [0.9] * 384
        results = await registry.similarity_search(
            query_embedding,
            limit=10,
            threshold=0.99,  # Very high threshold
        )

        # Should have few or no results due to high threshold
        assert len(results) <= 1

    async def test_similarity_search_ordering(self, registry):
        """Test that similarity search results are ordered by similarity."""
        # Create agents with different embeddings
        embeddings = [[0.1] * 384, [0.5] * 384, [0.9] * 384]

        for i, emb in enumerate(embeddings):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"test-agent-{i}"
            agent_data["agent_type"] = f"agent-{i}"
            agent_data["embedding"] = emb
            await registry.create_agent(**agent_data)

        # Search with embedding close to middle one
        query_embedding = [0.5] * 384
        results = await registry.similarity_search(
            query_embedding, limit=3, threshold=0.0
        )

        # Results should be ordered by similarity (descending)
        similarities = [sim for _, sim in results]
        assert similarities == sorted(similarities, reverse=True)


@pytest.mark.asyncio
class TestBulkOperations:
    """Test bulk operations."""

    async def test_bulk_insert_agents(self, registry):
        """Test bulk inserting multiple agents."""
        agents = []
        for i in range(10):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"bulk-agent-{i}"
            agent_data["agent_type"] = f"bulk-{i}"
            agents.append(agent_data)

        count = await registry.bulk_insert_agents(agents)
        assert count == 10

        total = await registry.get_agent_count()
        assert total == 10

    async def test_bulk_insert_with_duplicates(self, registry):
        """Test bulk insert skips duplicates."""
        # Create one agent first
        await registry.create_agent(**SAMPLE_AGENT)

        # Try to bulk insert including the duplicate
        agents = [SAMPLE_AGENT]
        for i in range(5):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"bulk-agent-{i}"
            agent_data["agent_type"] = f"bulk-{i}"
            agents.append(agent_data)

        count = await registry.bulk_insert_agents(agents)
        # Should insert 5 new agents, skip 1 duplicate
        assert count == 5

        total = await registry.get_agent_count()
        assert total == 6  # 1 original + 5 new


@pytest.mark.asyncio
class TestUtilityMethods:
    """Test utility methods."""

    async def test_health_check(self, registry):
        """Test health check returns status information."""
        health = await registry.health_check()

        assert health["status"] == "healthy"
        assert "pgvector_installed" in health
        assert "agent_count" in health
        assert "database_size" in health
        assert "timestamp" in health

    async def test_health_check_pgvector_installed(self, registry):
        """Test health check detects pgvector installation."""
        health = await registry.health_check()
        assert health["pgvector_installed"] is True


@pytest.mark.asyncio
class TestLoadFromIndex:
    """Test loading agents from index.json."""

    async def test_load_agents_from_index(self, registry, tmp_path):
        """Test loading agents from index.json file."""
        # Create a temporary index.json
        index_data = {
            "version": "1.0.0",
            "generated": "2025-10-21T00:00:00Z",
            "agent_count": 2,
            "agents": [
                {
                    "id": "test-agent-1",
                    "name": "test-agent-1",
                    "display_name": "Test Agent 1",
                    "category": "Test",
                    "description": "Test agent 1",
                    "file_path": "/test/agent1.md",
                    "tools": ["Bash"],
                    "keywords": ["test"],
                    "estimated_tokens": 100,
                },
                {
                    "id": "test-agent-2",
                    "name": "test-agent-2",
                    "display_name": "Test Agent 2",
                    "category": "Test",
                    "description": "Test agent 2",
                    "file_path": "/test/agent2.md",
                    "tools": ["Read"],
                    "keywords": ["test"],
                    "estimated_tokens": 150,
                },
            ],
        }

        index_path = tmp_path / "index.json"
        with open(index_path, "w") as f:
            json.dump(index_data, f)

        # Load agents from index
        count = await load_agents_from_index(index_path, registry)
        assert count == 2

        # Verify agents were loaded
        total = await registry.get_agent_count()
        assert total == 2

    async def test_load_from_nonexistent_index(self, registry):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            await load_agents_from_index("/nonexistent/index.json", registry)


@pytest.mark.asyncio
class TestPerformance:
    """Test performance requirements."""

    async def test_query_performance(self, registry):
        """Test that queries complete within performance requirements."""
        import time

        # Create 100 agents
        agents = []
        for i in range(100):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"perf-agent-{i}"
            agent_data["agent_type"] = f"perf-{i}"
            agents.append(agent_data)

        await registry.bulk_insert_agents(agents)

        # Test get_agent_by_id performance (<100ms)
        start = time.time()
        await registry.get_agent_by_id("perf-agent-50")
        duration = (time.time() - start) * 1000
        assert duration < 100, f"Query took {duration}ms, expected <100ms"

    async def test_search_performance(self, registry):
        """Test that search queries meet performance requirements."""
        import time

        # Create 100 agents with keywords
        agents = []
        for i in range(100):
            agent_data = {**SAMPLE_AGENT}
            agent_data["agent_id"] = f"search-agent-{i}"
            agent_data["agent_type"] = f"search-{i}"
            agent_data["keywords"] = [f"keyword-{i}", "common"]
            agents.append(agent_data)

        await registry.bulk_insert_agents(agents)

        # Test search performance (<100ms)
        start = time.time()
        await registry.search_agents("common")
        duration = (time.time() - start) * 1000
        assert duration < 100, f"Search took {duration}ms, expected <100ms"
