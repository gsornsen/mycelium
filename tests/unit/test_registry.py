"""Unit tests for agent registry client."""

from unittest.mock import MagicMock

import pytest

from mycelium.registry.client import REDIS_AVAILABLE, AgentInfo, RegistryClient


class TestAgentInfo:
    """Test AgentInfo dataclass."""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        agent = AgentInfo(
            name="test-agent",
            category="backend",
            status="healthy",
            pid=1234,
            description="Test agent",
        )

        data = agent.to_dict()
        assert data["name"] == "test-agent"
        assert data["category"] == "backend"
        assert data["status"] == "healthy"
        assert data["pid"] == 1234
        assert data["description"] == "Test agent"

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "name": "test-agent",
            "category": "backend",
            "status": "healthy",
            "pid": 1234,
            "port": 8080,
            "description": "Test agent",
        }

        agent = AgentInfo.from_dict(data)
        assert agent.name == "test-agent"
        assert agent.category == "backend"
        assert agent.status == "healthy"
        assert agent.pid == 1234
        assert agent.port == 8080
        assert agent.description == "Test agent"

    def test_from_dict_with_none_values(self) -> None:
        """Test creation from dictionary with None values."""
        data = {
            "name": "test-agent",
            "category": "backend",
            "status": "healthy",
            "pid": None,
            "port": None,
            "description": None,
        }

        agent = AgentInfo.from_dict(data)
        assert agent.name == "test-agent"
        assert agent.pid is None
        assert agent.port is None
        assert agent.description is None


class TestRegistryClient:
    """Test RegistryClient."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = RegistryClient()
        assert client.redis_url == "redis://localhost:6379"
        assert not client._connected

    def test_custom_redis_url(self) -> None:
        """Test client with custom Redis URL."""
        client = RegistryClient(redis_url="redis://custom:6379")
        assert client.redis_url == "redis://custom:6379"

    def test_register_agent(self) -> None:
        """Test agent registration creates correct AgentInfo."""
        client = RegistryClient()

        agent = client.register_agent(
            name="test-agent",
            category="backend",
            pid=1234,
            description="Test agent",
        )

        assert agent.name == "test-agent"
        assert agent.category == "backend"
        assert agent.status == "starting"
        assert agent.pid == 1234
        assert agent.description == "Test agent"
        assert agent.started_at is not None

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    def test_health_check_with_redis(self) -> None:
        """Test health check returns True when Redis is available."""
        client = RegistryClient()
        # If Redis is running, should return True
        result = client.health_check()
        assert isinstance(result, bool)

    def test_health_check_mocked(self) -> None:
        """Test health check with mocked Redis."""
        client = RegistryClient()

        # Mock the Redis client
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.smembers.return_value = set()
        client._redis_client = mock_redis
        client._connected = True

        assert client.health_check() is True

    def test_get_stats_structure(self) -> None:
        """Test statistics returns correct structure."""
        client = RegistryClient()

        # Mock to avoid actual Redis connection
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.smembers.return_value = set()
        client._redis_client = mock_redis
        client._connected = True

        stats = client.get_stats()

        assert "agent_count" in stats
        assert "active_count" in stats
        assert isinstance(stats["agent_count"], int)
        assert isinstance(stats["active_count"], int)

    def test_update_heartbeat_does_not_raise(self) -> None:
        """Test heartbeat update doesn't raise."""
        client = RegistryClient()

        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        client._redis_client = mock_redis
        client._connected = True

        # Should not raise
        client.update_heartbeat("test-agent")

    def test_get_agent_not_found(self) -> None:
        """Test getting non-existent agent returns None."""
        client = RegistryClient()

        # Mock Redis to return empty hash
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.hgetall.return_value = {}
        client._redis_client = mock_redis
        client._connected = True

        agent = client.get_agent("nonexistent")
        assert agent is None

    def test_list_agents_empty(self) -> None:
        """Test listing agents when none exist."""
        client = RegistryClient()

        # Mock Redis to return empty set
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.smembers.return_value = set()
        client._redis_client = mock_redis
        client._connected = True

        agents = client.list_agents()
        assert agents == []

    def test_list_agents_with_category_filter(self) -> None:
        """Test listing agents with category filter."""
        client = RegistryClient()

        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.smembers.return_value = {"agent1", "agent2"}
        mock_redis.hgetall.side_effect = [
            {"name": "agent1", "category": "backend", "status": "healthy"},
            {"name": "agent2", "category": "frontend", "status": "healthy"},
        ]
        client._redis_client = mock_redis
        client._connected = True

        # Filter by backend - should only return agent1
        agents = client.list_agents(category="backend")
        assert len(agents) == 1
        assert agents[0].name == "agent1"
        assert agents[0].category == "backend"

    def test_unregister_agent(self) -> None:
        """Test agent unregistration calls Redis delete."""
        client = RegistryClient()

        # Mock Redis
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        client._redis_client = mock_redis
        client._connected = True

        client.unregister_agent("test-agent")

        # Should have called delete and srem
        mock_redis.delete.assert_called_once_with("mycelium:agents:test-agent")
        mock_redis.srem.assert_called_once_with("mycelium:agent_names", "test-agent")


class TestRegistryClientIntegration:
    """Integration tests that require actual Redis - skipped if unavailable."""

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    def test_full_lifecycle(self) -> None:
        """Test full agent lifecycle with real Redis."""
        client = RegistryClient()

        # Skip if Redis not running
        if not client.health_check():
            pytest.skip("Redis not running")

        test_name = "test-integration-agent"

        try:
            # Register
            agent = client.register_agent(
                name=test_name,
                category="test",
                description="Integration test agent",
            )
            assert agent.name == test_name

            # Retrieve
            retrieved = client.get_agent(test_name)
            assert retrieved is not None
            assert retrieved.name == test_name

            # List
            agents = client.list_agents(category="test")
            assert any(a.name == test_name for a in agents)

        finally:
            # Cleanup
            client.unregister_agent(test_name)
