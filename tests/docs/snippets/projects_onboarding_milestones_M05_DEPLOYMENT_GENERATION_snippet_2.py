# Source: projects/onboarding/milestones/M05_DEPLOYMENT_GENERATION.md
# Line: 411
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/test_docker_compose_generator.py
"""Tests for Docker Compose generator."""

import yaml
from mycelium_onboarding.generators.docker_compose import DockerComposeGenerator

from mycelium_onboarding.config.schema import MyceliumConfig


def test_generate_valid_yaml():
    """Generated content should be valid YAML."""
    config = MyceliumConfig()  # Default config
    generator = DockerComposeGenerator()

    content = generator.generate(config)

    # Should parse without errors
    parsed = yaml.safe_load(content)
    assert 'version' in parsed
    assert 'services' in parsed

def test_redis_service_included_when_enabled():
    """Redis service should be included when enabled."""
    config = MyceliumConfig()
    config.services.redis.enabled = True

    generator = DockerComposeGenerator()
    content = generator.generate(config)
    parsed = yaml.safe_load(content)

    assert 'redis' in parsed['services']
    assert parsed['services']['redis']['image'].startswith('redis:')

def test_healthchecks_included():
    """All services should have healthchecks."""
    config = MyceliumConfig()
    config.services.redis.enabled = True
    config.services.postgres.enabled = True

    generator = DockerComposeGenerator()
    content = generator.generate(config)
    parsed = yaml.safe_load(content)

    for service_name in ['redis', 'postgres']:
        assert 'healthcheck' in parsed['services'][service_name]
        hc = parsed['services'][service_name]['healthcheck']
        assert 'test' in hc
        assert 'interval' in hc
        assert 'retries' in hc

def test_volumes_created_for_persistence():
    """Volumes should be created when persistence enabled."""
    config = MyceliumConfig()
    config.services.redis.enabled = True
    config.services.redis.persistence = True

    generator = DockerComposeGenerator()
    content = generator.generate(config)
    parsed = yaml.safe_load(content)

    assert 'volumes' in parsed
    assert 'redis-data' in parsed['volumes']

def test_env_example_generation():
    """Should generate .env.example with required variables."""
    config = MyceliumConfig()
    config.services.postgres.enabled = True

    generator = DockerComposeGenerator()
    env_content = generator.generate_env_example(config)

    assert 'POSTGRES_USER' in env_content
    assert 'POSTGRES_PASSWORD' in env_content
    assert '<generate-secure-password>' in env_content
