# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 934
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/fixtures/mcp_fixtures.py
"""Mock fixtures for MCP server interactions."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
async def mock_redis_mcp() -> AsyncGenerator[AsyncMock, None]:
    """Provide mocked Redis MCP client."""
    mock_client = AsyncMock()

    # Mock common Redis operations
    mock_client.hset = AsyncMock(return_value=1)
    mock_client.hget = AsyncMock(return_value=b"mocked_value")
    mock_client.hdel = AsyncMock(return_value=1)
    mock_client.hgetall = AsyncMock(return_value={b"key": b"value"})
    mock_client.publish = AsyncMock(return_value=1)
    mock_client.subscribe = AsyncMock()

    yield mock_client

    # Cleanup
    await mock_client.close()


@pytest.fixture
async def mock_taskqueue_mcp() -> AsyncGenerator[AsyncMock, None]:
    """Provide mocked TaskQueue MCP client."""
    mock_client = AsyncMock()

    # Mock task queue operations
    mock_client.create_project = AsyncMock(return_value={"project_id": "proj-1"})
    mock_client.add_tasks_to_project = AsyncMock(return_value={"task_ids": ["task-1"]})
    mock_client.get_next_task = AsyncMock(return_value={
        "task_id": "task-1",
        "title": "Test Task",
        "status": "not started"
    })
    mock_client.update_task = AsyncMock(return_value={"status": "completed"})

    yield mock_client


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Provide mocked subprocess.run for system command tests."""
    mock_run = Mock()
    mock_run.return_value = Mock(
        returncode=0,
        stdout="mocked output",
        stderr=""
    )

    monkeypatch.setattr("subprocess.run", mock_run)

    return mock_run
