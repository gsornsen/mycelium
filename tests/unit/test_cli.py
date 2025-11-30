"""Unit tests for CLI commands."""

import pytest
from click.testing import CliRunner

from mycelium.cli.main import cli


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


def test_cli_help(cli_runner):
    """Test CLI help output."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Mycelium" in result.output
    assert "agent" in result.output


def test_agent_list_help(cli_runner):
    """Test agent list help."""
    result = cli_runner.invoke(cli, ["agent", "list", "--help"])
    assert result.exit_code == 0
    assert "List available agents" in result.output


def test_registry_status_help(cli_runner):
    """Test registry status help."""
    result = cli_runner.invoke(cli, ["registry", "status", "--help"])
    assert result.exit_code == 0
    assert "Check registry status" in result.output
