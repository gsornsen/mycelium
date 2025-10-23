# Source: projects/onboarding/milestones/M06_COORDINATION_TESTING.md
# Line: 281
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/fixtures/mcp_clients.py
"""Pytest fixtures for MCP client management."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

# Real MCP client imports
try:
    from mcp_redis import RedisClient
    from mcp_taskqueue import TaskQueueClient
    from mcp_temporal import TemporalClient
    HAS_REAL_MCP = True
except ImportError:
    HAS_REAL_MCP = False

USE_MOCK_MCP = os.getenv('USE_MOCK_MCP', 'false').lower() == 'true'

@pytest.fixture
async def redis_client() -> AsyncGenerator:
    """
    Provide Redis MCP client (mock or real based on environment).

    Set USE_MOCK_MCP=true to use mocks during development.
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock Redis client for development
        mock_client = AsyncMock()
        mock_client.publish = AsyncMock(return_value=1)
        mock_client.subscribe = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)

        yield mock_client
    else:
        # Real Redis client for CI/CD
        client = RedisClient(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
        )

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def taskqueue_client() -> AsyncGenerator:
    """
    Provide TaskQueue MCP client (mock or real based on environment).
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock TaskQueue client
        mock_client = AsyncMock()
        mock_client.create_project = AsyncMock(return_value={'project_id': 'proj-test-1'})
        mock_client.add_task = AsyncMock(return_value={'task_id': 'task-test-1'})
        mock_client.get_next_task = AsyncMock(return_value=None)

        yield mock_client
    else:
        # Real TaskQueue client
        client = TaskQueueClient()

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def temporal_client() -> AsyncGenerator:
    """
    Provide Temporal MCP client (mock or real based on environment).
    """
    if USE_MOCK_MCP or not HAS_REAL_MCP:
        # Mock Temporal client
        mock_client = AsyncMock()
        mock_client.start_workflow = AsyncMock(return_value={'workflow_id': 'wf-test-1'})
        mock_client.get_workflow_status = AsyncMock(return_value={'status': 'COMPLETED'})

        yield mock_client
    else:
        # Real Temporal client
        client = TemporalClient(
            host=os.getenv('TEMPORAL_HOST', 'localhost'),
            port=int(os.getenv('TEMPORAL_PORT', 7233)),
        )

        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

@pytest.fixture
async def mcp_clients(
    redis_client,
    taskqueue_client,
    temporal_client,
) -> dict:
    """Provide all MCP clients as dictionary."""
    return {
        'redis': redis_client,
        'taskqueue': taskqueue_client,
        'temporal': temporal_client,
    }

@pytest.fixture(autouse=True)
async def cleanup_test_data(mcp_clients):
    """Automatically cleanup test data after each test."""
    yield

    # Cleanup Redis test keys
    if not USE_MOCK_MCP and HAS_REAL_MCP:
        redis = mcp_clients['redis']
        test_keys = await redis.keys('test:*')
        if test_keys:
            await redis.delete(*test_keys)
