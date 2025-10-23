# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 207
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/config/manager.py
"""Configuration manager for loading/saving configurations."""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import ValidationError

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config_loader import get_config_path, find_config_file


class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""
    pass


class ConfigManager:
    """Manages configuration loading, saving, and validation."""

    CONFIG_FILENAME = "config.yaml"

    @classmethod
    def load(cls, prefer_project: bool = True) -> MyceliumConfig:
        """Load configuration from file or return defaults.

        Args:
            prefer_project: Prefer project-local over user-global config

        Returns:
            MyceliumConfig instance

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        config_file = find_config_file(cls.CONFIG_FILENAME)

        if config_file is None:
            # No config file found, return defaults
            return MyceliumConfig()

        return cls.load_from_path(config_file)

    @classmethod
    def load_from_path(cls, path: Path) -> MyceliumConfig:
        """Load configuration from specific path.

        Args:
            path: Path to configuration file

        Returns:
            MyceliumConfig instance

        Raises:
            ConfigValidationError: If configuration is invalid
            FileNotFoundError: If path doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigValidationError(
                    f"Invalid YAML in {path}: {e}"
                ) from e

        if data is None:
            # Empty file, return defaults
            return MyceliumConfig()

        try:
            return MyceliumConfig.model_validate(data)
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration validation failed in {path}:\n{e}"
            ) from e

    @classmethod
    def save(
        cls,
        config: MyceliumConfig,
        project_local: bool = False,
        create_dirs: bool = True,
    ) -> Path:
        """Save configuration to file.

        Args:
            config: Configuration to save
            project_local: Save to project-local (.mycelium/) if True,
                          user-global (~/.config/mycelium/) if False
            create_dirs: Create parent directories if they don't exist

        Returns:
            Path where configuration was saved

        Raises:
            ConfigValidationError: If configuration is invalid before save
        """
        # Validate before saving
        try:
            config.model_validate(config.model_dump())
        except ValidationError as e:
            raise ConfigValidationError(
                f"Configuration invalid, not saving:\n{e}"
            ) from e

        # Determine save path
        config_path = get_config_path(
            cls.CONFIG_FILENAME,
            prefer_project=project_local
        )

        # Create parent directories if needed
        if create_dirs:
            config_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to YAML with nice formatting
        config_dict = config.model_dump(mode="json", exclude_none=True)

        with open(config_path, "w") as f:
            yaml.dump(
                config_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        return config_path

    @classmethod
    def exists(cls, prefer_project: bool = True) -> bool:
        """Check if configuration file exists.

        Args:
            prefer_project: Check project-local first if True

        Returns:
            True if configuration file exists
        """
        return find_config_file(cls.CONFIG_FILENAME) is not None

    @classmethod
    def get_config_location(cls, prefer_project: bool = True) -> Path:
        """Get path where configuration would be saved.

        Args:
            prefer_project: Get project-local path if True

        Returns:
            Path to configuration file (may not exist)
        """
        return get_config_path(cls.CONFIG_FILENAME, prefer_project=prefer_project)