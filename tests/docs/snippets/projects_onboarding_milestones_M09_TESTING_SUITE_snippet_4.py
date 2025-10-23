# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 771
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/conftest.py
"""Shared pytest fixtures for all tests."""

import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

from mycelium.config import MyceliumConfig, ServicesConfig, RedisConfig, PostgresConfig


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Provide temporary project directory with standard structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create standard directories
    (project_dir / ".mycelium").mkdir()
    (project_dir / "deployment").mkdir()

    return project_dir


@pytest.fixture
def sample_config() -> MyceliumConfig:
    """Provide sample valid configuration for testing."""
    return MyceliumConfig(
        services=ServicesConfig(
            redis=RedisConfig(
                enabled=True,
                port=6379,
                max_memory=512,
                persistence=True
            ),
            postgres=PostgresConfig(
                enabled=True,
                port=5432,
                database="mycelium",
                max_connections=100
            )
        )
    )


@pytest.fixture
def mock_detection_results() -> Mock:
    """Provide mock detection results."""
    return Mock(
        redis=Mock(available=True, method="docker", port=6379),
        postgres=Mock(available=True, method="docker", port=5432),
        docker=Mock(available=True, version="24.0.0"),
        taskqueue=Mock(available=False),
        temporal=Mock(available=False),
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Clear any cached singleton state
    from mycelium.config import ConfigManager
    ConfigManager._instance = None

    yield

    # Cleanup after test
    ConfigManager._instance = None


@pytest.fixture
def mock_docker_client() -> Generator[Mock, None, None]:
    """Provide mocked Docker client."""
    mock_client = Mock()
    mock_client.containers.list.return_value = []
    mock_client.images.list.return_value = []

    yield mock_client

    mock_client.close()


# Mark slow tests
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )