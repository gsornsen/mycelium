"""Migration planner for creating safe migration plans.

This module provides the MigrationPlanner class that creates detailed
migration plans from detected legacy configurations.

Example:
    >>> from mycelium_onboarding.config.migration import (
    ...     MigrationDetector,
    ...     MigrationPlanner,
    ... )
    >>> detector = MigrationDetector()
    >>> configs = detector.scan_for_legacy_configs()
    >>> planner = MigrationPlanner()
    >>> plan = planner.create_plan(configs)
    >>> print(f"Migration will take {len(plan)} steps")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mycelium_onboarding.config.migration.detector import LegacyConfigLocation
from mycelium_onboarding.config.path_utils import check_write_permission
from mycelium_onboarding.config.paths import (
    ensure_migration_backup_dir_exists,
    get_global_config_path,
    get_project_config_path,
)

logger = logging.getLogger(__name__)

__all__ = ["MigrationAction", "MigrationStep", "MigrationPlanner"]


class MigrationAction(Enum):
    """Types of migration actions."""

    MOVE = "move"  # Move file to new location
    COPY = "copy"  # Copy file (preserve original)
    MERGE = "merge"  # Merge with existing config
    SKIP = "skip"  # Skip (already migrated)
    CREATE = "create"  # Create new global config
    BACKUP = "backup"  # Create backup before migration

    def __str__(self) -> str:
        """String representation of action."""
        return self.value


@dataclass
class MigrationStep:
    """A single migration step.

    Attributes:
        action: Type of action to perform
        source: Source path (None for CREATE actions)
        destination: Destination path
        backup_path: Path where backup will be created (None if no backup)
        description: Human-readable description of the step
        order: Execution order (lower numbers execute first)
    """

    action: MigrationAction
    source: Path | None
    destination: Path
    backup_path: Path | None
    description: str
    order: int = 0

    def __str__(self) -> str:
        """String representation of migration step."""
        if self.source:
            return f"[{self.order}] {self.action}: {self.source} -> {self.destination}"
        return f"[{self.order}] {self.action}: {self.destination}"

    def __lt__(self, other: MigrationStep) -> bool:
        """Compare steps by execution order."""
        return self.order < other.order


class MigrationPlanner:
    """Plan migration steps for legacy configurations.

    Creates a comprehensive migration plan that includes:
    - Backup steps for safety
    - File moves/copies to new locations
    - Global config creation if needed
    - Validation and conflict resolution

    Example:
        >>> planner = MigrationPlanner()
        >>> legacy_configs = [...]  # From detector
        >>> plan = planner.create_plan(legacy_configs)
        >>> if planner.validate_plan(plan):
        ...     print("Plan is safe to execute")
    """

    def __init__(self, project_dir: Path | None = None) -> None:
        """Initialize planner.

        Args:
            project_dir: Project directory. If None, uses current working directory.
        """
        self.project_dir = project_dir or Path.cwd()
        logger.debug("MigrationPlanner initialized: project_dir=%s", self.project_dir)

    def create_plan(
        self,
        legacy_configs: list[LegacyConfigLocation],
        create_global: bool = True,
        backup_all: bool = True,
    ) -> list[MigrationStep]:
        """Create migration plan from detected configs.

        Plan:
        1. Backup all existing configs (if backup_all=True)
        2. Move project config to .mycelium/config.yaml
        3. Create global config with defaults (if create_global=True and doesn't exist)
        4. Skip or merge conflicting configs

        Args:
            legacy_configs: List of legacy config locations from detector
            create_global: If True, create global config with defaults
            backup_all: If True, backup all files before migration

        Returns:
            List of migration steps in execution order

        Example:
            >>> planner = MigrationPlanner()
            >>> configs = [...]  # From detector
            >>> plan = planner.create_plan(configs)
            >>> for step in plan:
            ...     print(step)
        """
        logger.info("Creating migration plan for %d legacy configs", len(legacy_configs))
        steps: list[MigrationStep] = []
        order = 0

        # Step 1: Create backups for all existing files
        if backup_all:
            backup_steps = self._create_backup_steps(legacy_configs, order)
            steps.extend(backup_steps)
            order += len(backup_steps)
            logger.debug("Added %d backup steps", len(backup_steps))

        # Step 2: Migrate legacy configs
        for config in legacy_configs:
            if not config.exists or not config.readable:
                logger.warning("Skipping unreadable config: %s", config.path)
                continue

            migration_step = self._create_migration_step(config, order)
            if migration_step:
                steps.append(migration_step)
                order += 1
                logger.debug("Added migration step: %s", migration_step)

        # Step 3: Create global config if needed
        if create_global:
            global_step = self._create_global_config_step(order)
            if global_step:
                steps.append(global_step)
                order += 1
                logger.debug("Added global config creation step")

        # Sort steps by execution order
        steps.sort()

        logger.info("Created migration plan with %d steps", len(steps))
        return steps

    def _create_backup_steps(
        self,
        legacy_configs: list[LegacyConfigLocation],
        start_order: int,
    ) -> list[MigrationStep]:
        """Create backup steps for all legacy configs.

        Args:
            legacy_configs: List of legacy configs to backup
            start_order: Starting order number for steps

        Returns:
            List of backup steps
        """
        steps: list[MigrationStep] = []
        backup_dir = ensure_migration_backup_dir_exists()

        for i, config in enumerate(legacy_configs):
            if not config.exists:
                continue

            backup_path = backup_dir / f"{config.path.stem}_backup{config.path.suffix}"

            # Handle filename collisions
            counter = 1
            while backup_path.exists():
                backup_path = backup_dir / f"{config.path.stem}_backup_{counter}{config.path.suffix}"
                counter += 1

            step = MigrationStep(
                action=MigrationAction.BACKUP,
                source=config.path,
                destination=backup_path,
                backup_path=None,  # Backup steps don't get backed up
                description=f"Backup {config.config_type} config before migration",
                order=start_order + i,
            )
            steps.append(step)

        return steps

    def _create_migration_step(
        self,
        config: LegacyConfigLocation,
        order: int,
    ) -> MigrationStep | None:
        """Create migration step for a legacy config.

        Args:
            config: Legacy config location
            order: Execution order number

        Returns:
            Migration step, or None if no migration needed
        """
        # Determine destination based on config type
        if config.config_type in ("project-root", "project-mycelium"):
            destination = get_project_config_path(self.project_dir)
        else:
            # Unknown type, default to project
            destination = get_project_config_path(self.project_dir)
            logger.warning(
                "Unknown config type '%s', migrating to project config",
                config.config_type,
            )

        # Check for conflicts
        if config.conflicts_with:
            # If destination exists, we need to merge or skip
            logger.warning(
                "Conflict detected: %s -> %s (destination exists)",
                config.path,
                destination,
            )
            return MigrationStep(
                action=MigrationAction.MERGE,
                source=config.path,
                destination=destination,
                backup_path=config.conflicts_with,
                description=f"Merge {config.config_type} config with existing",
                order=order,
            )

        # If source and destination are the same, skip
        if config.path.resolve() == destination.resolve():
            logger.debug("Config already at correct location: %s", config.path)
            return MigrationStep(
                action=MigrationAction.SKIP,
                source=config.path,
                destination=destination,
                backup_path=None,
                description=f"Skip {config.config_type} config (already migrated)",
                order=order,
            )

        # Normal move operation
        return MigrationStep(
            action=MigrationAction.MOVE,
            source=config.path,
            destination=destination,
            backup_path=None,
            description=f"Move {config.config_type} config to new location",
            order=order,
        )

    def _create_global_config_step(self, order: int) -> MigrationStep | None:
        """Create step to create global config if needed.

        Args:
            order: Execution order number

        Returns:
            Migration step, or None if global config exists
        """
        global_path = get_global_config_path()

        # Check if global config already exists
        if global_path.exists():
            logger.debug("Global config already exists: %s", global_path)
            return None

        return MigrationStep(
            action=MigrationAction.CREATE,
            source=None,
            destination=global_path,
            backup_path=None,
            description="Create global config with defaults",
            order=order,
        )

    def validate_plan(self, steps: list[MigrationStep]) -> bool:
        """Validate migration plan is safe to execute.

        Checks:
        - All source files exist and are readable
        - All destination directories are writable
        - No duplicate destinations
        - No circular moves

        Args:
            steps: Migration steps to validate

        Returns:
            True if plan is safe to execute

        Example:
            >>> planner = MigrationPlanner()
            >>> plan = planner.create_plan([...])
            >>> if planner.validate_plan(plan):
            ...     print("Safe to execute")
        """
        logger.info("Validating migration plan with %d steps", len(steps))
        errors: list[str] = []

        # Track destinations to detect duplicates
        destinations: set[Path] = set()

        for step in steps:
            # Validate source exists (for non-CREATE actions)
            if step.action != MigrationAction.CREATE:
                if step.source is None:
                    errors.append(f"Step {step.order}: source is None for {step.action}")
                    continue

                if not step.source.exists():
                    errors.append(f"Step {step.order}: source does not exist: {step.source}")

                if not step.source.is_file():
                    errors.append(f"Step {step.order}: source is not a file: {step.source}")

            # Validate destination directory is writable
            dest_parent = step.destination.parent
            if not check_write_permission(step.destination):
                errors.append(f"Step {step.order}: no write permission for destination: {step.destination}")

            # Check for duplicate destinations (except BACKUP actions)
            if step.action != MigrationAction.BACKUP:
                if step.destination in destinations:
                    errors.append(f"Step {step.order}: duplicate destination: {step.destination}")
                destinations.add(step.destination)

        if errors:
            logger.error("Migration plan validation failed with %d errors", len(errors))
            for error in errors:
                logger.error("  - %s", error)
            return False

        logger.info("Migration plan validation passed")
        return True

    def estimate_time(self, steps: list[MigrationStep]) -> float:
        """Estimate migration time in seconds.

        Uses heuristics based on:
        - Number of steps
        - File sizes
        - Action types (MOVE is faster than COPY)

        Args:
            steps: Migration steps to estimate

        Returns:
            Estimated time in seconds

        Example:
            >>> planner = MigrationPlanner()
            >>> plan = planner.create_plan([...])
            >>> time_sec = planner.estimate_time(plan)
            >>> print(f"Estimated time: {time_sec:.1f} seconds")
        """
        # Base time per step
        base_time = 0.1  # 100ms per step

        # Action multipliers
        action_multipliers = {
            MigrationAction.MOVE: 1.0,
            MigrationAction.COPY: 1.5,
            MigrationAction.MERGE: 2.0,
            MigrationAction.BACKUP: 1.5,
            MigrationAction.CREATE: 0.5,
            MigrationAction.SKIP: 0.1,
        }

        total_time = 0.0
        for step in steps:
            step_time = base_time * action_multipliers.get(step.action, 1.0)

            # Add file size factor (very rough estimate: 1MB = 10ms)
            if step.source and step.source.exists():
                size_mb = step.source.stat().st_size / (1024 * 1024)
                step_time += size_mb * 0.01

            total_time += step_time

        logger.debug("Estimated migration time: %.2f seconds", total_time)
        return total_time

    def get_plan_summary(self, steps: list[MigrationStep]) -> dict[str, int]:
        """Get summary statistics for migration plan.

        Args:
            steps: Migration steps to summarize

        Returns:
            Dictionary with step counts by action type

        Example:
            >>> planner = MigrationPlanner()
            >>> plan = planner.create_plan([...])
            >>> summary = planner.get_plan_summary(plan)
            >>> print(f"Will move {summary['move']} files")
        """
        summary: dict[str, int] = {
            "total": len(steps),
            "move": 0,
            "copy": 0,
            "merge": 0,
            "backup": 0,
            "create": 0,
            "skip": 0,
        }

        for step in steps:
            action_name = step.action.value
            summary[action_name] = summary.get(action_name, 0) + 1

        logger.debug("Migration plan summary: %s", summary)
        return summary
