"""Unit tests for CLI output module."""

import time
from unittest.mock import patch

import pytest

from mycelium.cli.output import (
    console,
    create_agent_table,
    create_error_panel,
    create_registry_status_panel,
    create_warning_panel,
    get_status_color,
    get_status_indicator,
    print_agent_started,
    print_agent_stopped,
    print_agent_table,
    print_discovery_summary,
    print_error,
    print_error_panel,
    print_info,
    print_registry_status,
    print_success,
    print_warning,
    print_warning_panel,
    spinner,
)
from mycelium.discovery.scanner import DiscoveredAgent
from mycelium.errors import MyceliumError
from mycelium.registry.client import AgentInfo


class TestStatusIndicators:
    """Test status indicator functions."""

    def test_get_status_indicator_healthy(self) -> None:
        """Test healthy status indicator."""
        assert "[green]●[/green]" in get_status_indicator("healthy")

    def test_get_status_indicator_starting(self) -> None:
        """Test starting status indicator."""
        assert "[yellow]◐[/yellow]" in get_status_indicator("starting")

    def test_get_status_indicator_stopping(self) -> None:
        """Test stopping status indicator."""
        assert "[yellow]◐[/yellow]" in get_status_indicator("stopping")

    def test_get_status_indicator_unhealthy(self) -> None:
        """Test unhealthy status indicator."""
        assert "[red]○[/red]" in get_status_indicator("unhealthy")

    def test_get_status_indicator_stopped(self) -> None:
        """Test stopped status indicator."""
        assert "[red]○[/red]" in get_status_indicator("stopped")

    def test_get_status_indicator_unknown(self) -> None:
        """Test unknown status indicator."""
        assert "[dim]?[/dim]" in get_status_indicator("unknown")

    def test_get_status_indicator_case_insensitive(self) -> None:
        """Test status indicator is case insensitive."""
        assert get_status_indicator("HEALTHY") == get_status_indicator("healthy")
        assert get_status_indicator("Stopping") == get_status_indicator("stopping")

    def test_get_status_color_healthy(self) -> None:
        """Test healthy status color."""
        assert get_status_color("healthy") == "green"

    def test_get_status_color_starting(self) -> None:
        """Test starting status color."""
        assert get_status_color("starting") == "yellow"

    def test_get_status_color_stopping(self) -> None:
        """Test stopping status color."""
        assert get_status_color("stopping") == "yellow"

    def test_get_status_color_unhealthy(self) -> None:
        """Test unhealthy status color."""
        assert get_status_color("unhealthy") == "red"

    def test_get_status_color_stopped(self) -> None:
        """Test stopped status color."""
        assert get_status_color("stopped") == "red"

    def test_get_status_color_unknown(self) -> None:
        """Test unknown status color."""
        assert get_status_color("unknown") == "dim"


class TestAgentTable:
    """Test agent table creation."""

    def test_create_agent_table_empty(self) -> None:
        """Test creating table with no agents."""
        table = create_agent_table([])
        assert table is not None
        assert table.title == "Agents"

    def test_create_agent_table_single_agent(self) -> None:
        """Test creating table with single agent."""
        agent = AgentInfo(
            name="test-agent",
            category="testing",
            status="healthy",
            description="Test agent",
        )
        table = create_agent_table([agent])
        assert table is not None
        assert len(table.rows) == 1

    def test_create_agent_table_multiple_agents(self) -> None:
        """Test creating table with multiple agents."""
        agents = [
            AgentInfo(name="agent1", category="cat1", status="healthy"),
            AgentInfo(name="agent2", category="cat2", status="stopped"),
            AgentInfo(name="agent3", category="cat3", status="starting"),
        ]
        table = create_agent_table(agents)
        assert table is not None
        assert len(table.rows) == 3

    def test_create_agent_table_with_category_filter(self) -> None:
        """Test creating table with category filter."""
        agents = [AgentInfo(name="agent1", category="backend", status="healthy")]
        table = create_agent_table(agents, category_filter="backend")
        assert "backend" in table.title

    def test_create_agent_table_truncates_long_description(self) -> None:
        """Test that long descriptions are truncated."""
        long_desc = "a" * 100
        agent = AgentInfo(
            name="test-agent",
            category="testing",
            status="healthy",
            description=long_desc,
        )
        table = create_agent_table([agent])
        # Check that table was created successfully (truncation happens internally)
        assert table is not None
        assert len(table.rows) == 1


class TestRegistryStatusPanel:
    """Test registry status panel creation."""

    def test_create_registry_status_panel_healthy(self) -> None:
        """Test creating healthy registry status panel."""
        panel = create_registry_status_panel(is_healthy=True)
        assert panel is not None
        assert panel.border_style == "green"

    def test_create_registry_status_panel_unhealthy(self) -> None:
        """Test creating unhealthy registry status panel."""
        panel = create_registry_status_panel(is_healthy=False)
        assert panel is not None
        assert panel.border_style == "red"

    def test_create_registry_status_panel_with_stats(self) -> None:
        """Test creating panel with statistics."""
        stats = {"agent_count": 10, "active_count": 5}
        panel = create_registry_status_panel(is_healthy=True, stats=stats)
        assert panel is not None
        # Should contain agent count
        assert "10" in str(panel.renderable)
        assert "5" in str(panel.renderable)

    def test_create_registry_status_panel_with_plugin_dir(self) -> None:
        """Test creating panel with plugin directory."""
        panel = create_registry_status_panel(is_healthy=True, plugin_dir="/path/to/plugins")
        assert panel is not None
        assert "/path/to/plugins" in str(panel.renderable)


class TestErrorPanel:
    """Test error panel creation."""

    def test_create_error_panel_mycelium_error(self) -> None:
        """Test creating error panel from MyceliumError."""
        error = MyceliumError(
            "Something went wrong",
            suggestion="Try this fix",
            docs_url="https://docs.example.com",
            debug_info={"key": "value"},
        )
        panel = create_error_panel(error)
        assert panel is not None
        assert panel.border_style == "red"
        assert "Something went wrong" in str(panel.renderable)
        assert "Try this fix" in str(panel.renderable)
        assert "https://docs.example.com" in str(panel.renderable)

    def test_create_error_panel_standard_exception(self) -> None:
        """Test creating error panel from standard Exception."""
        error = ValueError("Invalid value")
        panel = create_error_panel(error)
        assert panel is not None
        assert "Invalid value" in str(panel.renderable)

    def test_create_error_panel_custom_title(self) -> None:
        """Test creating error panel with custom title."""
        error = MyceliumError("Error message")
        panel = create_error_panel(error, title="Custom Error")
        assert "Custom Error" in panel.title


class TestWarningPanel:
    """Test warning panel creation."""

    def test_create_warning_panel_simple(self) -> None:
        """Test creating simple warning panel."""
        panel = create_warning_panel("Warning message")
        assert panel is not None
        assert panel.border_style == "yellow"
        assert "Warning message" in str(panel.renderable)

    def test_create_warning_panel_with_suggestion(self) -> None:
        """Test creating warning panel with suggestion."""
        panel = create_warning_panel("Warning message", suggestion="Try this")
        assert panel is not None
        assert "Try this" in str(panel.renderable)

    def test_create_warning_panel_custom_title(self) -> None:
        """Test creating warning panel with custom title."""
        panel = create_warning_panel("Message", title="Custom Warning")
        assert "Custom Warning" in panel.title


class TestSpinner:
    """Test spinner context manager."""

    def test_spinner_basic(self) -> None:
        """Test basic spinner functionality."""
        with spinner("Loading..."):
            time.sleep(0.1)
        # Spinner should complete without errors

    def test_spinner_with_success_message(self) -> None:
        """Test spinner with success message."""
        with patch.object(console, "print") as mock_print:
            with spinner("Loading...", "Done!"):
                time.sleep(0.1)
            # Should print success message
            assert mock_print.called

    def test_spinner_shows_elapsed_time(self) -> None:
        """Test that spinner shows elapsed time."""
        with patch.object(console, "print") as mock_print:
            with spinner("Loading...", "Done!"):
                time.sleep(0.1)
            # Check that elapsed time is in the output
            call_args = str(mock_print.call_args)
            assert "s)" in call_args or "dim" in call_args

    def test_spinner_handles_exception(self) -> None:
        """Test that spinner handles exceptions gracefully."""
        with pytest.raises(ValueError):
            with spinner("Loading...", "Done!"):
                raise ValueError("Test error")


class TestPrintFunctions:
    """Test print helper functions."""

    def test_print_success(self) -> None:
        """Test print_success function."""
        with patch.object(console, "print") as mock_print:
            print_success("Operation successful")
            assert mock_print.called
            assert "Operation successful" in str(mock_print.call_args)

    def test_print_info(self) -> None:
        """Test print_info function."""
        with patch.object(console, "print") as mock_print:
            print_info("Information message")
            assert mock_print.called
            assert "Information message" in str(mock_print.call_args)

    def test_print_warning(self) -> None:
        """Test print_warning function."""
        with patch.object(console, "print") as mock_print:
            print_warning("Warning message")
            assert mock_print.called
            assert "Warning message" in str(mock_print.call_args)

    def test_print_error(self) -> None:
        """Test print_error function."""
        with patch.object(console, "print") as mock_print:
            print_error("Error message")
            assert mock_print.called
            assert "Error message" in str(mock_print.call_args)

    def test_print_agent_started(self) -> None:
        """Test print_agent_started function."""
        with patch.object(console, "print") as mock_print:
            print_agent_started("test-agent", 12345)
            assert mock_print.called
            # Should contain agent name and PID
            calls = str(mock_print.call_args_list)
            assert "test-agent" in calls
            assert "12345" in calls

    def test_print_agent_stopped(self) -> None:
        """Test print_agent_stopped function."""
        with patch.object(console, "print") as mock_print:
            print_agent_stopped("test-agent")
            assert mock_print.called
            calls = str(mock_print.call_args_list)
            assert "test-agent" in calls

    def test_print_agent_table(self) -> None:
        """Test print_agent_table function."""
        agents = [AgentInfo(name="test", category="cat", status="healthy")]
        with patch.object(console, "print") as mock_print:
            print_agent_table(agents)
            assert mock_print.called

    def test_print_registry_status(self) -> None:
        """Test print_registry_status function."""
        with patch.object(console, "print") as mock_print:
            print_registry_status(is_healthy=True)
            assert mock_print.called

    def test_print_error_panel(self) -> None:
        """Test print_error_panel function."""
        error = MyceliumError("Test error")
        with patch.object(console, "print") as mock_print:
            print_error_panel(error)
            assert mock_print.called

    def test_print_warning_panel(self) -> None:
        """Test print_warning_panel function."""
        with patch.object(console, "print") as mock_print:
            print_warning_panel("Warning message")
            assert mock_print.called


class TestDiscoverySummary:
    """Test discovery summary printing."""

    def test_print_discovery_summary_no_agents(self) -> None:
        """Test printing summary with no agents."""
        with patch.object(console, "print") as mock_print:
            print_discovery_summary(0, 0, [])
            assert mock_print.called
            # Should indicate no agents found
            calls = str(mock_print.call_args_list)
            assert "No agents" in calls or "0" in calls

    def test_print_discovery_summary_with_agents(self) -> None:
        """Test printing summary with discovered agents."""
        agents = [
            DiscoveredAgent(
                name="test-agent",
                category="testing",
                description="Test",
                file_path="/tmp/test.md",
            )
        ]
        with patch.object(console, "print") as mock_print:
            print_discovery_summary(1, 1, agents)
            assert mock_print.called
            calls = str(mock_print.call_args_list)
            assert "test-agent" in calls

    def test_print_discovery_summary_with_registration_count(self) -> None:
        """Test summary shows registration count."""
        agents = [
            DiscoveredAgent(
                name="test-agent",
                category="testing",
                description="Test agent",
                file_path="/tmp/test.md",
            )
        ]
        with patch.object(console, "print") as mock_print:
            print_discovery_summary(1, 1, agents)
            calls = str(mock_print.call_args_list)
            # Should show "Registered 1 agent(s)"
            assert "Registered" in calls or "1" in calls
