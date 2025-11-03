"""Pytest configuration for integration tests."""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

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
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for module-scoped async fixtures.

    This fixture ensures that module-scoped async fixtures (like the
    discovery API test fixtures) have a proper event loop that persists
    for the entire module test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Clean up pending tasks
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass

    loop.close()
