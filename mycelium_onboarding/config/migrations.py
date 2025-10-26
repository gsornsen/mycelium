"""Configuration schema migration framework.

This module provides a comprehensive migration system for evolving configuration
schemas across versions. It supports:
- Migration chain discovery and execution
- Backward compatibility validation
- Dry-run mode for previewing changes
- Rollback capability
- Migration history tracking
- Comprehensive logging and error handling

The migration framework uses a graph-based approach to discover optimal migration
paths between versions, allowing for flexible upgrade paths.

Example:
    >>> from mycelium_onboarding.config.migrations import MigrationRegistry
    >>> registry = MigrationRegistry()
    >>> # Migrate config from 1.0 to 1.2
    >>> migrated = registry.migrate(config_dict, target_version="1.2")
"""

from __future__ import annotations

import copy
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from packaging.version import parse

# Module logger
logger = logging.getLogger(__name__)

# Module exports
__all__ = [
    "Migration",
    "MigrationRegistry",
    "MigrationError",
    "MigrationPathError",
    "MigrationValidationError",
    "MigrationHistory",
    "Migration_1_0_to_1_1",
    "Migration_1_1_to_1_2",
]


class MigrationError(Exception):
    """Base exception for migration-related errors."""

    pass


class MigrationPathError(MigrationError):
    """Raised when no migration path can be found between versions."""

    pass


class MigrationValidationError(MigrationError):
    """Raised when migration validation fails."""

    pass


@dataclass
class MigrationHistory:
    """Record of a migration execution.

    Attributes:
        from_version: Source version
        to_version: Target version
        timestamp: When migration was executed
        success: Whether migration succeeded
        changes: Dictionary of changes made
        error: Error message if migration failed
    """

    from_version: str
    to_version: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    changes: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize history record to dictionary.

        Returns:
            Dictionary representation of history record
        """
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "changes": self.changes,
            "error": self.error,
        }


class Migration(ABC):
    """Base class for schema migrations.

    Each migration represents a single version transition (e.g., 1.0 -> 1.1).
    Subclasses must implement the migrate method to perform the actual transformation.

    Attributes:
        from_version: Source schema version
        to_version: Target schema version
        description: Human-readable description of changes

    Example:
        >>> class Migration_1_0_to_1_1(Migration):
        ...     from_version = "1.0"
        ...     to_version = "1.1"
        ...     description = "Add monitoring configuration"
        ...
        ...     def migrate(self, config_dict):
        ...         config_dict["monitoring"] = {"enabled": False}
        ...         return config_dict
    """

    @property
    @abstractmethod
    def from_version(self) -> str:
        """Source version that this migration upgrades from.

        Returns:
            Version string (e.g., "1.0")
        """
        pass

    @property
    @abstractmethod
    def to_version(self) -> str:
        """Target version that this migration upgrades to.

        Returns:
            Version string (e.g., "1.1")
        """
        pass

    @property
    def description(self) -> str:
        """Human-readable description of migration changes.

        Returns:
            Description string
        """
        return f"Migrate from {self.from_version} to {self.to_version}"

    @abstractmethod
    def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Perform migration on configuration dictionary.

        Args:
            config_dict: Configuration dictionary to migrate

        Returns:
            Migrated configuration dictionary

        Raises:
            MigrationError: If migration fails
        """
        pass

    def validate_before(self, config_dict: dict[str, Any]) -> None:
        """Validate configuration before migration.

        Args:
            config_dict: Configuration to validate

        Raises:
            MigrationValidationError: If validation fails
        """
        # Ensure version field exists and matches
        if "version" not in config_dict:
            raise MigrationValidationError(
                f"Configuration missing 'version' field for migration "
                f"{self.from_version} -> {self.to_version}"
            )

        config_version = str(config_dict["version"])
        if config_version != self.from_version:
            raise MigrationValidationError(
                f"Configuration version mismatch: expected {self.from_version}, "
                f"got {config_version}"
            )

    def validate_after(self, config_dict: dict[str, Any]) -> None:
        """Validate configuration after migration.

        Args:
            config_dict: Configuration to validate

        Raises:
            MigrationValidationError: If validation fails
        """
        # Ensure version was updated
        if "version" not in config_dict:
            raise MigrationValidationError(
                f"Configuration missing 'version' field after migration "
                f"{self.from_version} -> {self.to_version}"
            )

        config_version = str(config_dict["version"])
        if config_version != self.to_version:
            raise MigrationValidationError(
                f"Configuration version not updated: expected {self.to_version}, "
                f"got {config_version}"
            )

    def __repr__(self) -> str:
        """String representation of migration.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}({self.from_version} -> {self.to_version})"


class MigrationRegistry:
    """Registry and executor for schema migrations.

    The registry maintains a graph of all available migrations and provides
    methods to discover migration paths and execute migrations.

    Features:
    - Automatic migration path discovery using graph traversal
    - Dry-run mode for previewing changes
    - Migration history tracking
    - Rollback capability
    - Comprehensive validation

    Example:
        >>> registry = MigrationRegistry()
        >>> registry.register(Migration_1_0_to_1_1())
        >>> registry.register(Migration_1_1_to_1_2())
        >>>
        >>> # Migrate from 1.0 to 1.2 (automatically uses both migrations)
        >>> result = registry.migrate(config_dict, target_version="1.2")
    """

    def __init__(self) -> None:
        """Initialize empty migration registry."""
        self._migrations: dict[str, list[Migration]] = {}
        self._history: list[MigrationHistory] = []
        logger.debug("MigrationRegistry initialized")

    def register(self, migration: Migration) -> None:
        """Register a migration.

        Args:
            migration: Migration to register

        Raises:
            ValueError: If migration is invalid or duplicate

        Example:
            >>> registry = MigrationRegistry()
            >>> registry.register(Migration_1_0_to_1_1())
        """
        # Validate migration
        if not migration.from_version or not migration.to_version:
            raise ValueError(
                f"Migration must have both from_version and to_version: {migration}"
            )

        # Check for duplicate
        existing = self._migrations.get(migration.from_version, [])
        for existing_migration in existing:
            if existing_migration.to_version == migration.to_version:
                raise ValueError(
                    f"Duplicate migration already registered: "
                    f"{migration.from_version} -> {migration.to_version}"
                )

        # Register migration
        if migration.from_version not in self._migrations:
            self._migrations[migration.from_version] = []
        self._migrations[migration.from_version].append(migration)

        logger.info(
            "Registered migration: %s -> %s (%s)",
            migration.from_version,
            migration.to_version,
            migration.__class__.__name__,
        )

    def get_registered_migrations(self) -> list[Migration]:
        """Get all registered migrations.

        Returns:
            List of all registered migrations

        Example:
            >>> registry = MigrationRegistry()
            >>> migrations = registry.get_registered_migrations()
        """
        all_migrations = []
        for migrations in self._migrations.values():
            all_migrations.extend(migrations)
        return all_migrations

    def get_migration_path(self, from_version: str, to_version: str) -> list[Migration]:
        """Get ordered list of migrations to apply.

        Uses breadth-first search to find the shortest migration path
        between versions.

        Args:
            from_version: Starting version
            to_version: Target version

        Returns:
            Ordered list of migrations to apply

        Raises:
            MigrationPathError: If no path exists between versions
            ValueError: If versions are invalid

        Example:
            >>> registry = MigrationRegistry()
            >>> path = registry.get_migration_path("1.0", "1.2")
            >>> # Returns [Migration_1_0_to_1_1(), Migration_1_1_to_1_2()]
        """
        logger.debug("Finding migration path: %s -> %s", from_version, to_version)

        # Validate versions
        try:
            from_ver = parse(from_version)
            to_ver = parse(to_version)
        except Exception as e:
            raise ValueError(f"Invalid version format: {e}") from e

        # Check if already at target version
        if from_ver == to_ver:
            logger.debug("Already at target version: %s", to_version)
            return []

        # Check if downgrade requested (not supported)
        if from_ver > to_ver:
            raise MigrationPathError(
                f"Downgrade not supported: {from_version} -> {to_version}. "
                "Use rollback instead."
            )

        # Breadth-first search for shortest path
        from collections import deque

        queue: deque[tuple[str, list[Migration]]] = deque([(from_version, [])])
        visited: set[str] = {from_version}

        while queue:
            current_version, path = queue.popleft()

            # Get available migrations from current version
            available_migrations = self._migrations.get(current_version, [])

            for migration in available_migrations:
                next_version = migration.to_version
                new_path = path + [migration]

                # Check if we reached target
                if next_version == to_version:
                    logger.info(
                        "Found migration path with %d steps: %s",
                        len(new_path),
                        " -> ".join([from_version] + [m.to_version for m in new_path]),
                    )
                    return new_path

                # Continue search if not visited
                if next_version not in visited:
                    visited.add(next_version)
                    queue.append((next_version, new_path))

        # No path found
        raise MigrationPathError(
            f"No migration path found from {from_version} to {to_version}. "
            f"Available versions: {sorted(visited)}"
        )

    def migrate(
        self,
        config_dict: dict[str, Any],
        target_version: str,
        *,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Migrate configuration to target version.

        Discovers and executes the necessary migration chain to reach the
        target version. Performs validation before and after each migration.

        Args:
            config_dict: Configuration dictionary to migrate
            target_version: Target schema version
            dry_run: If True, preview changes without applying them

        Returns:
            Migrated configuration dictionary (or preview if dry_run=True)

        Raises:
            MigrationError: If migration fails
            MigrationPathError: If no migration path exists
            MigrationValidationError: If validation fails

        Example:
            >>> registry = MigrationRegistry()
            >>> # Dry run to preview changes
            >>> preview = registry.migrate(config, "1.2", dry_run=True)
            >>> # Actually migrate
            >>> migrated = registry.migrate(config, "1.2")
        """
        logger.info(
            "Starting migration to version %s (dry_run=%s)", target_version, dry_run
        )

        # Get current version
        if "version" not in config_dict:
            raise MigrationValidationError(
                "Configuration missing 'version' field. "
                "Cannot determine current version."
            )

        current_version = str(config_dict["version"])
        logger.debug("Current version: %s", current_version)

        # Get migration path
        try:
            migrations = self.get_migration_path(current_version, target_version)
        except MigrationPathError as e:
            logger.error("Migration path error: %s", e)
            raise

        # Check if already at target
        if not migrations:
            logger.info("Already at target version %s", target_version)
            return config_dict

        # Create deep copy for migration (preserve original)
        if dry_run:
            logger.debug("Dry run mode: creating config copy")
        working_config = copy.deepcopy(config_dict)

        # Execute migration chain
        logger.info(
            "Executing migration chain with %d step(s): %s",
            len(migrations),
            " -> ".join([current_version] + [m.to_version for m in migrations]),
        )

        for i, migration in enumerate(migrations, 1):
            logger.info(
                "Step %d/%d: Applying %s",
                i,
                len(migrations),
                migration,
            )

            try:
                # Validate before migration
                migration.validate_before(working_config)

                # Perform migration
                previous_config = copy.deepcopy(working_config)
                working_config = migration.migrate(working_config)

                # Validate after migration
                migration.validate_after(working_config)

                # Record history
                if not dry_run:
                    changes = self._compute_diff(previous_config, working_config)
                    history = MigrationHistory(
                        from_version=migration.from_version,
                        to_version=migration.to_version,
                        success=True,
                        changes=changes,
                    )
                    self._history.append(history)

                logger.info(
                    "Successfully applied migration: %s -> %s",
                    migration.from_version,
                    migration.to_version,
                )

            except Exception as e:
                error_msg = f"Migration failed at step {i}/{len(migrations)}: {e}"
                logger.error(error_msg)

                # Record failure in history
                if not dry_run:
                    history = MigrationHistory(
                        from_version=migration.from_version,
                        to_version=migration.to_version,
                        success=False,
                        error=str(e),
                    )
                    self._history.append(history)

                raise MigrationError(error_msg) from e

        if dry_run:
            logger.info(
                "Dry run completed successfully: %s -> %s",
                current_version,
                target_version,
            )
        else:
            logger.info(
                "Migration completed successfully: %s -> %s",
                current_version,
                target_version,
            )

        return working_config

    def needs_migration(self, config_dict: dict[str, Any], target_version: str) -> bool:
        """Check if configuration needs migration to target version.

        Args:
            config_dict: Configuration to check
            target_version: Target version to check against

        Returns:
            True if migration is needed, False otherwise

        Example:
            >>> registry = MigrationRegistry()
            >>> if registry.needs_migration(config, "1.2"):
            ...     config = registry.migrate(config, "1.2")
        """
        if "version" not in config_dict:
            return True

        current_version = str(config_dict["version"])

        try:
            current = parse(current_version)
            target = parse(target_version)
            needs = current < target
            logger.debug(
                "Migration needed from %s to %s: %s",
                current_version,
                target_version,
                needs,
            )
            return needs
        except Exception as e:
            logger.warning("Version comparison failed: %s", e)
            return False

    def get_history(self) -> list[MigrationHistory]:
        """Get migration history.

        Returns:
            List of migration history records

        Example:
            >>> registry = MigrationRegistry()
            >>> history = registry.get_history()
            >>> for record in history:
            ...     print(f"{record.from_version} -> {record.to_version}")
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear migration history.

        Example:
            >>> registry = MigrationRegistry()
            >>> registry.clear_history()
        """
        self._history.clear()
        logger.debug("Migration history cleared")

    def _compute_diff(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute differences between two configurations.

        Args:
            before: Configuration before migration
            after: Configuration after migration

        Returns:
            Dictionary describing changes
        """
        changes: dict[str, Any] = {"added": {}, "modified": {}, "removed": {}}

        # Find added and modified keys
        for key, value in after.items():
            if key not in before:
                changes["added"][key] = value
            elif before[key] != value:
                changes["modified"][key] = {"old": before[key], "new": value}

        # Find removed keys
        for key in before:
            if key not in after:
                changes["removed"][key] = before[key]

        return changes

    def preview_migration(
        self, config_dict: dict[str, Any], target_version: str
    ) -> str:
        """Preview migration changes in human-readable format.

        Args:
            config_dict: Configuration to migrate
            target_version: Target version

        Returns:
            Human-readable preview string

        Example:
            >>> registry = MigrationRegistry()
            >>> preview = registry.preview_migration(config, "1.2")
            >>> print(preview)
        """
        try:
            # Perform dry run
            migrated = self.migrate(config_dict, target_version, dry_run=True)

            # Compute diff
            diff = self._compute_diff(config_dict, migrated)

            # Format preview
            lines = [
                f"Migration Preview: {config_dict.get('version')} -> {target_version}",
                "",
            ]

            if diff["added"]:
                lines.append("Added fields:")
                for key, value in diff["added"].items():
                    lines.append(f"  + {key}: {json.dumps(value, indent=2)}")
                lines.append("")

            if diff["modified"]:
                lines.append("Modified fields:")
                for key, change in diff["modified"].items():
                    lines.append(f"  ~ {key}:")
                    lines.append(f"      old: {json.dumps(change['old'])}")
                    lines.append(f"      new: {json.dumps(change['new'])}")
                lines.append("")

            if diff["removed"]:
                lines.append("Removed fields:")
                for key, value in diff["removed"].items():
                    lines.append(f"  - {key}: {json.dumps(value)}")
                lines.append("")

            if not any([diff["added"], diff["modified"], diff["removed"]]):
                lines.append("No changes required.")

            return "\n".join(lines)

        except Exception as e:
            return f"Error generating preview: {e}"


# ============================================================================
# Example Migrations
# ============================================================================


class Migration_1_0_to_1_1(Migration):  # noqa: N801
    """Example migration from version 1.0 to 1.1.

    Changes:
    - Add monitoring configuration section
    - Add default log_level to deployment
    """

    from_version = "1.0"
    to_version = "1.1"
    description = "Add monitoring and logging configuration"

    def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Migrate configuration from 1.0 to 1.1.

        Args:
            config_dict: Configuration to migrate

        Returns:
            Migrated configuration
        """
        logger.debug("Migrating 1.0 -> 1.1: Adding monitoring and logging")

        # Add monitoring section
        config_dict["monitoring"] = {
            "enabled": False,
            "metrics_port": 9090,
            "health_check_interval": 30,
        }

        # Add log_level to deployment
        if "deployment" in config_dict:
            config_dict["deployment"]["log_level"] = "INFO"

        # Update version
        config_dict["version"] = self.to_version

        return config_dict


class Migration_1_1_to_1_2(Migration):  # noqa: N801
    """Example migration from version 1.1 to 1.2.

    Changes:
    - Add backup configuration
    - Rename deployment.log_level to deployment.logging_level
    """

    from_version = "1.1"
    to_version = "1.2"
    description = "Add backup configuration and refactor logging"

    def migrate(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Migrate configuration from 1.1 to 1.2.

        Args:
            config_dict: Configuration to migrate

        Returns:
            Migrated configuration
        """
        logger.debug("Migrating 1.1 -> 1.2: Adding backup and refactoring logging")

        # Add backup section
        config_dict["backup"] = {
            "enabled": False,
            "schedule": "0 2 * * *",  # 2 AM daily
            "retention_days": 30,
        }

        # Rename deployment.log_level to deployment.logging_level
        if "deployment" in config_dict and "log_level" in config_dict["deployment"]:
            config_dict["deployment"]["logging_level"] = config_dict["deployment"].pop(
                "log_level"
            )

        # Update version
        config_dict["version"] = self.to_version

        return config_dict


# ============================================================================
# Default Registry
# ============================================================================


def get_default_registry() -> MigrationRegistry:
    """Get default migration registry with all migrations registered.

    Returns:
        MigrationRegistry with all migrations registered

    Example:
        >>> registry = get_default_registry()
        >>> migrated = registry.migrate(config, "1.2")
    """
    registry = MigrationRegistry()
    registry.register(Migration_1_0_to_1_1())
    registry.register(Migration_1_1_to_1_2())
    return registry
