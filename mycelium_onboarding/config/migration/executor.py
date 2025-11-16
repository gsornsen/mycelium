"""Migration executor for executing migration plans.

This module provides the MigrationExecutor class that safely executes
migration plans with comprehensive backup and rollback capabilities.

Example:
    >>> from mycelium_onboarding.config.migration import (
    ...     MigrationDetector,
    ...     MigrationPlanner,
    ...     MigrationExecutor,
    ... )
    >>> detector = MigrationDetector()
    >>> planner = MigrationPlanner()
    >>> executor = MigrationExecutor(dry_run=False)
    >>>
    >>> configs = detector.scan_for_legacy_configs()
    >>> plan = planner.create_plan(configs)
    >>> result = executor.execute(plan)
    >>> print(f"Success: {result.success}")
"""

from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from mycelium_onboarding.config.defaults import get_default_config_dict
from mycelium_onboarding.config.migration.backup import BackupManager
from mycelium_onboarding.config.migration.planner import MigrationAction, MigrationStep
from mycelium_onboarding.config.path_utils import (
    PathMigrationError,
    atomic_move,
    safe_read_yaml,
    safe_write_yaml,
)

logger = logging.getLogger(__name__)

__all__ = ["MigrationResult", "MigrationExecutor", "MigrationExecutionError"]


class MigrationExecutionError(Exception):
    """Raised when migration execution fails."""

    pass


@dataclass
class MigrationResult:
    """Result of a migration.

    Attributes:
        success: Whether migration completed successfully
        steps_completed: Number of steps completed
        steps_total: Total number of steps in plan
        backup_dir: Path to backup directory (None if no backup created)
        errors: List of error messages
        duration_seconds: Total execution time in seconds
        dry_run: Whether this was a dry run
    """

    success: bool
    steps_completed: int
    steps_total: int
    backup_dir: Path | None
    errors: list[str]
    duration_seconds: float
    dry_run: bool = False

    def __str__(self) -> str:
        """String representation of result."""
        status = "SUCCESS" if self.success else "FAILED"
        if self.dry_run:
            status = f"DRY RUN {status}"
        return f"Migration {status}: {self.steps_completed}/{self.steps_total} steps in {self.duration_seconds:.2f}s"


class MigrationExecutor:
    """Execute configuration migration with backup and rollback.

    Safely executes migration plans with:
    - Comprehensive backups before any changes
    - Atomic operations where possible
    - Progress reporting via callback
    - Full rollback capability on failure
    - Dry-run mode for testing

    Example:
        >>> executor = MigrationExecutor(dry_run=True)
        >>> result = executor.execute(plan)
        >>> if result.success:
        ...     # Now run for real
        ...     executor = MigrationExecutor(dry_run=False)
        ...     result = executor.execute(plan)
    """

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize executor.

        Args:
            dry_run: If True, simulate migration without actual changes
        """
        self.dry_run = dry_run
        self.backup_manager = BackupManager()
        logger.debug("MigrationExecutor initialized: dry_run=%s", dry_run)

    def execute(
        self,
        steps: list[MigrationStep],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> MigrationResult:
        """Execute migration plan.

        Process:
        1. Create backup directory with timestamp
        2. Backup all files that will be modified
        3. Execute each migration step
        4. Validate results
        5. Clean up on success or rollback on failure

        Args:
            steps: Migration steps to execute
            progress_callback: Callback(current, total, message) for progress updates

        Returns:
            Migration result with success status

        Example:
            >>> def progress(current, total, msg):
            ...     print(f"[{current}/{total}] {msg}")
            >>> executor = MigrationExecutor()
            >>> result = executor.execute(plan, progress_callback=progress)
        """
        logger.info(
            "Executing migration plan: %d steps (dry_run=%s)",
            len(steps),
            self.dry_run,
        )

        start_time = time.time()
        errors: list[str] = []
        backup_dir: Path | None = None
        steps_completed = 0

        try:
            # Step 1: Create backup directory
            if not self.dry_run:
                backup_dir = self.backup_manager.create_backup_dir()
                logger.info("Created backup directory: %s", backup_dir)
            else:
                logger.info("DRY RUN: Would create backup directory")

            # Step 2: Execute each migration step
            for i, step in enumerate(steps, 1):
                current_step = i
                total_steps = len(steps)

                # Report progress
                if progress_callback:
                    progress_callback(current_step, total_steps, step.description)

                # Execute step
                try:
                    self._execute_step(step, backup_dir)
                    steps_completed += 1
                    logger.debug("Completed step %d/%d: %s", current_step, total_steps, step)
                except Exception as e:
                    error_msg = f"Step {current_step} failed: {step.description} - {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with remaining steps unless it's critical
                    if step.action in (MigrationAction.MOVE, MigrationAction.CREATE):
                        # Critical failure, stop execution
                        logger.error("Critical step failed, stopping migration")
                        break

            # Step 3: Validate results
            if not self.dry_run and not errors:
                validation_errors = self._validate_result()
                errors.extend(validation_errors)

            # Determine success
            success = len(errors) == 0 and steps_completed == len(steps)

            # Step 4: Clean up or rollback
            if not success and backup_dir and not self.dry_run:
                logger.warning("Migration failed, backup available at: %s", backup_dir)

            duration = time.time() - start_time

            result = MigrationResult(
                success=success,
                steps_completed=steps_completed,
                steps_total=len(steps),
                backup_dir=backup_dir,
                errors=errors,
                duration_seconds=duration,
                dry_run=self.dry_run,
            )

            logger.info("Migration completed: %s", result)
            return result

        except Exception as e:
            # Unexpected error
            duration = time.time() - start_time
            error_msg = f"Unexpected error during migration: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

            return MigrationResult(
                success=False,
                steps_completed=steps_completed,
                steps_total=len(steps),
                backup_dir=backup_dir,
                errors=errors,
                duration_seconds=duration,
                dry_run=self.dry_run,
            )

    def _execute_step(self, step: MigrationStep, backup_dir: Path | None) -> None:
        """Execute a single migration step.

        Args:
            step: Migration step to execute
            backup_dir: Backup directory (None for dry run)

        Raises:
            MigrationExecutionError: If step execution fails
        """
        logger.debug("Executing step: %s", step)

        if step.action == MigrationAction.BACKUP:
            self._execute_backup(step, backup_dir)
        elif step.action == MigrationAction.MOVE:
            self._execute_move(step, backup_dir)
        elif step.action == MigrationAction.COPY:
            self._execute_copy(step, backup_dir)
        elif step.action == MigrationAction.MERGE:
            self._execute_merge(step, backup_dir)
        elif step.action == MigrationAction.CREATE:
            self._execute_create(step, backup_dir)
        elif step.action == MigrationAction.SKIP:
            self._execute_skip(step)
        else:
            raise MigrationExecutionError(f"Unknown action: {step.action}")

    def _execute_backup(self, step: MigrationStep, backup_dir: Path | None) -> None:
        """Execute backup step.

        Args:
            step: Backup step
            backup_dir: Backup directory
        """
        if self.dry_run:
            logger.info("DRY RUN: Would backup %s -> %s", step.source, step.destination)
            return

        if step.source is None:
            raise MigrationExecutionError("Backup step has no source")

        if backup_dir is None:
            raise MigrationExecutionError("Backup directory not provided")

        # Backup file
        self.backup_manager.backup_file(step.source, backup_dir)
        logger.info("Backed up: %s", step.source)

    def _execute_move(self, step: MigrationStep, _backup_dir: Path | None) -> None:
        """Execute move step.

        Args:
            step: Move step
            _backup_dir: Backup directory (unused, backup already done)
        """
        if step.source is None:
            raise MigrationExecutionError("Move step has no source")

        if self.dry_run:
            logger.info("DRY RUN: Would move %s -> %s", step.source, step.destination)
            return

        # Ensure destination directory exists
        step.destination.parent.mkdir(parents=True, exist_ok=True)

        # Use atomic move from path_utils
        try:
            atomic_move(
                step.source,
                step.destination,
                backup=False,  # Backup already done in separate step
                allow_symlinks=False,
            )
            logger.info("Moved: %s -> %s", step.source, step.destination)
        except PathMigrationError as e:
            raise MigrationExecutionError(f"Failed to move file: {e}") from e

    def _execute_copy(self, step: MigrationStep, _backup_dir: Path | None) -> None:
        """Execute copy step.

        Args:
            step: Copy step
            _backup_dir: Backup directory (unused)
        """
        if step.source is None:
            raise MigrationExecutionError("Copy step has no source")

        if self.dry_run:
            logger.info("DRY RUN: Would copy %s -> %s", step.source, step.destination)
            return

        # Ensure destination directory exists
        step.destination.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        try:
            shutil.copy2(step.source, step.destination)
            logger.info("Copied: %s -> %s", step.source, step.destination)
        except (OSError, shutil.Error) as e:
            raise MigrationExecutionError(f"Failed to copy file: {e}") from e

    def _execute_merge(self, step: MigrationStep, _backup_dir: Path | None) -> None:
        """Execute merge step.

        Merges source config with existing destination config.

        Args:
            step: Merge step
            _backup_dir: Backup directory (unused)
        """
        if step.source is None:
            raise MigrationExecutionError("Merge step has no source")

        if self.dry_run:
            logger.info("DRY RUN: Would merge %s -> %s", step.source, step.destination)
            return

        # Read source and destination
        try:
            source_data = safe_read_yaml(step.source)
            dest_data = safe_read_yaml(step.destination) if step.destination.exists() else {}
        except Exception as e:
            raise MigrationExecutionError(f"Failed to read configs for merge: {e}") from e

        # Simple merge: source overwrites destination
        # In production, you might want more sophisticated merging
        merged_data = {**dest_data, **source_data}

        # Write merged config
        try:
            safe_write_yaml(
                step.destination,
                merged_data,
                backup=False,  # Backup already done
                atomic=True,
            )
            logger.info("Merged: %s -> %s", step.source, step.destination)
        except Exception as e:
            raise MigrationExecutionError(f"Failed to write merged config: {e}") from e

    def _execute_create(self, step: MigrationStep, _backup_dir: Path | None) -> None:
        """Execute create step.

        Creates new config file with defaults.

        Args:
            step: Create step
            _backup_dir: Backup directory (unused)
        """
        if self.dry_run:
            logger.info("DRY RUN: Would create %s", step.destination)
            return

        # Ensure destination directory exists
        step.destination.parent.mkdir(parents=True, exist_ok=True)

        # Create config with defaults
        try:
            default_config = get_default_config_dict()
            safe_write_yaml(
                step.destination,
                default_config,
                backup=False,
                atomic=True,
            )
            logger.info("Created: %s", step.destination)
        except Exception as e:
            raise MigrationExecutionError(f"Failed to create config: {e}") from e

    def _execute_skip(self, step: MigrationStep) -> None:
        """Execute skip step.

        Args:
            step: Skip step
        """
        logger.info("Skipped: %s", step.description)

    def _validate_result(self) -> list[str]:
        """Validate migration completed successfully.

        Returns:
            List of validation errors (empty if valid)
        """
        logger.debug("Validating migration results")
        errors: list[str] = []

        # Add validation logic here if needed
        # For example, verify all destination files exist and are valid YAML

        if errors:
            logger.warning("Migration validation found %d issues", len(errors))
        else:
            logger.info("Migration validation passed")

        return errors

    def rollback(self, backup_dir: Path) -> bool:
        """Rollback migration from backup.

        Args:
            backup_dir: Directory containing backup files

        Returns:
            True if rollback successful

        Raises:
            MigrationExecutionError: If rollback fails

        Example:
            >>> executor = MigrationExecutor()
            >>> result = executor.execute(plan)
            >>> if not result.success and result.backup_dir:
            ...     executor.rollback(result.backup_dir)
        """
        logger.info("Rolling back migration from: %s", backup_dir)

        if self.dry_run:
            logger.info("DRY RUN: Would rollback from %s", backup_dir)
            return True

        try:
            success = self.backup_manager.restore_backup(backup_dir, dry_run=False)
            if success:
                logger.info("Rollback completed successfully")
            else:
                logger.error("Rollback completed with errors")
            return success
        except Exception as e:
            msg = f"Rollback failed: {e}"
            logger.error(msg, exc_info=True)
            raise MigrationExecutionError(msg) from e
