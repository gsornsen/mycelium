# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 997
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/fixtures/config_fixtures.py
"""Factory functions for creating test data."""

from factory import Factory, SubFactory
from mycelium.config import (
    DeploymentConfig,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServicesConfig,
)


class RedisConfigFactory(Factory):
    """Factory for generating RedisConfig instances."""

    class Meta:
        model = RedisConfig

    enabled = True
    port = 6379
    max_memory = 512
    persistence = True


class PostgresConfigFactory(Factory):
    """Factory for generating PostgresConfig instances."""

    class Meta:
        model = PostgresConfig

    enabled = True
    port = 5432
    database = "mycelium"
    max_connections = 100


class ServicesConfigFactory(Factory):
    """Factory for generating ServicesConfig instances."""

    class Meta:
        model = ServicesConfig

    redis = SubFactory(RedisConfigFactory)
    postgres = SubFactory(PostgresConfigFactory)


class DeploymentConfigFactory(Factory):
    """Factory for generating DeploymentConfig instances."""

    class Meta:
        model = DeploymentConfig

    method = "docker-compose"


class MyceliumConfigFactory(Factory):
    """Factory for generating complete MyceliumConfig instances."""

    class Meta:
        model = MyceliumConfig

    services = SubFactory(ServicesConfigFactory)
    deployment = SubFactory(DeploymentConfigFactory)


# Convenience functions
def create_minimal_config() -> MyceliumConfig:
    """Create minimal valid configuration (Redis only)."""
    return MyceliumConfigFactory.build(
        services__postgres__enabled=False,
        services__taskqueue__enabled=False,
    )


def create_full_config() -> MyceliumConfig:
    """Create configuration with all services enabled."""
    return MyceliumConfigFactory.build()


def create_docker_config() -> MyceliumConfig:
    """Create configuration for Docker deployment."""
    return MyceliumConfigFactory.build(
        deployment__method="docker-compose"
    )


def create_justfile_config() -> MyceliumConfig:
    """Create configuration for Justfile deployment."""
    return MyceliumConfigFactory.build(
        deployment__method="justfile"
    )
