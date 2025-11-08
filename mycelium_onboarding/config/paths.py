"""XDG-compliant path resolution for Mycelium configuration.

This module provides cross-platform, XDG-compliant path resolution for
global and project-local configuration files, as well as data, state,
and cache directories.

Follows the XDG Base Directory Specification on Linux/macOS and uses
platform-appropriate defaults on Windows.

Example:
    >>> from mycelium_onboarding.config.paths import (
    ...     get_global_config_path,
    ...     get_project_config_path,
    ... )
    >>> global_config = get_global_config_path()
    >>> project_config = get_project_config_path()
"""

from __future__ import annotations

from pathlib import Path

import platformdirs

from mycelium_onboarding.config.platform import Platform, get_platform

# Application identifier for platformdirs
APP_NAME = "mycelium"
APP_AUTHOR = "mycelium"  # Used on Windows

# Default configuration file names
GLOBAL_CONFIG_FILENAME = "config.yaml"
PROJECT_CONFIG_DIRNAME = ".mycelium"
PROJECT_CONFIG_FILENAME = "config.yaml"


def get_global_config_path() -> Path:
    """Get the XDG-compliant global configuration file path.

    Returns platform-appropriate paths:
        - Linux: ~/.config/mycelium/config.yaml
        - macOS: ~/Library/Application Support/mycelium/config.yaml
        - Windows: %APPDATA%\\mycelium\\config.yaml

    Returns:
        Path to global configuration file

    Example:
        >>> path = get_global_config_path()
        >>> path.parent.name
        'mycelium'
        >>> path.name
        'config.yaml'
    """
    config_dir = Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR))
    return config_dir / GLOBAL_CONFIG_FILENAME


def get_project_config_path(project_root: Path | str | None = None) -> Path:
    """Get the project-local configuration file path.

    Returns:
        <project_root>/.mycelium/config.yaml

    Args:
        project_root: Project root directory. If None, uses current working directory.

    Returns:
        Path to project-local configuration file

    Example:
        >>> path = get_project_config_path("/home/user/myproject")
        >>> str(path)
        '/home/user/myproject/.mycelium/config.yaml'
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)

    return project_root / PROJECT_CONFIG_DIRNAME / PROJECT_CONFIG_FILENAME


def get_data_dir() -> Path:
    """Get the XDG-compliant data directory.

    Returns platform-appropriate paths:
        - Linux: ~/.local/share/mycelium
        - macOS: ~/Library/Application Support/mycelium
        - Windows: %APPDATA%\\mycelium

    Returns:
        Path to application data directory

    Example:
        >>> data_dir = get_data_dir()
        >>> data_dir.name
        'mycelium'
    """
    return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))


def get_state_dir() -> Path:
    """Get the XDG-compliant state directory.

    Used for logs, history, and other state files.

    Returns platform-appropriate paths:
        - Linux: ~/.local/state/mycelium
        - macOS: ~/Library/Application Support/mycelium
        - Windows: %LOCALAPPDATA%\\mycelium

    Returns:
        Path to application state directory

    Example:
        >>> state_dir = get_state_dir()
        >>> state_dir.name
        'mycelium'
    """
    return Path(platformdirs.user_state_dir(APP_NAME, APP_AUTHOR))


def get_cache_dir() -> Path:
    """Get the XDG-compliant cache directory.

    Returns platform-appropriate paths:
        - Linux: ~/.cache/mycelium
        - macOS: ~/Library/Caches/mycelium
        - Windows: %LOCALAPPDATA%\\mycelium\\Cache

    Returns:
        Path to application cache directory

    Example:
        >>> cache_dir = get_cache_dir()
        >>> 'mycelium' in str(cache_dir)
        True
    """
    return Path(platformdirs.user_cache_dir(APP_NAME, APP_AUTHOR))


def get_log_dir() -> Path:
    """Get the directory for application logs.

    Returns platform-appropriate paths:
        - Linux: ~/.local/state/mycelium/logs
        - macOS: ~/Library/Logs/mycelium
        - Windows: %LOCALAPPDATA%\\mycelium\\logs

    Returns:
        Path to application log directory

    Example:
        >>> log_dir = get_log_dir()
        >>> log_dir.name
        'logs'
    """
    return Path(platformdirs.user_log_dir(APP_NAME, APP_AUTHOR))


def ensure_dir_exists(path: Path, mode: int = 0o755) -> Path:
    """Create directory if it doesn't exist, with proper permissions.

    Creates parent directories as needed (mkdir -p behavior).
    On POSIX systems, sets the specified mode. On Windows, mode is ignored.

    Args:
        path: Directory path to create
        mode: Permission mode (octal, e.g., 0o755). Only used on POSIX systems.

    Returns:
        The created/existing directory path

    Raises:
        OSError: If directory creation fails due to permissions or other errors
        ValueError: If path exists but is not a directory

    Example:
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> test_dir = temp_dir / "test" / "nested"
        >>> result = ensure_dir_exists(test_dir)
        >>> result.exists() and result.is_dir()
        True
    """
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"Path exists but is not a directory: {path}")
        return path

    # Create directory with parents
    try:
        path.mkdir(parents=True, exist_ok=True, mode=mode)
    except OSError as e:
        raise OSError(f"Failed to create directory {path}: {e}") from e

    # On POSIX systems, explicitly set permissions (mkdir mode can be affected by umask)
    platform = get_platform()
    if platform in {Platform.LINUX, Platform.MACOS}:
        try:
            path.chmod(mode)
        except OSError:
            # If chmod fails, directory was still created, so continue
            pass

    return path


def ensure_config_dir_exists() -> Path:
    """Ensure the global configuration directory exists.

    Returns:
        Path to the global configuration directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> config_dir = ensure_config_dir_exists()
        >>> config_dir.exists()
        True
    """
    config_path = get_global_config_path()
    return ensure_dir_exists(config_path.parent)


def ensure_data_dir_exists() -> Path:
    """Ensure the data directory exists.

    Returns:
        Path to the data directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> data_dir = ensure_data_dir_exists()
        >>> data_dir.exists()
        True
    """
    return ensure_dir_exists(get_data_dir())


def ensure_state_dir_exists() -> Path:
    """Ensure the state directory exists.

    Returns:
        Path to the state directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> state_dir = ensure_state_dir_exists()
        >>> state_dir.exists()
        True
    """
    return ensure_dir_exists(get_state_dir())


def ensure_cache_dir_exists() -> Path:
    """Ensure the cache directory exists.

    Returns:
        Path to the cache directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> cache_dir = ensure_cache_dir_exists()
        >>> cache_dir.exists()
        True
    """
    return ensure_dir_exists(get_cache_dir())


def ensure_log_dir_exists() -> Path:
    """Ensure the log directory exists.

    Returns:
        Path to the log directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> log_dir = ensure_log_dir_exists()
        >>> log_dir.exists()
        True
    """
    return ensure_dir_exists(get_log_dir())


def get_migration_backup_dir() -> Path:
    """Get the directory for configuration migration backups.

    Returns:
        Path to migration backup directory (within data directory)

    Example:
        >>> backup_dir = get_migration_backup_dir()
        >>> 'backups' in str(backup_dir)
        True
    """
    return get_data_dir() / "backups"


def ensure_migration_backup_dir_exists() -> Path:
    """Ensure the migration backup directory exists.

    Returns:
        Path to the migration backup directory

    Raises:
        OSError: If directory creation fails

    Example:
        >>> backup_dir = ensure_migration_backup_dir_exists()
        >>> backup_dir.exists()
        True
    """
    return ensure_dir_exists(get_migration_backup_dir())
