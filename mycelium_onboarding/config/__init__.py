"""Configuration system for Mycelium onboarding.

This package provides a type-safe configuration system using Pydantic v2.
It includes schema definitions, validation, serialization/deserialization,
and configuration management utilities.

Main Components:
    - schema: Pydantic models for configuration validation
    - manager: Configuration loading, saving, and management (Task 2.2)
    - migrations: Schema migration framework (Task 2.3)

Example:
    >>> from mycelium_onboarding.config import MyceliumConfig, ConfigManager
    >>> # Create and save configuration
    >>> config = MyceliumConfig(project_name="my-project")
    >>> config.services.redis.port = 6380
    >>> manager = ConfigManager()
    >>> manager.save(config)
    >>> # Load configuration
    >>> loaded_config = manager.load()
    >>> # Migrate configuration
    >>> migrated = manager.load_and_migrate()
"""

from __future__ import annotations

from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigManager,
    ConfigSaveError,
    ConfigValidationError,
)
from mycelium_onboarding.config.migrations import (
    Migration,
    MigrationError,
    MigrationHistory,
    MigrationPathError,
    MigrationRegistry,
    MigrationValidationError,
    get_default_registry,
)
from mycelium_onboarding.config.schema import (
    DeploymentConfig,
    DeploymentMethod,
    MyceliumConfig,
    PostgresConfig,
    RedisConfig,
    ServiceConfig,
    ServicesConfig,
    TemporalConfig,
)

__all__ = [
    # Schema classes
    "MyceliumConfig",
    "DeploymentConfig",
    "DeploymentMethod",
    "ServicesConfig",
    "ServiceConfig",
    "RedisConfig",
    "PostgresConfig",
    "TemporalConfig",
    # Manager classes
    "ConfigManager",
    "ConfigLoadError",
    "ConfigSaveError",
    "ConfigValidationError",
    # Migration classes
    "Migration",
    "MigrationRegistry",
    "MigrationHistory",
    "MigrationError",
    "MigrationPathError",
    "MigrationValidationError",
    "get_default_registry",
]
