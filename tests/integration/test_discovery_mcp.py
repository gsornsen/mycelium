"""Integration tests for Discovery MCP tools.

These tests validate end-to-end functionality of the MCP tool wrappers,
including interaction with the Discovery API.
"""

import asyncio
import json
import os
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from plugins.mycelium_core.mcp.tools.discovery_tools import (
    DiscoveryAPIError,
    DiscoveryTimeoutError,
    DiscoveryToolError,
    check_discovery_health,
    discover_agents,
    dispatch_tool,
    get_agent_details,
)


class TestDiscoverAgents:
    """Tests for discover_agents MCP tool."""

    @pytest.mark.asyncio
    async def test_discover_agents_success(self, mock_discovery_api):
        """Test successful agent discovery."""
        result = await discover_agents(
            query="Python backend development",
            limit=3,
            threshold=0.7,
        )

        assert result["success"] is True
        assert result["query"] == "Python backend development"
        assert len(result["agents"]) > 0
        assert result["total_count"] >= len(result["agents"])
        assert "processing_time_ms" in result

        # Validate agent structure
        agent = result["agents"][0]
        assert "id" in agent
        assert "type" in agent
        assert "name" in agent
        assert "description" in agent
        assert "capabilities" in agent
        assert "confidence" in agent
        assert "match_reason" in agent
        assert isinstance(agent["confidence"], float)
        assert 0.0 <= agent["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_discover_agents_with_defaults(self, mock_discovery_api):
        """Test discover_agents with default parameters."""
        result = await discover_agents(query="database optimization")

        assert result["success"] is True
        assert len(result["agents"]) <= 5  # Default limit
        assert all(a["confidence"] >= 0.6 for a in result["agents"])  # Default threshold

    @pytest.mark.asyncio
    async def test_discover_agents_empty_query_fails(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await discover_agents(query="")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await discover_agents(query="   ")

    @pytest.mark.asyncio
    async def test_discover_agents_invalid_limit(self):
        """Test that invalid limit raises ValueError."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 20"):
            await discover_agents(query="test", limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 20"):
            await discover_agents(query="test", limit=21)

    @pytest.mark.asyncio
    async def test_discover_agents_invalid_threshold(self):
        """Test that invalid threshold raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            await discover_agents(query="test", threshold=-0.1)

        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            await discover_agents(query="test", threshold=1.1)

    @pytest.mark.asyncio
    async def test_discover_agents_api_error(self, mock_api_error):
        """Test handling of API errors."""
        with pytest.raises(DiscoveryAPIError, match="Server error"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_discover_agents_timeout(self, mock_api_timeout):
        """Test handling of timeout errors."""
        with pytest.raises(DiscoveryTimeoutError, match="timed out"):
            await discover_agents(query="test", timeout=0.1)

    @pytest.mark.asyncio
    async def test_discover_agents_retry_logic(self, mock_api_retry):
        """Test retry logic on transient failures."""
        # Should succeed after retries
        result = await discover_agents(query="test")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_discover_agents_no_matches(self, mock_discovery_api_no_results):
        """Test handling of queries with no matches."""
        result = await discover_agents(
            query="very specific nonexistent capability",
            threshold=0.99,
        )

        assert result["success"] is True
        assert result["agents"] == []
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_discover_agents_performance(self, mock_discovery_api):
        """Test that discover_agents meets performance requirements."""
        import time

        start = time.time()
        result = await discover_agents(query="test")
        elapsed_ms = (time.time() - start) * 1000

        # End-to-end should be under 500ms
        assert elapsed_ms < 500
        assert result["success"] is True


class TestGetAgentDetails:
    """Tests for get_agent_details MCP tool."""

    @pytest.mark.asyncio
    async def test_get_agent_details_success(self, mock_discovery_api):
        """Test successful agent details retrieval."""
        result = await get_agent_details(agent_id="backend-developer")

        assert result["success"] is True
        assert result["agent"]["id"] == "backend-developer"
        assert "type" in result["agent"]
        assert "name" in result["agent"]
        assert "description" in result["agent"]
        assert "capabilities" in result["agent"]
        assert "tools" in result["agent"]
        assert "keywords" in result["agent"]
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_get_agent_details_by_type(self, mock_discovery_api):
        """Test retrieval by agent type."""
        result = await get_agent_details(agent_id="01-core-backend-developer")

        assert result["success"] is True
        assert result["agent"]["type"] == "backend-developer"

    @pytest.mark.asyncio
    async def test_get_agent_details_empty_id_fails(self):
        """Test that empty agent_id raises ValueError."""
        with pytest.raises(ValueError, match="Agent ID cannot be empty"):
            await get_agent_details(agent_id="")

        with pytest.raises(ValueError, match="Agent ID cannot be empty"):
            await get_agent_details(agent_id="   ")

    @pytest.mark.asyncio
    async def test_get_agent_details_not_found(self, mock_api_not_found):
        """Test handling of agent not found errors."""
        with pytest.raises(DiscoveryAPIError, match="not found"):
            await get_agent_details(agent_id="nonexistent-agent")

    @pytest.mark.asyncio
    async def test_get_agent_details_timeout(self, mock_api_timeout):
        """Test handling of timeout errors."""
        with pytest.raises(DiscoveryTimeoutError, match="timed out"):
            await get_agent_details(agent_id="test", timeout=0.1)

    @pytest.mark.asyncio
    async def test_get_agent_details_with_metadata(self, mock_discovery_api_with_metadata):
        """Test that metadata is properly included."""
        result = await get_agent_details(agent_id="backend-developer")

        assert result["success"] is True
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)


class TestCheckDiscoveryHealth:
    """Tests for check_discovery_health utility."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_health_api):
        """Test successful health check."""
        result = await check_discovery_health()

        assert result["success"] is True
        assert result["status"] == "healthy"
        assert "agent_count" in result
        assert "database_size" in result
        assert result["agent_count"] > 0

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_health_api_unhealthy):
        """Test handling of unhealthy API."""
        result = await check_discovery_health()

        assert result["success"] is False
        assert result["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, mock_api_timeout):
        """Test health check timeout."""
        with pytest.raises(DiscoveryTimeoutError):
            await check_discovery_health(timeout=0.1)


class TestToolDispatcher:
    """Tests for MCP tool dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatch_discover_agents(self, mock_discovery_api):
        """Test dispatching discover_agents tool."""
        result = await dispatch_tool(
            "discover_agents",
            {"query": "test", "limit": 3, "threshold": 0.7},
        )

        assert result["success"] is True
        assert "agents" in result

    @pytest.mark.asyncio
    async def test_dispatch_get_agent_details(self, mock_discovery_api):
        """Test dispatching get_agent_details tool."""
        result = await dispatch_tool(
            "get_agent_details",
            {"agent_id": "backend-developer"},
        )

        assert result["success"] is True
        assert "agent" in result

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self):
        """Test that unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await dispatch_tool("unknown_tool", {})


# Fixtures

@pytest.fixture
def mock_discovery_api(monkeypatch):
    """Mock the Discovery API with successful responses."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
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
        }
        return response

    async def mock_get(*args, **kwargs):
        url = args[0]
        response = Mock()
        if "/health" in url:
            response.status_code = 200
            response.json.return_value = {
                "status": "healthy",
                "agent_count": 130,
                "database_size": 1024000,
                "pgvector_installed": True,
                "timestamp": "2025-10-21T12:00:00Z",
            }
        else:
            response.status_code = 200
            response.json.return_value = {
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
            }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_discovery_api_no_results(monkeypatch):
    """Mock API with no results."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "query": "test",
            "matches": [],
            "total_count": 0,
            "processing_time_ms": 50,
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_discovery_api_with_metadata(monkeypatch):
    """Mock API with metadata included."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "agent": {
                "agent_id": "backend-developer",
                "agent_type": "backend-developer",
                "name": "Backend Developer",
                "display_name": "Backend Developer",
                "category": "core",
                "description": "Backend expert",
                "capabilities": [],
                "tools": [],
                "keywords": [],
                "file_path": "/path/to/agent.md",
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
            },
            "metadata": {
                "dependencies": ["python-pro"],
                "examples": ["Build REST API"],
            },
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_api_error(monkeypatch):
    """Mock API error response."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 500
        response.json.return_value = {
            "error": "ServerError",
            "message": "Internal server error",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_api_not_found(monkeypatch):
    """Mock API not found response."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 404
        response.json.return_value = {
            "error": "NotFound",
            "message": "Agent not found",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_api_timeout(monkeypatch):
    """Mock API timeout."""

    async def mock_request(*args, **kwargs):
        raise httpx.TimeoutException("Request timed out")

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_request
        mock_client.return_value.__aenter__.return_value.get = mock_request
        yield mock_client


@pytest.fixture
def mock_api_retry(monkeypatch):
    """Mock API that fails once then succeeds."""
    call_count = {"count": 0}

    async def mock_post(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise httpx.HTTPError("Temporary error")

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "query": "test",
            "matches": [],
            "total_count": 0,
            "processing_time_ms": 50,
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_health_api(monkeypatch):
    """Mock health check API."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "status": "healthy",
            "agent_count": 130,
            "database_size": 1024000,
            "pgvector_installed": True,
            "timestamp": "2025-10-21T12:00:00Z",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_health_api_unhealthy(monkeypatch):
    """Mock unhealthy API."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 503
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


class TestErrorPaths:
    """Additional tests for error handling paths."""

    @pytest.mark.asyncio
    async def test_discover_agents_json_decode_error(self, mock_api_invalid_json):
        """Test handling of invalid JSON response."""
        with pytest.raises(DiscoveryAPIError, match="Invalid JSON"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_discover_agents_400_error(self, mock_api_400_error):
        """Test handling of 400 bad request."""
        with pytest.raises(DiscoveryAPIError, match="Invalid request"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_discover_agents_404_error(self, mock_api_404_error):
        """Test handling of 404 endpoint not found."""
        with pytest.raises(DiscoveryAPIError, match="not found"):
            await discover_agents(query="test")

    @pytest.mark.asyncio
    async def test_get_agent_details_400_error(self, mock_api_400_error_get):
        """Test handling of 400 for get_agent_details."""
        with pytest.raises(DiscoveryAPIError, match="Invalid request"):
            await get_agent_details(agent_id="test")

    @pytest.mark.asyncio
    async def test_get_agent_details_500_error(self, mock_api_500_error_get):
        """Test handling of 500 for get_agent_details."""
        with pytest.raises(DiscoveryAPIError, match="Server error"):
            await get_agent_details(agent_id="test")

    @pytest.mark.asyncio
    async def test_get_agent_details_json_decode_error(self, mock_api_invalid_json_get):
        """Test handling of invalid JSON in get_agent_details."""
        with pytest.raises(DiscoveryAPIError, match="Invalid JSON"):
            await get_agent_details(agent_id="test")

    @pytest.mark.asyncio
    async def test_health_check_http_error(self, mock_health_api_http_error):
        """Test health check with HTTP error."""
        with pytest.raises(DiscoveryAPIError, match="Health check failed"):
            await check_discovery_health()

    @pytest.mark.asyncio
    async def test_health_check_generic_error(self, mock_health_api_generic_error):
        """Test health check with generic error."""
        with pytest.raises(DiscoveryToolError, match="Unexpected error"):
            await check_discovery_health()


# Additional fixtures for error paths

@pytest.fixture
def mock_api_invalid_json(monkeypatch):
    """Mock API with invalid JSON response."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_api_400_error(monkeypatch):
    """Mock API 400 error."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "error": "ValidationError",
            "message": "Invalid request parameters",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_api_404_error(monkeypatch):
    """Mock API 404 error."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 404
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = mock_post
        yield mock_client


@pytest.fixture
def mock_api_400_error_get(monkeypatch):
    """Mock API 400 error for GET."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 400
        response.json.return_value = {
            "error": "ValidationError",
            "message": "Invalid agent ID",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_api_500_error_get(monkeypatch):
    """Mock API 500 error for GET."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 500
        response.json.return_value = {
            "error": "ServerError",
            "message": "Internal server error",
        }
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_api_invalid_json_get(monkeypatch):
    """Mock API with invalid JSON for GET."""

    async def mock_get(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        return response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_health_api_http_error(monkeypatch):
    """Mock health API with HTTP error."""

    async def mock_get(*args, **kwargs):
        raise httpx.HTTPError("Connection failed")

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client


@pytest.fixture
def mock_health_api_generic_error(monkeypatch):
    """Mock health API with generic error."""

    async def mock_get(*args, **kwargs):
        raise RuntimeError("Unexpected error")

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = mock_get
        yield mock_client
