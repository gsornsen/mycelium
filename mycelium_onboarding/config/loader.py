"""Configuration loader with 3-tier precedence system.

This module provides the ConfigLoader class that implements a robust 3-tier
configuration loading system: defaults → global → project.

The loader handles:
- Safe YAML loading with comprehensive error handling
- Automatic path resolution for global and project configs
- Deep merging with proper precedence
- Validation with clear error messages
- Configuration caching for performance

Example:
    >>> from mycelium_onboarding.config.loader import ConfigLoader
    >>> loader = ConfigLoader()
    >>> config = loader.load()
    >>> print(config.project_name)
    mycelium
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mycelium_onboarding.config.defaults import get_default_config_dict
from mycelium_onboarding.config.precedence import merge_with_precedence
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config_loader import find_config_file, get_all_config_paths
from mycelium_onboarding.xdg_dirs import get_config_dir

logger = logging.getLogger(__name__)

# Module exports
__all__ = [
    "ConfigLoader",
    "ConfigLoadError",
    "ConfigValidationError",
    "ConfigParseError",
]


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigParseError(Exception):
    """Raised when YAML parsing fails."""

    pass


class ConfigLoader:
    """Load configuration with 3-tier precedence: defaults → global → project.

    This class implements a robust configuration loading system that:
    1. Loads default configuration values
    2. Overlays user-global configuration (~/.config/mycelium/config.yaml)
    3. Overlays project-local configuration ($MYCELIUM_PROJECT_DIR/config.yaml)
    4. Validates the merged configuration
    5. Caches the result for performance

    The loader provides comprehensive error handling with clear messages
    for common issues like missing files, invalid YAML, and validation errors.

    Attributes:
        config_filename: Name of the configuration file to load
        cache_enabled: Whether to cache loaded configurations

    Example:
        >>> # Load with defaults
        >>> loader = ConfigLoader()
        >>> config = loader.load()
        >>>
        >>> # Load without cache
        >>> loader = ConfigLoader(cache_enabled=False)
        >>> config = loader.load()
        >>>
        >>> # Get configuration paths
        >>> paths = loader.get_config_paths()
        >>> for scope, path in paths.items():
        ...     print(f"{scope}: {path}")
    """

    CONFIG_FILENAME = "config.yaml"

    def __init__(
        self,
        *,
        config_filename: str = CONFIG_FILENAME,
        cache_enabled: bool = True,
    ) -> None:
        """Initialize ConfigLoader.

        Args:
            config_filename: Name of configuration file (default: "config.yaml")
            cache_enabled: Enable configuration caching (default: True)

        Example:
            >>> loader = ConfigLoader()
            >>> loader = ConfigLoader(config_filename="custom-config.yaml")
        """
        self.config_filename = config_filename
        self.cache_enabled = cache_enabled
        self._cached_config: MyceliumConfig | None = None
        logger.debug(
            "ConfigLoader initialized: filename=%s, cache=%s",
            config_filename,
            cache_enabled,
        )

    def load(self) -> MyceliumConfig:
        """Load configuration with 3-tier precedence.

        Loads and merges configuration from three sources:
        1. Built-in defaults (lowest precedence)
        2. User-global config (medium precedence)
        3. Project-local config (highest precedence)

        Returns:
            Validated MyceliumConfig instance

        Raises:
            ConfigLoadError: If file reading fails
            ConfigParseError: If YAML parsing fails
            ConfigValidationError: If validation fails

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load()
            >>> print(config.version)
            1.0
        """
        logger.info("Loading configuration with 3-tier precedence")

        # If cache is enabled and we have cached config, return it
        if self.cache_enabled and self._cached_config is not None:
            logger.debug("Returning cached configuration")
            return self._cached_config

        # Load fresh configuration
        config = self._load_uncached()

        # Cache if enabled
        if self.cache_enabled:
            self._cached_config = config
            logger.debug("Configuration cached")

        return config

    def _load_uncached(self) -> MyceliumConfig:
        """Load configuration without caching.

        Returns:
            MyceliumConfig instance
        """
        # 1. Load defaults
        defaults = get_default_config_dict()
        logger.debug("Loaded default configuration")

        # 2. Load global config (if exists)
        global_config = self._load_global_config()

        # 3. Load project config (if exists)
        project_config = self._load_project_config()

        # 4. Merge with precedence
        merged_dict = merge_with_precedence(
            defaults,
            global_config,
            project_config,
            merge_lists=False,
        )

        # 5. Validate and construct config
        try:
            config = MyceliumConfig.from_dict(merged_dict)
            logger.info("Configuration loaded and validated successfully")
            return config
        except ValidationError as e:
            msg = "Configuration validation failed after merging"
            logger.error("%s: %s", msg, e)
            raise ConfigValidationError(f"{msg}\n{e}") from e

    def _load_global_config(self) -> dict[str, Any] | None:
        """Load user-global configuration from XDG config directory.

        Returns:
            Configuration dictionary or None if file doesn't exist

        Raises:
            ConfigLoadError: If file exists but cannot be read
            ConfigParseError: If YAML parsing fails
        """
        global_path = get_config_dir() / self.config_filename
        logger.debug("Checking for global config: %s", global_path)

        if not global_path.exists():
            logger.debug("Global config not found, skipping")
            return None

        return self._load_yaml_file(global_path, scope="global")

    def _load_project_config(self) -> dict[str, Any] | None:
        """Load project-local configuration if in project context.

        Returns:
            Configuration dictionary or None if file doesn't exist

        Raises:
            ConfigLoadError: If file exists but cannot be read
            ConfigParseError: If YAML parsing fails
        """
        # Find project config using existing utility
        project_path = find_config_file(self.config_filename)

        # If we got global path, there's no project config
        global_path = get_config_dir() / self.config_filename
        if project_path == global_path:
            logger.debug("No project config found, using global only")
            return None

        if project_path is None:
            logger.debug("No project config found")
            return None

        logger.debug("Checking for project config: %s", project_path)
        return self._load_yaml_file(project_path, scope="project")

    def _load_yaml_file(
        self,
        path: Path,
        scope: str = "unknown",
    ) -> dict[str, Any]:
        """Load and parse YAML configuration file.

        Args:
            path: Path to YAML file
            scope: Scope label for error messages (e.g., "global", "project")

        Returns:
            Parsed configuration dictionary

        Raises:
            ConfigLoadError: If file cannot be read
            ConfigParseError: If YAML parsing fails
        """
        logger.debug("Loading YAML file: %s (scope: %s)", path, scope)

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except OSError as e:
            msg = f"Failed to read {scope} configuration file: {path}"
            logger.error("%s: %s", msg, e)
            raise ConfigLoadError(f"{msg}\nError: {e}") from e
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML in {scope} configuration file: {path}"
            logger.error("%s: %s", msg, e)
            raise ConfigParseError(f"{msg}\nError: {e}") from e

        # Handle empty file
        if data is None:
            logger.warning("Configuration file is empty: %s", path)
            return {}

        if not isinstance(data, dict):
            msg = f"Invalid {scope} configuration: expected dictionary, got {type(data).__name__}"
            logger.error("%s in file: %s", msg, path)
            raise ConfigParseError(f"{msg}\nFile: {path}")

        logger.info("Loaded %s configuration from: %s", scope, path)
        return data

    def get_config_paths(self) -> dict[str, Path | None]:
        """Get all configuration file paths in the precedence chain.

        Returns:
            Dictionary mapping scope to path:
            - "global": User-global config path
            - "project": Project-local config path (None if not in project)

        Example:
            >>> loader = ConfigLoader()
            >>> paths = loader.get_config_paths()
            >>> if paths["project"]:
            ...     print(f"Using project config: {paths['project']}")
        """
        paths = get_all_config_paths(self.config_filename)

        result: dict[str, Path | None] = {
            "global": get_config_dir() / self.config_filename,
            "project": None,
        }

        # Check if we have a project path (will be in addition to global)
        if len(paths) > 1:
            # Second path is project-local
            result["project"] = paths[0]

        return result

    def clear_cache(self) -> None:
        """Clear the configuration cache.

        Forces next load() call to re-read and re-merge all configuration files.

        Example:
            >>> loader = ConfigLoader()
            >>> config1 = loader.load()  # Loads and caches
            >>> # ... modify config files ...
            >>> loader.clear_cache()
            >>> config2 = loader.load()  # Re-loads from files
        """
        if self.cache_enabled:
            self._cached_config = None
            logger.debug("Configuration cache cleared")

    def reload(self) -> MyceliumConfig:
        """Clear cache and reload configuration.

        Convenience method that clears cache and reloads in one call.

        Returns:
            Freshly loaded MyceliumConfig instance

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.reload()  # Always fresh
        """
        self.clear_cache()
        return self.load()

    def validate_config_file(self, path: Path) -> list[str]:
        """Validate a configuration file without merging.

        Loads and validates a single configuration file independently,
        without applying precedence or merging with other configs.

        Args:
            path: Path to configuration file to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            >>> loader = ConfigLoader()
            >>> errors = loader.validate_config_file(Path("config.yaml"))
            >>> if errors:
            ...     for error in errors:
            ...         print(f"Error: {error}")
        """
        logger.debug("Validating configuration file: %s", path)
        errors: list[str] = []

        try:
            # Load YAML
            config_dict = self._load_yaml_file(path, scope="validation")

            # Merge with defaults to get complete config
            defaults = get_default_config_dict()
            complete_dict = merge_with_precedence(
                defaults,
                config_dict,
                None,
                merge_lists=False,
            )

            # Validate
            MyceliumConfig.from_dict(complete_dict)
            logger.info("Configuration file is valid: %s", path)

        except ConfigLoadError as e:
            errors.append(f"Load error: {e}")
        except ConfigParseError as e:
            errors.append(f"Parse error: {e}")
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")

        return errors
