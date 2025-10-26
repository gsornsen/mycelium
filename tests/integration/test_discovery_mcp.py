"""Integration tests for FastMCP-based discovery tools.

Simplified test suite using Pydantic models and reduced fixture complexity.
"""

from unittest.mock import Mock

import httpx
import pytest
from mcp.models import (
    AgentDetails,
    AgentMatch,
    DiscoverAgentsResponse,
    GetAgentDetailsResponse,
    HealthCheckResponse,
)
from mcp.tools.discovery_tools import (
    DiscoveryAPIError,
    DiscoveryTimeoutError,
    check_discovery_health,
    close_http_client,
    discover_agents,
    get_agent_details,
)


class TestDiscoverAgents:
    """Tests for discover_agents MCP tool."""

    @pytest.mark.asyncio
    async def test_discover_agents_success(self, mock_discovery_response):
        """Test successful agent discovery."""
        result = await discover_agents(
            query="Python backend development",
            limit=3,
            threshold=0.7,
        )

        assert isinstance(result, DiscoverAgentsResponse)
        assert result.success is True
        assert result.query == "Python backend development"
        assert len(result.agents) > 0
        assert result.total_count >= len(result.agents)

        # Validate Pydantic model
        agent = result.agents[0]
        assert isinstance(agent, AgentMatch)
        assert 0.0 <= agent.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_discover_agents_with_defaults(self, mock_discovery_response):
        """Test discover_agents with default parameters."""
        result = await discover_agents(query="database optimization")

        assert result.success is True
        assert len(result.agents) <= 5  # Default limit

    @pytest.mark.asyncio
    async def test_discover_agents_validation_errors(self):
        """Test Pydantic validation catches invalid inputs."""
        # Empty query
        with pytest.raises(Exception):  # Pydantic ValidationError
            await discover_agents(query="")

        # Invalid limit
        with pytest.raises(Exception):
            await discover_agents(query="test", limit=0)

        # Invalid threshold
        with pytest.raises(Exception):
            await discover_agents(query="test", threshold=1.5)

    @pytest.mark.asyncio
    async def test_discover_agents_api_error(self, mock_api_500):
        """Test handling of API errors."""
        with pytest.raises(DiscoveryAPIError, match="Server error"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_discover_agents_timeout(self, mock_timeout):
        """Test handling of timeout errors."""
        with pytest.raises(DiscoveryTimeoutError, match="timed out"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_discover_agents_retry_success(self, mock_retry_then_success):
        """Test retry logic succeeds after transient failure."""
        result = await discover_agents(query="test")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_discover_agents_no_matches(self, mock_no_results):
        """Test handling of queries with no matches."""
        result = await discover_agents(query="nonexistent capability")

        assert result.success is True
        assert result.agents == []
        assert result.total_count == 0


class TestGetAgentDetails:
    """Tests for get_agent_details MCP tool."""

    @pytest.mark.asyncio
    async def test_get_agent_details_success(self, mock_agent_details):
        """Test successful agent details retrieval."""
        result = await get_agent_details(agent_id="backend-developer")

        assert isinstance(result, GetAgentDetailsResponse)
        assert result.success is True
        assert isinstance(result.agent, AgentDetails)
        assert result.agent.id == "backend-developer"
        assert "metadata" in result.model_dump()

    @pytest.mark.asyncio
    async def test_get_agent_details_validation(self):
        """Test Pydantic validation for agent_id."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            await get_agent_details(agent_id="")

    @pytest.mark.asyncio
    async def test_get_agent_details_not_found(self, mock_404):
        """Test handling of agent not found errors."""
        with pytest.raises(DiscoveryAPIError, match="not found"):
            await get_agent_details(agent_id="nonexistent-agent")

    @pytest.mark.asyncio
    async def test_get_agent_details_timeout(self, mock_timeout):
        """Test handling of timeout errors."""
        with pytest.raises(DiscoveryTimeoutError, match="timed out"):
            await get_agent_details(agent_id="test")


class TestCheckDiscoveryHealth:
    """Tests for check_discovery_health utility."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_health_ok):
        """Test successful health check."""
        result = await check_discovery_health()

        assert isinstance(result, HealthCheckResponse)
        assert result.success is True
        assert result.status == "healthy"
        assert result.agent_count is not None

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_health_error):
        """Test handling of unhealthy API."""
        result = await check_discovery_health()

        assert result.success is False
        assert result.status == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, mock_timeout):
        """Test health check timeout."""
        with pytest.raises(DiscoveryTimeoutError):
            await check_discovery_health()


# Simplified fixtures using pytest-asyncio


@pytest.fixture(autouse=True)
async def cleanup_client():
    """Cleanup HTTP client after each test."""
    yield
    await close_http_client()


@pytest.fixture
def mock_discovery_response(monkeypatch):
    """Mock successful discovery API response."""

    async def mock_post(self, url, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "query": "Python backend development",
                "matches": [
                    {
                        "agent": {
                            "agent_id": "backend-developer",
                            "agent_type": "backend-developer",
                            "name": "Backend Developer",
                            "display_name": "Backend Developer",
                            "category": "core",
                            "description": "Full-stack backend development expert",
                            "capabilities": ["API development", "Database design"],
                            "tools": ["FastAPI", "PostgreSQL"],
                            "keywords": ["backend", "api", "database"],
                            "estimated_tokens": 5000,
                            "avg_response_time_ms": 200,
                        },
                        "confidence": 0.95,
                        "match_reason": "exact match on keywords",
                    }
                ],
                "total_count": 1,
                "processing_time_ms": 85,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)


@pytest.fixture
def mock_agent_details(monkeypatch):
    """Mock successful agent details response."""

    async def mock_get(self, url, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "agent": {
                    "agent_id": "backend-developer",
                    "agent_type": "backend-developer",
                    "name": "Backend Developer",
                    "display_name": "Backend Developer",
                    "category": "core",
                    "description": "Full-stack backend development expert",
                    "capabilities": ["API development"],
                    "tools": ["FastAPI"],
                    "keywords": ["backend"],
                    "file_path": "/path/to/agent.md",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
                "metadata": {},
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_no_results(monkeypatch):
    """Mock API with no results."""

    async def mock_post(self, url, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "query": "test",
                "matches": [],
                "total_count": 0,
                "processing_time_ms": 50,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)


@pytest.fixture
def mock_api_500(monkeypatch):
    """Mock API 500 error."""

    async def mock_post(self, url, **kwargs):
        return Mock(
            status_code=500,
            json=lambda: {"error": "ServerError", "message": "Internal server error"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)


@pytest.fixture
def mock_404(monkeypatch):
    """Mock API 404 error."""

    async def mock_get(self, url, **kwargs):
        return Mock(
            status_code=404,
            json=lambda: {"error": "NotFound", "message": "Agent not found"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_timeout(monkeypatch):
    """Mock API timeout."""

    async def mock_request(self, *args, **kwargs):
        raise httpx.TimeoutException("Request timed out")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_request)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_request)


@pytest.fixture
def mock_retry_then_success(monkeypatch):
    """Mock API that fails once then succeeds."""
    call_count = {"count": 0}

    async def mock_post(self, url, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise httpx.HTTPError("Temporary error")

        return Mock(
            status_code=200,
            json=lambda: {
                "query": "test",
                "matches": [],
                "total_count": 0,
                "processing_time_ms": 50,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)


@pytest.fixture
def mock_health_ok(monkeypatch):
    """Mock healthy API response."""

    async def mock_get(self, url, **kwargs):
        return Mock(
            status_code=200,
            json=lambda: {
                "status": "healthy",
                "agent_count": 130,
                "database_size": 1024000,
                "pgvector_installed": True,
                "timestamp": "2025-10-21T12:00:00Z",
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)


@pytest.fixture
def mock_health_error(monkeypatch):
    """Mock unhealthy API response."""

    async def mock_get(self, url, **kwargs):
        return Mock(status_code=503)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
