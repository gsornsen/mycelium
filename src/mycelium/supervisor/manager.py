"""Process supervisor for managing agent lifecycle.

Handles process startup, monitoring, restart, and graceful shutdown.
Python-based supervisor (no systemd dependency) for baremetal-first approach.
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mycelium.errors import SupervisorError
from mycelium.logging import LogManager
from mycelium.registry.client import RegistryClient
from mycelium.config.agent_loader import AgentLoader, AgentConfig
from mycelium.mcp.isolation import EnvironmentIsolation, OutputSanitizer

# Default plugin directory for agent definitions
DEFAULT_PLUGIN_DIR = Path.home() / "git" / "mycelium" / "plugins" / "mycelium-core" / "agents"


@dataclass
class ProcessConfig:
    """Configuration for a managed process."""

    name: str
    command: list[str]
    cwd: Optional[Path] = None
    env: Optional[dict[str, str]] = None
    restart_on_failure: bool = True
    max_restarts: int = 3


class ProcessManager:
    """Manage agent processes.

    Features:
    - Process lifecycle (start, stop, restart)
    - Health monitoring
    - Graceful shutdown
    - Log streaming
    - Auto-restart on failure
    - Environment isolation
    - Output sanitization
    """

    def __init__(
        self,
        log_manager: Optional[LogManager] = None,
        plugin_dir: Optional[Path] = None,
    ) -> None:
        """Initialize process manager.

        Args:
            log_manager: Optional log manager instance (creates default if None)
            plugin_dir: Optional plugin directory for agent definitions
        """
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        self.configs: dict[str, ProcessConfig] = {}
        self.restart_counts: dict[str, int] = {}
        self.registry = RegistryClient()
        self.log_manager = log_manager or LogManager()
        self.agent_loader = AgentLoader(plugin_dir or DEFAULT_PLUGIN_DIR)
        self.isolation = EnvironmentIsolation()
        self.sanitizer = OutputSanitizer()

    def start_agent(
        self,
        name: str,
        config: Optional[Path] = None,
    ) -> int:
        """Start an agent process.

        Args:
            name: Agent name
            config: Optional configuration file path

        Returns:
            Process ID

        Raises:
            SupervisorError: If start fails
        """
        if name in self.processes:
            raise SupervisorError(
                f"Agent '{name}' is already running",
                suggestion=f"Stop it first: mycelium agent stop {name}",
                debug_info={"name": name, "pid": self.processes[name].pid}
            )

        # Load agent configuration from plugin directory
        agent_config = self.agent_loader.load_agent(name)

        # Log agent startup
        metadata: dict[str, str] = {}
        if config:
            metadata["config"] = str(config)
        if agent_config:
            metadata["command"] = " ".join(agent_config.command)

        self.log_manager.write(
            agent_name=name,
            level="INFO",
            message=f"Starting agent '{name}'",
            metadata=metadata if metadata else None,
        )

        # Build command from agent config or use default
        if agent_config:
            command = agent_config.command
            category = agent_config.category
            workdir = agent_config.workdir or Path.cwd()
        else:
            # Fallback for agents without .md definition
            command = ["claude", "--agent", name]
            category = "unknown"
            workdir = Path.cwd()

        try:
            # Create isolated environment
            clean_env = self.isolation.filter_environment(os.environ.copy())

            # Start process with isolated environment
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                env=clean_env,  # Use filtered environment
                start_new_session=True,
            )

            self.processes[name] = process
            self.restart_counts[name] = 0

            # Register in registry with actual category
            self.registry.register_agent(
                name=name,
                category=category,
                pid=process.pid,
                description=agent_config.description if agent_config else None,
            )

            # Log successful start
            self.log_manager.write(
                agent_name=name,
                level="INFO",
                message=f"Agent started successfully with PID {process.pid}",
                metadata={
                    "pid": str(process.pid),
                    "command": " ".join(command),
                    "category": category,
                },
            )

            return process.pid

        except Exception as e:
            # Log failure
            self.log_manager.write(
                agent_name=name,
                level="ERROR",
                message=f"Failed to start agent: {str(e)}",
                metadata={"error": str(e), "command": " ".join(command)},
            )

            raise SupervisorError(
                f"Failed to start agent '{name}'",
                suggestion="Check agent configuration and system resources",
                docs_url="https://docs.mycelium.dev/troubleshooting/agent-start",
                debug_info={"name": name, "error": str(e), "command": " ".join(command)}
            )

    def stop_agent(self, name: str, graceful: bool = True) -> None:
        """Stop an agent process.

        Args:
            name: Agent name
            graceful: If True, send SIGTERM; if False, send SIGKILL

        Raises:
            SupervisorError: If stop fails
        """
        # First check in-memory processes (same session)
        process = self.processes.get(name)
        pid: Optional[int] = None

        # If not in memory, check registry for PID (cross-session support)
        if process is None:
            agent_info = self.registry.get_agent(name)
            if agent_info and agent_info.pid:
                pid = agent_info.pid
                # Verify the process is actually running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                except OSError:
                    # Process doesn't exist
                    # Clean up stale registry entry
                    self.registry.unregister_agent(name)
                    raise SupervisorError(
                        f"Agent '{name}' is not running",
                        suggestion="List running agents: mycelium agent list",
                        debug_info={"name": name}
                    )
            else:
                raise SupervisorError(
                    f"Agent '{name}' is not running",
                    suggestion="List running agents: mycelium agent list",
                    debug_info={"name": name}
                )
        else:
            pid = process.pid

        # Log stop request
        self.log_manager.write(
            agent_name=name,
            level="INFO",
            message=f"Stopping agent (graceful={graceful})",
            metadata={"pid": str(pid), "graceful": str(graceful)},
        )

        try:
            if process is not None:
                # We have the Popen object (same session)
                if graceful:
                    process.send_signal(signal.SIGTERM)
                    for _ in range(10):
                        if process.poll() is not None:
                            break
                        time.sleep(1)
                    if process.poll() is None:
                        self.log_manager.write(
                            agent_name=name,
                            level="WARNING",
                            message="Graceful shutdown timeout, forcing kill",
                        )
                        process.kill()
                else:
                    process.kill()
                process.wait(timeout=5)
            else:
                # Cross-session: we only have the PID, use os.kill
                try:
                    if graceful:
                        os.kill(pid, signal.SIGTERM)
                        # Wait up to 10 seconds for graceful shutdown
                        for _ in range(10):
                            time.sleep(1)
                            try:
                                os.kill(pid, 0)  # Check if still running
                            except OSError:
                                break  # Process exited
                        else:
                            # Still running after 10s, force kill
                            self.log_manager.write(
                                agent_name=name,
                                level="WARNING",
                                message="Graceful shutdown timeout, forcing kill",
                            )
                            os.kill(pid, signal.SIGKILL)
                    else:
                        os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass  # Process already exited

            # Unregister from registry
            self.registry.unregister_agent(name)

            # Log successful stop
            self.log_manager.write(
                agent_name=name,
                level="INFO",
                message="Agent stopped successfully",
            )

            # Clean up in-memory tracking if present
            if name in self.processes:
                del self.processes[name]
            if name in self.restart_counts:
                del self.restart_counts[name]

        except Exception as e:
            # Log failure
            self.log_manager.write(
                agent_name=name,
                level="ERROR",
                message=f"Failed to stop agent: {str(e)}",
                metadata={"error": str(e)},
            )

            raise SupervisorError(
                f"Failed to stop agent '{name}'",
                suggestion=f"Try force stop: mycelium agent stop {name} --force",
                docs_url="https://docs.mycelium.dev/troubleshooting/agent-stop",
                debug_info={"name": name, "pid": pid, "error": str(e)}
            )

    def restart_agent(self, name: str) -> int:
        """Restart an agent.

        Args:
            name: Agent name

        Returns:
            New process ID
        """
        self.log_manager.write(
            agent_name=name,
            level="INFO",
            message="Restarting agent",
        )

        self.stop_agent(name)
        return self.start_agent(name)

    def get_logs(self, name: str, lines: int = 50) -> str:
        """Get agent logs with sanitization.

        Args:
            name: Agent name
            lines: Number of lines to retrieve

        Returns:
            Sanitized log output
        """
        # Read log entries from log manager
        entries = self.log_manager.read(agent_name=name, lines=lines)

        if not entries:
            return f"No logs found for agent '{name}'\n"

        # Format and sanitize entries
        output_lines = []
        for entry in entries:
            formatted = entry.format(include_timestamp=True)
            sanitized = self.sanitizer.sanitize(formatted)
            output_lines.append(sanitized)

        return "\n".join(output_lines) + "\n"

    def stream_logs(self, name: str) -> None:
        """Stream agent logs (like tail -f).

        Args:
            name: Agent name
        """
        try:
            # Stream log entries from log manager
            for entry in self.log_manager.stream(agent_name=name, follow=True):
                # Print formatted and sanitized entry
                formatted = entry.format(include_timestamp=True)
                sanitized = self.sanitizer.sanitize(formatted)
                print(sanitized)
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            pass

    def health_check_agent(self, name: str) -> bool:
        """Check if agent is healthy.

        Args:
            name: Agent name

        Returns:
            True if healthy, False otherwise
        """
        if name not in self.processes:
            return False

        process = self.processes[name]

        # Check if process is still running
        if process.poll() is not None:
            # Process has exited, log it
            self.log_manager.write(
                agent_name=name,
                level="WARNING",
                message=f"Agent process exited with code {process.returncode}",
                metadata={"exit_code": str(process.returncode)},
            )
            return False

        # Additional health checks would go here
        # (e.g., HTTP health endpoint, heartbeat)

        return True

    def get_process_status(self, name: str) -> dict[str, str | int | None]:
        """Get process status information.

        Args:
            name: Agent name

        Returns:
            Status dictionary
        """
        if name not in self.processes:
            return {"status": "stopped"}

        process = self.processes[name]

        if process.poll() is not None:
            return {"status": "stopped", "exit_code": process.returncode}

        return {
            "status": "running",
            "pid": process.pid,
            "restart_count": self.restart_counts.get(name, 0),
        }

    def monitor_all_processes(self) -> dict[str, dict[str, str | int | None]]:
        """Monitor all managed processes and update registry status.

        Checks each process, handles restarts if needed, and syncs
        status with the agent registry.

        Returns:
            Dictionary of agent statuses
        """
        statuses: dict[str, dict[str, str | int | None]] = {}

        for name, process in list(self.processes.items()):
            status = self.get_process_status(name)
            statuses[name] = status

            # If process exited unexpectedly, handle restart
            if status.get("status") == "stopped":
                exit_code = status.get("exit_code")

                # Log the exit
                self.log_manager.write(
                    agent_name=name,
                    level="WARNING",
                    message=f"Process exited with code {exit_code}",
                    metadata={"exit_code": str(exit_code)},
                )

                # Check if we should restart
                config = self.configs.get(name)
                restart_count = self.restart_counts.get(name, 0)

                if config and config.restart_on_failure:
                    if restart_count < config.max_restarts:
                        self.log_manager.write(
                            agent_name=name,
                            level="INFO",
                            message=f"Restarting agent (attempt {restart_count + 1}/{config.max_restarts})",
                        )

                        # Clean up old process
                        del self.processes[name]

                        # Restart with incremented count
                        try:
                            self.start_agent(name)
                            self.restart_counts[name] = restart_count + 1
                            statuses[name] = {"status": "restarting"}
                        except Exception as e:
                            self.log_manager.write(
                                agent_name=name,
                                level="ERROR",
                                message=f"Restart failed: {str(e)}",
                            )
                    else:
                        self.log_manager.write(
                            agent_name=name,
                            level="ERROR",
                            message=f"Max restarts ({config.max_restarts}) exceeded, not restarting",
                        )
                        # Clean up from process list
                        del self.processes[name]

                # Update registry status
                try:
                    self.registry._redis_update_field(
                        f"mycelium:agents:{name}",
                        "status",
                        "stopped",
                    )
                except Exception:
                    pass  # Best effort update

            elif status.get("status") == "running":
                # Update heartbeat in registry
                try:
                    self.registry.update_heartbeat(name)
                    self.registry._redis_update_field(
                        f"mycelium:agents:{name}",
                        "status",
                        "healthy",
                    )
                except Exception:
                    pass  # Best effort update

        return statuses

    def list_running_agents(self) -> list[str]:
        """List all currently running agent names.

        Returns:
            List of running agent names
        """
        running = []
        for name in self.processes:
            status = self.get_process_status(name)
            if status.get("status") == "running":
                running.append(name)
        return running
