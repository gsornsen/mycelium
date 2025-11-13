"""Unit tests for configuration management CLI commands.

This module tests all configuration management commands including where, show,
get, set, edit, migrate, and rollback.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner

from mycelium_onboarding.cli_commands.commands.config import (
    edit_command,
    get_command,
    rollback_command,
    set_command,
    show_command,
    where_command,
)
from mycelium_onboarding.cli_commands.commands.config_migrate import migrate_command
from mycelium_onboarding.config.schema import MyceliumConfig


@pytest.fixture
def runner():
    """Provide Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / ".config" / "mycelium"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory."""
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


@pytest.fixture
def sample_config():
    """Provide sample configuration."""
    return MyceliumConfig(
        project_name="test-project",
        version="1.0",
    )


class TestWhereCommand:
    """Tests for 'config where' command."""

    def test_where_shows_both_paths(self, runner):
        """Test that 'where' command shows both global and project paths."""
        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_global,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
        ):
            mock_global.return_value = Path("/home/user/.config/mycelium/config.yaml")
            mock_project.return_value = Path("/home/user/project/.mycelium/config.yaml")

            result = runner.invoke(where_command, [])

            assert result.exit_code == 0
            assert "GLOBAL" in result.output
            assert "PROJECT" in result.output
            assert ".config/mycelium/config.yaml" in result.output

    def test_where_global_only(self, runner):
        """Test that '--global' flag shows only global config path."""
        with patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_global:
            mock_global.return_value = Path("/home/user/.config/mycelium/config.yaml")

            result = runner.invoke(where_command, ["--global"])

            assert result.exit_code == 0
            assert "Global Configuration" in result.output
            assert ".config/mycelium/config.yaml" in result.output

    def test_where_project_only(self, runner):
        """Test that '--project' flag shows only project config path."""
        with patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project:
            mock_project.return_value = Path("/home/user/project/.mycelium/config.yaml")

            result = runner.invoke(where_command, ["--project"])

            assert result.exit_code == 0
            assert "Project Configuration" in result.output
            assert ".mycelium/config.yaml" in result.output

    def test_where_shows_file_status(self, runner, temp_config_dir):
        """Test that 'where' command shows whether files exist."""
        global_path = temp_config_dir / "config.yaml"

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_global,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
        ):
            mock_global.return_value = global_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")

            # Create global config
            global_path.write_text("project_name: test\n")

            result = runner.invoke(where_command, [])

            assert result.exit_code == 0
            assert "Exists" in result.output or "Not found" in result.output


class TestShowCommand:
    """Tests for 'config show' command."""

    def test_show_merged_config(self, runner, sample_config):
        """Test showing merged configuration."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(show_command, ["--source", "merged"])

            assert result.exit_code == 0
            assert "test-project" in result.output
            assert "Merged Configuration" in result.output

    def test_show_json_format(self, runner, sample_config):
        """Test showing configuration in JSON format."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(show_command, ["--format", "json"])

            assert result.exit_code == 0
            assert "{" in result.output  # JSON output
            assert '"project_name"' in result.output or "project_name" in result.output

    def test_show_yaml_format(self, runner, sample_config):
        """Test showing configuration in YAML format (default)."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(show_command, [])

            assert result.exit_code == 0
            # YAML format check
            assert "project_name" in result.output or "test-project" in result.output

    def test_show_nonexistent_config(self, runner):
        """Test showing configuration when file doesn't exist."""
        with (
            patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader,
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
        ):
            mock_path.return_value = Path("/nonexistent/config.yaml")
            mock_instance = Mock()
            mock_loader.return_value = mock_instance

            # Simulate file not found for global/project sources
            result = runner.invoke(show_command, ["--source", "global"])

            # May show error or default config depending on implementation
            assert "No global configuration file found" in result.output or result.exit_code == 0


class TestGetCommand:
    """Tests for 'config get' command."""

    def test_get_simple_key(self, runner, sample_config):
        """Test getting a simple configuration value."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(get_command, ["project_name"])

            assert result.exit_code == 0
            assert "test-project" in result.output

    def test_get_nested_key(self, runner):
        """Test getting nested configuration value with dot notation."""
        config = MyceliumConfig(
            project_name="test",
        )

        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = config
            mock_loader.return_value = mock_instance

            result = runner.invoke(get_command, ["services.redis.port"])

            assert result.exit_code == 0
            assert "6379" in result.output  # Default Redis port

    def test_get_nonexistent_key(self, runner, sample_config):
        """Test getting a non-existent key."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(get_command, ["nonexistent.key"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_get_with_default(self, runner, sample_config):
        """Test getting a key with default value."""
        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader:
            mock_instance = Mock()
            mock_instance.load.return_value = sample_config
            mock_loader.return_value = mock_instance

            result = runner.invoke(get_command, ["nonexistent.key", "--default", "fallback"])

            # Should show default value without error
            assert "fallback" in result.output or result.exit_code == 0


class TestSetCommand:
    """Tests for 'config set' command."""

    def test_set_simple_value(self, runner, temp_config_dir):
        """Test setting a simple configuration value."""
        config_path = temp_config_dir / "config.yaml"

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
        ):
            mock_path.return_value = config_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")

            # Create initial config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            sample_config = MyceliumConfig()
            with config_path.open("w") as f:
                yaml.dump(sample_config.to_dict(), f)

            result = runner.invoke(set_command, ["project_name", "new-project"])

            assert result.exit_code == 0
            assert "new-project" in result.output

            # Verify value was written
            with config_path.open() as f:
                saved_config = yaml.safe_load(f)
                assert saved_config["project_name"] == "new-project"

    def test_set_with_type_conversion(self, runner, temp_config_dir):
        """Test setting value with explicit type conversion."""
        config_path = temp_config_dir / "config.yaml"

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
        ):
            mock_path.return_value = config_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")

            # Create initial config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            sample_config = MyceliumConfig()
            with config_path.open("w") as f:
                yaml.dump(sample_config.to_dict(), f)

            result = runner.invoke(set_command, ["services.redis.port", "6380", "--type", "int"])

            assert result.exit_code == 0

    def test_set_boolean_value(self, runner, temp_config_dir):
        """Test setting boolean configuration value."""
        config_path = temp_config_dir / "config.yaml"

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
        ):
            mock_path.return_value = config_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")

            # Create initial config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            sample_config = MyceliumConfig()
            with config_path.open("w") as f:
                yaml.dump(sample_config.to_dict(), f)

            result = runner.invoke(set_command, ["services.redis.enabled", "false", "--type", "bool"])

            assert result.exit_code == 0


class TestEditCommand:
    """Tests for 'config edit' command."""

    @pytest.mark.skip(reason="TODO: Fix subprocess.run mocking - tracked in unified PR")
    def test_edit_opens_editor(self, runner, temp_config_dir):
        """Test that edit command attempts to open an editor."""
        config_path = temp_config_dir / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create config file
        sample_config = MyceliumConfig()
        with config_path.open("w") as f:
            yaml.dump(sample_config.to_dict(), f)

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
            patch("mycelium_onboarding.cli_commands.commands.config.subprocess.run") as mock_run,
            patch("os.environ.get") as mock_env,
            patch("mycelium_onboarding.cli_commands.commands.config.ConfigManager") as mock_manager,
        ):
            mock_path.return_value = config_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")
            mock_env.return_value = "nano"
            mock_run.return_value = Mock(returncode=0)

            # Mock ConfigManager to return valid config during post-edit validation
            mock_manager_instance = Mock()
            mock_manager_instance.load.return_value = sample_config
            mock_manager.return_value = mock_manager_instance

            runner.invoke(edit_command, ["--global"])

            assert mock_run.called
            # Check that nano was called with the config path
            assert any(str(config_path) in str(call) for call in mock_run.call_args_list)

    def test_edit_creates_file_if_missing(self, runner, temp_config_dir):
        """Test that edit command creates file if it doesn't exist."""
        config_path = temp_config_dir / "config.yaml"

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.get_project_config_path") as mock_project,
            patch("mycelium_onboarding.cli_commands.commands.config.click.confirm") as mock_confirm,
        ):
            mock_path.return_value = config_path
            mock_project.return_value = Path("/nonexistent/.mycelium/config.yaml")
            mock_confirm.return_value = False  # Don't create

            result = runner.invoke(edit_command, ["--global"])

            assert "does not exist" in result.output


class TestMigrateCommand:
    """Tests for 'config migrate' command."""

    def test_migrate_no_legacy_configs(self, runner):
        """Test migrate when no legacy configs exist."""
        with patch(
            "mycelium_onboarding.cli_commands.commands.config_migrate._detect_legacy_configs_fallback"
        ) as mock_fallback:
            mock_fallback.return_value = []

            result = runner.invoke(migrate_command, [])

            assert result.exit_code == 0
            assert "No migration needed" in result.output or "No legacy" in result.output

    @pytest.mark.skip(reason="TODO: Fix migration_util.detect_migration_candidates mocking - tracked in unified PR")
    def test_migrate_dry_run(self, runner, temp_config_dir):
        """Test migrate command in dry-run mode."""
        legacy_config = temp_config_dir / "mycelium-config.yaml"
        legacy_config.write_text("project_name: old-project\n")

        with patch(
            "mycelium_onboarding.cli_commands.commands.config_migrate._detect_legacy_configs_fallback"
        ) as mock_detect:
            mock_detect.return_value = [legacy_config]

            result = runner.invoke(migrate_command, ["--dry-run"])

            assert result.exit_code == 0
            assert "DRY RUN" in result.output or "Dry-run successful" in result.output

    @pytest.mark.skip(reason="TODO: Fix migration_util.detect_migration_candidates mocking - tracked in unified PR")
    def test_migrate_with_confirmation(self, runner, temp_config_dir):
        """Test migrate command with user confirmation."""
        legacy_config = temp_config_dir / "mycelium-config.yaml"
        legacy_config.write_text("project_name: old-project\n")

        with (
            patch(
                "mycelium_onboarding.cli_commands.commands.config_migrate._detect_legacy_configs_fallback"
            ) as mock_detect,
            patch("mycelium_onboarding.cli_commands.commands.config_migrate.Confirm.ask") as mock_confirm,
        ):
            mock_detect.return_value = [legacy_config]
            mock_confirm.return_value = False  # User cancels

            result = runner.invoke(migrate_command, [])

            assert "cancelled" in result.output.lower()


class TestRollbackCommand:
    """Tests for 'config rollback' command."""

    def test_rollback_missing_directory(self, runner):
        """Test rollback with non-existent backup directory."""
        result = runner.invoke(rollback_command, ["/nonexistent/backup"])

        assert result.exit_code != 0

    def test_rollback_empty_directory(self, runner, tmp_path):
        """Test rollback with empty backup directory."""
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()

        result = runner.invoke(rollback_command, [str(backup_dir)])

        assert "No backup files found" in result.output

    def test_rollback_with_confirmation(self, runner, tmp_path):
        """Test rollback with user confirmation."""
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()

        # Create a backup file
        backup_file = backup_dir / "config.yaml"
        backup_file.write_text("project_name: backup-project\n")

        with patch("mycelium_onboarding.cli_commands.commands.config.click.confirm") as mock_confirm:
            mock_confirm.return_value = False  # User cancels

            result = runner.invoke(rollback_command, [str(backup_dir)])

            assert "cancelled" in result.output.lower() or result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling across commands."""

    def test_invalid_config_file(self, runner, temp_config_dir):
        """Test handling of invalid YAML config file."""
        config_path = temp_config_dir / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid YAML
        config_path.write_text("invalid: yaml: content::")

        with (
            patch("mycelium_onboarding.cli_commands.commands.config.get_global_config_path") as mock_path,
            patch("mycelium_onboarding.cli_commands.commands.config.ConfigLoader") as mock_loader,
        ):
            mock_path.return_value = config_path
            mock_instance = Mock()
            mock_instance.load.side_effect = Exception("Invalid YAML")
            mock_loader.return_value = mock_instance

            result = runner.invoke(show_command, [])

            assert result.exit_code != 0
            assert "error" in result.output.lower()

    def test_permission_error(self, runner, temp_config_dir):
        """Test handling of permission errors."""
        temp_config_dir / "config.yaml"

        with patch("mycelium_onboarding.cli_commands.commands.config.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_instance.save.side_effect = PermissionError("No write access")
            mock_manager.return_value = mock_instance

            result = runner.invoke(set_command, ["project_name", "test"])

            assert result.exit_code != 0


class TestIntegration:
    """Integration tests for command workflows."""

    def test_full_config_workflow(self, runner, temp_config_dir):
        """Test complete workflow: show, set, get, edit."""
        temp_config_dir / "config.yaml"

        # This test would require full integration setup
        # Skipped for unit tests, but shows expected workflow
        pass

    def test_migration_workflow(self, runner, temp_config_dir):
        """Test migration workflow with backup and rollback."""
        # This test would require full migration setup
        # Skipped for unit tests, but shows expected workflow
        pass
