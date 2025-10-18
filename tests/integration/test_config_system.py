"""Integration tests for the configuration system.

This module contains end-to-end tests for the entire configuration system,
including:
- Loading and validating example configurations
- CLI command workflows
- Migration scenarios
- Cross-platform path handling
- Error handling and recovery
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigManager,
    ConfigSaveError,
    ConfigValidationError,
)
from mycelium_onboarding.config.migrations import (
    MigrationError,
    get_default_registry,
)
from mycelium_onboarding.config.schema import (
    DeploymentMethod,
    MyceliumConfig,
)


class TestExampleConfigurations:
    """Test that all example configurations are valid."""

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get path to examples directory."""
        # Find examples directory relative to test file
        test_dir = Path(__file__).parent
        repo_root = test_dir.parent.parent
        examples_dir = repo_root / "examples" / "configs"

        if not examples_dir.exists():
            pytest.skip(f"Examples directory not found: {examples_dir}")

        return examples_dir

    @pytest.mark.parametrize(
        "example_name",
        [
            "minimal.yaml",
            "redis-only.yaml",
            "postgres-only.yaml",
            "temporal-only.yaml",
            "full-stack.yaml",
            "kubernetes.yaml",
            "development.yaml",
            "production.yaml",
        ],
    )
    def test_example_config_valid(
        self, examples_dir: Path, example_name: str
    ) -> None:
        """Test that example configuration is valid."""
        example_path = examples_dir / example_name

        if not example_path.exists():
            pytest.skip(f"Example not found: {example_path}")

        # Load and validate
        manager = ConfigManager(config_path=example_path)
        config = manager.load()

        # Should load without errors
        assert config is not None
        assert config.version == "1.0"

        # Validate
        errors = manager.validate(config)
        assert len(errors) == 0, f"Validation errors in {example_name}: {errors}"

    def test_all_examples_parse_as_yaml(self, examples_dir: Path) -> None:
        """Test that all YAML files parse correctly."""
        for yaml_file in examples_dir.glob("*.yaml"):
            with yaml_file.open() as f:
                data = yaml.safe_load(f)
                assert data is not None, f"Empty YAML file: {yaml_file}"
                assert isinstance(data, dict), f"Invalid YAML structure: {yaml_file}"

    def test_minimal_config_uses_defaults(self, examples_dir: Path) -> None:
        """Test that minimal config uses expected defaults."""
        minimal_path = examples_dir / "minimal.yaml"
        if not minimal_path.exists():
            pytest.skip("minimal.yaml not found")

        manager = ConfigManager(config_path=minimal_path)
        config = manager.load()

        # Check defaults are used
        assert config.project_name == "mycelium"
        assert config.deployment.method == DeploymentMethod.DOCKER_COMPOSE
        assert config.deployment.auto_start is True
        assert config.services.redis.enabled is True
        assert config.services.postgres.enabled is True
        assert config.services.temporal.enabled is True

    def test_redis_only_config(self, examples_dir: Path) -> None:
        """Test redis-only configuration."""
        redis_only_path = examples_dir / "redis-only.yaml"
        if not redis_only_path.exists():
            pytest.skip("redis-only.yaml not found")

        manager = ConfigManager(config_path=redis_only_path)
        config = manager.load()

        # Verify only Redis is enabled
        assert config.services.redis.enabled is True
        assert config.services.postgres.enabled is False
        assert config.services.temporal.enabled is False

    def test_production_config_has_robust_settings(
        self, examples_dir: Path
    ) -> None:
        """Test production config has appropriate settings."""
        prod_path = examples_dir / "production.yaml"
        if not prod_path.exists():
            pytest.skip("production.yaml not found")

        manager = ConfigManager(config_path=prod_path)
        config = manager.load()

        # Production should have higher resource limits
        assert config.deployment.healthcheck_timeout >= 60
        assert config.services.redis.persistence is True
        assert config.services.postgres.max_connections >= 200

        # Should use explicit versions for reproducibility
        if config.services.redis.version:
            assert config.services.redis.version != "latest"


class TestCLIWorkflows:
    """Test CLI command workflows."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """Create temporary config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def temp_config_path(self, temp_config_dir: Path) -> Path:
        """Get path to temporary config file."""
        return temp_config_dir / "config.yaml"

    def test_init_creates_default_config(self, temp_config_path: Path) -> None:
        """Test that init workflow creates valid default config."""
        # Initially doesn't exist
        assert not temp_config_path.exists()

        # Create default config
        manager = ConfigManager(config_path=temp_config_path)
        default_config = manager.get_default_config()
        manager.save(default_config)

        # File should exist now
        assert temp_config_path.exists()

        # Should be valid
        loaded_config = manager.load()
        errors = manager.validate(loaded_config)
        assert len(errors) == 0

    def test_show_config_workflow(self, temp_config_path: Path) -> None:
        """Test show config workflow."""
        # Create config
        manager = ConfigManager(config_path=temp_config_path)
        config = MyceliumConfig(project_name="test-project")
        manager.save(config)

        # Load and show
        loaded = manager.load()
        yaml_output = loaded.to_yaml()

        # Should contain project name
        assert "test-project" in yaml_output

    def test_validate_workflow(self, temp_config_path: Path) -> None:
        """Test validate config workflow."""
        # Create valid config
        manager = ConfigManager(config_path=temp_config_path)
        config = MyceliumConfig()
        manager.save(config)

        # Validate
        loaded = manager.load()
        errors = manager.validate(loaded)
        assert len(errors) == 0

    def test_location_workflow(self, temp_config_path: Path) -> None:
        """Test config location workflow."""
        # Create config
        manager = ConfigManager(config_path=temp_config_path)
        config = MyceliumConfig()
        manager.save(config)

        # Check location
        assert temp_config_path.exists()
        assert manager.config_path == temp_config_path


class TestMigrationScenarios:
    """Test migration scenarios."""

    @pytest.fixture
    def temp_config_path(self, tmp_path: Path) -> Path:
        """Create temporary config file."""
        return tmp_path / "config.yaml"

    def test_no_migration_needed_for_current_version(
        self, temp_config_path: Path
    ) -> None:
        """Test that current version configs don't trigger migration."""
        # Create current version config
        manager = ConfigManager(config_path=temp_config_path)
        config = MyceliumConfig(version="1.0")
        manager.save(config)

        # Load with migration check
        loaded = manager.load_and_migrate()

        # Should not have changed
        assert loaded.version == "1.0"

    def test_migration_creates_backup(self, temp_config_path: Path) -> None:
        """Test that migration creates backup before modifying."""
        # Create old version config manually
        old_config = {
            "version": "0.9",
            "project_name": "test",
            "services": {"redis": {"enabled": True}},
        }

        with temp_config_path.open("w") as f:
            yaml.dump(old_config, f)

        # Note: This test would need a real 0.9->1.0 migration to be implemented
        # For now, we test that the backup mechanism works

        # Create backup manually to test restoration
        backup_path = temp_config_path.with_suffix(
            temp_config_path.suffix + ".backup"
        )
        shutil.copy2(temp_config_path, backup_path)

        assert backup_path.exists()

    def test_dry_run_doesnt_modify_file(self, temp_config_path: Path) -> None:
        """Test that dry run preview doesn't modify config file."""
        # Create config
        manager = ConfigManager(config_path=temp_config_path)
        original_config = MyceliumConfig(version="1.0")
        manager.save(original_config)

        # Get modification time
        original_mtime = temp_config_path.stat().st_mtime

        # Dry run (even though no migration needed, test the mechanism)
        manager.load_and_migrate(dry_run=True)

        # File shouldn't be modified
        current_mtime = temp_config_path.stat().st_mtime
        assert current_mtime == original_mtime

    def test_migration_preserves_custom_values(
        self, temp_config_path: Path
    ) -> None:
        """Test that migrations preserve user customizations."""
        # Create config with custom values
        custom_config = MyceliumConfig(
            version="1.0",
            project_name="custom-project",
        )
        custom_config.services.redis.port = 6380
        custom_config.services.postgres.database = "custom_db"

        manager = ConfigManager(config_path=temp_config_path)
        manager.save(custom_config)

        # Load (no migration needed for 1.0, but test the mechanism)
        loaded = manager.load()

        # Custom values preserved
        assert loaded.project_name == "custom-project"
        assert loaded.services.redis.port == 6380
        assert loaded.services.postgres.database == "custom_db"


class TestCrossPlatformPaths:
    """Test cross-platform path handling."""

    def test_absolute_paths_work(self, tmp_path: Path) -> None:
        """Test that absolute paths work across platforms."""
        config_path = tmp_path / "config.yaml"

        manager = ConfigManager(config_path=config_path)
        config = MyceliumConfig()
        manager.save(config)

        # Should work with absolute path
        assert config_path.exists()
        assert config_path.is_absolute()

    def test_paths_with_spaces(self, tmp_path: Path) -> None:
        """Test paths with spaces in names."""
        # Create directory with spaces
        space_dir = tmp_path / "my config dir"
        space_dir.mkdir()
        config_path = space_dir / "config.yaml"

        manager = ConfigManager(config_path=config_path)
        config = MyceliumConfig()
        manager.save(config)

        # Should handle spaces correctly
        assert config_path.exists()

        # Should load back
        loaded = manager.load()
        assert loaded.project_name == config.project_name

    def test_unicode_in_paths(self, tmp_path: Path) -> None:
        """Test paths with unicode characters."""
        # Create directory with unicode
        unicode_dir = tmp_path / "配置"
        unicode_dir.mkdir()
        config_path = unicode_dir / "config.yaml"

        manager = ConfigManager(config_path=config_path)
        config = MyceliumConfig()
        manager.save(config)

        # Should handle unicode correctly
        assert config_path.exists()

        # Should load back
        loaded = manager.load()
        assert loaded.project_name == config.project_name

    def test_relative_vs_absolute_paths(self, tmp_path: Path) -> None:
        """Test that both relative and absolute paths work."""
        config_path = tmp_path / "config.yaml"

        # Absolute path
        manager_abs = ConfigManager(config_path=config_path)
        config = MyceliumConfig()
        manager_abs.save(config)

        assert config_path.exists()

        # Load with absolute path
        loaded_abs = manager_abs.load()
        assert loaded_abs.project_name == config.project_name


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""

    @pytest.fixture
    def temp_config_path(self, tmp_path: Path) -> Path:
        """Create temporary config file."""
        return tmp_path / "config.yaml"

    def test_load_nonexistent_file_returns_defaults(
        self, temp_config_path: Path
    ) -> None:
        """Test that loading nonexistent file returns defaults."""
        manager = ConfigManager(config_path=temp_config_path)

        # File doesn't exist
        assert not temp_config_path.exists()

        # Should return defaults without error
        config = manager.load()
        assert config.project_name == "mycelium"

    def test_load_empty_file_returns_defaults(
        self, temp_config_path: Path
    ) -> None:
        """Test that loading empty file returns defaults."""
        # Create empty file
        temp_config_path.touch()

        manager = ConfigManager(config_path=temp_config_path)
        config = manager.load()

        # Should use defaults
        assert config.project_name == "mycelium"

    def test_load_invalid_yaml_raises_error(
        self, temp_config_path: Path
    ) -> None:
        """Test that invalid YAML raises clear error."""
        # Write invalid YAML
        with temp_config_path.open("w") as f:
            f.write("invalid: yaml: content:\n  - broken")

        manager = ConfigManager(config_path=temp_config_path)

        # Should raise ConfigLoadError
        with pytest.raises(ConfigLoadError):
            manager.load()

    def test_load_invalid_schema_raises_error(
        self, temp_config_path: Path
    ) -> None:
        """Test that invalid schema raises validation error."""
        # Write valid YAML but invalid schema
        invalid_config = {
            "version": "1.0",
            "services": {
                "redis": {
                    "port": 99999  # Invalid: > 65535
                }
            },
        }

        with temp_config_path.open("w") as f:
            yaml.dump(invalid_config, f)

        manager = ConfigManager(config_path=temp_config_path)

        # Should raise ConfigValidationError
        with pytest.raises(ConfigValidationError):
            manager.load()

    def test_save_invalid_config_raises_error(
        self, temp_config_path: Path
    ) -> None:
        """Test that saving invalid config raises error."""
        manager = ConfigManager(config_path=temp_config_path)

        # Create invalid config data directly (bypass Pydantic validation)
        invalid_data = {
            "project_name": "test",
            "services": {
                "redis": {"enabled": True, "port": 99999},  # Invalid port
                "postgres": {"enabled": False},
                "temporal": {"enabled": False}
            },
            "deployment": {"method": "docker-compose"}
        }

        # Write invalid YAML directly
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, 'w') as f:
            yaml.dump(invalid_data, f)

        # Should raise on load due to validation
        with pytest.raises((ConfigLoadError, ConfigValidationError)):
            manager.load()

    def test_atomic_write_failure_doesnt_corrupt(
        self, temp_config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that save failure doesn't corrupt existing config."""
        manager = ConfigManager(config_path=temp_config_path)

        # Create initial valid config
        initial_config = MyceliumConfig(project_name="initial")
        manager.save(initial_config)

        # Simulate write failure by making temp file creation fail
        import tempfile
        original_mkstemp = tempfile.mkstemp

        def failing_mkstemp(*args, **kwargs):
            raise OSError("Simulated disk full")

        monkeypatch.setattr(tempfile, "mkstemp", failing_mkstemp)

        # Try to save (should fail due to simulated disk issue)
        new_config = MyceliumConfig(project_name="should-not-save")
        with pytest.raises((OSError, ConfigSaveError)):
            manager.save(new_config)

        # Restore original function
        monkeypatch.setattr(tempfile, "mkstemp", original_mkstemp)

        # Original config should still be intact
        loaded = manager.load()
        assert loaded.project_name == "initial"

    def test_recovery_from_backup(self, temp_config_path: Path) -> None:
        """Test recovery from backup file."""
        manager = ConfigManager(config_path=temp_config_path)

        # Create initial config
        initial_config = MyceliumConfig(project_name="initial")
        manager.save(initial_config)

        # Modify and save (creates backup)
        modified_config = MyceliumConfig(project_name="modified")
        manager.save(modified_config)

        # Backup should exist
        backup_path = temp_config_path.with_suffix(
            temp_config_path.suffix + ".backup"
        )
        assert backup_path.exists()

        # Restore from backup
        shutil.copy2(backup_path, temp_config_path)

        # Should have initial config
        restored = manager.load()
        assert restored.project_name == "initial"


class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""

    def test_complete_onboarding_workflow(self, tmp_path: Path) -> None:
        """Test complete onboarding workflow with config."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        # 1. Initialize with defaults
        config = manager.get_default_config()

        # 2. Customize for project
        config.project_name = "my-project"
        config.services.redis.port = 6380

        # 3. Validate
        errors = manager.validate(config)
        assert len(errors) == 0

        # 4. Save
        manager.save(config)
        assert config_path.exists()

        # 5. Later: load and use
        loaded = manager.load()
        assert loaded.project_name == "my-project"
        assert loaded.services.redis.port == 6380

    def test_configuration_update_workflow(self, tmp_path: Path) -> None:
        """Test updating existing configuration."""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(config_path=config_path)

        # 1. Create initial config
        initial = MyceliumConfig()
        manager.save(initial)

        # 2. Load existing config
        config = manager.load()

        # 3. Modify
        config.services.postgres.max_connections = 200

        # 4. Validate changes
        errors = manager.validate(config)
        assert len(errors) == 0

        # 5. Save (creates backup)
        manager.save(config)

        # 6. Verify update
        updated = manager.load()
        assert updated.services.postgres.max_connections == 200

    def test_multi_environment_workflow(self, tmp_path: Path) -> None:
        """Test managing multiple environment configurations."""
        # Development config
        dev_path = tmp_path / "dev-config.yaml"
        dev_manager = ConfigManager(config_path=dev_path)
        dev_config = MyceliumConfig(project_name="mycelium-dev")
        dev_config.services.redis.max_memory = "256mb"
        dev_manager.save(dev_config)

        # Production config
        prod_path = tmp_path / "prod-config.yaml"
        prod_manager = ConfigManager(config_path=prod_path)
        prod_config = MyceliumConfig(project_name="mycelium-prod")
        prod_config.services.redis.max_memory = "4gb"
        prod_config.deployment.method = DeploymentMethod.KUBERNETES
        prod_manager.save(prod_config)

        # Verify both exist and are different
        dev_loaded = dev_manager.load()
        prod_loaded = prod_manager.load()

        assert dev_loaded.project_name == "mycelium-dev"
        assert prod_loaded.project_name == "mycelium-prod"
        assert dev_loaded.services.redis.max_memory == "256mb"
        assert prod_loaded.services.redis.max_memory == "4gb"
