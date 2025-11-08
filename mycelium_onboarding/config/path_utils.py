"""Path migration utilities for safe file operations.

This module provides safe file operations for configuration migration,
including atomic file moves, backup creation, permission checking, and
symlink handling.

All operations are designed to be safe and atomic, with proper error
handling and backup strategies.

Example:
    >>> from mycelium_onboarding.config.path_utils import (
    ...     find_legacy_configs,
    ...     atomic_move,
    ... )
    >>> legacy_files = find_legacy_configs()
    >>> for old_path in legacy_files:
    ...     atomic_move(old_path, new_path, backup=True)
"""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from mycelium_onboarding.config.paths import (
    ensure_migration_backup_dir_exists,
)


class PathMigrationError(Exception):
    """Base exception for path migration errors."""

    pass


class PermissionError(PathMigrationError):
    """Raised when permission check fails."""

    pass


class SymlinkError(PathMigrationError):
    """Raised when unsafe symlink is detected."""

    pass


class AtomicMoveError(PathMigrationError):
    """Raised when atomic move operation fails."""

    pass


class YAMLError(PathMigrationError):
    """Raised when YAML read/write operation fails."""

    pass


def find_legacy_configs(
    search_paths: list[Path | str] | None = None,
    legacy_filename: str = "mycelium-config.yaml",
) -> list[Path]:
    """Find legacy configuration files in specified paths.

    Searches for old-style configuration files that need migration.

    Args:
        search_paths: List of paths to search. If None, searches common locations:
            - Current working directory
            - User home directory
            - Project .mycelium directory
        legacy_filename: Name of legacy config file to search for

    Returns:
        List of paths to found legacy configuration files

    Example:
        >>> legacy_files = find_legacy_configs()
        >>> isinstance(legacy_files, list)
        True
        >>> all(isinstance(p, Path) for p in legacy_files)
        True
    """
    if search_paths is None:
        # Default search paths
        search_paths = [
            Path.cwd(),
            Path.home(),
            Path.cwd() / ".mycelium",
        ]
    else:
        search_paths = [Path(p) for p in search_paths]

    found_configs: list[Path] = []

    for search_path in search_paths:
        if not search_path.exists() or not search_path.is_dir():
            continue

        # Check for legacy config in this directory
        legacy_path = search_path / legacy_filename
        if legacy_path.exists() and legacy_path.is_file():
            found_configs.append(legacy_path)

    return found_configs


def check_write_permission(path: Path) -> bool:
    """Check if we have write permission to a path.

    Checks both the file (if it exists) and the parent directory.

    Args:
        path: Path to check

    Returns:
        True if we have write permission, False otherwise

    Example:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> test_file = temp_dir / "test.txt"
        >>> check_write_permission(test_file)
        True
    """
    # If file exists, check if we can write to it
    if path.exists():
        return os.access(path, os.W_OK)

    # If file doesn't exist, check if we can write to parent directory
    parent = path.parent
    if not parent.exists():
        # Try to create parent directories to test
        try:
            parent.mkdir(parents=True, exist_ok=True)
            can_write = os.access(parent, os.W_OK)
            # Clean up if we created it
            if not any(parent.iterdir()):
                parent.rmdir()
            return can_write
        except OSError:
            return False

    return os.access(parent, os.W_OK)


def is_symlink_safe(path: Path, allow_symlinks: bool = False) -> bool:
    """Check if a path is safe from symlink attacks.

    Args:
        path: Path to check
        allow_symlinks: If True, allows symlinks. If False, rejects any symlink.

    Returns:
        True if path is safe, False if it's an unsafe symlink

    Raises:
        SymlinkError: If path is an unsafe symlink

    Example:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> regular_file = temp_dir / "regular.txt"
        >>> regular_file.touch()
        >>> is_symlink_safe(regular_file)
        True
    """
    if not path.exists():
        # Non-existent paths are safe
        return True

    # Check if path is a symlink
    if path.is_symlink():
        if not allow_symlinks:
            raise SymlinkError(f"Path is a symlink (not allowed): {path}")

        # If symlinks are allowed, verify the target is within safe bounds
        try:
            resolved = path.resolve()
            # Check if resolved path is absolute (not relative escape)
            if not resolved.is_absolute():
                raise SymlinkError(f"Symlink target is not absolute: {path} -> {resolved}")
        except (OSError, RuntimeError) as e:
            raise SymlinkError(f"Cannot resolve symlink: {path}") from e

    # Check parent directories for symlinks
    for parent in path.parents:
        if parent.is_symlink() and not allow_symlinks:
            raise SymlinkError(f"Parent directory is a symlink: {parent}")

    return True


def create_backup(
    path: Path,
    backup_dir: Path | None = None,
    timestamp: bool = True,
) -> Path:
    """Create a backup of a file before migration.

    Args:
        path: File to backup
        backup_dir: Directory to store backup. If None, uses migration backup dir.
        timestamp: If True, adds timestamp to backup filename

    Returns:
        Path to created backup file

    Raises:
        PathMigrationError: If backup creation fails

    Example:
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> test_file = temp_dir / "test.txt"
        >>> test_file.write_text("content")
        7
        >>> backup = create_backup(test_file, backup_dir=temp_dir)
        >>> backup.exists()
        True
    """
    if not path.exists():
        raise PathMigrationError(f"Cannot backup non-existent file: {path}")

    if backup_dir is None:
        backup_dir = ensure_migration_backup_dir_exists()
    else:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp_str}{path.suffix}"
    else:
        backup_name = f"{path.name}.bak"

    backup_path = backup_dir / backup_name

    # Handle filename collisions
    counter = 1
    while backup_path.exists():
        if timestamp:
            backup_name = f"{path.stem}_{timestamp_str}_{counter}{path.suffix}"
        else:
            backup_name = f"{path.name}.bak.{counter}"
        backup_path = backup_dir / backup_name
        counter += 1

    # Create backup
    try:
        shutil.copy2(path, backup_path)
    except OSError as e:
        raise PathMigrationError(f"Failed to create backup: {e}") from e

    return backup_path


def atomic_move(
    src: Path | str,
    dst: Path | str,
    backup: bool = True,
    allow_symlinks: bool = False,
) -> Path:
    """Atomically move a file from source to destination.

    This operation is as atomic as possible on the target platform:
    - On POSIX: Uses os.rename which is atomic on the same filesystem
    - On Windows: Falls back to copy + delete

    Args:
        src: Source file path
        dst: Destination file path
        backup: If True and destination exists, creates backup before overwriting
        allow_symlinks: If True, allows symlink sources/destinations

    Returns:
        Path to destination file

    Raises:
        PathMigrationError: If source doesn't exist or move fails
        PermissionError: If lacking write permissions
        SymlinkError: If unsafe symlink detected
        AtomicMoveError: If atomic move operation fails

    Example:
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> src_file = temp_dir / "source.txt"
        >>> src_file.write_text("content")
        7
        >>> dst_file = temp_dir / "dest.txt"
        >>> result = atomic_move(src_file, dst_file, backup=False)
        >>> result.exists() and not src_file.exists()
        True
    """
    src_path = Path(src)
    dst_path = Path(dst)

    # Validation
    if not src_path.exists():
        raise PathMigrationError(f"Source file does not exist: {src_path}")

    if not src_path.is_file():
        raise PathMigrationError(f"Source is not a file: {src_path}")

    # Check symlink safety
    is_symlink_safe(src_path, allow_symlinks=allow_symlinks)
    is_symlink_safe(dst_path.parent, allow_symlinks=allow_symlinks)

    # Check permissions
    if not check_write_permission(src_path.parent):
        raise PermissionError(f"No write permission for source directory: {src_path.parent}")

    if not check_write_permission(dst_path):
        raise PermissionError(f"No write permission for destination: {dst_path}")

    # Create destination directory if needed
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing destination if requested
    if backup and dst_path.exists():
        try:
            create_backup(dst_path)
        except PathMigrationError as e:
            raise AtomicMoveError(f"Failed to create backup before move: {e}") from e

    # Perform atomic move
    try:
        # Try atomic rename first (works on same filesystem)
        src_path.rename(dst_path)
    except OSError:
        # Fall back to copy + delete for cross-filesystem moves
        try:
            shutil.copy2(src_path, dst_path)
            src_path.unlink()
        except OSError as e:
            raise AtomicMoveError(f"Failed to move file: {e}") from e

    return dst_path


def safe_read_yaml(path: Path | str) -> dict[str, Any]:
    """Safely read a YAML configuration file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        PathMigrationError: If file doesn't exist
        YAMLError: If YAML parsing fails

    Example:
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> yaml_file = temp_dir / "config.yaml"
        >>> yaml_file.write_text("key: value\\n")
        11
        >>> data = safe_read_yaml(yaml_file)
        >>> data['key']
        'value'
    """
    path = Path(path)

    if not path.exists():
        raise PathMigrationError(f"YAML file does not exist: {path}")

    if not path.is_file():
        raise PathMigrationError(f"Path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if content is not None else {}
    except yaml.YAMLError as e:
        raise YAMLError(f"Failed to parse YAML file {path}: {e}") from e
    except OSError as e:
        raise YAMLError(f"Failed to read YAML file {path}: {e}") from e


def safe_write_yaml(
    path: Path | str,
    data: dict[str, Any],
    backup: bool = True,
    atomic: bool = True,
) -> Path:
    """Safely write a YAML configuration file.

    Args:
        path: Path to YAML file
        data: Dictionary to serialize to YAML
        backup: If True and file exists, creates backup before writing
        atomic: If True, writes to temp file first then moves (atomic write)

    Returns:
        Path to written file

    Raises:
        PermissionError: If lacking write permissions
        YAMLError: If YAML serialization or write fails

    Example:
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> yaml_file = temp_dir / "config.yaml"
        >>> result = safe_write_yaml(yaml_file, {"key": "value"}, backup=False)
        >>> result.exists()
        True
    """
    path = Path(path)

    # Check permissions
    if not check_write_permission(path):
        raise PermissionError(f"No write permission for file: {path}")

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing file if requested
    if backup and path.exists():
        try:
            create_backup(path)
        except PathMigrationError as e:
            raise YAMLError(f"Failed to create backup before write: {e}") from e

    # Serialize to YAML
    try:
        yaml_content = yaml.safe_dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
    except yaml.YAMLError as e:
        raise YAMLError(f"Failed to serialize data to YAML: {e}") from e

    # Write file
    if atomic:
        # Atomic write: write to temp file, then rename
        try:
            # Create temp file in same directory as target (for same-filesystem rename)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                delete=False,
                suffix=".tmp",
            ) as f:
                temp_path = Path(f.name)
                f.write(yaml_content)

            # Atomic rename
            temp_path.rename(path)
        except OSError as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise YAMLError(f"Failed to write YAML file {path}: {e}") from e
    else:
        # Direct write (not atomic)
        try:
            with path.open("w", encoding="utf-8") as f:
                f.write(yaml_content)
        except OSError as e:
            raise YAMLError(f"Failed to write YAML file {path}: {e}") from e

    return path
