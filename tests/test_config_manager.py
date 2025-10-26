"""Comprehensive tests for ConfigManager.

Tests cover:
- Loading from project-local and user-global files
- Hierarchical precedence (project > user > defaults)
- Saving configuration with atomic writes
- Backup creation before overwrite
- YAML parsing error handling
- Validation error handling
- Default config generation
- Configuration merging
- Edge cases and error conditions
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigManager,
    ConfigSaveError,
    ConfigValidationError,
)
from mycelium_onboarding.config.schema import (
    DeploymentMethod,
    MyceliumConfig,
)


class TestConfigManagerInit:
    """Test ConfigManager initialization."""

    def test_init_without_path(self) -> None:
        """Test initialization without explicit config path."""
        manager = ConfigManager()
        assert manager.config_path is None

    def test_init_with_path(self, tmp_path: Path) -> None:
        """Test initialization with explicit config path."""
        config_path = tmp_path / "test-config.yaml"
        manager = ConfigManager(config_path=config_path)
        assert manager.config_path == config_path


class TestConfigManagerLoad:
    """Test configuration loading functionality."""

    def test_load_default_config_when_no_file_exists(self, tmp_path: Path) -> None:
        """Test loading returns defaults when no config file exists."""
        # Ensure no config file exists
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path,
            ),
        ):
            manager = ConfigManager()
            config = manager.load()

            assert isinstance(config, MyceliumConfig)
            assert config.project_name == "mycelium"
            assert config.version == "1.0"

    def test_load_from_user_global(self, tmp_path: Path) -> None:
        """Test loading from user-global config directory."""
        # Create user-global config
        config_path = tmp_path / "config.yaml"
        test_config = MyceliumConfig(project_name="test-project")
        config_path.write_text(test_config.to_yaml())

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path,
            ),
        ):
            manager = ConfigManager()
            config = manager.load()

            assert config.project_name == "test-project"

    def test_load_from_project_local(self, tmp_path: Path) -> None:
        """Test loading from project-local config directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create project-local config
        config_path = project_dir / "config.yaml"
        test_config = MyceliumConfig(project_name="project-local")
        config_path.write_text(test_config.to_yaml())

        with (
            patch.dict(
                os.environ,
                {"MYCELIUM_PROJECT_DIR": str(project_dir)},
                clear=True,
            ),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path,
            ),
        ):
            manager = ConfigManager()
            config = manager.load()

            assert config.project_name == "project-local"

    def test_load_precedence_project_over_user(self, tmp_path: Path) -> None:
        """Test that project-local config takes precedence over user-global."""
        # Create user-global config
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        user_config = user_dir / "config.yaml"
        user_config.write_text(MyceliumConfig(project_name="user-global").to_yaml())

        # Create project-local config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / "config.yaml"
        project_config.write_text(
            MyceliumConfig(project_name="project-local").to_yaml()
        )

        with (
            patch.dict(
                os.environ,
                {"MYCELIUM_PROJECT_DIR": str(project_dir)},
                clear=True,
            ),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=user_dir,
            ),
        ):
            manager = ConfigManager()
            config = manager.load()

            # Project-local should win
            assert config.project_name == "project-local"

    def test_load_explicit_path(self, tmp_path: Path) -> None:
        """Test loading from explicit config path."""
        config_path = tmp_path / "custom-config.yaml"
        test_config = MyceliumConfig(project_name="explicit-path")
        config_path.write_text(test_config.to_yaml())

        manager = ConfigManager(config_path=config_path)
        config = manager.load()

        assert config.project_name == "explicit-path"

    def test_load_explicit_path_not_exists_returns_defaults(
        self, tmp_path: Path
    ) -> None:
        """Test loading from non-existent explicit path returns defaults."""
        config_path = tmp_path / "nonexistent.yaml"

        manager = ConfigManager(config_path=config_path)
        config = manager.load()

        assert isinstance(config, MyceliumConfig)
        assert config.project_name == "mycelium"

    def test_load_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        """Test loading empty config file returns defaults."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")

        manager = ConfigManager(config_path=config_path)
        config = manager.load()

        assert isinstance(config, MyceliumConfig)
        assert config.project_name == "mycelium"

    def test_load_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test loading invalid YAML raises ConfigLoadError."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content:\n  - bad indentation")

        manager = ConfigManager(config_path=config_path)

        with pytest.raises(ConfigLoadError) as exc_info:
            manager.load()

        assert "Failed to parse YAML" in str(exc_info.value)

    def test_load_validation_error_raises_exception(self, tmp_path: Path) -> None:
        """Test loading config with validation errors raises ConfigValidationError."""
        config_path = tmp_path / "config.yaml"
        # Invalid port number
        config_path.write_text(
            """
version: "1.0"
project_name: test
services:
  redis:
    port: 99999
"""
        )

        manager = ConfigManager(config_path=config_path)

        with pytest.raises(ConfigValidationError) as exc_info:
            manager.load()

        assert "validation failed" in str(exc_info.value).lower()

    def test_load_unreadable_file_raises_error(self, tmp_path: Path) -> None:
        """Test loading unreadable file raises ConfigLoadError."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("version: '1.0'")
        config_path.chmod(0o000)  # Make unreadable

        manager = ConfigManager(config_path=config_path)

        try:
            with pytest.raises(ConfigLoadError) as exc_info:
                manager.load()

            assert "Failed to read configuration file" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            config_path.chmod(0o644)


class TestConfigManagerSave:
    """Test configuration saving functionality."""

    def test_save_to_new_file(self, tmp_path: Path) -> None:
        """Test saving configuration to new file."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        config = MyceliumConfig(project_name="test-save")
        manager.save(config)

        assert config_path.exists()
        loaded = MyceliumConfig.from_yaml(config_path.read_text())
        assert loaded.project_name == "test-save"

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that save creates parent directories."""
        config_path = tmp_path / "subdir" / "nested" / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        config = MyceliumConfig(project_name="nested-save")
        manager.save(config)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_creates_backup(self, tmp_path: Path) -> None:
        """Test that save creates backup of existing file."""
        config_path = tmp_path / "config.yaml"

        # Create initial config
        original_config = MyceliumConfig(project_name="original")
        config_path.write_text(original_config.to_yaml())

        # Save new config
        manager = ConfigManager(config_path=config_path)
        new_config = MyceliumConfig(project_name="updated")
        manager.save(new_config)

        # Check backup exists
        backup_path = config_path.with_suffix(".yaml.backup")
        assert backup_path.exists()

        # Verify backup contains original content
        backup_config = MyceliumConfig.from_yaml(backup_path.read_text())
        assert backup_config.project_name == "original"

        # Verify main file has new content
        saved_config = MyceliumConfig.from_yaml(config_path.read_text())
        assert saved_config.project_name == "updated"

    def test_save_atomic_write_on_failure_no_corruption(self, tmp_path: Path) -> None:
        """Test that failed save doesn't corrupt existing file."""
        config_path = tmp_path / "config.yaml"

        # Create initial config
        original_config = MyceliumConfig(project_name="original")
        config_path.write_text(original_config.to_yaml())

        # Try to save with write failure
        manager = ConfigManager(config_path=config_path)

        with (
            patch(
                "mycelium_onboarding.config.manager.yaml.dump",
                side_effect=Exception("Serialization failed"),
            ),
            pytest.raises(ConfigSaveError),
        ):
            manager.save(MyceliumConfig(project_name="new"))

        # Original file should still exist and be unchanged
        assert config_path.exists()
        loaded = MyceliumConfig.from_yaml(config_path.read_text())
        assert loaded.project_name == "original"

    def test_save_invalid_config_raises_error(self, tmp_path: Path) -> None:
        """Test saving invalid config raises ConfigValidationError."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        # Create config and manually break it
        config = MyceliumConfig()
        # Disable all services (should fail validation)
        config.services.redis.enabled = False
        config.services.postgres.enabled = False
        config.services.temporal.enabled = False

        with pytest.raises(ConfigValidationError):
            manager.save(config)

        # File should not be created
        assert not config_path.exists()

    def test_save_determines_user_global_path_by_default(self, tmp_path: Path) -> None:
        """Test save uses user-global path when no config exists."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "mycelium_onboarding.config.manager.get_config_dir",
                return_value=tmp_path,
            ),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path,
            ),
        ):
            manager = ConfigManager()
            config = MyceliumConfig(project_name="user-save")
            manager.save(config)

            expected_path = tmp_path / "config.yaml"
            assert expected_path.exists()

    def test_save_determines_project_local_path_in_project(
        self, tmp_path: Path
    ) -> None:
        """Test save uses project-local path when in project context."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with (
            patch.dict(
                os.environ,
                {"MYCELIUM_PROJECT_DIR": str(project_dir)},
                clear=True,
            ),
            patch(
                "mycelium_onboarding.config.manager.get_config_dir",
                return_value=tmp_path / "user",
            ),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path / "user",
            ),
        ):
            manager = ConfigManager()
            config = MyceliumConfig(project_name="project-save")
            manager.save(config)

            expected_path = project_dir / "config.yaml"
            assert expected_path.exists()

    def test_save_to_existing_config_location(self, tmp_path: Path) -> None:
        """Test save updates existing config at its original location."""
        config_path = tmp_path / "config.yaml"

        # Create and save initial config
        initial_config = MyceliumConfig(project_name="initial")
        config_path.write_text(initial_config.to_yaml())

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "mycelium_onboarding.config_loader.get_config_dir",
                return_value=tmp_path,
            ),
            patch(
                "mycelium_onboarding.config.manager.get_config_dir",
                return_value=tmp_path,
            ),
        ):
            # Load and modify
            manager = ConfigManager()
            config = manager.load()
            config.project_name = "updated"

            # Save should update same file
            manager.save(config)

            assert config_path.exists()
            loaded = MyceliumConfig.from_yaml(config_path.read_text())
            assert loaded.project_name == "updated"

    def test_save_sets_secure_permissions(self, tmp_path: Path) -> None:
        """Test that saved config file has secure permissions (0600)."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        config = MyceliumConfig(project_name="secure")
        manager.save(config)

        # Check permissions (should be 0600)
        mode = config_path.stat().st_mode & 0o777
        assert mode == 0o600


class TestConfigManagerValidate:
    """Test configuration validation functionality."""

    def test_validate_valid_config_returns_empty_list(self) -> None:
        """Test validating valid config returns empty error list."""
        manager = ConfigManager()
        config = MyceliumConfig(project_name="valid")

        errors = manager.validate(config)

        assert errors == []

    def test_validate_invalid_config_returns_errors(self) -> None:
        """Test validating invalid config returns error list."""
        manager = ConfigManager()
        config = MyceliumConfig()

        # Manually break config to bypass validation
        config.services.redis.enabled = False
        config.services.postgres.enabled = False
        config.services.temporal.enabled = False

        errors = manager.validate(config)

        assert len(errors) > 0
        assert any("at least one service" in err.lower() for err in errors)

    def test_validate_catches_field_errors(self) -> None:
        """Test validate catches and formats field validation errors."""
        # Create a config dict with invalid data and try to validate
        invalid_data = {
            "version": "1.0",
            "project_name": "test",
            "services": {
                "redis": {
                    "port": 99999  # Invalid port
                }
            },
        }

        # This should raise during from_dict
        with pytest.raises(ValidationError):
            MyceliumConfig.from_dict(invalid_data)


class TestConfigManagerDefaults:
    """Test default configuration functionality."""

    def test_get_default_config_returns_valid_config(self) -> None:
        """Test get_default_config returns valid MyceliumConfig."""
        manager = ConfigManager()
        config = manager.get_default_config()

        assert isinstance(config, MyceliumConfig)
        assert config.version == "1.0"
        assert config.project_name == "mycelium"
        assert config.services.redis.enabled is True
        assert config.services.postgres.enabled is True
        assert config.services.temporal.enabled is True

    def test_default_config_has_sensible_defaults(self) -> None:
        """Test default config has expected default values."""
        manager = ConfigManager()
        config = manager.get_default_config()

        # Check service ports
        assert config.services.redis.port == 6379
        assert config.services.postgres.port == 5432
        assert config.services.temporal.ui_port == 8080

        # Check deployment
        assert config.deployment.method == DeploymentMethod.DOCKER_COMPOSE
        assert config.deployment.auto_start is True


class TestConfigManagerMerge:
    """Test configuration merging functionality."""

    def test_merge_configs_simple_override(self) -> None:
        """Test merging configs with simple field override."""
        manager = ConfigManager()
        base = MyceliumConfig(project_name="base")
        overlay = MyceliumConfig(project_name="overlay")

        merged = manager.merge_configs(base, overlay)

        assert merged.project_name == "overlay"

    def test_merge_configs_nested_override(self) -> None:
        """Test merging configs with nested field override."""
        manager = ConfigManager()
        base = MyceliumConfig()
        base.services.redis.port = 6379

        overlay = MyceliumConfig()
        overlay.services.redis.port = 6380

        merged = manager.merge_configs(base, overlay)

        assert merged.services.redis.port == 6380
        # Other fields should remain from base
        assert merged.services.postgres.port == 5432

    def test_merge_configs_deep_merge(self) -> None:
        """Test deep merging preserves non-overlapping fields."""
        manager = ConfigManager()

        base = MyceliumConfig()
        base.services.redis.port = 6379
        base.services.postgres.port = 5432

        overlay = MyceliumConfig()
        overlay.services.redis.port = 6380
        # Don't set postgres port in overlay

        merged = manager.merge_configs(base, overlay)

        # Redis port from overlay
        assert merged.services.redis.port == 6380
        # Postgres port from base (not overridden)
        assert merged.services.postgres.port == 5432

    def test_merge_configs_invalid_result_raises_error(self) -> None:
        """Test merging that produces invalid config raises error."""
        manager = ConfigManager()

        # Create two valid configs
        base = MyceliumConfig(project_name="base")
        overlay = MyceliumConfig(project_name="overlay")

        # Mock from_dict to raise ValidationError during merge
        # First need to create a proper ValidationError by trying to
        # validate invalid data
        try:
            MyceliumConfig.model_validate(
                {
                    "services": {
                        "redis": {"enabled": False},
                        "postgres": {"enabled": False},
                        "temporal": {"enabled": False},
                    }
                }
            )
        except ValidationError as validation_error:
            # Now use this error in the mock
            with patch.object(
                MyceliumConfig,
                "from_dict",
                side_effect=validation_error,
            ):
                with pytest.raises(ConfigValidationError) as exc_info:
                    manager.merge_configs(base, overlay)

                assert "Merged configuration is invalid" in str(exc_info.value)

    def test_merge_configs_overlay_takes_precedence(self) -> None:
        """Test that overlay values always override base values."""
        manager = ConfigManager()

        base = MyceliumConfig(project_name="base")
        base.services.redis.persistence = True
        base.services.redis.max_memory = "512mb"

        overlay = MyceliumConfig(project_name="overlay")
        overlay.services.redis.persistence = False
        overlay.services.redis.max_memory = "1gb"

        merged = manager.merge_configs(base, overlay)

        assert merged.project_name == "overlay"
        assert merged.services.redis.persistence is False
        assert merged.services.redis.max_memory == "1gb"


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Test saving and loading config preserves all data."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        # Create config with custom values
        original = MyceliumConfig(project_name="roundtrip-test")
        original.services.redis.port = 6380
        original.services.postgres.database = "custom_db"
        original.deployment.method = DeploymentMethod.KUBERNETES

        # Save and reload
        manager.save(original)

        manager2 = ConfigManager(config_path=config_path)
        loaded = manager2.load()

        # Verify all fields match
        assert loaded.project_name == "roundtrip-test"
        assert loaded.services.redis.port == 6380
        assert loaded.services.postgres.database == "custom_db"
        assert loaded.deployment.method == DeploymentMethod.KUBERNETES

    def test_multiple_saves_create_multiple_backups(self, tmp_path: Path) -> None:
        """Test multiple saves update backup each time."""
        config_path = tmp_path / "config.yaml"
        backup_path = config_path.with_suffix(".yaml.backup")
        manager = ConfigManager(config_path=config_path)

        # First save
        config1 = MyceliumConfig(project_name="version1")
        manager.save(config1)
        assert not backup_path.exists()  # No backup for first save

        # Second save
        config2 = MyceliumConfig(project_name="version2")
        manager.save(config2)
        assert backup_path.exists()

        # Backup should contain version1
        backup_config = MyceliumConfig.from_yaml(backup_path.read_text())
        assert backup_config.project_name == "version1"

        # Main file should contain version2
        current_config = MyceliumConfig.from_yaml(config_path.read_text())
        assert current_config.project_name == "version2"

    def test_yaml_formatting_is_readable(self, tmp_path: Path) -> None:
        """Test that saved YAML is human-readable."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        config = MyceliumConfig(project_name="formatting-test")
        manager.save(config)

        yaml_content = config_path.read_text()

        # Check for readable formatting
        assert "version:" in yaml_content
        assert "project_name:" in yaml_content
        assert "services:" in yaml_content
        assert "redis:" in yaml_content

        # Should not be flow style (all on one line)
        assert yaml_content.count("\n") > 5

    def test_handles_permission_error_on_directory_creation(
        self, tmp_path: Path
    ) -> None:
        """Test graceful handling of permission errors during directory creation."""
        config_dir = tmp_path / "readonly"
        config_dir.mkdir()
        config_path = config_dir / "subdir" / "config.yaml"

        manager = ConfigManager(config_path=config_path)
        config = MyceliumConfig(project_name="permission-test")

        # Make directory read-only to prevent subdirectory creation
        config_dir.chmod(0o444)

        try:
            with pytest.raises(ConfigSaveError) as exc_info:
                manager.save(config)

            assert "Failed to create config directory" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            config_dir.chmod(0o755)
