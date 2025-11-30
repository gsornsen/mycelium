"""Unit tests for agent selector module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mycelium.cli.selector import (
    check_fzf_installed,
    create_preview_script,
    get_fzf_install_instructions,
    run_fzf_selector,
    sanitize_agent_name,
    select_agent_interactive,
)
from mycelium.errors import MyceliumError
from mycelium.registry.client import AgentInfo


class TestCheckFzfInstalled:
    """Test fzf installation check."""

    def test_fzf_installed(self) -> None:
        """Test when fzf is installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            assert check_fzf_installed() is True
            mock_run.assert_called_once()

    def test_fzf_not_installed(self) -> None:
        """Test when fzf is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert check_fzf_installed() is False

    def test_fzf_timeout(self) -> None:
        """Test when fzf check times out."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("fzf", 2)):
            assert check_fzf_installed() is False


class TestGetFzfInstallInstructions:
    """Test fzf installation instructions."""

    def test_instructions_contain_platforms(self) -> None:
        """Test that instructions mention all major platforms."""
        instructions = get_fzf_install_instructions()
        assert "macOS" in instructions
        assert "Linux" in instructions
        assert "Windows" in instructions
        assert "brew install fzf" in instructions
        assert "apt install fzf" in instructions


class TestSanitizeAgentName:
    """Test agent name sanitization."""

    def test_valid_name_alphanumeric(self) -> None:
        """Test valid alphanumeric name."""
        assert sanitize_agent_name("backend-developer") == "backend-developer"

    def test_valid_name_with_dots(self) -> None:
        """Test valid name with dots."""
        assert sanitize_agent_name("test.agent.v1") == "test.agent.v1"

    def test_valid_name_with_underscores(self) -> None:
        """Test valid name with underscores."""
        assert sanitize_agent_name("test_agent_123") == "test_agent_123"

    def test_invalid_name_with_spaces(self) -> None:
        """Test invalid name with spaces."""
        with pytest.raises(MyceliumError, match="Invalid agent name"):
            sanitize_agent_name("test agent")

    def test_invalid_name_with_semicolon(self) -> None:
        """Test invalid name with semicolon (shell injection)."""
        with pytest.raises(MyceliumError, match="Invalid agent name"):
            sanitize_agent_name("test;rm -rf /")

    def test_invalid_name_with_pipe(self) -> None:
        """Test invalid name with pipe (shell injection)."""
        with pytest.raises(MyceliumError, match="Invalid agent name"):
            sanitize_agent_name("test|cat /etc/passwd")

    def test_invalid_name_with_dollar(self) -> None:
        """Test invalid name with dollar sign (shell injection)."""
        with pytest.raises(MyceliumError, match="Invalid agent name"):
            sanitize_agent_name("test$(whoami)")


class TestCreatePreviewScript:
    """Test preview script creation."""

    def test_creates_script_file(self) -> None:
        """Test that preview script file is created."""
        agents_data = {
            "test-agent": AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
                description="Test agent for unit tests",
            )
        }

        script_path = create_preview_script(agents_data)

        try:
            assert script_path.exists()
            assert script_path.is_file()
            # Check script is executable
            assert script_path.stat().st_mode & 0o100  # Owner execute bit
        finally:
            # Cleanup
            if script_path.exists():
                script_path.unlink()
            json_file = Path("/tmp/mycelium_agents.json")
            if json_file.exists():
                json_file.unlink()

    def test_creates_json_data_file(self) -> None:
        """Test that JSON data file is created."""
        agents_data = {
            "test-agent": AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
                description="Test agent",
            )
        }

        script_path = create_preview_script(agents_data)
        json_file = Path("/tmp/mycelium_agents.json")

        try:
            assert json_file.exists()
            # Check JSON is valid
            import json

            data = json.loads(json_file.read_text())
            assert "test-agent" in data
            assert data["test-agent"]["name"] == "test-agent"
            assert data["test-agent"]["category"] == "testing"
        finally:
            # Cleanup
            if script_path.exists():
                script_path.unlink()
            if json_file.exists():
                json_file.unlink()


class TestRunFzfSelector:
    """Test fzf selector execution."""

    def test_no_agents_error(self) -> None:
        """Test error when no agents provided."""
        with pytest.raises(MyceliumError, match="No agents available"):
            run_fzf_selector([])

    def test_fzf_not_installed(self) -> None:
        """Test error when fzf is not installed."""
        agents = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=False):
            with pytest.raises(MyceliumError, match="fzf is not installed"):
                run_fzf_selector(agents)

    def test_successful_selection(self) -> None:
        """Test successful agent selection."""
        agents = [
            AgentInfo(
                name="backend-developer",
                category="backend",
                status="healthy",
                description="Backend specialist",
            ),
            AgentInfo(
                name="frontend-developer",
                category="frontend",
                status="healthy",
                description="Frontend specialist",
            ),
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.return_value = ("backend-developer\n", None)
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                result = run_fzf_selector(agents)

                assert result == "backend-developer"
                # Verify fzf was called
                assert mock_popen.called

    def test_cancelled_selection_ctrl_c(self) -> None:
        """Test cancelled selection with Ctrl+C."""
        agents = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.return_value = ("", None)
                mock_process.returncode = 130  # SIGINT
                mock_popen.return_value = mock_process

                result = run_fzf_selector(agents)

                assert result is None

    def test_cancelled_selection_esc(self) -> None:
        """Test cancelled selection with ESC."""
        agents = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.return_value = ("", None)
                mock_process.returncode = 1  # No match
                mock_popen.return_value = mock_process

                result = run_fzf_selector(agents)

                assert result is None

    def test_category_filter_in_prompt(self) -> None:
        """Test that category filter appears in prompt."""
        agents = [
            AgentInfo(
                name="backend-dev",
                category="backend",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.return_value = ("backend-dev\n", None)
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                run_fzf_selector(agents, category="backend")

                # Check that category is in the fzf command args
                call_args = mock_popen.call_args[0][0]
                # Find the prompt argument
                prompt_idx = call_args.index("--prompt")
                prompt_value = call_args[prompt_idx + 1]
                assert "backend" in prompt_value.lower()

    def test_invalid_agent_names_filtered(self) -> None:
        """Test that agents with invalid names are filtered out."""
        agents = [
            AgentInfo(
                name="valid-agent",
                category="testing",
                status="healthy",
            ),
            AgentInfo(
                name="invalid;agent",  # Contains semicolon
                category="testing",
                status="healthy",
            ),
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.return_value = ("valid-agent\n", None)
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                result = run_fzf_selector(agents)

                assert result == "valid-agent"

    def test_timeout_error(self) -> None:
        """Test timeout error handling."""
        agents = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.side_effect = subprocess.TimeoutExpired("fzf", 300)
                mock_popen.return_value = mock_process

                with pytest.raises(MyceliumError, match="timed out"):
                    run_fzf_selector(agents)

    def test_keyboard_interrupt(self) -> None:
        """Test KeyboardInterrupt handling."""
        agents = [
            AgentInfo(
                name="test-agent",
                category="testing",
                status="healthy",
            )
        ]

        with patch("mycelium.cli.selector.check_fzf_installed", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.communicate.side_effect = KeyboardInterrupt
                mock_popen.return_value = mock_process

                result = run_fzf_selector(agents)
                assert result is None


class TestSelectAgentInteractive:
    """Test interactive agent selection."""

    def test_successful_selection(self) -> None:
        """Test successful interactive selection."""
        mock_registry = MagicMock()
        test_agent = AgentInfo(
            name="test-agent",
            category="testing",
            status="healthy",
            description="Test description",
        )
        mock_registry.list_agents.return_value = [test_agent]
        mock_registry.get_agent.return_value = test_agent

        with patch("mycelium.cli.selector.run_fzf_selector", return_value="test-agent"):
            result = select_agent_interactive(mock_registry)

            assert result == test_agent
            mock_registry.list_agents.assert_called_once_with(category=None)
            mock_registry.get_agent.assert_called_once_with("test-agent")

    def test_cancelled_selection(self) -> None:
        """Test cancelled selection returns None."""
        mock_registry = MagicMock()
        test_agent = AgentInfo(
            name="test-agent",
            category="testing",
            status="healthy",
        )
        mock_registry.list_agents.return_value = [test_agent]

        with patch("mycelium.cli.selector.run_fzf_selector", return_value=None):
            result = select_agent_interactive(mock_registry)

            assert result is None

    def test_category_filter_passed(self) -> None:
        """Test that category filter is passed to registry."""
        mock_registry = MagicMock()
        test_agent = AgentInfo(
            name="backend-dev",
            category="backend",
            status="healthy",
        )
        mock_registry.list_agents.return_value = [test_agent]
        mock_registry.get_agent.return_value = test_agent

        with patch("mycelium.cli.selector.run_fzf_selector", return_value="backend-dev"):
            select_agent_interactive(mock_registry, category="backend")

            mock_registry.list_agents.assert_called_once_with(category="backend")

    def test_no_agents_error(self) -> None:
        """Test error when no agents are registered."""
        mock_registry = MagicMock()
        mock_registry.list_agents.return_value = []

        with pytest.raises(MyceliumError, match="No agents registered"):
            select_agent_interactive(mock_registry)

    def test_registry_error(self) -> None:
        """Test error when registry fails."""
        mock_registry = MagicMock()
        mock_registry.list_agents.side_effect = Exception("Redis connection failed")

        with pytest.raises(MyceliumError, match="Failed to list agents"):
            select_agent_interactive(mock_registry)

    def test_selected_agent_not_found(self) -> None:
        """Test error when selected agent is not found in registry."""
        mock_registry = MagicMock()
        test_agent = AgentInfo(
            name="test-agent",
            category="testing",
            status="healthy",
        )
        mock_registry.list_agents.return_value = [test_agent]
        mock_registry.get_agent.return_value = None  # Agent not found

        with patch("mycelium.cli.selector.run_fzf_selector", return_value="test-agent"):
            with pytest.raises(MyceliumError, match="not found in registry"):
                select_agent_interactive(mock_registry)
