"""Configuration migration utilities for moving between scopes.

This module provides utilities for migrating configuration files between
different scopes (project-local to global, or vice versa) and for consolidating
multiple configuration files.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.scope import (
    ConfigLocation,
    ConfigScope,
    get_config_location,
    list_all_configs,
)
from mycelium_onboarding.xdg_dirs import get_config_dir

logger = logging.getLogger(__name__)

__all__ = [
    "MigrationResult",
    "MigrationAction",
    "migrate_to_global",
    "migrate_to_project",
    "detect_migration_candidates",
    "preview_migration",
]


class MigrationAction(NamedTuple):
    """Description of a migration action to be performed.

    Attributes:
        source: Source configuration file path
        destination: Destination configuration file path
        source_scope: Source configuration scope
        destination_scope: Destination configuration scope
        backup_path: Path where backup will be created
        will_merge: Whether configurations will be merged
    """

    source: Path
    destination: Path
    source_scope: ConfigScope
    destination_scope: ConfigScope
    backup_path: Path | None
    will_merge: bool


class MigrationResult(NamedTuple):
    """Result of a configuration migration operation.

    Attributes:
        success: Whether migration was successful
        source: Source configuration file path
        destination: Destination configuration file path
        backup_created: Path to backup file if created
        merged: Whether configurations were merged
        error: Error message if migration failed
    """

    success: bool
    source: Path
    destination: Path
    backup_created: Path | None
    merged: bool
    error: str | None


def migrate_to_global(
    *,
    source_path: Path | None = None,
    merge: bool = False,
    create_backup: bool = True,
    remove_source: bool = False,
) -> MigrationResult:
    """Migrate configuration from project-local to global scope.

    Copies or moves a project-local configuration file to the global
    user configuration directory. Optionally merges with existing global
    configuration.

    Args:
        source_path: Source configuration file (auto-detected if None)
        merge: If True, merge with existing global config instead of replacing
        create_backup: Create backup of existing global config before migration
        remove_source: Remove source file after successful migration

    Returns:
        MigrationResult with operation details

    Raises:
        FileNotFoundError: If source configuration file not found
        OSError: If migration operation fails

    Example:
        >>> result = migrate_to_global(merge=True, remove_source=False)
        >>> if result.success:
        ...     print(f"Migrated to: {result.destination}")
    """
    # Determine source
    if source_path is None:
        location = get_config_location(prefer_global=False)
        if location.scope != ConfigScope.PROJECT or not location.path or not location.exists:
            return MigrationResult(
                success=False,
                source=location.path or Path("unknown"),
                destination=get_config_dir() / "config.yaml",
                backup_created=None,
                merged=False,
                error="No project-local configuration found to migrate",
            )
        source_path = location.path

    if not source_path.exists():
        return MigrationResult(
            success=False,
            source=source_path,
            destination=get_config_dir() / "config.yaml",
            backup_created=None,
            merged=False,
            error=f"Source configuration not found: {source_path}",
        )

    # Determine destination
    destination_path = get_config_dir() / "config.yaml"
    backup_path: Path | None = None

    try:
        # Load source configuration
        manager_source = ConfigManager(config_path=source_path)
        source_config = manager_source.load()

        # Handle existing destination
        merged = False
        if destination_path.exists():
            if create_backup:
                backup_path = _create_backup(destination_path)
                logger.info("Created backup: %s", backup_path)

            if merge:
                # Load and merge configurations
                manager_dest = ConfigManager(config_path=destination_path)
                dest_config = manager_dest.load()

                # Merge: source takes precedence over destination
                merged_config = manager_dest.merge_configs(dest_config, source_config)
                source_config = merged_config
                merged = True
                logger.info("Merged configurations")

        # Ensure destination directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Save to destination
        manager_dest = ConfigManager(config_path=destination_path)
        manager_dest.save(source_config)

        # Remove source if requested
        if remove_source:
            source_path.unlink()
            logger.info("Removed source configuration: %s", source_path)

        return MigrationResult(
            success=True,
            source=source_path,
            destination=destination_path,
            backup_created=backup_path,
            merged=merged,
            error=None,
        )

    except Exception as e:
        logger.exception("Migration to global failed")
        return MigrationResult(
            success=False,
            source=source_path,
            destination=destination_path,
            backup_created=backup_path,
            merged=False,
            error=str(e),
        )


def migrate_to_project(
    *,
    project_dir: Path,
    merge: bool = False,
    create_backup: bool = True,
) -> MigrationResult:
    """Migrate configuration from global to project-local scope.

    Copies global configuration to a project-local location. Optionally
    merges with existing project configuration.

    Args:
        project_dir: Project directory where config will be created
        merge: If True, merge with existing project config instead of replacing
        create_backup: Create backup of existing project config before migration

    Returns:
        MigrationResult with operation details

    Example:
        >>> result = migrate_to_project(project_dir=Path("/path/to/project"))
        >>> if result.success:
        ...     print(f"Created project config at: {result.destination}")
    """
    source_path = get_config_dir() / "config.yaml"
    destination_path = project_dir / "config.yaml"
    backup_path: Path | None = None

    try:
        if not source_path.exists():
            return MigrationResult(
                success=False,
                source=source_path,
                destination=destination_path,
                backup_created=None,
                merged=False,
                error="No global configuration found to migrate",
            )

        # Load source configuration
        manager_source = ConfigManager(config_path=source_path)
        source_config = manager_source.load()

        # Handle existing destination
        merged = False
        if destination_path.exists():
            if create_backup:
                backup_path = _create_backup(destination_path)
                logger.info("Created backup: %s", backup_path)

            if merge:
                # Load and merge configurations
                manager_dest = ConfigManager(config_path=destination_path)
                dest_config = manager_dest.load()

                # Merge: source takes precedence
                merged_config = manager_dest.merge_configs(dest_config, source_config)
                source_config = merged_config
                merged = True
                logger.info("Merged configurations")

        # Ensure destination directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

        # Save to destination
        manager_dest = ConfigManager(config_path=destination_path)
        manager_dest.save(source_config)

        return MigrationResult(
            success=True,
            source=source_path,
            destination=destination_path,
            backup_created=backup_path,
            merged=merged,
            error=None,
        )

    except Exception as e:
        logger.exception("Migration to project failed")
        return MigrationResult(
            success=False,
            source=source_path,
            destination=destination_path,
            backup_created=backup_path,
            merged=False,
            error=str(e),
        )


def detect_migration_candidates() -> list[ConfigLocation]:
    """Detect configuration files that could be migrated to global scope.

    Scans for project-local configuration files that could be consolidated
    into the global configuration.

    Returns:
        List of ConfigLocation objects for migration candidates

    Example:
        >>> candidates = detect_migration_candidates()
        >>> if candidates:
        ...     print(f"Found {len(candidates)} configs that could be migrated to global")
    """
    candidates: list[ConfigLocation] = []

    # Check all possible config locations
    all_configs = list_all_configs()

    for location in all_configs:
        # Project configs that exist are candidates for migration
        if location.scope == ConfigScope.PROJECT and location.exists:
            candidates.append(location)

    return candidates


def preview_migration(
    source_path: Path,
    destination_scope: ConfigScope,
    *,
    merge: bool = False,
) -> MigrationAction:
    """Preview a migration action without executing it.

    Shows what would happen if a migration were performed, including
    whether files would be merged or replaced.

    Args:
        source_path: Source configuration file
        destination_scope: Target configuration scope
        merge: Whether configurations would be merged

    Returns:
        MigrationAction describing the planned operation

    Example:
        >>> action = preview_migration(
        ...     Path("/project/config.yaml"),
        ...     ConfigScope.GLOBAL,
        ...     merge=True
        ... )
        >>> print(f"Would migrate {action.source} -> {action.destination}")
    """
    # Determine destination path based on scope
    if destination_scope == ConfigScope.GLOBAL:
        destination_path = get_config_dir() / "config.yaml"
    elif destination_scope == ConfigScope.PROJECT:
        # This would need project_dir parameter in real implementation
        raise ValueError("Project scope requires project_dir parameter")
    else:
        raise ValueError(f"Unsupported destination scope: {destination_scope}")

    # Determine backup path
    backup_path: Path | None = None
    if destination_path.exists():
        backup_path = destination_path.with_suffix(".yaml.backup")

    # Determine source scope
    if get_config_dir() in source_path.parents:
        source_scope = ConfigScope.GLOBAL
    else:
        source_scope = ConfigScope.PROJECT

    return MigrationAction(
        source=source_path,
        destination=destination_path,
        source_scope=source_scope,
        destination_scope=destination_scope,
        backup_path=backup_path,
        will_merge=merge and destination_path.exists(),
    )


def _create_backup(path: Path) -> Path:
    """Create a timestamped backup of a configuration file.

    Args:
        path: Path to file to backup

    Returns:
        Path to created backup file

    Raises:
        OSError: If backup creation fails
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".yaml.backup.{timestamp}")

    shutil.copy2(path, backup_path)
    logger.info("Created backup: %s", backup_path)

    return backup_path
