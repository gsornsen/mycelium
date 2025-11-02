"""Unit tests for the Agent Registry module.

Tests cover the core functionality of the AgentRegistry class including
CRUD operations, search functionality, and bulk operations.
"""

import json
import os
import sys
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

from registry.registry import (
    AgentAlreadyExistsError,
    AgentNotFoundError,
    AgentRegistry,
    AgentRegistryError,
    load_agents_from_index,
)


@pytest.fixture
def mock_pool(mocker):
    """Create a mock connection pool for testing."""
    return mocker.AsyncMock()


@pytest_asyncio.fixture
async def registry():
    """Create a registry instance for testing.

    Note: This requires a test database to be configured.
    For CI, we'll use mocking or skip these tests if no DB available.
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        pytest.skip("Test database not configured")

    registry = AgentRegistry(connection_string=test_db_url)
    await registry.initialize()
    yield registry
    await registry.close()


@pytest.mark.asyncio
class TestAgentRegistry:
    """Test AgentRegistry core functionality."""

    async def test_registry_initialization(self):
        """Test that registry initializes properly."""
        registry = AgentRegistry(connection_string="postgresql://test")
        assert registry._pool is None
        assert registry._owns_pool is True

    async def test_registry_with_existing_pool(self, mock_pool):
        """Test registry initialization with existing pool."""
        registry = AgentRegistry(pool=mock_pool)
        assert registry._pool is mock_pool
        assert registry._owns_pool is False

    async def test_registry_error_without_initialization(self):
        """Test that operations fail without initialization."""
        registry = AgentRegistry()
        with pytest.raises(AgentRegistryError, match="Registry not initialized"):
            await registry.create_agent(
                agent_id="test-agent",
                agent_type="test",
                name="Test",
                display_name="Test Agent",
                category="Test",
                description="Test agent",
                file_path="test.md",
            )

    async def test_context_manager(self):
        """Test async context manager functionality."""
        test_db_url = os.getenv("TEST_DATABASE_URL")
        if not test_db_url:
            pytest.skip("Test database not configured")

        async with AgentRegistry(connection_string=test_db_url) as registry:
            assert registry._pool is not None


@pytest.mark.asyncio
class TestAgentCRUD:
    """Test CRUD operations for agents."""

    async def test_create_agent_minimal(self, registry):
        """Test creating agent with minimal fields."""
        if not registry:
            pytest.skip("Registry not available")

        agent_uuid = await registry.create_agent(
            agent_id="test-minimal",
            agent_type="minimal",
            name="Minimal Agent",
            display_name="Minimal",
            category="Test",
            description="Minimal test agent",
            file_path="minimal.md",
        )
        assert isinstance(agent_uuid, UUID)

    async def test_create_agent_full(self, registry):
        """Test creating agent with all fields."""
        if not registry:
            pytest.skip("Registry not available")

        agent_uuid = await registry.create_agent(
            agent_id="test-full",
            agent_type="full",
            name="Full Agent",
            display_name="Full",
            category="Test",
            description="Full test agent",
            file_path="full.md",
            capabilities=["test", "validate"],
            tools=["Read", "Write"],
            keywords=["testing", "validation"],
            embedding=[0.1] * 384,
            estimated_tokens=500,
            metadata={"version": "1.0"},
        )
        assert isinstance(agent_uuid, UUID)

    async def test_create_duplicate_agent(self, registry):
        """Test that duplicate agents raise error."""
        if not registry:
            pytest.skip("Registry not available")

        # Create first agent
        await registry.create_agent(
            agent_id="test-duplicate",
            agent_type="duplicate",
            name="Duplicate",
            display_name="Duplicate",
            category="Test",
            description="Test",
            file_path="dup.md",
        )

        # Try to create duplicate
        with pytest.raises(AgentAlreadyExistsError):
            await registry.create_agent(
                agent_id="test-duplicate",
                agent_type="duplicate-2",
                name="Duplicate 2",
                display_name="Duplicate 2",
                category="Test",
                description="Test",
                file_path="dup2.md",
            )

    async def test_get_agent_by_id(self, registry):
        """Test retrieving agent by ID."""
        if not registry:
            pytest.skip("Registry not available")

        # Create agent
        await registry.create_agent(
            agent_id="test-get-id",
            agent_type="get-id",
            name="Get ID",
            display_name="Get by ID",
            category="Test",
            description="Test get by ID",
            file_path="get.md",
        )

        # Retrieve agent
        agent = await registry.get_agent_by_id("test-get-id")
        assert agent["agent_id"] == "test-get-id"
        assert agent["name"] == "Get ID"

    async def test_get_nonexistent_agent(self, registry):
        """Test that getting nonexistent agent raises error."""
        if not registry:
            pytest.skip("Registry not available")

        with pytest.raises(AgentNotFoundError):
            await registry.get_agent_by_id("nonexistent")

    async def test_update_agent(self, registry):
        """Test updating agent fields."""
        if not registry:
            pytest.skip("Registry not available")

        # Create agent
        await registry.create_agent(
            agent_id="test-update",
            agent_type="update",
            name="Original",
            display_name="Original",
            category="Test",
            description="Original description",
            file_path="update.md",
        )

        # Update agent
        await registry.update_agent("test-update", description="Updated description", keywords=["updated", "modified"])

        # Verify update
        agent = await registry.get_agent_by_id("test-update")
        assert agent["description"] == "Updated description"
        assert agent["keywords"] == ["updated", "modified"]

    async def test_delete_agent(self, registry):
        """Test deleting agent."""
        if not registry:
            pytest.skip("Registry not available")

        # Create agent
        await registry.create_agent(
            agent_id="test-delete",
            agent_type="delete",
            name="Delete",
            display_name="Delete",
            category="Test",
            description="Test delete",
            file_path="delete.md",
        )

        # Delete agent
        await registry.delete_agent("test-delete")

        # Verify deletion
        with pytest.raises(AgentNotFoundError):
            await registry.get_agent_by_id("test-delete")


@pytest.mark.asyncio
class TestAgentSearch:
    """Test agent search and listing functionality."""

    async def test_list_all_agents(self, registry):
        """Test listing all agents."""
        if not registry:
            pytest.skip("Registry not available")

        agents = await registry.list_agents()
        assert isinstance(agents, list)

    async def test_list_agents_by_category(self, registry):
        """Test listing agents filtered by category."""
        if not registry:
            pytest.skip("Registry not available")

        # Create test agents
        await registry.create_agent(
            agent_id="test-cat1",
            agent_type="cat1",
            name="Cat1",
            display_name="Category 1",
            category="TestCat",
            description="Test category 1",
            file_path="cat1.md",
        )

        await registry.create_agent(
            agent_id="test-cat2",
            agent_type="cat2",
            name="Cat2",
            display_name="Category 2",
            category="OtherCat",
            description="Test category 2",
            file_path="cat2.md",
        )

        # List by category
        agents = await registry.list_agents(category="TestCat")
        assert len(agents) >= 1
        assert all(a["category"] == "TestCat" for a in agents)

    async def test_search_agents(self, registry):
        """Test searching agents."""
        if not registry:
            pytest.skip("Registry not available")

        # Create searchable agent
        await registry.create_agent(
            agent_id="test-search",
            agent_type="searchable",
            name="Searchable Agent",
            display_name="Search Test",
            category="Test",
            description="This agent handles API operations",
            file_path="search.md",
            keywords=["api", "rest", "http"],
        )

        # Search for agent
        results = await registry.search_agents("api")
        assert len(results) >= 1
        assert any(r["agent_id"] == "test-search" for r in results)

    async def test_get_categories(self, registry):
        """Test getting all categories."""
        if not registry:
            pytest.skip("Registry not available")

        categories = await registry.get_categories()
        assert isinstance(categories, list)

    async def test_get_agent_count(self, registry):
        """Test getting agent count."""
        if not registry:
            pytest.skip("Registry not available")

        count = await registry.get_agent_count()
        assert isinstance(count, int)
        assert count >= 0


@pytest.mark.asyncio
class TestBulkOperations:
    """Test bulk operations."""

    async def test_bulk_insert_agents(self, registry):
        """Test bulk inserting agents."""
        if not registry:
            pytest.skip("Registry not available")

        agents = [
            {
                "agent_id": f"bulk-{i}",
                "agent_type": f"bulk-type-{i}",
                "name": f"Bulk Agent {i}",
                "display_name": f"Bulk {i}",
                "category": "Bulk",
                "description": f"Bulk test agent {i}",
                "file_path": f"bulk{i}.md",
                "tools": ["Read", "Write"],
                "keywords": ["bulk", "test"],
                "estimated_tokens": 100 + i,
            }
            for i in range(5)
        ]

        inserted = await registry.bulk_insert_agents(agents, batch_size=3)
        assert inserted == 5

    async def test_bulk_insert_skip_duplicates(self, registry):
        """Test that bulk insert skips duplicates."""
        if not registry:
            pytest.skip("Registry not available")

        # Create existing agent
        await registry.create_agent(
            agent_id="bulk-existing",
            agent_type="existing",
            name="Existing",
            display_name="Existing",
            category="Test",
            description="Existing agent",
            file_path="existing.md",
        )

        # Try to bulk insert with duplicate
        agents = [
            {
                "agent_id": "bulk-existing",
                "agent_type": "existing",
                "name": "Duplicate",
                "display_name": "Duplicate",
                "category": "Test",
                "description": "Duplicate",
                "file_path": "dup.md",
            },
            {
                "agent_id": "bulk-new",
                "agent_type": "new",
                "name": "New",
                "display_name": "New",
                "category": "Test",
                "description": "New agent",
                "file_path": "new.md",
            },
        ]

        inserted = await registry.bulk_insert_agents(agents)
        assert inserted == 1  # Only new agent inserted


@pytest.mark.asyncio
class TestUtilityMethods:
    """Test utility methods."""

    async def test_health_check(self, registry):
        """Test health check functionality."""
        if not registry:
            pytest.skip("Registry not available")

        health = await registry.health_check()
        assert "status" in health
        assert "timestamp" in health
        assert health["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
class TestLoadFromIndex:
    """Test loading agents from index.json."""

    async def test_load_agents_from_index(self, registry, tmp_path):
        """Test loading agents from index file."""
        if not registry:
            pytest.skip("Registry not available")

        # Create test index file
        index_data = {
            "version": "1.0.0",
            "generated": "2025-01-01T00:00:00Z",
            "agents": [
                {
                    "id": "index-agent-1",
                    "name": "agent-one",
                    "display_name": "Agent One",
                    "category": "Test",
                    "description": "Test agent from index",
                    "tools": ["Read"],
                    "keywords": ["test"],
                    "file_path": "agent1.md",
                    "estimated_tokens": 200,
                },
                {
                    "id": "index-agent-2",
                    "name": "agent-two",
                    "display_name": "Agent Two",
                    "category": "Test",
                    "description": "Another test agent",
                    "tools": ["Write"],
                    "keywords": ["test", "sample"],
                    "file_path": "agent2.md",
                    "estimated_tokens": 300,
                },
            ],
        }

        index_path = tmp_path / "test_index.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Load agents
        loaded = await load_agents_from_index(index_path, registry)
        assert loaded == 2

    async def test_load_missing_index_file(self, registry):
        """Test error handling for missing index file."""
        if not registry:
            pytest.skip("Registry not available")

        with pytest.raises(FileNotFoundError):
            await load_agents_from_index("nonexistent.json", registry)


# Mock-based tests for CI without database
class TestRegistryMocked:
    """Test registry with mocked database connection."""

    def test_initialization_defaults(self):
        """Test default initialization without database."""
        registry = AgentRegistry()
        assert registry._pool is None
        assert registry._owns_pool is True
        assert registry._connection_string == os.getenv("DATABASE_URL", "postgresql://localhost:5432/mycelium_registry")

    def test_initialization_with_connection_string(self):
        """Test initialization with custom connection string."""
        registry = AgentRegistry(connection_string="postgresql://custom:5432/test")
        assert registry._connection_string == "postgresql://custom:5432/test"
        assert registry._pool is None
        assert registry._owns_pool is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
