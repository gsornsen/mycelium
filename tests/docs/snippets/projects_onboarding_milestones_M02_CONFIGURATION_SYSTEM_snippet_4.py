# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 412
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/config/migrations.py
"""Configuration schema migrations."""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Type alias for migration function
MigrationFunc = Callable[[dict[str, Any]], dict[str, Any]]

# Registry of migrations: version -> migration function
_MIGRATIONS: dict[str, MigrationFunc] = {}


def register_migration(from_version: str, to_version: str):
    """Decorator to register a migration function.

    Args:
        from_version: Source schema version
        to_version: Target schema version
    """
    def decorator(func: MigrationFunc) -> MigrationFunc:
        key = f"{from_version}->{to_version}"
        _MIGRATIONS[key] = func
        logger.debug(f"Registered migration: {key}")
        return func
    return decorator


def migrate_config(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Migrate configuration to latest schema version.

    Args:
        config_dict: Raw configuration dictionary

    Returns:
        Migrated configuration dictionary

    Raises:
        ValueError: If migration path not found
    """
    current_version = config_dict.get("version", "0.9")  # Assume 0.9 if missing
    target_version = "1.0"

    if current_version == target_version:
        logger.debug(f"Configuration already at version {target_version}")
        return config_dict

    # Find migration path
    migration_path = _find_migration_path(current_version, target_version)

    if not migration_path:
        raise ValueError(
            f"No migration path from {current_version} to {target_version}"
        )

    # Apply migrations in sequence
    migrated = config_dict.copy()
    for from_ver, to_ver in migration_path:
        key = f"{from_ver}->{to_ver}"
        migration_func = _MIGRATIONS[key]

        logger.info(f"Applying migration: {key}")
        migrated = migration_func(migrated)
        migrated["version"] = to_ver

    return migrated


def _find_migration_path(
    from_version: str,
    to_version: str
) -> list[tuple[str, str]]:
    """Find shortest migration path between versions.

    Args:
        from_version: Starting version
        to_version: Target version

    Returns:
        List of (from, to) version tuples forming migration path
    """
    # Simple linear path for now (can extend to graph search later)
    if from_version == "0.9" and to_version == "1.0":
        return [("0.9", "1.0")]

    return []


# Define migrations

@register_migration("0.9", "1.0")
def migrate_0_9_to_1_0(config: dict[str, Any]) -> dict[str, Any]:
    """Migrate from schema 0.9 to 1.0.

    Changes:
    - Add deployment.healthcheck_timeout field
    - Rename service.redis.memory to service.redis.max_memory
    - Add service.postgres.max_connections field
    """
    migrated = config.copy()

    # Add deployment.healthcheck_timeout
    if "deployment" not in migrated:
        migrated["deployment"] = {}
    if "healthcheck_timeout" not in migrated["deployment"]:
        migrated["deployment"]["healthcheck_timeout"] = 60

    # Rename redis.memory to redis.max_memory
    if "services" in migrated and "redis" in migrated["services"]:
        redis = migrated["services"]["redis"]
        if "memory" in redis:
            redis["max_memory"] = redis.pop("memory")

    # Add postgres.max_connections
    if "services" in migrated and "postgres" in migrated["services"]:
        postgres = migrated["services"]["postgres"]
        if "max_connections" not in postgres:
            postgres["max_connections"] = 100

    return migrated
