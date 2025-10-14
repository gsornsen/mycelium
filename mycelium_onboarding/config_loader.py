"""Hierarchical configuration loading with project-local precedence.

This module provides functions to load configuration files with hierarchical
precedence: project-local → user-global → defaults. Supports the environment
isolation strategy by respecting MYCELIUM_PROJECT_DIR when set.

Precedence Order:
    1. Project-local: $MYCELIUM_PROJECT_DIR/<filename> (highest priority)
    2. User-global: $XDG_CONFIG_HOME/mycelium/<filename> (medium priority)
    3. Defaults: Hardcoded or package-provided defaults (lowest priority)

Example:
    >>> from mycelium_onboarding.config_loader import find_config_file
    >>> config_path = find_config_file("config.yaml")
    >>> if config_path:
    ...     with open(config_path) as f:
    ...         config = yaml.safe_load(f)
    ... else:
    ...     config = get_default_config()

Example with explicit precedence:
    >>> from mycelium_onboarding.config_loader import get_all_config_paths
    >>> # Try loading from all possible locations
    >>> for path in get_all_config_paths("config.yaml"):
    ...     if path.exists():
    ...         print(f"Found config at: {path}")
    ...         config = load_yaml(path)
    ...         break
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mycelium_onboarding.xdg_dirs import get_config_dir

# Module logger
logger = logging.getLogger(__name__)

# Export list
__all__ = [
    "get_config_path",
    "get_all_config_paths",
    "find_config_file",
    "ConfigLoaderError",
]


class ConfigLoaderError(Exception):
    """Raised when configuration loading operations fail."""

    pass


def get_config_path(filename: str, prefer_project: bool = True) -> Path:
    """Get configuration file path following hierarchical precedence.

    Returns the path to the configuration file based on precedence order.
    If prefer_project is True (default), checks project-local directory first.
    Falls back to user-global directory if project-local file doesn't exist.

    If neither file exists, returns the preferred location (project-local if
    prefer_project=True, user-global otherwise) for the caller to create the file.

    Args:
        filename: Name of the configuration file (e.g., "config.yaml")
        prefer_project: If True, prefer project-local config over user-global
            (default: True)

    Returns:
        Path object pointing to the configuration file location

    Raises:
        ConfigLoaderError: If filename is empty or contains path separators

    Example:
        >>> # Get path for reading (checks existence with fallback)
        >>> config_path = get_config_path("config.yaml")
        >>> if config_path.exists():
        ...     config = load_yaml(config_path)
        ...
        >>> # Get path for writing (prefer project-local)
        >>> config_path = get_config_path("config.yaml", prefer_project=True)
        >>> save_yaml(config_path, user_config)
        ...
        >>> # Get path for writing (prefer user-global)
        >>> config_path = get_config_path("config.yaml", prefer_project=False)
        >>> save_yaml(config_path, default_config)

    Notes:
        - Respects MYCELIUM_PROJECT_DIR environment variable if set
        - Falls back to user-global XDG config directory
        - Does not create any directories or files
        - Returns a path that may not exist (caller should check)
    """
    # Validate filename
    if not filename:
        raise ConfigLoaderError("Filename cannot be empty")

    if "/" in filename or "\\" in filename:
        raise ConfigLoaderError(
            f"Filename cannot contain path separators: {filename}\n"
            "Use simple filename like 'config.yaml'"
        )

    logger.debug(
        "Getting config path for '%s' (prefer_project=%s)", filename, prefer_project
    )

    # Check project-local first if preferred
    if prefer_project and "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename
        logger.debug(
            "Checking project-local: %s (exists=%s)",
            project_path,
            project_path.exists(),
        )

        if project_path.exists():
            logger.info("Using project-local config: %s", project_path)
            return project_path

    # Check user-global second
    user_path = get_config_dir() / filename
    logger.debug("Checking user-global: %s (exists=%s)", user_path, user_path.exists())

    if user_path.exists():
        logger.info("Using user-global config: %s", user_path)
        return user_path

    # Neither exists - return preferred location for creation
    if prefer_project and "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename
        logger.debug("Returning project-local path for creation: %s", project_path)
        return project_path
    logger.debug("Returning user-global path for creation: %s", user_path)
    return user_path


def get_all_config_paths(filename: str) -> list[Path]:
    """Get all possible configuration file paths in precedence order.

    Returns a list of all possible locations where the configuration file
    could exist, ordered by precedence (highest to lowest). Useful for
    checking all locations or displaying configuration sources.

    Args:
        filename: Name of the configuration file (e.g., "config.yaml")

    Returns:
        List of Path objects in precedence order:
        [project-local, user-global]

    Raises:
        ConfigLoaderError: If filename is empty or contains path separators

    Example:
        >>> # Get all possible locations
        >>> paths = get_all_config_paths("config.yaml")
        >>> for path in paths:
        ...     if path.exists():
        ...         print(f"Found: {path}")
        ...     else:
        ...         print(f"Missing: {path}")
        ...
        >>> # Try loading from first available location
        >>> for path in get_all_config_paths("config.yaml"):
        ...     if path.exists():
        ...         config = load_yaml(path)
        ...         break

    Notes:
        - Returned paths may not exist
        - Order reflects configuration precedence
        - Project-local path only included if MYCELIUM_PROJECT_DIR is set
    """
    # Validate filename
    if not filename:
        raise ConfigLoaderError("Filename cannot be empty")

    if "/" in filename or "\\" in filename:
        raise ConfigLoaderError(
            f"Filename cannot contain path separators: {filename}"
        )

    logger.debug("Getting all config paths for '%s'", filename)

    paths: list[Path] = []

    # Add project-local path if environment variable is set
    if "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename
        paths.append(project_path)
        logger.debug("Added project-local path: %s", project_path)

    # Always add user-global path
    user_path = get_config_dir() / filename
    paths.append(user_path)
    logger.debug("Added user-global path: %s", user_path)

    logger.debug("All config paths: %s", [str(p) for p in paths])
    return paths


def find_config_file(filename: str) -> Path | None:
    """Find the first existing configuration file following precedence order.

    Searches for the configuration file in all possible locations and returns
    the path to the first one that exists. Returns None if no config file exists.

    Args:
        filename: Name of the configuration file (e.g., "config.yaml")

    Returns:
        Path to the first existing config file, or None if not found

    Raises:
        ConfigLoaderError: If filename is empty or contains path separators

    Example:
        >>> # Simple config loading with fallback
        >>> config_path = find_config_file("config.yaml")
        >>> if config_path:
        ...     print(f"Loading config from: {config_path}")
        ...     config = load_yaml(config_path)
        ... else:
        ...     print("No config file found, using defaults")
        ...     config = get_default_config()
        ...
        >>> # Check which config is being used
        >>> config_path = find_config_file("preferences.yaml")
        >>> if config_path:
        ...     if "MYCELIUM_PROJECT_DIR" in str(config_path):
        ...         print("Using project-specific preferences")
        ...     else:
        ...         print("Using user-global preferences")

    Notes:
        - Returns None if no config file exists at any location
        - Project-local config takes precedence over user-global
        - Does not create any directories or files
    """
    logger.debug("Finding config file '%s'", filename)

    for path in get_all_config_paths(filename):
        if path.exists():
            logger.info("Found config file: %s", path)
            return path

    logger.debug("No config file found for '%s'", filename)
    return None
