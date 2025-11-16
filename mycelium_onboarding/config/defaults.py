"""Default configuration values for Mycelium onboarding.

This module provides default configuration values that serve as the foundation
for the 3-tier configuration precedence system: defaults → global → project.

All defaults are defined as type-safe dictionaries that can be used to create
MyceliumConfig instances or merged with user-provided configurations.

Example:
    >>> from mycelium_onboarding.config.defaults import get_default_config_dict
    >>> defaults = get_default_config_dict()
    >>> print(defaults['project_name'])
    mycelium
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final

from mycelium_onboarding.config.schema import DeploymentMethod

# Module exports
__all__ = [
    "DEFAULT_PROJECT_NAME",
    "DEFAULT_SCHEMA_VERSION",
    "DEFAULT_REDIS_PORT",
    "DEFAULT_POSTGRES_PORT",
    "DEFAULT_TEMPORAL_UI_PORT",
    "DEFAULT_TEMPORAL_FRONTEND_PORT",
    "DEFAULT_HEALTHCHECK_TIMEOUT",
    "get_default_config_dict",
    "get_default_redis_config",
    "get_default_postgres_config",
    "get_default_temporal_config",
    "get_default_services_config",
    "get_default_deployment_config",
]

# Project defaults
DEFAULT_PROJECT_NAME: Final[str] = "mycelium"
DEFAULT_SCHEMA_VERSION: Final[str] = "1.0"

# Redis defaults
DEFAULT_REDIS_PORT: Final[int] = 6379
DEFAULT_REDIS_PERSISTENCE: Final[bool] = True
DEFAULT_REDIS_MAX_MEMORY: Final[str] = "256mb"
DEFAULT_REDIS_VERSION: Final[str | None] = None

# PostgreSQL defaults
DEFAULT_POSTGRES_PORT: Final[int] = 5432
DEFAULT_POSTGRES_DATABASE: Final[str] = "mycelium"
DEFAULT_POSTGRES_MAX_CONNECTIONS: Final[int] = 100
DEFAULT_POSTGRES_VERSION: Final[str | None] = None

# Temporal defaults
DEFAULT_TEMPORAL_UI_PORT: Final[int] = 8080
DEFAULT_TEMPORAL_FRONTEND_PORT: Final[int] = 7233
DEFAULT_TEMPORAL_NAMESPACE: Final[str] = "default"
DEFAULT_TEMPORAL_VERSION: Final[str | None] = None

# Deployment defaults
DEFAULT_DEPLOYMENT_METHOD: Final[DeploymentMethod] = DeploymentMethod.DOCKER_COMPOSE
DEFAULT_AUTO_START: Final[bool] = True
DEFAULT_HEALTHCHECK_TIMEOUT: Final[int] = 60

# Service enabled defaults
DEFAULT_REDIS_ENABLED: Final[bool] = True
DEFAULT_POSTGRES_ENABLED: Final[bool] = True
DEFAULT_TEMPORAL_ENABLED: Final[bool] = True


def get_default_redis_config() -> dict[str, Any]:
    """Get default Redis configuration dictionary.

    Returns:
        Dictionary with Redis configuration defaults

    Example:
        >>> redis_config = get_default_redis_config()
        >>> redis_config['port']
        6379
    """
    return {
        "enabled": DEFAULT_REDIS_ENABLED,
        "version": DEFAULT_REDIS_VERSION,
        "custom_config": {},
        "port": DEFAULT_REDIS_PORT,
        "persistence": DEFAULT_REDIS_PERSISTENCE,
        "max_memory": DEFAULT_REDIS_MAX_MEMORY,
    }


def get_default_postgres_config() -> dict[str, Any]:
    """Get default PostgreSQL configuration dictionary.

    Returns:
        Dictionary with PostgreSQL configuration defaults

    Example:
        >>> postgres_config = get_default_postgres_config()
        >>> postgres_config['database']
        'mycelium'
    """
    return {
        "enabled": DEFAULT_POSTGRES_ENABLED,
        "version": DEFAULT_POSTGRES_VERSION,
        "custom_config": {},
        "port": DEFAULT_POSTGRES_PORT,
        "database": DEFAULT_POSTGRES_DATABASE,
        "max_connections": DEFAULT_POSTGRES_MAX_CONNECTIONS,
    }


def get_default_temporal_config() -> dict[str, Any]:
    """Get default Temporal configuration dictionary.

    Returns:
        Dictionary with Temporal configuration defaults

    Example:
        >>> temporal_config = get_default_temporal_config()
        >>> temporal_config['namespace']
        'default'
    """
    return {
        "enabled": DEFAULT_TEMPORAL_ENABLED,
        "version": DEFAULT_TEMPORAL_VERSION,
        "custom_config": {},
        "ui_port": DEFAULT_TEMPORAL_UI_PORT,
        "frontend_port": DEFAULT_TEMPORAL_FRONTEND_PORT,
        "namespace": DEFAULT_TEMPORAL_NAMESPACE,
    }


def get_default_services_config() -> dict[str, Any]:
    """Get default services configuration dictionary.

    Returns:
        Dictionary with all services configuration defaults

    Example:
        >>> services = get_default_services_config()
        >>> services['redis']['port']
        6379
    """
    return {
        "redis": get_default_redis_config(),
        "postgres": get_default_postgres_config(),
        "temporal": get_default_temporal_config(),
    }


def get_default_deployment_config() -> dict[str, Any]:
    """Get default deployment configuration dictionary.

    Returns:
        Dictionary with deployment configuration defaults

    Example:
        >>> deployment = get_default_deployment_config()
        >>> deployment['method']
        'docker-compose'
    """
    return {
        "method": DEFAULT_DEPLOYMENT_METHOD.value,
        "auto_start": DEFAULT_AUTO_START,
        "healthcheck_timeout": DEFAULT_HEALTHCHECK_TIMEOUT,
    }


def get_default_config_dict() -> dict[str, Any]:
    """Get complete default configuration dictionary.

    This returns the full configuration structure with all default values.
    Can be used as the base layer in the 3-tier precedence system.

    Returns:
        Dictionary with complete default configuration

    Example:
        >>> config_dict = get_default_config_dict()
        >>> config_dict['version']
        '1.0'
        >>> config_dict['services']['redis']['port']
        6379
    """
    return {
        "version": DEFAULT_SCHEMA_VERSION,
        "project_name": DEFAULT_PROJECT_NAME,
        "deployment": get_default_deployment_config(),
        "services": get_default_services_config(),
        "created_at": datetime.now().isoformat(),
    }
