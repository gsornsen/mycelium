# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 1098
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/unit/test_config_validation.py
"""Parametrized tests for configuration validation."""

import pytest
from mycelium.config import RedisConfig
from pydantic import ValidationError


@pytest.mark.parametrize("port,should_pass", [
    (1024, True),      # Valid: lower bound
    (6379, True),      # Valid: standard
    (65535, True),     # Valid: upper bound
    (0, False),        # Invalid: too low
    (70000, False),    # Invalid: too high
    (-1, False),       # Invalid: negative
])
def test_redis_port_validation(port: int, should_pass: bool):
    """Test Redis port validation with various inputs."""
    if should_pass:
        config = RedisConfig(enabled=True, port=port)
        assert config.port == port
    else:
        with pytest.raises(ValidationError):
            RedisConfig(enabled=True, port=port)


@pytest.mark.parametrize("max_memory,should_pass", [
    (128, True),       # Valid: minimum
    (512, True),       # Valid: standard
    (4096, True),      # Valid: large
    (0, False),        # Invalid: zero
    (-100, False),     # Invalid: negative
])
def test_redis_memory_validation(max_memory: int, should_pass: bool):
    """Test Redis max_memory validation with various inputs."""
    if should_pass:
        config = RedisConfig(enabled=True, max_memory=max_memory)
        assert config.max_memory == max_memory
    else:
        with pytest.raises(ValidationError):
            RedisConfig(enabled=True, max_memory=max_memory)
