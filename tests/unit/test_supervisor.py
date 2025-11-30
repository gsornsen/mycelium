"""Unit tests for ProcessManager/supervisor functionality."""

import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mycelium.config.agent_loader import AgentConfig
from mycelium.errors import SupervisorError
from mycelium.logging import LogManager
from mycelium.logging.manager import LogEntry
from mycelium.registry.client import AgentInfo, RegistryClient
from mycelium.supervisor.manager import ProcessManager


class TestProcessManager:
    """Test ProcessManager class."""

    @pytest.fixture
    def mock_registry(self) -> MagicMock:
        """Create a mock RegistryClient."""
        registry = MagicMock(spec=RegistryClient)
        registry.register_agent.return_value = AgentInfo(
            name="test-agent",
            category="core",
            status="starting",
            pid=12345,
        )
        return registry

    @pytest.fixture
    def mock_log_manager(self) -> MagicMock:
        """Create a mock LogManager."""
        return MagicMock(spec=LogManager)

    @pytest.fixture
    def mock_agent_config(self) -> AgentConfig:
        """Create a mock AgentConfig."""
        return AgentConfig(
            name="test-agent",
            category="core",
            description="Test agent for unit testing",
            command=["echo", "test"],
        )

    @pytest.fixture
    def manager(self, mock_registry: MagicMock, mock_log_manager: MagicMock, tmp_path: Path) -> ProcessManager:
        """Create ProcessManager with mocked dependencies."""
        manager = ProcessManager(log_manager=mock_log_manager, plugin_dir=tmp_path)
        manager.registry = mock_registry
        return manager

    def test_init(self, tmp_path: Path) -> None:
        """Test ProcessManager initialization."""
        manager = ProcessManager(plugin_dir=tmp_path)

        assert isinstance(manager.processes, dict)
        assert isinstance(manager.configs, dict)
        assert isinstance(manager.restart_counts, dict)
        assert isinstance(manager.registry, RegistryClient)
        assert isinstance(manager.log_manager, LogManager)

    @patch("subprocess.Popen")
    def test_start_agent_success(
        self,
        mock_popen: MagicMock,
        manager: ProcessManager,
        mock_agent_config: AgentConfig,
    ) -> None:
        """Test successfully starting an agent."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock agent loader
        manager.agent_loader.load_agent = MagicMock(return_value=mock_agent_config)

        # Start agent
        pid = manager.start_agent("test-agent")

        # Verify
        assert pid == 12345
        assert "test-agent" in manager.processes
        assert manager.restart_counts["test-agent"] == 0

        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args.kwargs["stdout"] == subprocess.PIPE
        assert call_args.kwargs["stderr"] == subprocess.PIPE
        assert call_args.kwargs["start_new_session"] is True

        # Verify registry registration
        manager.registry.register_agent.assert_called_once_with(
            name="test-agent",
            category="core",
            pid=12345,
            description="Test agent for unit testing",
        )

    def test_start_agent_already_running(self, manager: ProcessManager) -> None:
        """Test starting an already-running agent raises error."""
        # Add a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        manager.processes["test-agent"] = mock_process

        # Try to start again
        with pytest.raises(SupervisorError, match="already running"):
            manager.start_agent("test-agent")

    @patch("subprocess.Popen")
    def test_start_agent_fallback_command(self, mock_popen: MagicMock, manager: ProcessManager) -> None:
        """Test starting agent with fallback command when no config found."""
        # Mock the process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock agent loader to return None (no config found)
        manager.agent_loader.load_agent = MagicMock(return_value=None)

        # Start agent
        pid = manager.start_agent("unknown-agent")

        # Verify fallback command was used
        assert pid == 12345
        call_args = mock_popen.call_args
        command = call_args.args[0]
        assert command == ["claude", "--agent", "unknown-agent"]

    @patch("subprocess.Popen")
    def test_start_agent_subprocess_failure(
        self,
        mock_popen: MagicMock,
        manager: ProcessManager,
        mock_agent_config: AgentConfig,
    ) -> None:
        """Test handling subprocess failure during agent start."""
        # Mock subprocess to raise exception
        mock_popen.side_effect = OSError("Command not found")

        # Mock agent loader
        manager.agent_loader.load_agent = MagicMock(return_value=mock_agent_config)

        # Try to start agent
        with pytest.raises(SupervisorError, match="Failed to start"):
            manager.start_agent("test-agent")

        # Verify error was logged
        manager.log_manager.write.assert_any_call(
            agent_name="test-agent",
            level="ERROR",
            message="Failed to start agent: Command not found",
            metadata={"error": "Command not found", "command": "echo test"},
        )

    def test_stop_agent_graceful(self, manager: ProcessManager) -> None:
        """Test gracefully stopping an agent."""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Running initially
        # After SIGTERM, simulate process exits
        mock_process.poll.side_effect = [None] + [0] * 15  # Running then exited
        manager.processes["test-agent"] = mock_process

        # Stop agent
        manager.stop_agent("test-agent", graceful=True)

        # Verify graceful shutdown
        mock_process.send_signal.assert_called_once_with(signal.SIGTERM)
        mock_process.wait.assert_called_once_with(timeout=5)

        # Verify cleanup
        assert "test-agent" not in manager.processes
        manager.registry.unregister_agent.assert_called_once_with("test-agent")

    def test_stop_agent_force(self, manager: ProcessManager) -> None:
        """Test force stopping an agent."""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        manager.processes["test-agent"] = mock_process

        # Force stop
        manager.stop_agent("test-agent", graceful=False)

        # Verify force kill
        mock_process.kill.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)

    def test_stop_agent_not_running(self, manager: ProcessManager) -> None:
        """Test stopping a non-running agent raises error."""
        # Agent not in processes dict and not in registry
        manager.registry.get_agent.return_value = None

        with pytest.raises(SupervisorError, match="not running"):
            manager.stop_agent("test-agent")

    @patch("os.kill")
    def test_stop_agent_cross_session(self, mock_kill: MagicMock, manager: ProcessManager) -> None:
        """Test stopping agent from different session using PID from registry."""
        # Agent not in memory but in registry
        agent_info = AgentInfo(
            name="test-agent",
            category="core",
            status="running",
            pid=12345,
        )
        manager.registry.get_agent.return_value = agent_info

        # Stop agent
        manager.stop_agent("test-agent", graceful=True)

        # Verify kill signals were sent
        assert mock_kill.call_count >= 1
        # First call should be signal 0 (check existence)
        first_call = mock_kill.call_args_list[0]
        assert first_call.args == (12345, 0)

        # Should have SIGTERM call
        term_calls = [c for c in mock_kill.call_args_list if c.args[1] == signal.SIGTERM]
        assert len(term_calls) == 1

    def test_stop_agent_graceful_timeout(self, manager: ProcessManager) -> None:
        """Test that graceful shutdown escalates to SIGKILL on timeout."""
        # Create a mock process that doesn't terminate gracefully
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Still running after SIGTERM
        manager.processes["test-agent"] = mock_process

        # Stop agent
        manager.stop_agent("test-agent", graceful=True)

        # Verify both SIGTERM and SIGKILL were called
        mock_process.send_signal.assert_called_with(signal.SIGTERM)
        mock_process.kill.assert_called_once()

    @patch("subprocess.Popen")
    def test_restart_agent(
        self,
        mock_popen: MagicMock,
        manager: ProcessManager,
        mock_agent_config: AgentConfig,
    ) -> None:
        """Test restarting an agent."""
        # Set up initial process
        old_process = MagicMock()
        old_process.pid = 12345
        old_process.poll.side_effect = [None] + [0] * 15  # Running then exited
        manager.processes["test-agent"] = old_process

        # Set up new process
        new_process = MagicMock()
        new_process.pid = 67890
        mock_popen.return_value = new_process

        # Mock agent loader
        manager.agent_loader.load_agent = MagicMock(return_value=mock_agent_config)

        # Restart
        new_pid = manager.restart_agent("test-agent")

        # Verify old process was stopped
        old_process.send_signal.assert_called_with(signal.SIGTERM)

        # Verify new process was started
        assert new_pid == 67890
        assert manager.processes["test-agent"] == new_process

    def test_health_check_agent_healthy(self, manager: ProcessManager) -> None:
        """Test health check for healthy agent."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        manager.processes["test-agent"] = mock_process

        is_healthy = manager.health_check_agent("test-agent")

        assert is_healthy is True

    def test_health_check_agent_exited(self, manager: ProcessManager) -> None:
        """Test health check for exited agent."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Exit code
        mock_process.returncode = 1
        manager.processes["test-agent"] = mock_process

        is_healthy = manager.health_check_agent("test-agent")

        assert is_healthy is False

        # Verify logging
        manager.log_manager.write.assert_called_with(
            agent_name="test-agent",
            level="WARNING",
            message="Agent process exited with code 1",
            metadata={"exit_code": "1"},
        )

    def test_health_check_agent_not_found(self, manager: ProcessManager) -> None:
        """Test health check for non-existent agent."""
        is_healthy = manager.health_check_agent("nonexistent")

        assert is_healthy is False

    def test_get_process_status_running(self, manager: ProcessManager) -> None:
        """Test getting status of running process."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        manager.processes["test-agent"] = mock_process
        manager.restart_counts["test-agent"] = 2

        status = manager.get_process_status("test-agent")

        assert status["status"] == "running"
        assert status["pid"] == 12345
        assert status["restart_count"] == 2

    def test_get_process_status_stopped(self, manager: ProcessManager) -> None:
        """Test getting status of stopped process."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        manager.processes["test-agent"] = mock_process

        status = manager.get_process_status("test-agent")

        assert status["status"] == "stopped"
        assert status["exit_code"] == 0

    def test_get_process_status_not_found(self, manager: ProcessManager) -> None:
        """Test getting status of non-existent process."""
        status = manager.get_process_status("nonexistent")

        assert status["status"] == "stopped"

    def test_list_running_agents(self, manager: ProcessManager) -> None:
        """Test listing running agents."""
        # Add some processes
        running_process = MagicMock()
        running_process.poll.return_value = None
        manager.processes["running-agent"] = running_process

        stopped_process = MagicMock()
        stopped_process.poll.return_value = 0
        stopped_process.returncode = 0
        manager.processes["stopped-agent"] = stopped_process

        running = manager.list_running_agents()

        assert "running-agent" in running
        assert "stopped-agent" not in running

    def test_get_logs(self, manager: ProcessManager) -> None:
        """Test getting agent logs."""
        # Mock log entries with proper datetime objects
        mock_entries = [
            LogEntry(
                timestamp=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                agent_name="test-agent",
                level="INFO",
                message="Test message 1",
            ),
            LogEntry(
                timestamp=datetime(2025, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
                agent_name="test-agent",
                level="ERROR",
                message="Test message 2",
            ),
        ]
        manager.log_manager.read.return_value = mock_entries

        logs = manager.get_logs("test-agent", lines=50)

        assert "Test message 1" in logs
        assert "Test message 2" in logs
        manager.log_manager.read.assert_called_once_with(agent_name="test-agent", lines=50)

    def test_get_logs_no_logs(self, manager: ProcessManager) -> None:
        """Test getting logs when none exist."""
        manager.log_manager.read.return_value = []

        logs = manager.get_logs("test-agent")

        assert "No logs found" in logs


class TestMonitorAllProcesses:
    """Test monitor_all_processes functionality."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> ProcessManager:
        """Create ProcessManager with mocked dependencies."""
        mock_log = MagicMock(spec=LogManager)
        mock_registry = MagicMock(spec=RegistryClient)
        manager = ProcessManager(log_manager=mock_log, plugin_dir=tmp_path)
        manager.registry = mock_registry
        return manager

    def test_monitor_all_running(self, manager: ProcessManager) -> None:
        """Test monitoring when all processes are running."""
        # Add running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        manager.processes["test-agent"] = mock_process

        statuses = manager.monitor_all_processes()

        assert statuses["test-agent"]["status"] == "running"
        # Should update heartbeat
        manager.registry.update_heartbeat.assert_called_with("test-agent")

    @patch("subprocess.Popen")
    def test_monitor_with_restart(self, mock_popen: MagicMock, manager: ProcessManager) -> None:
        """Test monitoring with auto-restart on failure."""
        # Add exited process
        old_process = MagicMock()
        old_process.poll.return_value = 1  # Exited
        old_process.returncode = 1
        old_process.pid = 12345
        manager.processes["test-agent"] = old_process

        # Set up config for restart
        from mycelium.supervisor.manager import ProcessConfig

        manager.configs["test-agent"] = ProcessConfig(
            name="test-agent",
            command=["echo", "test"],
            restart_on_failure=True,
            max_restarts=3,
        )
        manager.restart_counts["test-agent"] = 0

        # Mock agent loader
        mock_agent_config = AgentConfig(
            name="test-agent",
            category="core",
            description="Test",
            command=["echo", "test"],
        )
        manager.agent_loader.load_agent = MagicMock(return_value=mock_agent_config)

        # Mock new process
        new_process = MagicMock()
        new_process.pid = 67890
        mock_popen.return_value = new_process

        statuses = manager.monitor_all_processes()

        # Should have attempted restart
        assert manager.restart_counts.get("test-agent", 0) >= 1
        assert statuses["test-agent"]["status"] == "restarting"

    def test_monitor_max_restarts_exceeded(self, manager: ProcessManager) -> None:
        """Test monitoring when max restarts exceeded."""
        # Add exited process
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        manager.processes["test-agent"] = mock_process

        # Set up config with max restarts reached
        from mycelium.supervisor.manager import ProcessConfig

        manager.configs["test-agent"] = ProcessConfig(
            name="test-agent",
            command=["echo", "test"],
            restart_on_failure=True,
            max_restarts=3,
        )
        manager.restart_counts["test-agent"] = 3  # Already at max

        manager.monitor_all_processes()

        # Should not restart, should be removed from processes
        assert "test-agent" not in manager.processes
        assert manager.restart_counts["test-agent"] == 3
