"""Configuration scope management for global and project-local configs.

This module provides utilities for managing configuration scope, determining
which configuration file to use based on the current context, and migrating
between scopes.

Configuration Hierarchy (new global-first approach):
    1. Environment variables (MYCELIUM_*) - highest priority
    2. User-global config (~/.config/mycelium/config.yaml) - default
    3. Project-local config ($MYCELIUM_PROJECT_DIR/config.yaml) - opt-in override
    4. Built-in defaults - lowest priority

The new approach makes global configuration the default, encouraging centralized
configuration management while still allowing project-specific overrides when needed.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from mycelium_onboarding.xdg_dirs import get_config_dir

logger = logging.getLogger(__name__)

__all__ = [
    "ConfigScope",
    "ConfigLocation",
    "get_active_scope",
    "get_config_location",
    "list_all_configs",
    "should_use_project_config",
]


class ConfigScope(str, Enum):
    """Configuration scope types.

    Attributes:
        GLOBAL: User-global configuration (~/.config/mycelium/)
        PROJECT: Project-local configuration ($MYCELIUM_PROJECT_DIR/)
        EXPLICIT: Explicitly specified configuration path
        DEFAULT: Using built-in defaults (no config file)
    """

    GLOBAL = "global"
    PROJECT = "project"
    EXPLICIT = "explicit"
    DEFAULT = "default"


class ConfigLocation(NamedTuple):
    """Configuration location information.

    Attributes:
        scope: The configuration scope (global, project, explicit, default)
        path: Path to configuration file (None if using defaults)
        exists: Whether the configuration file exists
        writable: Whether the configuration file/directory is writable
    """

    scope: ConfigScope
    path: Path | None
    exists: bool
    writable: bool

    def __str__(self) -> str:
        """Human-readable representation."""
        if self.path is None:
            return f"{self.scope.value} (using defaults)"
        status = "exists" if self.exists else "not found"
        writable = "writable" if self.writable else "read-only"
        return f"{self.scope.value}: {self.path} ({status}, {writable})"


def get_active_scope() -> ConfigScope:
    """Determine the active configuration scope.

    Returns the scope that would be used for loading configuration
    based on the current environment and file existence.

    Returns:
        ConfigScope indicating which scope is active

    Example:
        >>> scope = get_active_scope()
        >>> if scope == ConfigScope.GLOBAL:
        ...     print("Using global configuration")
    """
    # Check if explicit path is set (via environment or other means)
    # This would require integration with ConfigManager

    # Check for project-local config with override flag
    if should_use_project_config():
        project_path = _get_project_config_path()
        if project_path and project_path.exists():
            return ConfigScope.PROJECT

    # Check for global config
    global_path = get_config_dir() / "config.yaml"
    if global_path.exists():
        return ConfigScope.GLOBAL

    # Using defaults
    return ConfigScope.DEFAULT


def get_config_location(
    config_filename: str = "config.yaml",
    prefer_global: bool = True,
) -> ConfigLocation:
    """Get detailed information about configuration location.

    Determines which configuration file would be used and provides
    detailed information about its status.

    Args:
        config_filename: Name of configuration file (default: "config.yaml")
        prefer_global: If True, prefer global over project-local (default: True)

    Returns:
        ConfigLocation with detailed information

    Example:
        >>> location = get_config_location()
        >>> print(f"Config at: {location.path}")
        >>> if not location.exists:
        ...     print("Configuration file not found")
    """
    # Check for project override flag
    if not prefer_global and should_use_project_config():
        project_path = _get_project_config_path()
        if project_path:
            return ConfigLocation(
                scope=ConfigScope.PROJECT,
                path=project_path,
                exists=project_path.exists(),
                writable=_is_writable(project_path),
            )

    # Default to global
    global_path = get_config_dir() / config_filename

    # Check if global exists, otherwise check project as fallback
    if global_path.exists():
        return ConfigLocation(
            scope=ConfigScope.GLOBAL,
            path=global_path,
            exists=True,
            writable=_is_writable(global_path),
        )

    # Check project-local as fallback
    if should_use_project_config():
        project_path = _get_project_config_path()
        if project_path and project_path.exists():
            return ConfigLocation(
                scope=ConfigScope.PROJECT,
                path=project_path,
                exists=True,
                writable=_is_writable(project_path),
            )

    # No config exists, return global as default location for creation
    return ConfigLocation(
        scope=ConfigScope.GLOBAL,
        path=global_path,
        exists=False,
        writable=_is_writable(global_path.parent),
    )


def list_all_configs(config_filename: str = "config.yaml") -> list[ConfigLocation]:
    """List all possible configuration file locations.

    Returns information about all potential configuration files,
    including whether they exist and are writable.

    Args:
        config_filename: Name of configuration file (default: "config.yaml")

    Returns:
        List of ConfigLocation objects for all possible locations

    Example:
        >>> configs = list_all_configs()
        >>> for config in configs:
        ...     print(f"{config.scope.value}: {config.path} (exists: {config.exists})")
    """
    locations: list[ConfigLocation] = []

    # Global config
    global_path = get_config_dir() / config_filename
    locations.append(
        ConfigLocation(
            scope=ConfigScope.GLOBAL,
            path=global_path,
            exists=global_path.exists(),
            writable=_is_writable(global_path if global_path.exists() else global_path.parent),
        )
    )

    # Project-local config (if project context exists)
    if should_use_project_config():
        project_path = _get_project_config_path()
        if project_path:
            locations.append(
                ConfigLocation(
                    scope=ConfigScope.PROJECT,
                    path=project_path,
                    exists=project_path.exists(),
                    writable=_is_writable(project_path if project_path.exists() else project_path.parent),
                )
            )

    return locations


def should_use_project_config() -> bool:
    """Check if project-local configuration should be considered.

    Returns True if we're in a project context and project-local
    config is explicitly enabled via environment variable.

    Returns:
        True if project-local config should be used

    Example:
        >>> if should_use_project_config():
        ...     print("Project-local config enabled")
    """
    # Check for explicit project config opt-in
    if os.environ.get("MYCELIUM_USE_PROJECT_CONFIG", "").lower() in ("true", "1", "yes"):
        return "MYCELIUM_PROJECT_DIR" in os.environ

    # Check if MYCELIUM_PROJECT_DIR is set (backward compatibility)
    # Only use project config if the file actually exists (don't create new project configs by default)
    if "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = _get_project_config_path()
        return project_path is not None and project_path.exists()

    return False


def _get_project_config_path() -> Path | None:
    """Get project-local configuration path if available.

    Returns:
        Path to project config or None if not in project context
    """
    project_dir = os.environ.get("MYCELIUM_PROJECT_DIR")
    if not project_dir:
        return None

    return Path(project_dir) / "config.yaml"


def _is_writable(path: Path) -> bool:
    """Check if a path is writable.

    Args:
        path: Path to check (file or directory)

    Returns:
        True if path is writable
    """
    try:
        # If path exists, check if it's writable
        if path.exists():
            return os.access(path, os.W_OK)

        # If path doesn't exist, check if parent directory is writable
        parent = path.parent
        return parent.exists() and os.access(parent, os.W_OK)
    except (OSError, PermissionError):
        return False
