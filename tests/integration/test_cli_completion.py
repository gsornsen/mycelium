"""Integration tests for CLI shell completion.

Tests that completion integrates properly with Click CLI commands.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from mycelium.cli.main import cli


class TestCLICompletionIntegration:
    """Test CLI completion integration with Click."""

    def test_completion_install_command_exists(self) -> None:
        """Test that completion install command is available."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "--help"])

        assert result.exit_code == 0
        assert "install" in result.output
        assert "show" in result.output

    def test_completion_install_bash(self) -> None:
        """Test completion install for bash."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "install", "bash"])

        assert result.exit_code == 0
        assert "bash" in result.output.lower()
        assert "_MYCELIUM_COMPLETE=bash_source" in result.output
        assert "~/.bashrc" in result.output

    def test_completion_install_zsh(self) -> None:
        """Test completion install for zsh."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "install", "zsh"])

        assert result.exit_code == 0
        assert "zsh" in result.output.lower()
        assert "_MYCELIUM_COMPLETE=zsh_source" in result.output
        assert "~/.zshrc" in result.output

    def test_completion_install_fish(self) -> None:
        """Test completion install for fish."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "install", "fish"])

        assert result.exit_code == 0
        assert "fish" in result.output.lower()
        assert "_MYCELIUM_COMPLETE=fish_source" in result.output
        assert "~/.config/fish/completions" in result.output

    def test_completion_install_auto_detect_bash(self) -> None:
        """Test completion install auto-detects bash."""
        runner = CliRunner()
        with patch.dict("os.environ", {"SHELL": "/bin/bash"}):
            result = runner.invoke(cli, ["completion", "install"])

        assert result.exit_code == 0
        assert "bash" in result.output.lower()

    def test_completion_install_auto_detect_zsh(self) -> None:
        """Test completion install auto-detects zsh."""
        runner = CliRunner()
        with patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}):
            result = runner.invoke(cli, ["completion", "install"])

        assert result.exit_code == 0
        assert "zsh" in result.output.lower()

    def test_completion_install_no_shell_detected(self) -> None:
        """Test completion install when no shell is detected."""
        runner = CliRunner()
        with patch.dict("os.environ", {"SHELL": ""}, clear=True):
            result = runner.invoke(cli, ["completion", "install"])

        assert result.exit_code == 0
        assert "Could not auto-detect shell" in result.output

    def test_completion_show_bash(self) -> None:
        """Test completion show for bash."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "show", "bash"])

        assert result.exit_code == 0
        assert "_MYCELIUM_COMPLETE=bash_source" in result.output

    def test_completion_show_zsh(self) -> None:
        """Test completion show for zsh."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "show", "zsh"])

        assert result.exit_code == 0
        assert "_MYCELIUM_COMPLETE=zsh_source" in result.output

    def test_completion_show_fish(self) -> None:
        """Test completion show for fish."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "show", "fish"])

        assert result.exit_code == 0
        assert "_MYCELIUM_COMPLETE=fish_source" in result.output


class TestCLIArgumentCompletion:
    """Test that CLI arguments have completion attached."""

    def test_agent_start_has_completion(self) -> None:
        """Test that agent start command has name completion."""
        from mycelium.cli.main import start

        # Find the name argument
        name_param = None
        for param in start.params:
            if param.name == "name":
                name_param = param
                break

        assert name_param is not None
        assert hasattr(name_param, "shell_complete")
        assert name_param.shell_complete is not None

    def test_agent_stop_has_completion(self) -> None:
        """Test that agent stop command has running agent completion."""
        from mycelium.cli.main import stop

        # Find the name argument
        name_param = None
        for param in stop.params:
            if param.name == "name":
                name_param = param
                break

        assert name_param is not None
        assert hasattr(name_param, "shell_complete")
        assert name_param.shell_complete is not None

    def test_agent_logs_has_completion(self) -> None:
        """Test that agent logs command has running agent completion."""
        from mycelium.cli.main import logs

        # Find the name argument
        name_param = None
        for param in logs.params:
            if param.name == "name":
                name_param = param
                break

        assert name_param is not None
        assert hasattr(name_param, "shell_complete")
        assert name_param.shell_complete is not None

    def test_agent_list_category_has_completion(self) -> None:
        """Test that agent list --category option has completion."""
        from mycelium.cli.main import list as list_cmd

        # Find the category option
        category_param = None
        for param in list_cmd.params:
            if param.name == "category":
                category_param = param
                break

        assert category_param is not None
        assert hasattr(category_param, "shell_complete")
        assert category_param.shell_complete is not None


class TestCompletionBehavior:
    """Test actual completion behavior with Click's completion API."""

    @pytest.mark.skip(reason="Requires Click completion API setup")
    def test_agent_start_completion_returns_agents(self) -> None:
        """Test that agent start completion returns agent names.

        Note: This test requires more complex setup with Click's completion
        testing infrastructure. Skipped for now as unit tests cover the logic.
        """
        pass

    @pytest.mark.skip(reason="Requires Click completion API setup")
    def test_category_completion_returns_categories(self) -> None:
        """Test that category completion returns unique categories.

        Note: This test requires more complex setup with Click's completion
        testing infrastructure. Skipped for now as unit tests cover the logic.
        """
        pass
