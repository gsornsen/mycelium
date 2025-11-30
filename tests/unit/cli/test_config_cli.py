"""Unit tests for config CLI commands.

Tests the mycelium config show/edit/validate commands.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mycelium.cli.main import cli


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


class TestConfigShow:
    """Tests for 'config show' command."""

    def test_show_default_yaml(self, runner):
        """Test showing configuration in YAML format (default)."""
        with patch("mycelium.cli.main.ConfigManager") as mock_manager:
            from mycelium.config.manager import MyceliumConfig

            mock_instance = Mock()
            mock_config = MyceliumConfig()
            mock_instance.load.return_value = mock_config
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "Configuration" in result.output
            assert "redis_url" in result.output

    def test_show_json_format(self, runner):
        """Test showing configuration in JSON format."""
        with patch("mycelium.cli.main.ConfigManager") as mock_manager:
            from mycelium.config.manager import MyceliumConfig

            mock_instance = Mock()
            mock_config = MyceliumConfig()
            mock_instance.load.return_value = mock_config
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "show", "--format", "json"])

            assert result.exit_code == 0
            assert "Configuration" in result.output
            assert "redis_url" in result.output

    def test_show_handles_error(self, runner):
        """Test error handling in show command."""
        with patch("mycelium.cli.main.ConfigManager") as mock_manager:
            mock_instance = Mock()
            mock_instance.load.side_effect = Exception("Test error")
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 1


class TestConfigValidate:
    """Tests for 'config validate' command."""

    def test_validate_success(self, runner):
        """Test successful validation."""
        with patch("mycelium.cli.main.ConfigManager") as mock_manager:
            from mycelium.config.manager import MyceliumConfig

            mock_instance = Mock()
            mock_config = MyceliumConfig()
            mock_instance.load.return_value = mock_config
            mock_instance.validate.return_value = []  # No errors
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "validate"])

            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_with_errors(self, runner):
        """Test validation with errors."""
        with patch("mycelium.cli.main.ConfigManager") as mock_manager:
            from mycelium.config.manager import MyceliumConfig

            mock_instance = Mock()
            mock_config = MyceliumConfig()
            mock_instance.load.return_value = mock_config
            mock_instance.validate.return_value = ["Invalid redis_url", "Invalid port"]
            mock_manager.return_value = mock_instance

            result = runner.invoke(cli, ["config", "validate"])

            assert result.exit_code == 1
            assert "error" in result.output.lower()
            assert "Invalid redis_url" in result.output


class TestConfigEdit:
    """Tests for 'config edit' command."""

    def test_edit_creates_file_if_missing(self, runner, tmp_path):
        """Test that edit command creates file if it doesn't exist."""
        config_file = tmp_path / ".env"

        with (
            patch("mycelium.cli.main.Path.cwd") as mock_cwd,
            patch("mycelium.cli.main.subprocess.run") as mock_run,
        ):
            mock_cwd.return_value = tmp_path
            mock_run.return_value = Mock(returncode=0)

            result = runner.invoke(cli, ["config", "edit"])

            # Should create the file
            assert config_file.exists()
            # Should have invoked the editor
            assert mock_run.called
            # Should succeed
            assert result.exit_code == 0

    def test_edit_global_flag(self, runner, tmp_path):
        """Test editing global config with --global flag."""
        with (
            patch("mycelium.cli.main.Path.home") as mock_home,
            patch("mycelium.cli.main.subprocess.run") as mock_run,
        ):
            mock_home.return_value = tmp_path
            mock_run.return_value = Mock(returncode=0)

            result = runner.invoke(cli, ["config", "edit", "--global"])

            # Should create global config
            global_config = tmp_path / ".config" / "mycelium" / ".env"
            assert global_config.exists()
            # Should succeed
            assert result.exit_code == 0

    def test_edit_opens_editor(self, runner, tmp_path):
        """Test that edit command opens editor."""
        with (
            patch("mycelium.cli.main.Path.cwd") as mock_cwd,
            patch("mycelium.cli.main.subprocess.run") as mock_run,
        ):
            mock_cwd.return_value = tmp_path
            mock_run.return_value = Mock(returncode=0)

            result = runner.invoke(cli, ["config", "edit"])

            # Should call subprocess.run to open editor
            assert mock_run.called
            # First arg should be command list [editor, file_path]
            call_args = mock_run.call_args[0][0]
            assert isinstance(call_args, list)
            assert len(call_args) == 2
            # Should succeed
            assert result.exit_code == 0


class TestConfigHelp:
    """Tests for config command help text."""

    def test_config_help(self, runner):
        """Test config command help."""
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "Manage Mycelium configuration" in result.output
        assert "show" in result.output
        assert "edit" in result.output
        assert "validate" in result.output

    def test_config_show_help(self, runner):
        """Test config show help."""
        result = runner.invoke(cli, ["config", "show", "--help"])

        assert result.exit_code == 0
        assert "Show current configuration" in result.output

    def test_config_edit_help(self, runner):
        """Test config edit help."""
        result = runner.invoke(cli, ["config", "edit", "--help"])

        assert result.exit_code == 0
        assert "Edit configuration" in result.output

    def test_config_validate_help(self, runner):
        """Test config validate help."""
        result = runner.invoke(cli, ["config", "validate", "--help"])

        assert result.exit_code == 0
        assert "Validate configuration" in result.output
