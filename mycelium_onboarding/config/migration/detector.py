"""Migration detector for legacy configuration files.

This module provides the MigrationDetector class that scans for legacy
configuration files that need migration to the new XDG-compliant structure.

Example:
    >>> from mycelium_onboarding.config.migration.detector import MigrationDetector
    >>> detector = MigrationDetector()
    >>> legacy_configs = detector.scan_for_legacy_configs()
    >>> if detector.needs_migration():
    ...     summary = detector.get_migration_summary()
    ...     print(f"Found {summary['total_configs']} configs to migrate")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mycelium_onboarding.config.path_utils import find_legacy_configs
from mycelium_onboarding.config.paths import (
    get_project_config_path,
)

logger = logging.getLogger(__name__)

__all__ = ["LegacyConfigLocation", "MigrationDetector"]


@dataclass
class LegacyConfigLocation:
    """Represents a legacy config file location.

    Attributes:
        path: Path to the legacy config file
        config_type: Type of config ("project", "global", etc.)
        exists: Whether the file exists
        readable: Whether the file is readable
        size_bytes: Size of the file in bytes
        conflicts_with: Path to new config if it already exists
    """

    path: Path
    config_type: str
    exists: bool
    readable: bool
    size_bytes: int
    conflicts_with: Path | None = None

    def __str__(self) -> str:
        """String representation of legacy config location."""
        status = "exists" if self.exists else "missing"
        if self.exists:
            status += f", {self.size_bytes} bytes"
            if not self.readable:
                status += ", NOT READABLE"
            if self.conflicts_with:
                status += f", CONFLICTS with {self.conflicts_with}"
        return f"{self.config_type}: {self.path} ({status})"


class MigrationDetector:
    """Detect legacy configuration files that need migration.

    Scans the filesystem for legacy configuration files (e.g., mycelium-config.yaml)
    and determines what needs to be migrated to the new XDG-compliant structure.

    Attributes:
        project_dir: Project directory to scan for legacy configs
        legacy_filename: Name of legacy config file to search for

    Example:
        >>> detector = MigrationDetector()
        >>> if detector.needs_migration():
        ...     configs = detector.scan_for_legacy_configs()
        ...     for config in configs:
        ...         print(f"Found: {config}")
    """

    DEFAULT_LEGACY_FILENAME = "mycelium-config.yaml"

    def __init__(
        self,
        project_dir: Path | None = None,
        legacy_filename: str = DEFAULT_LEGACY_FILENAME,
    ) -> None:
        """Initialize detector.

        Args:
            project_dir: Project root directory. If None, uses current working directory.
            legacy_filename: Name of legacy config file to search for
        """
        self.project_dir = project_dir or Path.cwd()
        self.legacy_filename = legacy_filename
        self._cached_configs: list[LegacyConfigLocation] | None = None
        logger.debug(
            "MigrationDetector initialized: project_dir=%s, legacy_filename=%s",
            self.project_dir,
            legacy_filename,
        )

    def scan_for_legacy_configs(self) -> list[LegacyConfigLocation]:
        """Scan for legacy mycelium-config.yaml files.

        Checks:
        - <project>/mycelium-config.yaml (Phase 1 project config)
        - <project>/.mycelium/mycelium-config.yaml (old location)
        - Any other legacy locations

        Returns:
            List of found legacy config locations

        Example:
            >>> detector = MigrationDetector()
            >>> configs = detector.scan_for_legacy_configs()
            >>> for config in configs:
            ...     if config.exists:
            ...         print(f"Legacy config: {config.path}")
        """
        if self._cached_configs is not None:
            logger.debug("Returning cached legacy configs")
            return self._cached_configs

        logger.info("Scanning for legacy configuration files")
        legacy_configs: list[LegacyConfigLocation] = []

        # Define search paths
        search_paths = [
            self.project_dir,  # Root of project
            self.project_dir / ".mycelium",  # Old .mycelium directory
        ]

        # Find legacy configs using path_utils
        found_paths = find_legacy_configs(
            search_paths=search_paths,  # type: ignore[arg-type]
            legacy_filename=self.legacy_filename,
        )

        # Process each found config
        for legacy_path in found_paths:
            config_info = self._analyze_legacy_config(legacy_path)
            legacy_configs.append(config_info)
            logger.debug("Found legacy config: %s", config_info)

        self._cached_configs = legacy_configs
        logger.info("Found %d legacy configuration file(s)", len(legacy_configs))
        return legacy_configs

    def _analyze_legacy_config(self, path: Path) -> LegacyConfigLocation:
        """Analyze a legacy config file.

        Args:
            path: Path to legacy config file

        Returns:
            LegacyConfigLocation with analysis results
        """
        # Determine config type
        if path.parent == self.project_dir:
            config_type = "project-root"
        elif path.parent.name == ".mycelium":
            config_type = "project-mycelium"
        else:
            config_type = "unknown"

        # Check file properties
        exists = path.exists()
        readable = exists and os.access(path, os.R_OK)
        size_bytes = path.stat().st_size if exists else 0

        # Check for conflicts with new config structure
        conflicts_with = self._check_for_conflicts(path, config_type)

        return LegacyConfigLocation(
            path=path,
            config_type=config_type,
            exists=exists,
            readable=readable,
            size_bytes=size_bytes,
            conflicts_with=conflicts_with,
        )

    def _check_for_conflicts(
        self,
        legacy_path: Path,
        config_type: str,
    ) -> Path | None:
        """Check if migration would conflict with existing new config.

        Args:
            legacy_path: Path to legacy config
            config_type: Type of legacy config

        Returns:
            Path to conflicting new config, or None if no conflict
        """
        # Determine where this would migrate to
        if config_type in ("project-root", "project-mycelium"):
            new_path = get_project_config_path(self.project_dir)
        else:
            # Unknown type, check both
            new_path = get_project_config_path(self.project_dir)

        # Check if new config already exists
        if new_path.exists() and new_path != legacy_path:
            logger.warning("Migration conflict detected: %s already exists", new_path)
            return new_path

        return None

    def needs_migration(self) -> bool:
        """Check if migration is needed.

        Returns:
            True if any legacy configs need migration

        Example:
            >>> detector = MigrationDetector()
            >>> if detector.needs_migration():
            ...     print("Migration required")
        """
        configs = self.scan_for_legacy_configs()
        return len(configs) > 0

    def get_migration_summary(self) -> dict[str, Any]:
        """Get summary of what will be migrated.

        Returns:
            Dictionary with migration summary:
            - total_configs: Total number of legacy configs found
            - total_size_bytes: Total size of all configs
            - readable_configs: Number of readable configs
            - conflicting_configs: Number of configs with conflicts
            - configs_by_type: Dict of config type -> count

        Example:
            >>> detector = MigrationDetector()
            >>> summary = detector.get_migration_summary()
            >>> print(f"Total configs: {summary['total_configs']}")
            >>> print(f"Total size: {summary['total_size_bytes']} bytes")
        """
        configs = self.scan_for_legacy_configs()

        # Calculate summary statistics
        total_configs = len(configs)
        total_size = sum(c.size_bytes for c in configs)
        readable = sum(1 for c in configs if c.readable)
        conflicting = sum(1 for c in configs if c.conflicts_with is not None)

        # Count by type
        configs_by_type: dict[str, int] = {}
        for config in configs:
            configs_by_type[config.config_type] = configs_by_type.get(config.config_type, 0) + 1

        summary = {
            "total_configs": total_configs,
            "total_size_bytes": total_size,
            "readable_configs": readable,
            "conflicting_configs": conflicting,
            "configs_by_type": configs_by_type,
            "has_conflicts": conflicting > 0,
            "all_readable": readable == total_configs,
            "migration_needed": total_configs > 0,
        }

        logger.debug("Migration summary: %s", summary)
        return summary

    def clear_cache(self) -> None:
        """Clear cached scan results.

        Forces next scan to re-read filesystem.

        Example:
            >>> detector = MigrationDetector()
            >>> configs = detector.scan_for_legacy_configs()  # Caches
            >>> detector.clear_cache()
            >>> configs = detector.scan_for_legacy_configs()  # Re-scans
        """
        self._cached_configs = None
        logger.debug("Cleared cached legacy configs")

    def validate_migration_feasibility(self) -> list[str]:
        """Validate if migration is feasible.

        Checks for issues that would prevent migration:
        - Unreadable files
        - Permission issues
        - Conflicts with new configs

        Returns:
            List of validation errors (empty if feasible)

        Example:
            >>> detector = MigrationDetector()
            >>> errors = detector.validate_migration_feasibility()
            >>> if errors:
            ...     for error in errors:
            ...         print(f"Error: {error}")
        """
        configs = self.scan_for_legacy_configs()
        errors: list[str] = []

        for config in configs:
            if not config.exists:
                errors.append(f"Config file does not exist: {config.path}")
            elif not config.readable:
                errors.append(f"Config file is not readable: {config.path}")

            if config.conflicts_with:
                errors.append(f"Migration conflict: {config.path} would overwrite existing {config.conflicts_with}")

        logger.debug("Migration feasibility check: %d errors", len(errors))
        return errors
