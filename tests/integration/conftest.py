"""Pytest configuration for integration tests."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from registry import AgentRegistry


@pytest.fixture(scope="session")
def database_url():
    """Get database URL for tests."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test",
    )


@pytest_asyncio.fixture(scope="function")
async def registry(database_url) -> AsyncGenerator[AgentRegistry, None]:
    """Create AgentRegistry instance for tests."""
    reg = AgentRegistry(connection_string=database_url)
    await reg.initialize()
    yield reg
    await reg.close()


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
