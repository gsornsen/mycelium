"""Unit tests for Mycelium API endpoints.

Tests all API endpoints including health check, agent listing,
agent details, and categories.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from mycelium.api.app import create_app
from mycelium.registry.client import AgentInfo


@pytest.fixture
def mock_registry():
    """Create a mock registry client."""
    registry = Mock()

    # Mock agents for testing
    mock_agents = [
        AgentInfo(
            name="backend-engineer",
            category="backend",
            status="healthy",
            pid=12345,
            port=8000,
            description="Backend development specialist",
            last_heartbeat="2024-11-28T10:00:00Z",
            started_at="2024-11-28T09:00:00Z",
        ),
        AgentInfo(
            name="frontend-developer",
            category="frontend",
            status="healthy",
            pid=12346,
            port=8001,
            description="Frontend development specialist",
            last_heartbeat="2024-11-28T10:00:00Z",
            started_at="2024-11-28T09:00:00Z",
        ),
        AgentInfo(
            name="devops-engineer",
            category="infrastructure",
            status="starting",
            pid=12347,
            port=None,
            description="DevOps specialist",
            last_heartbeat=None,
            started_at="2024-11-28T09:30:00Z",
        ),
    ]

    registry.list_agents.return_value = mock_agents
    registry.get_agent.side_effect = lambda name: next((a for a in mock_agents if a.name == name), None)
    registry.health_check.return_value = True
    registry.get_stats.return_value = {
        "agent_count": 3,
        "active_count": 2,
    }

    return registry


@pytest.fixture
def client(mock_registry):
    """Create a test client with mocked registry."""
    with patch("mycelium.api.app.RegistryClient", return_value=mock_registry):
        app = create_app()
        # Create a fresh client for each test to avoid rate limiting issues
        return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_check_healthy(self, client):
        """Test health check when registry is healthy."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["registry_connected"] is True
        assert data["agent_count"] == 3
        assert data["active_count"] == 2

    def test_health_check_unhealthy(self, client, mock_registry):
        """Test health check when registry is unhealthy."""
        mock_registry.health_check.return_value = False

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["registry_connected"] is False

    def test_health_check_exception(self, client, mock_registry):
        """Test health check when registry raises exception."""
        mock_registry.health_check.side_effect = Exception("Redis connection failed")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["registry_connected"] is False


class TestAgentsListEndpoint:
    """Tests for /api/v1/agents endpoint."""

    def test_list_all_agents(self, client):
        """Test listing all agents without filter."""
        response = client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["agents"]) == 3
        assert data["category"] is None

        # Check agent data structure
        agent = data["agents"][0]
        assert "name" in agent
        assert "category" in agent
        assert "status" in agent

    def test_list_agents_by_category(self, client, mock_registry):
        """Test listing agents filtered by category."""
        # Mock filtered response
        mock_registry.list_agents.return_value = [
            AgentInfo(
                name="backend-engineer",
                category="backend",
                status="healthy",
                pid=12345,
                port=8000,
                description="Backend development specialist",
                last_heartbeat="2024-11-28T10:00:00Z",
                started_at="2024-11-28T09:00:00Z",
            ),
        ]

        response = client.get("/api/v1/agents?category=backend")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["category"] == "backend"
        assert data["agents"][0]["category"] == "backend"

    def test_list_agents_empty(self, client, mock_registry):
        """Test listing agents when registry is empty."""
        mock_registry.list_agents.return_value = []

        response = client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["agents"]) == 0

    def test_list_agents_registry_error(self, client, mock_registry):
        """Test listing agents when registry fails."""
        mock_registry.list_agents.side_effect = Exception("Registry unavailable")

        response = client.get("/api/v1/agents")

        assert response.status_code == 503
        assert "Registry unavailable" in response.json()["detail"]


class TestAgentDetailsEndpoint:
    """Tests for /api/v1/agents/{name} endpoint."""

    def test_get_agent_exists(self, client):
        """Test getting details for an existing agent."""
        response = client.get("/api/v1/agents/backend-engineer")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "backend-engineer"
        assert data["category"] == "backend"
        assert data["status"] == "healthy"
        assert data["pid"] == 12345
        assert data["port"] == 8000
        assert data["description"] == "Backend development specialist"

    def test_get_agent_not_found(self, client):
        """Test getting details for non-existent agent."""
        response = client.get("/api/v1/agents/non-existent-agent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_agent_registry_error(self, client, mock_registry):
        """Test getting agent when registry fails."""
        mock_registry.get_agent.side_effect = Exception("Registry unavailable")

        response = client.get("/api/v1/agents/backend-engineer")

        assert response.status_code == 503
        assert "Registry unavailable" in response.json()["detail"]


class TestCategoriesEndpoint:
    """Tests for /api/v1/categories endpoint."""

    def test_list_categories(self, client):
        """Test listing all categories."""
        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["categories"]) == 3

        # Check categories are sorted
        categories = [cat["name"] for cat in data["categories"]]
        assert categories == sorted(categories)

        # Check category counts
        backend_cat = next(c for c in data["categories"] if c["name"] == "backend")
        assert backend_cat["agent_count"] == 1

    def test_list_categories_empty(self, client, mock_registry):
        """Test listing categories when no agents exist."""
        mock_registry.list_agents.return_value = []

        response = client.get("/api/v1/categories")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["categories"]) == 0

    def test_list_categories_registry_error(self, client, mock_registry):
        """Test listing categories when registry fails."""
        mock_registry.list_agents.side_effect = Exception("Registry unavailable")

        response = client.get("/api/v1/categories")

        assert response.status_code == 503
        assert "Registry unavailable" in response.json()["detail"]


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_applied(self, mock_registry):
        """Test that rate limiting is configured on endpoints."""
        # Create a fresh app to test rate limiting
        with patch("mycelium.api.app.RegistryClient", return_value=mock_registry):
            app = create_app()
            test_client = TestClient(app, raise_server_exceptions=False)

            # First request should succeed
            response = test_client.get("/api/v1/agents")
            assert response.status_code == 200

            # The rate limiter is configured - we just verify it's present
            # Testing actual rate limiting would require making 100+ requests
            # which is impractical for unit tests

    def test_rate_limit_configuration(self, mock_registry):
        """Test that rate limit configuration is applied to app."""
        with patch("mycelium.api.app.RegistryClient", return_value=mock_registry):
            app = create_app()

            # Verify rate limiter is attached to app state
            assert hasattr(app.state, "limiter")
            assert app.state.limiter is not None


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_localhost_allowed(self, client):
        """Test that localhost origins are allowed."""
        response = client.get("/api/v1/health", headers={"Origin": "http://localhost:8080"})

        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_options_request(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/v1/agents",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Preflight should succeed
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation endpoints."""

    def test_swagger_ui_available(self, client):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_available(self, client):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")

        assert response.status_code == 200

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert schema["openapi"] == "3.1.0"
        assert "paths" in schema
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/agents" in schema["paths"]
        assert "/api/v1/categories" in schema["paths"]
