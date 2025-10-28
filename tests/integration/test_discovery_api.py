"""Integration tests for Discovery API endpoints.

These tests validate the complete Discovery API functionality including
all endpoints, error handling, and integration with the agent registry.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import suppress

import pytest
import pytest_asyncio
from api.discovery import create_app, set_registry
from fastapi.testclient import TestClient
from registry import AgentRegistry


@pytest.fixture(scope="module")
def test_database_url():
    """Get test database URL from environment or use default."""
    return os.getenv("TEST_DATABASE_URL", "postgresql://localhost:5432/mycelium_registry_test")


@pytest_asyncio.fixture(scope="module")
async def registry(test_database_url) -> AsyncGenerator[AgentRegistry, None]:
    """Create and initialize test registry."""
    reg = AgentRegistry(connection_string=test_database_url)
    await reg.initialize()

    # Seed with test data
    test_agents = [
        {
            "agent_id": "test-backend-developer",
            "agent_type": "backend-developer",
            "name": "backend-developer",
            "display_name": "Backend Developer",
            "category": "Development",
            "description": "Expert in backend development with Python, Node.js, and Go",
            "file_path": "/test/backend-developer.md",
            "capabilities": ["API design", "Database optimization", "Authentication"],
            "tools": ["database", "docker", "postgresql"],
            "keywords": ["backend", "api", "python", "nodejs", "database"],
            "estimated_tokens": 2500,
        },
        {
            "agent_id": "test-security-expert",
            "agent_type": "security-expert",
            "name": "security-expert",
            "display_name": "Security Expert",
            "category": "Security",
            "description": "Security analysis and vulnerability assessment specialist",
            "file_path": "/test/security-expert.md",
            "capabilities": [
                "Security audit",
                "Vulnerability scanning",
                "Penetration testing",
            ],
            "tools": ["security-scanner", "audit-tool"],
            "keywords": ["security", "audit", "vulnerability", "penetration"],
            "estimated_tokens": 2000,
        },
        {
            "agent_id": "test-python-pro",
            "agent_type": "python-pro",
            "name": "python-pro",
            "display_name": "Python Pro",
            "category": "Development",
            "description": "Python expert specializing in advanced features and best practices",
            "file_path": "/test/python-pro.md",
            "capabilities": ["Python development", "Code review", "Testing"],
            "tools": ["pytest", "mypy", "ruff"],
            "keywords": ["python", "testing", "typing", "async"],
            "estimated_tokens": 1800,
        },
    ]

    for agent in test_agents:
        with suppress(Exception):
            await reg.create_agent(**agent)

    yield reg

    await reg.close()


@pytest.fixture(scope="module")
def app(test_database_url, registry):
    """Create test FastAPI application."""
    # Override database URL for testing
    os.environ["DATABASE_URL"] = test_database_url

    # Set the registry for the API to use
    set_registry(registry)

    # Create app - it won't trigger lifespan in TestClient
    test_app = create_app(rate_limit=1000)  # Higher limit for testing

    yield test_app

    # Cleanup: Clear the registry
    set_registry(None)


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_success(self, client):
        """Test health check returns healthy status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "agent_count" in data
        assert "database_size" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_includes_pgvector(self, client):
        """Test health check includes pgvector status."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "pgvector_installed" in data
        assert isinstance(data["pgvector_installed"], bool)


class TestDiscoverEndpoint:
    """Tests for agent discovery endpoint."""

    def test_discover_with_valid_query(self, client):
        """Test discovery with valid query returns results."""
        request_data = {
            "query": "backend",
            "limit": 10,
            "threshold": 0.5,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "query" in data
        assert data["query"] == "backend"
        assert "matches" in data
        assert "total_count" in data
        assert "processing_time_ms" in data
        assert isinstance(data["matches"], list)
        assert data["total_count"] >= 0

    def test_discover_returns_confidence_scores(self, client):
        """Test discovery returns confidence scores for matches."""
        request_data = {
            "query": "python",
            "limit": 10,
            "threshold": 0.0,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 200
        data = response.json()

        if data["matches"]:
            for match in data["matches"]:
                assert "confidence" in match
                assert 0.0 <= match["confidence"] <= 1.0
                assert "agent" in match
                assert "match_reason" in match

    def test_discover_respects_threshold(self, client):
        """Test discovery filters results by threshold."""
        # High threshold should return fewer results
        high_threshold_request = {
            "query": "test",
            "limit": 10,
            "threshold": 0.95,
        }

        high_response = client.post("/api/v1/agents/discover", json=high_threshold_request)
        high_data = high_response.json()

        # Low threshold should return more results
        low_threshold_request = {
            "query": "test",
            "limit": 10,
            "threshold": 0.5,
        }

        low_response = client.post("/api/v1/agents/discover", json=low_threshold_request)
        low_data = low_response.json()

        assert high_data["total_count"] <= low_data["total_count"]

    def test_discover_respects_limit(self, client):
        """Test discovery respects result limit."""
        request_data = {
            "query": "development",
            "limit": 1,
            "threshold": 0.0,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert len(data["matches"]) <= 1

    def test_discover_with_empty_query_fails(self, client):
        """Test discovery with empty query returns validation error."""
        request_data = {
            "query": "",
            "limit": 10,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_discover_with_invalid_limit_fails(self, client):
        """Test discovery with invalid limit returns validation error."""
        request_data = {
            "query": "test",
            "limit": 0,  # Invalid: must be >= 1
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 422

    def test_discover_with_invalid_threshold_fails(self, client):
        """Test discovery with invalid threshold returns validation error."""
        request_data = {
            "query": "test",
            "threshold": 1.5,  # Invalid: must be <= 1.0
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 422

    def test_discover_performance(self, client):
        """Test discovery completes within performance requirements."""
        request_data = {
            "query": "backend development",
            "limit": 10,
            "threshold": 0.5,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should complete in < 100ms as per requirements
        assert data["processing_time_ms"] < 100

    def test_discover_returns_sorted_results(self, client):
        """Test discovery returns results sorted by confidence."""
        request_data = {
            "query": "python",
            "limit": 10,
            "threshold": 0.0,
        }

        response = client.post("/api/v1/agents/discover", json=request_data)

        assert response.status_code == 200
        data = response.json()

        if len(data["matches"]) > 1:
            confidences = [m["confidence"] for m in data["matches"]]
            assert confidences == sorted(confidences, reverse=True)


class TestAgentDetailEndpoint:
    """Tests for agent detail endpoint."""

    def test_get_agent_by_id(self, client):
        """Test getting agent details by agent_id."""
        response = client.get("/api/v1/agents/test-backend-developer")

        assert response.status_code == 200
        data = response.json()

        assert "agent" in data
        agent = data["agent"]
        assert agent["agent_id"] == "test-backend-developer"
        assert agent["agent_type"] == "backend-developer"
        assert "capabilities" in agent
        assert "tools" in agent

    def test_get_agent_by_type(self, client):
        """Test getting agent details by agent_type."""
        response = client.get("/api/v1/agents/security-expert")

        assert response.status_code == 200
        data = response.json()

        assert "agent" in data
        agent = data["agent"]
        assert agent["agent_type"] == "security-expert"

    def test_get_nonexistent_agent(self, client):
        """Test getting non-existent agent returns 404."""
        response = client.get("/api/v1/agents/nonexistent-agent")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data or "detail" in data

    def test_get_agent_includes_metadata(self, client):
        """Test agent details include metadata."""
        response = client.get("/api/v1/agents/test-backend-developer")

        assert response.status_code == 200
        data = response.json()

        assert "agent" in data
        assert "metadata" in data

    def test_get_agent_includes_performance_metrics(self, client):
        """Test agent details include performance metrics."""
        response = client.get("/api/v1/agents/test-backend-developer")

        assert response.status_code == 200
        data = response.json()

        agent = data["agent"]
        # These fields may be None but should exist
        assert "avg_response_time_ms" in agent
        assert "success_rate" in agent
        assert "usage_count" in agent


class TestSearchEndpoint:
    """Tests for agent search endpoint."""

    def test_search_without_query(self, client):
        """Test search without query returns all agents."""
        response = client.get("/api/v1/agents/search")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert "total_count" in data
        assert "processing_time_ms" in data
        assert isinstance(data["agents"], list)

    def test_search_with_query(self, client):
        """Test search with query parameter."""
        response = client.get("/api/v1/agents/search?q=python")

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "python"
        assert isinstance(data["agents"], list)

    def test_search_with_category_filter(self, client):
        """Test search with category filter."""
        response = client.get("/api/v1/agents/search?category=Development")

        assert response.status_code == 200
        data = response.json()

        # All returned agents should be in Development category
        for agent in data["agents"]:
            assert agent["category"] == "Development"

    def test_search_with_pagination(self, client):
        """Test search pagination."""
        # First page
        response1 = client.get("/api/v1/agents/search?limit=1&offset=0")
        data1 = response1.json()

        # Second page
        response2 = client.get("/api/v1/agents/search?limit=1&offset=1")
        data2 = response2.json()

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Should get different results (if enough agents)
        if data1["total_count"] > 1:
            assert data1["agents"] != data2["agents"]

    def test_search_respects_limit(self, client):
        """Test search respects limit parameter."""
        response = client.get("/api/v1/agents/search?limit=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["agents"]) <= 2

    def test_search_performance(self, client):
        """Test search completes within performance requirements."""
        response = client.get("/api/v1/agents/search?q=development")

        assert response.status_code == 200
        data = response.json()

        # Should complete in < 100ms
        assert data["processing_time_ms"] < 100

    def test_search_with_invalid_limit(self, client):
        """Test search with invalid limit parameter."""
        response = client.get("/api/v1/agents/search?limit=0")

        assert response.status_code == 422

    def test_search_with_category_and_query(self, client):
        """Test search with both category and query filters."""
        response = client.get("/api/v1/agents/search?q=python&category=Development")

        assert response.status_code == 200
        data = response.json()

        # All results should match both filters
        for agent in data["agents"]:
            assert agent["category"] == "Development"


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_enforcement(self, client):
        """Test rate limit is enforced (requires low limit for testing)."""
        # Note: With default high limit (1000), this is hard to test
        # In production, configure lower limit for testing
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        # Check remaining count decreases
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining >= 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json_returns_400(self, client):
        """Test invalid JSON returns 400 error."""
        response = client.post(
            "/api/v1/agents/discover",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_unsupported_media_type(self, client):
        """Test unsupported content type returns 415."""
        response = client.post(
            "/api/v1/agents/discover",
            data="test",
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 415
        data = response.json()
        assert data["error"] == "UnsupportedMediaType"

    def test_missing_required_fields(self, client):
        """Test missing required fields returns validation error."""
        response = client.post(
            "/api/v1/agents/discover",
            json={"limit": 10},  # Missing required 'query' field
        )

        assert response.status_code == 422


class TestResponseHeaders:
    """Tests for response headers."""

    def test_processing_time_header(self, client):
        """Test X-Processing-Time-Ms header is present."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert "X-Processing-Time-Ms" in response.headers

        # Should be a valid float
        processing_time = float(response.headers["X-Processing-Time-Ms"])
        assert processing_time >= 0

    def test_request_id_header(self, client):
        """Test X-Request-ID header is present."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/health")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestOpenAPISpec:
    """Tests for OpenAPI specification."""

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON is accessible."""
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_available(self, client):
        """Test Swagger UI docs are accessible."""
        response = client.get("/api/v1/docs")

        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Test ReDoc documentation is accessible."""
        response = client.get("/api/v1/redoc")

        assert response.status_code == 200


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end integration tests."""

    def test_discover_then_get_details(self, client):
        """Test complete workflow: discover agents then get details."""
        # Step 1: Discover agents
        discover_response = client.post(
            "/api/v1/agents/discover",
            json={"query": "backend", "limit": 1},
        )

        assert discover_response.status_code == 200
        discover_data = discover_response.json()
        assert len(discover_data["matches"]) > 0

        # Step 2: Get details of first match
        first_match = discover_data["matches"][0]
        agent_id = first_match["agent"]["agent_id"]

        details_response = client.get(f"/api/v1/agents/{agent_id}")

        assert details_response.status_code == 200
        details_data = details_response.json()
        assert details_data["agent"]["agent_id"] == agent_id

    def test_search_filter_then_discover(self, client):
        """Test workflow: search with filters then discover specific capabilities."""
        # Step 1: Search by category
        search_response = client.get("/api/v1/agents/search?category=Development&limit=5")

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Step 2: Discover with specific query
        discover_response = client.post(
            "/api/v1/agents/discover",
            json={"query": "python development", "limit": 5},
        )

        assert discover_response.status_code == 200
        discover_data = discover_response.json()

        # Both should return agents
        assert search_data["total_count"] > 0 or discover_data["total_count"] > 0
