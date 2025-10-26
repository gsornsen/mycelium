"""Configuration manager for loading, saving, and validating configurations.

This module provides the ConfigManager class for managing Mycelium configuration
with full YAML support, atomic file writes, backup creation, and comprehensive
error handling.

Features:
- Hierarchical configuration loading (project-local > user-global > defaults)
- Safe YAML loading/dumping with error handling
- Atomic file writes with temp files to prevent corruption
- Automatic backup creation before overwriting
- Configuration validation with clear error messages
- Config merging with proper precedence
- Schema migration support for version upgrades
- Structured logging for debugging

Example:
    >>> from mycelium_onboarding.config.manager import ConfigManager
    >>> from mycelium_onboarding.config.schema import MyceliumConfig
    >>>
    >>> # Load existing config or get defaults
    >>> config = ConfigManager().load()
    >>>
    >>> # Modify configuration
    >>> config.services.redis.port = 6380
    >>>
    >>> # Save with automatic backup
    >>> manager = ConfigManager()
    >>> manager.save(config)
    >>>
    >>> # Validate configuration
    >>> errors = manager.validate(config)
    >>> if errors:
    ...     print(f"Validation errors: {errors}")
    >>>
    >>> # Load and migrate to latest version
    >>> config = manager.load_and_migrate()
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config_loader import find_config_file
from mycelium_onboarding.xdg_dirs import get_config_dir

# Module logger
logger = logging.getLogger(__name__)

# Module exports
__all__ = [
    "ConfigManager",
    "ConfigLoadError",
    "ConfigSaveError",
    "ConfigValidationError",
]


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    pass


class ConfigSaveError(Exception):
    """Raised when configuration saving fails."""

    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigManager:
    """Manages configuration loading, saving, and validation.

    This class provides a high-level interface for working with Mycelium
    configurations, handling all the complexity of file I/O, validation,
    migration, and error handling.

    Attributes:
        config_path: Optional explicit path to configuration file.
            If not provided, uses hierarchical search.

    Example:
        >>> # Use default config path resolution
        >>> manager = ConfigManager()
        >>> config = manager.load()
        >>>
        >>> # Use explicit config path
        >>> manager = ConfigManager(config_path=Path("custom-config.yaml"))
        >>> config = manager.load()
    """

    CONFIG_FILENAME = "config.yaml"
    BACKUP_SUFFIX = ".backup"

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize ConfigManager with optional explicit config path.

        Args:
            config_path: Optional path to configuration file.
                If None, uses hierarchical search (project-local > user-global).

        Example:
            >>> manager = ConfigManager()  # Use default search
            >>> manager = ConfigManager(Path("/path/to/config.yaml"))  # Explicit
        """
        self.config_path = config_path
        logger.debug("ConfigManager initialized with config_path=%s", config_path)

    def load(self) -> MyceliumConfig:
        """Load configuration from file with hierarchical fallback.

        Searches for configuration in order:
        1. Explicit config_path (if provided to __init__)
        2. Project-local: $MYCELIUM_PROJECT_DIR/config.yaml
        3. User-global: ~/.config/mycelium/config.yaml
        4. Defaults: Returns default MyceliumConfig instance

        Returns:
            MyceliumConfig instance, either loaded from file or defaults

        Raises:
            ConfigLoadError: If file exists but cannot be read/parsed
            ConfigValidationError: If file contents fail validation

        Example:
            >>> manager = ConfigManager()
            >>> config = manager.load()
            >>> print(config.project_name)
            mycelium
        """
        logger.info("Loading configuration")

        # Use explicit path if provided
        if self.config_path is not None:
            if not self.config_path.exists():
                logger.warning(
                    "Explicit config path does not exist: %s, using defaults",
                    self.config_path,
                )
                return self.get_default_config()

            logger.info("Loading from explicit path: %s", self.config_path)
            return self._load_from_file(self.config_path)

        # Find config file using hierarchical search
        config_file = find_config_file(self.CONFIG_FILENAME)

        if config_file is None:
            logger.info("No config file found, using defaults")
            return self.get_default_config()

        logger.info("Found config file: %s", config_file)
        return self._load_from_file(config_file)

    def _load_from_file(self, path: Path) -> MyceliumConfig:
        """Load and validate configuration from file.

        Args:
            path: Path to configuration file

        Returns:
            Validated MyceliumConfig instance

        Raises:
            ConfigLoadError: If file cannot be read or parsed
            ConfigValidationError: If validation fails
        """
        logger.debug("Reading config file: %s", path)

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except OSError as e:
            msg = f"Failed to read configuration file: {path}"
            logger.error("%s: %s", msg, e)
            raise ConfigLoadError(f"{msg}\nError: {e}") from e
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML in configuration file: {path}"
            logger.error("%s: %s", msg, e)
            raise ConfigLoadError(f"{msg}\nError: {e}") from e

        # Handle empty file
        if data is None:
            logger.warning("Config file is empty, using defaults: %s", path)
            return self.get_default_config()

        # Validate and construct config
        try:
            config = MyceliumConfig.from_dict(data)
            logger.info("Successfully loaded config from: %s", path)
            return config
        except ValidationError as e:
            msg = f"Configuration validation failed in: {path}"
            logger.error("%s\n%s", msg, e)
            raise ConfigValidationError(f"{msg}\n{e}") from e

    def load_and_migrate(
        self, target_version: str | None = None, *, dry_run: bool = False
    ) -> MyceliumConfig:
        """Load configuration and migrate to target version if needed.

        This method loads the configuration and automatically migrates it
        to the target version (or latest supported version if not specified).

        Args:
            target_version: Target schema version to migrate to.
                If None, uses the current default version.
            dry_run: If True, preview migration without applying changes

        Returns:
            MyceliumConfig instance, migrated if necessary

        Raises:
            ConfigLoadError: If loading fails
            ConfigValidationError: If validation fails
            MigrationError: If migration fails

        Example:
            >>> manager = ConfigManager()
            >>> # Migrate to latest version
            >>> config = manager.load_and_migrate()
            >>>
            >>> # Preview migration without applying
            >>> preview = manager.load_and_migrate(target_version="1.2", dry_run=True)
        """
        from mycelium_onboarding.config.migrations import (
            MigrationError,
            get_default_registry,
        )

        logger.info(
            "Loading configuration with migration (target=%s, dry_run=%s)",
            target_version,
            dry_run,
        )

        # Use explicit path if provided
        if self.config_path is not None:
            if not self.config_path.exists():
                logger.warning(
                    "Explicit config path does not exist: %s, using defaults",
                    self.config_path,
                )
                return self.get_default_config()

            config_file: Path = self.config_path
        else:
            # Find config file using hierarchical search
            found_file = find_config_file(self.CONFIG_FILENAME)

            if found_file is None:
                logger.info("No config file found, using defaults")
                return self.get_default_config()
            config_file = found_file

        logger.info("Found config file: %s", config_file)

        # Load raw YAML
        try:
            with config_file.open("r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        except OSError as e:
            msg = f"Failed to read configuration file: {config_file}"
            logger.error("%s: %s", msg, e)
            raise ConfigLoadError(f"{msg}\nError: {e}") from e
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML in configuration file: {config_file}"
            logger.error("%s: %s", msg, e)
            raise ConfigLoadError(f"{msg}\nError: {e}") from e

        # Handle empty file
        if config_dict is None:
            logger.warning("Config file is empty, using defaults: %s", config_file)
            return self.get_default_config()

        # Determine target version
        if target_version is None:
            # Use current default version from schema
            target_version = MyceliumConfig().version
            logger.debug("Using default target version: %s", target_version)

        # Check if migration is needed
        registry = get_default_registry()
        if registry.needs_migration(config_dict, target_version):
            logger.info(
                "Migration needed: %s -> %s",
                config_dict.get("version"),
                target_version,
            )

            try:
                # Perform migration
                migrated_dict = registry.migrate(
                    config_dict, target_version, dry_run=dry_run
                )

                # Save migrated config if not dry run
                if not dry_run:
                    # Create backup before migration
                    if config_file.exists():
                        self._create_backup(config_file)

                    # Validate migrated config
                    migrated_config = MyceliumConfig.from_dict(migrated_dict)

                    # Save migrated config
                    temp_manager = ConfigManager(config_path=config_file)
                    temp_manager.save(migrated_config)

                    logger.info("Configuration migrated and saved: %s", config_file)
                    return migrated_config
                # Dry run: just validate and return
                migrated_config = MyceliumConfig.from_dict(migrated_dict)
                logger.info("Dry run: migration preview completed")
                return migrated_config

            except MigrationError as e:
                msg = f"Migration failed: {e}"
                logger.error(msg)
                raise ConfigValidationError(msg) from e
        else:
            logger.info("No migration needed, config is up to date")

        # Load and validate normally
        try:
            config = MyceliumConfig.from_dict(config_dict)
            logger.info("Successfully loaded config from: %s", config_file)
            return config
        except ValidationError as e:
            msg = f"Configuration validation failed in: {config_file}"
            logger.error("%s\n%s", msg, e)
            raise ConfigValidationError(f"{msg}\n{e}") from e

    def needs_migration(self, config_dict: dict[str, Any]) -> bool:
        """Check if configuration needs migration to current schema version.

        Args:
            config_dict: Configuration dictionary to check

        Returns:
            True if migration is needed, False otherwise

        Example:
            >>> manager = ConfigManager()
            >>> config_dict = {"version": "1.0", ...}
            >>> if manager.needs_migration(config_dict):
            ...     print("Migration required")
        """
        from mycelium_onboarding.config.migrations import get_default_registry

        target_version = MyceliumConfig().version
        registry = get_default_registry()
        return registry.needs_migration(config_dict, target_version)

    def save(self, config: MyceliumConfig) -> None:
        """Save configuration to file with atomic write and backup.

        Saves to the location determined by:
        1. Explicit config_path (if provided to __init__)
        2. Existing config file location (if found)
        3. User-global config directory (fallback)

        Performs atomic write by:
        1. Validating configuration
        2. Creating backup of existing file
        3. Writing to temporary file
        4. Atomically renaming temp file to target

        Args:
            config: Configuration to save

        Raises:
            ConfigValidationError: If configuration is invalid
            ConfigSaveError: If save operation fails

        Example:
            >>> manager = ConfigManager()
            >>> config = manager.get_default_config()
            >>> config.project_name = "my-project"
            >>> manager.save(config)
        """
        logger.info("Saving configuration")

        # Validate before saving
        validation_errors = self.validate(config)
        if validation_errors:
            msg = "Configuration validation failed, not saving"
            logger.error("%s: %s", msg, validation_errors)
            raise ConfigValidationError(f"{msg}:\n" + "\n".join(validation_errors))

        # Determine save path
        save_path = self._determine_save_path()
        logger.debug("Save path determined: %s", save_path)

        # Ensure parent directory exists
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as e:
            msg = f"Failed to create config directory: {save_path.parent}"
            logger.error("%s: %s", msg, e)
            raise ConfigSaveError(f"{msg}\nError: {e}") from e

        # Create backup if file exists
        if save_path.exists():
            self._create_backup(save_path)

        # Atomic write
        self._atomic_write(save_path, config)

        logger.info("Configuration saved successfully: %s", save_path)

    def _determine_save_path(self) -> Path:
        """Determine where to save configuration.

        Returns:
            Path where configuration should be saved
        """
        # Use explicit path if provided
        if self.config_path is not None:
            return self.config_path

        # Find existing config file
        existing_config = find_config_file(self.CONFIG_FILENAME)
        if existing_config is not None:
            logger.debug("Using existing config location: %s", existing_config)
            return existing_config

        # Fallback to user-global config directory
        # Check if we're in a project context
        if "MYCELIUM_PROJECT_DIR" in os.environ:
            project_path = (
                Path(os.environ["MYCELIUM_PROJECT_DIR"]) / self.CONFIG_FILENAME
            )
            logger.debug("Using project-local path: %s", project_path)
            return project_path

        user_path = get_config_dir() / self.CONFIG_FILENAME
        logger.debug("Using user-global path: %s", user_path)
        return user_path

    def _create_backup(self, path: Path) -> None:
        """Create backup of existing configuration file.

        Args:
            path: Path to file to backup

        Raises:
            ConfigSaveError: If backup creation fails
        """
        backup_path = path.with_suffix(path.suffix + self.BACKUP_SUFFIX)
        logger.debug("Creating backup: %s -> %s", path, backup_path)

        try:
            shutil.copy2(path, backup_path)
            logger.info("Backup created: %s", backup_path)
        except OSError as e:
            msg = f"Failed to create backup: {backup_path}"
            logger.error("%s: %s", msg, e)
            raise ConfigSaveError(f"{msg}\nError: {e}") from e

    def _atomic_write(self, path: Path, config: MyceliumConfig) -> None:
        """Write configuration atomically using temp file.

        Args:
            path: Target path for configuration file
            config: Configuration to write

        Raises:
            ConfigSaveError: If write operation fails
        """
        # Serialize to YAML
        try:
            config_dict = config.to_dict(exclude_none=False)
            yaml_content = yaml.dump(
                config_dict,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
            )
        except Exception as e:
            msg = "Failed to serialize configuration to YAML"
            logger.error("%s: %s", msg, e)
            raise ConfigSaveError(f"{msg}\nError: {e}") from e

        # Write to temp file in same directory (ensures same filesystem)
        try:
            # Use tempfile in same directory for atomic rename
            fd, temp_path_str = tempfile.mkstemp(
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                text=True,
            )

            temp_path = Path(temp_path_str)

            try:
                # Write content
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(yaml_content)
                    f.flush()
                    os.fsync(f.fileno())

                # Set permissions (0600 for security)
                temp_path.chmod(0o600)

                # Atomic rename
                temp_path.replace(path)
                logger.debug("Atomic write completed: %s", path)

            except Exception:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise

        except OSError as e:
            msg = f"Failed to write configuration to: {path}"
            logger.error("%s: %s", msg, e)
            raise ConfigSaveError(f"{msg}\nError: {e}") from e

    def validate(self, config: MyceliumConfig) -> list[str]:
        """Validate configuration and return list of warnings/errors.

        Performs comprehensive validation including:
        - Pydantic model validation
        - Business logic validation
        - Service dependency checks

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            >>> manager = ConfigManager()
            >>> config = manager.get_default_config()
            >>> errors = manager.validate(config)
            >>> if not errors:
            ...     print("Configuration is valid")
        """
        logger.debug("Validating configuration")
        errors: list[str] = []

        # Pydantic validation
        try:
            # Re-validate through Pydantic to catch any issues
            MyceliumConfig.model_validate(config.model_dump())
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")
            logger.warning("Validation errors found: %s", errors)

        # Additional business logic validation could go here
        # For now, Pydantic handles all validation through model_post_init

        return errors

    def get_default_config(self) -> MyceliumConfig:
        """Return default configuration.

        Creates a new MyceliumConfig instance with all default values.

        Returns:
            Default MyceliumConfig instance

        Example:
            >>> manager = ConfigManager()
            >>> config = manager.get_default_config()
            >>> print(config.project_name)
            mycelium
        """
        logger.debug("Creating default configuration")
        return MyceliumConfig()

    def merge_configs(
        self,
        base: MyceliumConfig,
        overlay: MyceliumConfig,
    ) -> MyceliumConfig:
        """Merge two configurations with overlay taking precedence.

        Performs a deep merge where:
        - Overlay values override base values
        - Nested objects are merged recursively
        - Lists are replaced (not merged)

        Args:
            base: Base configuration (lower precedence)
            overlay: Overlay configuration (higher precedence)

        Returns:
            Merged MyceliumConfig instance

        Raises:
            ConfigValidationError: If merged config is invalid

        Example:
            >>> manager = ConfigManager()
            >>> base = manager.get_default_config()
            >>> overlay = MyceliumConfig(project_name="custom")
            >>> merged = manager.merge_configs(base, overlay)
            >>> print(merged.project_name)
            custom
        """
        logger.debug("Merging configurations")

        # Convert to dicts for merging
        base_dict = base.to_dict(exclude_none=False)
        overlay_dict = overlay.to_dict(exclude_none=False)

        # Deep merge
        merged_dict = self._deep_merge(base_dict, overlay_dict)

        # Validate and construct merged config
        try:
            merged_config = MyceliumConfig.from_dict(merged_dict)
            logger.info("Configurations merged successfully")
            return merged_config
        except ValidationError as e:
            msg = "Merged configuration is invalid"
            logger.error("%s: %s", msg, e)
            raise ConfigValidationError(f"{msg}\n{e}") from e

    def _deep_merge(
        self, base: dict[str, Any], overlay: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            overlay: Overlay dictionary (takes precedence)

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dicts
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override with overlay value
                result[key] = value

        return result
