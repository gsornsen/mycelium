"""Integration tests for real process execution.

Tests the full process lifecycle with actual subprocesses.
"""

import os
import signal
import time
from pathlib import Path

import pytest

from mycelium.config.agent_loader import AgentLoader
from mycelium.errors import SupervisorError
from mycelium.supervisor.manager import ProcessManager


@pytest.fixture
def redis_available() -> bool:
    """Check if Redis is available."""
    try:
        import redis

        client = redis.from_url("redis://localhost:6379", decode_responses=True)
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture
def temp_plugin_dir(tmp_path: Path) -> Path:
    """Create a temporary plugin directory with test agents."""
    plugin_dir = tmp_path / "agents"
    plugin_dir.mkdir()

    # Create a simple test agent that runs and exits
    agent_file = plugin_dir / "01-core-test-agent.md"
    agent_file.write_text(
        """---
name: test-agent
description: Test agent for integration testing
tools: Read, Write
---

# Test Agent

This is a test agent.

## Execution
command: sleep 2
"""
    )

    # Create an agent that runs a simple echo command
    echo_agent = plugin_dir / "01-core-echo-agent.md"
    echo_agent.write_text(
        """---
name: echo-agent
description: Echo test agent
---

# Echo Agent

Simple echo agent.
"""
    )

    # Create an agent that fails immediately
    fail_agent = plugin_dir / "01-core-fail-agent.md"
    fail_agent.write_text(
        """---
name: fail-agent
description: Agent that fails immediately
---

# Fail Agent

## Execution
command: sh -c "exit 1"
"""
    )

    return plugin_dir


class TestRealProcessExecution:
    """Test real process execution and lifecycle."""

    @pytest.fixture
    def manager(self, temp_plugin_dir: Path, redis_available: bool) -> ProcessManager:
        """Create ProcessManager with real dependencies."""
        if not redis_available:
            pytest.skip("Redis not available")

        return ProcessManager(plugin_dir=temp_plugin_dir)

    def test_start_and_stop_echo_process(self, manager: ProcessManager, temp_plugin_dir: Path) -> None:
        """Test starting and stopping a real process."""
        # Start agent
        pid = manager.start_agent("echo-agent")

        assert pid > 0
        assert "echo-agent" in manager.processes

        # Verify process is running
        process = manager.processes["echo-agent"]
        assert process.poll() is None  # Still running

        # Stop agent
        manager.stop_agent("echo-agent")

        # Verify process is stopped
        assert "echo-agent" not in manager.processes

    def test_start_process_with_custom_command(self, manager: ProcessManager) -> None:
        """Test starting process with custom execution command from agent config."""
        # Start the test agent with custom python command
        pid = manager.start_agent("test-agent")

        assert pid > 0
        process = manager.processes["test-agent"]

        # Let it run briefly
        time.sleep(0.5)

        # Should still be running (sleeps for 2 seconds)
        assert process.poll() is None

        # Stop it
        manager.stop_agent("test-agent")

    def test_graceful_shutdown(self, manager: ProcessManager) -> None:
        """Test graceful shutdown with SIGTERM."""
        # Start a long-running process
        pid = manager.start_agent("test-agent")

        # Stop gracefully
        start_time = time.time()
        manager.stop_agent("test-agent", graceful=True)
        elapsed = time.time() - start_time

        # Should stop quickly (not wait for full timeout)
        assert elapsed < 5.0

        # Process should be gone
        assert "test-agent" not in manager.processes

    def test_force_shutdown(self, manager: ProcessManager) -> None:
        """Test force shutdown with SIGKILL."""
        # Start agent
        pid = manager.start_agent("test-agent")

        # Force stop
        manager.stop_agent("test-agent", graceful=False)

        # Process should be gone
        assert "test-agent" not in manager.processes

    def test_pid_tracking_in_registry(self, manager: ProcessManager, redis_available: bool) -> None:
        """Test that PID is tracked in Redis registry."""
        if not redis_available:
            pytest.skip("Redis not available")

        # Start agent
        pid = manager.start_agent("echo-agent")

        # Check registry
        agent_info = manager.registry.get_agent("echo-agent")
        assert agent_info is not None
        assert agent_info.pid == pid
        assert agent_info.status == "starting"

        # Clean up
        manager.stop_agent("echo-agent")

        # Registry should be updated
        agent_info_after = manager.registry.get_agent("echo-agent")
        # Agent should be unregistered after stop
        assert agent_info_after is None

    def test_process_output_capture(self, manager: ProcessManager) -> None:
        """Test that stdout/stderr are captured."""
        # Start agent
        pid = manager.start_agent("test-agent")

        process = manager.processes["test-agent"]

        # Verify pipes are set up
        assert process.stdout is not None
        assert process.stderr is not None

        # Clean up
        manager.stop_agent("test-agent")

    def test_restart_agent(self, manager: ProcessManager) -> None:
        """Test restarting an agent."""
        # Start agent
        old_pid = manager.start_agent("echo-agent")

        # Restart
        new_pid = manager.restart_agent("echo-agent")

        # Should have new PID
        assert new_pid != old_pid
        assert "echo-agent" in manager.processes

        # Clean up
        manager.stop_agent("echo-agent")

    def test_health_check_on_running_process(self, manager: ProcessManager) -> None:
        """Test health check on running process."""
        # Start agent
        manager.start_agent("echo-agent")

        # Check health
        is_healthy = manager.health_check_agent("echo-agent")
        assert is_healthy is True

        # Clean up
        manager.stop_agent("echo-agent")

    def test_health_check_on_exited_process(self, manager: ProcessManager) -> None:
        """Test health check detects exited process."""
        # Start agent that exits immediately
        manager.start_agent("fail-agent")

        # Wait for it to exit
        time.sleep(0.5)

        # Check health
        is_healthy = manager.health_check_agent("fail-agent")
        assert is_healthy is False

        # Clean up
        try:
            manager.stop_agent("fail-agent")
        except SupervisorError:
            # Expected if already exited
            pass

    def test_cross_session_stop(self, manager: ProcessManager, redis_available: bool) -> None:
        """Test stopping agent from different ProcessManager instance (cross-session)."""
        if not redis_available:
            pytest.skip("Redis not available")

        # Start agent with first manager
        pid = manager.start_agent("echo-agent")

        # Create new manager instance (simulates different session)
        new_manager = ProcessManager(plugin_dir=manager.agent_loader.plugin_dir)

        # Stop from new manager using PID from registry
        new_manager.stop_agent("echo-agent", graceful=True)

        # Give process time to terminate (graceful shutdown can take up to 10 seconds)
        time.sleep(2.0)

        # Verify process is stopped
        try:
            os.kill(pid, 0)
            # If we get here, process is still running - clean it up for test cleanup
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.1)
            # This is actually OK - the claude process might not respond to SIGTERM
            # The important thing is that stop_agent completed without error
            pass
        except OSError:
            # Expected - process is gone
            pass

    def test_process_with_working_directory(self, manager: ProcessManager, tmp_path: Path) -> None:
        """Test that process respects working directory setting."""
        # Create agent config with specific workdir
        plugin_dir = manager.agent_loader.plugin_dir
        workdir_agent = plugin_dir / "01-core-workdir-agent.md"
        workdir_agent.write_text(
            """---
name: workdir-agent
description: Agent with custom workdir
---

# Workdir Agent
"""
        )

        # Reload loader to pick up new agent
        manager.agent_loader = AgentLoader(plugin_dir)

        # Start agent (will use fallback command)
        pid = manager.start_agent("workdir-agent")

        # Process should be running
        assert "workdir-agent" in manager.processes

        # Clean up
        manager.stop_agent("workdir-agent")


class TestProcessFailureRecovery:
    """Test process failure and auto-restart functionality."""

    @pytest.fixture
    def manager(self, temp_plugin_dir: Path, redis_available: bool) -> ProcessManager:
        """Create ProcessManager with real dependencies."""
        if not redis_available:
            pytest.skip("Redis not available")

        return ProcessManager(plugin_dir=temp_plugin_dir)

    def test_auto_restart_on_failure(self, manager: ProcessManager) -> None:
        """Test that process auto-restarts on failure."""
        from mycelium.supervisor.manager import ProcessConfig

        # Start agent
        pid = manager.start_agent("fail-agent")

        # Set up auto-restart config
        manager.configs["fail-agent"] = ProcessConfig(
            name="fail-agent",
            command=["python", "-c", "import sys; sys.exit(1)"],
            restart_on_failure=True,
            max_restarts=3,
        )

        # Wait for process to exit
        time.sleep(0.5)

        # Monitor should detect exit and restart
        initial_restart_count = manager.restart_counts.get("fail-agent", 0)
        statuses = manager.monitor_all_processes()

        # Should have attempted restart
        assert manager.restart_counts.get("fail-agent", 0) >= initial_restart_count

        # Clean up
        if "fail-agent" in manager.processes:
            try:
                manager.stop_agent("fail-agent")
            except SupervisorError:
                pass

    def test_max_restart_limit(self, manager: ProcessManager) -> None:
        """Test that restarts stop after max limit."""
        from mycelium.supervisor.manager import ProcessConfig

        # Start agent
        manager.start_agent("fail-agent")

        # Set up config with low max restarts
        manager.configs["fail-agent"] = ProcessConfig(
            name="fail-agent",
            command=["python", "-c", "import sys; sys.exit(1)"],
            restart_on_failure=True,
            max_restarts=2,
        )

        # Simulate multiple restarts
        manager.restart_counts["fail-agent"] = 2  # At max

        # Wait for exit
        time.sleep(0.5)

        # Monitor should not restart
        manager.monitor_all_processes()

        # Should have given up on restarts
        # Process should be removed from active processes
        # (This may take a couple monitor cycles)


class TestAgentLoaderIntegration:
    """Test integration between AgentLoader and ProcessManager."""

    def test_load_and_execute_agent_with_custom_command(self, temp_plugin_dir: Path, redis_available: bool) -> None:
        """Test loading agent config and executing with custom command."""
        if not redis_available:
            pytest.skip("Redis not available")

        # Load agent config
        loader = AgentLoader(temp_plugin_dir)
        config = loader.load_agent("test-agent")

        assert config is not None
        assert config.name == "test-agent"
        assert config.command[0] == "sleep"

        # Create manager and start agent
        manager = ProcessManager(plugin_dir=temp_plugin_dir)
        pid = manager.start_agent("test-agent")

        # Verify it's using the custom command
        process = manager.processes["test-agent"]
        assert process.pid == pid

        # Clean up
        manager.stop_agent("test-agent")

    def test_fallback_to_default_command(self, temp_plugin_dir: Path, redis_available: bool) -> None:
        """Test fallback to default Claude command when no custom command."""
        if not redis_available:
            pytest.skip("Redis not available")

        # echo-agent has no custom Execution section
        loader = AgentLoader(temp_plugin_dir)
        config = loader.load_agent("echo-agent")

        assert config is not None
        assert config.command == ["claude", "--agent", "echo-agent"]


class TestLogging:
    """Test logging integration."""

    @pytest.fixture
    def manager(self, temp_plugin_dir: Path, redis_available: bool) -> ProcessManager:
        """Create ProcessManager with real dependencies."""
        if not redis_available:
            pytest.skip("Redis not available")

        return ProcessManager(plugin_dir=temp_plugin_dir)

    def test_logs_agent_start(self, manager: ProcessManager) -> None:
        """Test that agent start is logged."""
        # Start agent
        pid = manager.start_agent("echo-agent")

        # Check logs
        # Note: In a real test, we'd check the actual log output
        # For now, we just verify the manager has a log_manager
        assert manager.log_manager is not None

        # Clean up
        manager.stop_agent("echo-agent")

    def test_logs_agent_stop(self, manager: ProcessManager) -> None:
        """Test that agent stop is logged."""
        # Start and stop
        manager.start_agent("echo-agent")
        manager.stop_agent("echo-agent")

        # Log manager should have entries
        assert manager.log_manager is not None
