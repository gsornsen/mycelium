"""Integration tests for agent selector CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mycelium.cli.main import cli
from mycelium.registry.client import AgentInfo, RegistryClient


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


class TestAgentSelectCommand:
    """Test the 'mycelium agent select' command."""

    def test_select_help(self, cli_runner):
        """Test select command help output."""
        result = cli_runner.invoke(cli, ["agent", "select", "--help"])
        assert result.exit_code == 0
        assert "Fuzzy-search and select an agent" in result.output
        assert "fzf" in result.output
        assert "--category" in result.output

    def test_select_requires_fzf(self, cli_runner):
        """Test that select command checks for fzf."""
        # Create a mock registry that returns agents
        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=False):
                result = cli_runner.invoke(cli, ["agent", "select"], catch_exceptions=False)

                assert result.exit_code == 1
                # Check exception string representation
                assert result.exception is not None
                assert "fzf is not installed" in str(result.exception)

    def test_select_successful(self, cli_runner):
        """Test successful agent selection."""
        # Create agents for testing
        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
                description="Backend development specialist",
            ),
            AgentInfo(
                name="frontend-developer",
                category="frontend",
                status="healthy",
                description="Frontend development specialist",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents
        mock_registry.get_agent.return_value = test_agents[0]  # Return backend-developer

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "backend-developer\n"

                    result = cli_runner.invoke(cli, ["agent", "select"])

                    assert result.exit_code == 0
                    assert "Selected: backend-developer" in result.output
                    assert "Backend development specialist" in result.output

    def test_select_with_category(self, cli_runner):
        """Test agent selection with category filter."""
        test_agents = [
            AgentInfo(
                name="frontend-developer",
                category="frontend",
                status="healthy",
                description="Frontend development specialist",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents
        mock_registry.get_agent.return_value = test_agents[0]

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "frontend-developer\n"

                    result = cli_runner.invoke(cli, ["agent", "select", "--category", "frontend"])

                    assert result.exit_code == 0
                    assert "Selected: frontend-developer" in result.output

    def test_select_cancelled(self, cli_runner):
        """Test cancelled selection."""
        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 130  # Ctrl+C

                    result = cli_runner.invoke(cli, ["agent", "select"])

                    assert result.exit_code == 0
                    assert "Selection cancelled" in result.output

    def test_select_no_agents(self, cli_runner):
        """Test select with no agents registered."""
        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = []

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            result = cli_runner.invoke(cli, ["agent", "select"], catch_exceptions=False)

            assert result.exit_code == 1
            # Check exception since output is not captured
            assert result.exception is not None
            assert "No agents registered" in str(result.exception)

    def test_select_with_copy_flag(self, cli_runner):
        """Test select with --copy flag (without pyperclip installed)."""
        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents
        mock_registry.get_agent.return_value = test_agents[0]

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "backend-developer\n"

                    result = cli_runner.invoke(cli, ["agent", "select", "--copy"])

                    assert result.exit_code == 0
                    # Should show warning about pyperclip not being installed
                    # or success if it is installed
                    assert "Selected: backend-developer" in result.output

    def test_select_keyboard_interrupt(self, cli_runner):
        """Test handling of keyboard interrupt."""
        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run", side_effect=KeyboardInterrupt):
                    result = cli_runner.invoke(cli, ["agent", "select"])

                    assert result.exit_code == 0
                    assert "Selection cancelled" in result.output


class TestAgentSelectIntegration:
    """Integration tests for agent select with real components."""

    @pytest.mark.integration
    def test_select_creates_preview_script(self, cli_runner, tmp_path):
        """Test that preview script is created and cleaned up."""
        from pathlib import Path

        preview_script = Path("/tmp/mycelium_fzf_preview.sh")
        json_file = Path("/tmp/mycelium_agents.json")

        # Ensure files don't exist before test
        if preview_script.exists():
            preview_script.unlink()
        if json_file.exists():
            json_file.unlink()

        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
                description="Backend development specialist",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents
        mock_registry.get_agent.return_value = test_agents[0]

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    # Make fzf succeed and check that files exist during execution
                    def check_files(*args, **kwargs):
                        # Files should exist when fzf is running
                        assert preview_script.exists(), "Preview script should exist during fzf execution"
                        assert json_file.exists(), "JSON file should exist during fzf execution"

                        result = type("Result", (), {})()
                        result.returncode = 0
                        result.stdout = "backend-developer\n"
                        return result

                    mock_run.side_effect = check_files

                    result = cli_runner.invoke(cli, ["agent", "select"])

                    assert result.exit_code == 0

                    # Files should be cleaned up after execution
                    assert not preview_script.exists(), "Preview script should be cleaned up"
                    assert not json_file.exists(), "JSON file should be cleaned up"

    @pytest.mark.integration
    def test_select_sanitizes_agent_names(self, cli_runner):
        """Test that malicious agent names are filtered out."""
        malicious_agents = [
            AgentInfo(
                name="valid-agent",
                category="testing",
                status="healthy",
            ),
            AgentInfo(
                name="evil;rm -rf /",
                category="malicious",
                status="healthy",
            ),
            AgentInfo(
                name="also|bad",
                category="malicious",
                status="healthy",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = malicious_agents
        mock_registry.get_agent.return_value = malicious_agents[0]  # Return valid-agent

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "valid-agent\n"

                    result = cli_runner.invoke(cli, ["agent", "select"])

                    # Check that only valid agent was passed to fzf
                    assert mock_run.called
                    call_kwargs = mock_run.call_args[1]
                    input_text = call_kwargs["input"]

                    assert "valid-agent" in input_text
                    assert "evil;rm" not in input_text
                    assert "also|bad" not in input_text

    @pytest.mark.integration
    def test_select_shows_next_steps(self, cli_runner):
        """Test that select shows next steps after selection."""
        test_agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
                description="Backend development specialist",
            ),
        ]

        mock_registry = MagicMock(spec=RegistryClient)
        mock_registry.list_agents.return_value = test_agents
        mock_registry.get_agent.return_value = test_agents[0]

        with patch("mycelium.cli.main.RegistryClient", return_value=mock_registry):
            with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = "backend-developer\n"

                    result = cli_runner.invoke(cli, ["agent", "select"])

                    assert result.exit_code == 0
                    assert "Next steps:" in result.output
                    assert "mycelium agent start backend-developer" in result.output
