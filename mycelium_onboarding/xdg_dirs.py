"""XDG Base Directory Specification compliant directory management.

This module provides functions to get and manage XDG-compliant directories
for the Mycelium onboarding system. All functions follow the XDG Base
Directory Specification (https://specifications.freedesktop.org/basedir-spec/).

Example:
    >>> from mycelium_onboarding.xdg_dirs import get_config_dir
    >>> config_dir = get_config_dir()
    >>> config_file = config_dir / "config.yaml"
"""

from __future__ import annotations

import logging
import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Final

# Module logger
logger = logging.getLogger(__name__)

# Module constants
DEFAULT_PROJECT_NAME: Final[str] = "mycelium"

# Directory permission modes
CONFIG_DIR_MODE: Final[int] = 0o700  # rwx------
DATA_DIR_MODE: Final[int] = 0o755  # rwxr-xr-x
CACHE_DIR_MODE: Final[int] = 0o755  # rwxr-xr-x
STATE_DIR_MODE: Final[int] = 0o700  # rwx------
PROJECT_DIR_MODE: Final[int] = 0o755  # rwxr-xr-x

# Export list
__all__ = [
    "get_config_dir",
    "get_data_dir",
    "get_cache_dir",
    "get_state_dir",
    "get_all_dirs",
    "clear_cache",
    "XDGDirectoryError",
]


class XDGDirectoryError(Exception):
    """Raised when XDG directory operations fail."""

    pass


@lru_cache(maxsize=1)
def get_config_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Get XDG config directory, creating if needed.

    Respects XDG_CONFIG_HOME environment variable, falling back to
    ~/.config if not set. Creates the directory with restrictive
    permissions (0700) to protect configuration data.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Returns:
        Path object pointing to the config directory

    Raises:
        XDGDirectoryError: If directory creation fails or is not writable

    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)
        PosixPath('/home/user/.config/mycelium')
    """
    base_str = os.environ.get("XDG_CONFIG_HOME")
    if base_str is None:
        base: Path = Path.home() / ".config"
    else:
        base = Path(base_str)

    config_dir: Path = base / project_name

    try:
        config_dir.mkdir(parents=True, exist_ok=True, mode=CONFIG_DIR_MODE)
        logger.debug("Config directory ensured: %s", config_dir)
    except OSError as e:
        logger.error("Failed to create config directory: %s", config_dir, exc_info=True)
        raise XDGDirectoryError(f"Failed to create config directory: {config_dir}\nError: {e}") from e

    # Verify directory is writable
    if not os.access(config_dir, os.W_OK):
        logger.error("Config directory not writable: %s", config_dir)
        raise XDGDirectoryError(f"Config directory is not writable: {config_dir}\nCheck permissions and try again")

    return config_dir


@lru_cache(maxsize=1)
def get_data_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Get XDG data directory, creating if needed.

    Respects XDG_DATA_HOME environment variable, falling back to
    ~/.local/share if not set.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Returns:
        Path object pointing to the data directory

    Raises:
        XDGDirectoryError: If directory creation fails or is not writable

    Example:
        >>> data_dir = get_data_dir()
        >>> templates = data_dir / "templates"
    """
    base_str = os.environ.get("XDG_DATA_HOME")
    if base_str is None:
        base: Path = Path.home() / ".local" / "share"
    else:
        base = Path(base_str)

    data_dir: Path = base / project_name

    try:
        data_dir.mkdir(parents=True, exist_ok=True, mode=DATA_DIR_MODE)
        logger.debug("Data directory ensured: %s", data_dir)
    except OSError as e:
        logger.error("Failed to create data directory: %s", data_dir, exc_info=True)
        raise XDGDirectoryError(f"Failed to create data directory: {data_dir}\nError: {e}") from e

    if not os.access(data_dir, os.W_OK):
        logger.error("Data directory not writable: %s", data_dir)
        raise XDGDirectoryError(f"Data directory is not writable: {data_dir}")

    return data_dir


@lru_cache(maxsize=1)
def get_cache_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Get XDG cache directory, creating if needed.

    Respects XDG_CACHE_HOME environment variable, falling back to
    ~/.cache if not set. Cache directory can be safely deleted.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Returns:
        Path object pointing to the cache directory

    Raises:
        XDGDirectoryError: If directory creation fails or is not writable

    Example:
        >>> cache_dir = get_cache_dir()
        >>> detection_cache = cache_dir / "detection_cache.json"
    """
    base_str = os.environ.get("XDG_CACHE_HOME")
    if base_str is None:
        base: Path = Path.home() / ".cache"
    else:
        base = Path(base_str)

    cache_dir: Path = base / project_name

    try:
        cache_dir.mkdir(parents=True, exist_ok=True, mode=CACHE_DIR_MODE)
        logger.debug("Cache directory ensured: %s", cache_dir)
    except OSError as e:
        logger.error("Failed to create cache directory: %s", cache_dir, exc_info=True)
        raise XDGDirectoryError(f"Failed to create cache directory: {cache_dir}\nError: {e}") from e

    if not os.access(cache_dir, os.W_OK):
        logger.error("Cache directory not writable: %s", cache_dir)
        raise XDGDirectoryError(f"Cache directory is not writable: {cache_dir}")

    return cache_dir


@lru_cache(maxsize=1)
def get_state_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Get XDG state directory, creating if needed.

    Respects XDG_STATE_HOME environment variable, falling back to
    ~/.local/state if not set. Used for application state and logs.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Returns:
        Path object pointing to the state directory

    Raises:
        XDGDirectoryError: If directory creation fails or is not writable

    Example:
        >>> state_dir = get_state_dir()
        >>> logs = state_dir / "logs"
    """
    base_str = os.environ.get("XDG_STATE_HOME")
    if base_str is None:
        base: Path = Path.home() / ".local" / "state"
    else:
        base = Path(base_str)

    state_dir: Path = base / project_name

    try:
        state_dir.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)
        logger.debug("State directory ensured: %s", state_dir)
    except OSError as e:
        logger.error("Failed to create state directory: %s", state_dir, exc_info=True)
        raise XDGDirectoryError(f"Failed to create state directory: {state_dir}\nError: {e}") from e

    if not os.access(state_dir, os.W_OK):
        logger.error("State directory not writable: %s", state_dir)
        raise XDGDirectoryError(f"State directory is not writable: {state_dir}")

    return state_dir


def clear_cache(project_name: str = DEFAULT_PROJECT_NAME) -> None:
    """Clear all cached data by removing cache directory contents.

    This is a safe operation as cache data can be regenerated.
    The directory itself is preserved.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Raises:
        XDGDirectoryError: If cache clearing fails

    Example:
        >>> clear_cache()
        >>> # Cache directory now empty
    """
    cache_dir = get_cache_dir(project_name)

    try:
        # Remove all contents but preserve directory
        for item in cache_dir.iterdir():
            if item.is_file():
                item.unlink()
                logger.debug("Removed cache file: %s", item)
            elif item.is_dir():
                shutil.rmtree(item)
                logger.debug("Removed cache directory: %s", item)
        logger.info("Cache cleared: %s", cache_dir)
    except OSError as e:
        logger.error("Failed to clear cache directory: %s", cache_dir, exc_info=True)
        raise XDGDirectoryError(f"Failed to clear cache directory: {cache_dir}\nError: {e}") from e


def get_all_dirs(project_name: str = DEFAULT_PROJECT_NAME) -> dict[str, Path]:
    """Get all XDG directories at once.

    Useful for initialization or status display. Creates all directories
    if they don't exist.

    Args:
        project_name: Name of the project subdirectory (default: "mycelium")

    Returns:
        Dictionary mapping directory type to Path object

    Example:
        >>> dirs = get_all_dirs()
        >>> print(dirs["config"])
        PosixPath('/home/user/.config/mycelium')
        >>> for name, path in dirs.items():
        ...     print(f"{name}: {path}")
    """
    logger.debug("Getting all XDG directories for project: %s", project_name)
    return {
        "config": get_config_dir(project_name),
        "data": get_data_dir(project_name),
        "cache": get_cache_dir(project_name),
        "state": get_state_dir(project_name),
    }
