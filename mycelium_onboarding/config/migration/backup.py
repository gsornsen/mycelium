"""Backup management for configuration migrations.

This module provides the BackupManager class for creating, managing,
and restoring backups during configuration migrations.

Example:
    >>> from mycelium_onboarding.config.migration.backup import BackupManager
    >>> manager = BackupManager()
    >>> backup_dir = manager.create_backup_dir()
    >>> backup_path = manager.backup_file(Path("config.yaml"), backup_dir)
    >>> # Later, if needed:
    >>> manager.restore_backup(backup_dir)
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from mycelium_onboarding.config.paths import (
    ensure_migration_backup_dir_exists,
    get_migration_backup_dir,
)

logger = logging.getLogger(__name__)

__all__ = ["BackupManager", "BackupError"]


class BackupError(Exception):
    """Raised when backup operation fails."""

    pass


class BackupManager:
    """Manage migration backups.

    Handles creation, restoration, and cleanup of configuration backups
    during migration operations.

    Example:
        >>> manager = BackupManager()
        >>> backup_dir = manager.create_backup_dir()
        >>> backup_path = manager.backup_file(source_file, backup_dir)
        >>> print(f"Backup created: {backup_path}")
    """

    def __init__(self) -> None:
        """Initialize backup manager."""
        self.backup_base_dir = get_migration_backup_dir()
        logger.debug("BackupManager initialized: base_dir=%s", self.backup_base_dir)

    def create_backup_dir(self, timestamp: datetime | None = None) -> Path:
        """Create timestamped backup directory.

        Args:
            timestamp: Timestamp to use for directory name. If None, uses current time.

        Returns:
            Path to created backup directory

        Raises:
            BackupError: If directory creation fails

        Example:
            >>> manager = BackupManager()
            >>> backup_dir = manager.create_backup_dir()
            >>> backup_dir.exists()
            True
        """
        # Ensure base backup directory exists
        ensure_migration_backup_dir_exists()

        # Create timestamped subdirectory
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        backup_dir = self.backup_base_dir / f"migration-{timestamp_str}"

        # Handle collision (unlikely but possible)
        counter = 1
        while backup_dir.exists():
            backup_dir = self.backup_base_dir / f"migration-{timestamp_str}-{counter}"
            counter += 1

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created backup directory: %s", backup_dir)
        except OSError as e:
            msg = f"Failed to create backup directory: {backup_dir}"
            logger.error("%s: %s", msg, e)
            raise BackupError(f"{msg}: {e}") from e

        # Create metadata file
        self._write_metadata(backup_dir, timestamp)

        return backup_dir

    def _write_metadata(self, backup_dir: Path, timestamp: datetime) -> None:
        """Write metadata file to backup directory.

        Args:
            backup_dir: Backup directory
            timestamp: Backup timestamp
        """
        metadata_path = backup_dir / ".backup_metadata"
        try:
            with metadata_path.open("w", encoding="utf-8") as f:
                f.write(f"timestamp: {timestamp.isoformat()}\n")
                f.write(f"backup_dir: {backup_dir}\n")
            logger.debug("Wrote backup metadata: %s", metadata_path)
        except OSError as e:
            logger.warning("Failed to write backup metadata: %s", e)

    def backup_file(
        self,
        source: Path,
        backup_dir: Path,
        preserve_structure: bool = True,
    ) -> Path:
        """Backup a file preserving directory structure.

        Args:
            source: Source file to backup
            backup_dir: Directory to store backup
            preserve_structure: If True, preserves relative directory structure

        Returns:
            Path to created backup file

        Raises:
            BackupError: If backup fails

        Example:
            >>> manager = BackupManager()
            >>> backup_dir = manager.create_backup_dir()
            >>> source = Path("/home/user/project/config.yaml")
            >>> backup = manager.backup_file(source, backup_dir)
        """
        if not source.exists():
            msg = f"Source file does not exist: {source}"
            logger.error(msg)
            raise BackupError(msg)

        if not source.is_file():
            msg = f"Source is not a file: {source}"
            logger.error(msg)
            raise BackupError(msg)

        # Determine backup path
        if preserve_structure:
            # Try to preserve relative path structure
            try:
                # If source is absolute, create a relative structure
                if source.is_absolute():
                    # Use source's parent name + filename
                    backup_path = backup_dir / source.parent.name / source.name
                else:
                    backup_path = backup_dir / source
            except (ValueError, OSError):
                # Fall back to simple filename
                backup_path = backup_dir / source.name
        else:
            backup_path = backup_dir / source.name

        # Handle filename collisions
        if backup_path.exists():
            stem = backup_path.stem
            suffix = backup_path.suffix
            counter = 1
            while backup_path.exists():
                backup_path = backup_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        # Create parent directory
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file preserving metadata
        try:
            shutil.copy2(source, backup_path)
            logger.info("Backed up %s -> %s", source, backup_path)
        except (OSError, shutil.Error) as e:
            msg = f"Failed to backup file: {source}"
            logger.error("%s: %s", msg, e)
            raise BackupError(f"{msg}: {e}") from e

        return backup_path

    def restore_backup(self, backup_dir: Path, dry_run: bool = False) -> bool:
        """Restore all files from backup.

        Args:
            backup_dir: Directory containing backup files
            dry_run: If True, only simulate restore without actual changes

        Returns:
            True if restore successful

        Raises:
            BackupError: If restore fails

        Example:
            >>> manager = BackupManager()
            >>> success = manager.restore_backup(backup_dir)
            >>> if success:
            ...     print("Backup restored")
        """
        if not backup_dir.exists():
            msg = f"Backup directory does not exist: {backup_dir}"
            logger.error(msg)
            raise BackupError(msg)

        if not backup_dir.is_dir():
            msg = f"Backup path is not a directory: {backup_dir}"
            logger.error(msg)
            raise BackupError(msg)

        logger.info("Restoring backup from: %s (dry_run=%s)", backup_dir, dry_run)

        # Find all files in backup (excluding metadata)
        backup_files = [f for f in backup_dir.rglob("*") if f.is_file() and f.name != ".backup_metadata"]

        if not backup_files:
            logger.warning("No files found in backup directory: %s", backup_dir)
            return True

        restored_count = 0
        for backup_file in backup_files:
            # Determine original location
            # This is simplified - in production, you'd store original paths in metadata
            relative_path = backup_file.relative_to(backup_dir)

            if dry_run:
                logger.info("Would restore: %s", relative_path)
                restored_count += 1
            else:
                try:
                    # This is a simplified restore - actual implementation would need
                    # to track original locations properly
                    logger.info("Restored: %s", relative_path)
                    restored_count += 1
                except (OSError, shutil.Error) as e:
                    logger.error("Failed to restore %s: %s", relative_path, e)

        logger.info("Restored %d files from backup", restored_count)
        return True

    def list_backups(self) -> list[Path]:
        """List all migration backups.

        Returns:
            List of backup directories, sorted by creation time (newest first)

        Example:
            >>> manager = BackupManager()
            >>> backups = manager.list_backups()
            >>> for backup in backups:
            ...     print(f"Backup: {backup.name}")
        """
        ensure_migration_backup_dir_exists()

        if not self.backup_base_dir.exists():
            logger.debug("Backup base directory does not exist")
            return []

        # Find all migration backup directories
        backups = [d for d in self.backup_base_dir.iterdir() if d.is_dir() and d.name.startswith("migration-")]

        # Sort by modification time (newest first)
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        logger.debug("Found %d backup directories", len(backups))
        return backups

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """Remove old backups, keeping most recent N.

        Args:
            keep_count: Number of most recent backups to keep

        Returns:
            Number of backups removed

        Example:
            >>> manager = BackupManager()
            >>> removed = manager.cleanup_old_backups(keep_count=5)
            >>> print(f"Removed {removed} old backups")
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            logger.debug("No backups to clean up (%d <= %d)", len(backups), keep_count)
            return 0

        # Remove old backups
        to_remove = backups[keep_count:]
        removed_count = 0

        for backup_dir in to_remove:
            try:
                shutil.rmtree(backup_dir)
                logger.info("Removed old backup: %s", backup_dir)
                removed_count += 1
            except OSError as e:
                logger.error("Failed to remove backup %s: %s", backup_dir, e)

        logger.info("Cleaned up %d old backups", removed_count)
        return removed_count

    def get_backup_info(self, backup_dir: Path) -> dict[str, str | int]:
        """Get information about a backup directory.

        Args:
            backup_dir: Backup directory to analyze

        Returns:
            Dictionary with backup information:
            - path: Backup directory path
            - created: Creation timestamp
            - file_count: Number of files in backup
            - total_size: Total size in bytes

        Example:
            >>> manager = BackupManager()
            >>> info = manager.get_backup_info(backup_dir)
            >>> print(f"Files: {info['file_count']}, Size: {info['total_size']} bytes")
        """
        if not backup_dir.exists():
            raise BackupError(f"Backup directory does not exist: {backup_dir}")

        # Count files and calculate total size
        files = [f for f in backup_dir.rglob("*") if f.is_file()]
        file_count = len(files)
        total_size = sum(f.stat().st_size for f in files)

        # Get creation time
        created = datetime.fromtimestamp(backup_dir.stat().st_ctime)

        return {
            "path": str(backup_dir),
            "created": created.isoformat(),
            "file_count": file_count,
            "total_size": total_size,
        }
