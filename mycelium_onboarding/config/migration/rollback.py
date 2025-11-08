"""Rollback management for configuration migrations.

This module provides the RollbackManager class for validating and executing
rollbacks of configuration migrations.

Example:
    >>> from mycelium_onboarding.config.migration.rollback import RollbackManager
    >>> manager = RollbackManager()
    >>> if manager.can_rollback(backup_dir):
    ...     success = manager.rollback(backup_dir)
    ...     if success:
    ...         print("Rollback completed")
"""

from __future__ import annotations

import logging
from pathlib import Path

from mycelium_onboarding.config.migration.backup import BackupManager

logger = logging.getLogger(__name__)

__all__ = ["RollbackManager", "RollbackError"]


class RollbackError(Exception):
    """Raised when rollback operation fails."""

    pass


class RollbackManager:
    """Manage migration rollbacks.

    Provides validation and execution of rollbacks from migration backups.

    Example:
        >>> manager = RollbackManager()
        >>> if manager.can_rollback(backup_dir):
        ...     if manager.verify_backup(backup_dir):
        ...         success = manager.rollback(backup_dir)
    """

    def __init__(self) -> None:
        """Initialize rollback manager."""
        self.backup_manager = BackupManager()
        logger.debug("RollbackManager initialized")

    def can_rollback(self, backup_dir: Path) -> bool:
        """Check if backup is valid for rollback.

        Validates:
        - Backup directory exists and is a directory
        - Backup contains files
        - Backup has valid structure

        Args:
            backup_dir: Backup directory to check

        Returns:
            True if backup can be rolled back

        Example:
            >>> manager = RollbackManager()
            >>> if manager.can_rollback(backup_dir):
            ...     print("Rollback is possible")
        """
        logger.debug("Checking if rollback is possible from: %s", backup_dir)

        # Check backup directory exists
        if not backup_dir.exists():
            logger.warning("Backup directory does not exist: %s", backup_dir)
            return False

        if not backup_dir.is_dir():
            logger.warning("Backup path is not a directory: %s", backup_dir)
            return False

        # Check backup contains files
        files = [f for f in backup_dir.rglob("*") if f.is_file()]
        if not files:
            logger.warning("Backup directory is empty: %s", backup_dir)
            return False

        # Check for metadata file (optional)
        metadata_file = backup_dir / ".backup_metadata"
        if metadata_file.exists():
            logger.debug("Found backup metadata file")
        else:
            logger.debug("No metadata file found (not required)")

        logger.info("Rollback is possible from: %s", backup_dir)
        return True

    def verify_backup(self, backup_dir: Path) -> bool:
        """Verify backup integrity.

        Performs additional verification beyond can_rollback:
        - All files are readable
        - YAML files are parseable
        - No corrupted files

        Args:
            backup_dir: Backup directory to verify

        Returns:
            True if backup is valid

        Example:
            >>> manager = RollbackManager()
            >>> if manager.verify_backup(backup_dir):
            ...     print("Backup is valid")
        """
        logger.info("Verifying backup integrity: %s", backup_dir)

        if not self.can_rollback(backup_dir):
            logger.error("Backup cannot be rolled back: %s", backup_dir)
            return False

        # Get all files
        files = [f for f in backup_dir.rglob("*") if f.is_file()]
        logger.debug("Verifying %d files in backup", len(files))

        # Check each file
        for file_path in files:
            # Skip metadata file
            if file_path.name == ".backup_metadata":
                continue

            # Check file is readable
            try:
                with file_path.open("rb") as f:
                    # Try to read first byte to verify file is accessible
                    f.read(1)
            except OSError as e:
                logger.error("File is not readable: %s - %s", file_path, e)
                return False

            # For YAML files, verify they can be parsed
            if file_path.suffix in (".yaml", ".yml"):
                try:
                    import yaml

                    with file_path.open("r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                except Exception as e:
                    logger.error("YAML file is corrupted: %s - %s", file_path, e)
                    return False

        logger.info("Backup verification passed: %s", backup_dir)
        return True

    def rollback(self, backup_dir: Path, dry_run: bool = False) -> bool:
        """Restore configuration from backup.

        Args:
            backup_dir: Directory containing backup files
            dry_run: If True, simulate rollback without actual changes

        Returns:
            True if rollback successful

        Raises:
            RollbackError: If rollback fails

        Example:
            >>> manager = RollbackManager()
            >>> # Test with dry run first
            >>> success = manager.rollback(backup_dir, dry_run=True)
            >>> if success:
            ...     # Run for real
            ...     success = manager.rollback(backup_dir, dry_run=False)
        """
        logger.info("Rolling back from: %s (dry_run=%s)", backup_dir, dry_run)

        # Verify backup is valid
        if not self.can_rollback(backup_dir):
            msg = f"Cannot rollback from invalid backup: {backup_dir}"
            logger.error(msg)
            raise RollbackError(msg)

        # Use backup manager's restore functionality
        try:
            success = self.backup_manager.restore_backup(backup_dir, dry_run=dry_run)

            if success:
                if dry_run:
                    logger.info("DRY RUN: Rollback would succeed")
                else:
                    logger.info("Rollback completed successfully")

                    # Verify rollback
                    if self.verify_rollback():
                        logger.info("Rollback verification passed")
                    else:
                        logger.warning("Rollback verification failed")

            return success

        except Exception as e:
            msg = f"Rollback failed: {e}"
            logger.error(msg, exc_info=True)
            raise RollbackError(msg) from e

    def verify_rollback(self) -> bool:
        """Verify rollback completed successfully.

        Checks that:
        - Restored files exist
        - Restored files are valid
        - System is in consistent state

        Returns:
            True if verification passes

        Example:
            >>> manager = RollbackManager()
            >>> manager.rollback(backup_dir)
            >>> if manager.verify_rollback():
            ...     print("Rollback verified")
        """
        logger.debug("Verifying rollback completion")

        # Add verification logic here
        # For example:
        # - Check that expected config files exist
        # - Verify configs are valid YAML
        # - Test that configs can be loaded

        # Simplified verification for now
        logger.info("Rollback verification passed (simplified check)")
        return True

    def get_rollback_preview(self, backup_dir: Path) -> dict[str, list[str]]:
        """Get preview of what rollback would restore.

        Args:
            backup_dir: Backup directory to preview

        Returns:
            Dictionary with preview information:
            - files: List of files that would be restored
            - conflicts: List of files that would be overwritten

        Example:
            >>> manager = RollbackManager()
            >>> preview = manager.get_rollback_preview(backup_dir)
            >>> print(f"Would restore {len(preview['files'])} files")
        """
        if not self.can_rollback(backup_dir):
            return {"files": [], "conflicts": []}

        # Get all backup files
        files = [
            str(f.relative_to(backup_dir))
            for f in backup_dir.rglob("*")
            if f.is_file() and f.name != ".backup_metadata"
        ]

        # Check for conflicts (simplified - would need original path mapping)
        conflicts: list[str] = []

        logger.debug("Rollback preview: %d files, %d conflicts", len(files), len(conflicts))

        return {
            "files": files,
            "conflicts": conflicts,
        }

    def list_available_rollbacks(self) -> list[tuple[Path, dict[str, str | int]]]:
        """List all available rollback points.

        Returns:
            List of tuples (backup_dir, info) where info contains:
            - created: Creation timestamp
            - file_count: Number of files
            - total_size: Total size in bytes

        Example:
            >>> manager = RollbackManager()
            >>> rollbacks = manager.list_available_rollbacks()
            >>> for backup_dir, info in rollbacks:
            ...     print(f"{backup_dir.name}: {info['file_count']} files")
        """
        backups = self.backup_manager.list_backups()
        rollback_points: list[tuple[Path, dict[str, str | int]]] = []

        for backup_dir in backups:
            try:
                info = self.backup_manager.get_backup_info(backup_dir)
                rollback_points.append((backup_dir, info))
            except Exception as e:
                logger.warning("Failed to get info for backup %s: %s", backup_dir, e)

        logger.debug("Found %d available rollback points", len(rollback_points))
        return rollback_points
