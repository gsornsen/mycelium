"""Log file management.

Manages JSONL log files for agents with rotation support, compression,
and thread-safe writes with file locking.
"""

import gzip
import json
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

# File locking using fcntl on Unix or msvcrt on Windows
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False


@dataclass
class LogEntry:
    """Structured log entry.

    Represents a single log line in JSONL format with timestamp,
    level, message, agent name, and optional metadata.
    """

    timestamp: datetime
    level: str
    message: str
    agent_name: str
    metadata: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "agent_name": self.agent_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create LogEntry from dictionary."""
        metadata = data.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None

        return cls(
            timestamp=datetime.fromisoformat(str(data["timestamp"])),
            level=str(data["level"]),
            message=str(data["message"]),
            agent_name=str(data["agent_name"]),
            metadata=metadata,
        )

    def format(self, include_timestamp: bool = True) -> str:
        """Format log entry for display.

        Args:
            include_timestamp: Whether to include timestamp in output

        Returns:
            Formatted log string
        """
        parts = []

        if include_timestamp:
            ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{ts}]")

        # Color code by level
        level_color = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
        }.get(self.level, "")
        reset = "\033[0m" if level_color else ""

        parts.append(f"{level_color}{self.level:7}{reset}")
        parts.append(f"[{self.agent_name}]")
        parts.append(self.message)

        if self.metadata:
            parts.append(f"| {self.metadata}")

        return " ".join(parts)


class LogManager:
    """Manage agent log files with rotation and compression.

    Features:
    - Thread-safe writes with file locking
    - JSONL format for structured logs
    - Automatic rotation based on file size
    - Gzip compression of rotated logs
    - Configurable retention of old logs
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        max_size_mb: int = 10,
        max_rotations: int = 5,
    ) -> None:
        """Initialize log manager.

        Args:
            log_dir: Directory for log files (default: ~/.local/share/mycelium/logs)
            max_size_mb: Maximum size of log file before rotation (MB)
            max_rotations: Number of rotated log files to keep
        """
        if log_dir is None:
            log_dir = Path.home() / ".local" / "share" / "mycelium" / "logs"

        self.log_dir = log_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_rotations = max_rotations

        # Thread locks for each agent (for thread-safe writes)
        self._locks: dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock(self, agent_name: str) -> threading.Lock:
        """Get or create lock for agent.

        Args:
            agent_name: Agent name

        Returns:
            Thread lock for agent
        """
        with self._locks_lock:
            if agent_name not in self._locks:
                self._locks[agent_name] = threading.Lock()
            return self._locks[agent_name]

    def get_log_file(self, agent_name: str) -> Path:
        """Get log file path for agent.

        Args:
            agent_name: Agent name

        Returns:
            Path to log file
        """
        # Create agent-specific directory
        agent_dir = self.log_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir / f"{agent_name}.log"

    def write(
        self,
        agent_name: str,
        level: str,
        message: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Write log entry in JSONL format (thread-safe).

        Args:
            agent_name: Agent name
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            metadata: Optional metadata dictionary
        """
        # Get lock for this agent
        lock = self._get_lock(agent_name)

        with lock:
            # Check if rotation needed before writing
            self._rotate_if_needed(agent_name)

            log_file = self.get_log_file(agent_name)
            timestamp = datetime.now(timezone.utc)

            # Create log entry
            entry = LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                agent_name=agent_name,
                metadata=metadata,
            )

            # Write to file with platform-specific locking
            with log_file.open("a", encoding="utf-8") as f:
                # Acquire file lock
                self._lock_file(f)
                try:
                    f.write(json.dumps(entry.to_dict()) + "\n")
                    f.flush()
                finally:
                    # Release file lock
                    self._unlock_file(f)

    def _lock_file(self, file_handle: TextIO) -> None:
        """Lock file for exclusive write access (platform-specific).

        Args:
            file_handle: Open file handle
        """
        if HAS_FCNTL:
            # Unix/Linux
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        elif HAS_MSVCRT:
            # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
        # If neither available, proceed without locking (not ideal but functional)

    def _unlock_file(self, file_handle: TextIO) -> None:
        """Unlock file (platform-specific).

        Args:
            file_handle: Open file handle
        """
        if HAS_FCNTL:
            # Unix/Linux
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        elif HAS_MSVCRT:
            # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]

    def read(self, agent_name: str, lines: int = 50) -> list[LogEntry]:
        """Read last N log entries from log file.

        Args:
            agent_name: Agent name
            lines: Number of lines to return

        Returns:
            List of log entries
        """
        log_file = self.get_log_file(agent_name)

        if not log_file.exists():
            return []

        entries: list[LogEntry] = []

        with log_file.open("r", encoding="utf-8") as f:
            # Read all lines and parse
            all_lines = f.readlines()

            # Take last N lines
            for line in all_lines[-lines:]:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    entries.append(LogEntry.from_dict(data))
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Skip malformed lines
                    continue

        return entries

    def stream(self, agent_name: str, follow: bool = True) -> Iterator[LogEntry]:
        """Stream log entries (like tail -f).

        Args:
            agent_name: Agent name
            follow: If True, continuously follow new entries

        Yields:
            Log entries as they are written
        """
        log_file = self.get_log_file(agent_name)

        # Ensure file exists
        if not log_file.exists():
            log_file.touch()

        with log_file.open("r", encoding="utf-8") as f:
            # First, read existing content
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield LogEntry.from_dict(data)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

            if not follow:
                return

            # Then, follow new content
            while True:
                line = f.readline()

                if line:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            yield LogEntry.from_dict(data)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
                else:
                    # No new data, sleep briefly
                    time.sleep(0.1)

    def rotate(self, agent_name: str) -> None:
        """Rotate log file manually.

        Rotation pattern:
        - agent.log -> agent.log.1.gz (compressed)
        - agent.log.1.gz -> agent.log.2.gz
        - ...
        - agent.log.N.gz deleted if N > max_rotations

        Args:
            agent_name: Agent name
        """
        log_file = self.get_log_file(agent_name)

        if not log_file.exists():
            return

        # Rotate existing backups (in reverse order)
        for i in range(self.max_rotations - 1, 0, -1):
            old_backup = log_file.parent / f"{agent_name}.log.{i}.gz"
            new_backup = log_file.parent / f"{agent_name}.log.{i + 1}.gz"

            if old_backup.exists():
                if i + 1 > self.max_rotations:
                    # Delete oldest backup
                    old_backup.unlink()
                else:
                    # Rename to next number
                    old_backup.rename(new_backup)

        # Compress current log to .log.1.gz
        first_backup = log_file.parent / f"{agent_name}.log.1.gz"

        with log_file.open("rb") as f_in, gzip.open(first_backup, "wb") as f_out:
            f_out.writelines(f_in)

        # Clear current log file
        log_file.unlink()
        log_file.touch()

    def _rotate_if_needed(self, agent_name: str) -> None:
        """Rotate log file if it exceeds max size.

        Args:
            agent_name: Agent name
        """
        log_file = self.get_log_file(agent_name)

        if not log_file.exists():
            return

        if log_file.stat().st_size >= self.max_size_bytes:
            self.rotate(agent_name)

    def get_log_size(self, agent_name: str) -> int:
        """Get current log file size in bytes.

        Args:
            agent_name: Agent name

        Returns:
            Size in bytes (0 if file doesn't exist)
        """
        log_file = self.get_log_file(agent_name)

        if not log_file.exists():
            return 0

        return log_file.stat().st_size

    def list_rotated_logs(self, agent_name: str) -> list[Path]:
        """List all rotated log files for agent.

        Args:
            agent_name: Agent name

        Returns:
            List of rotated log file paths (sorted newest to oldest)
        """
        log_dir = self.log_dir / agent_name

        if not log_dir.exists():
            return []

        # Find all .log.N.gz files
        return sorted(
            log_dir.glob(f"{agent_name}.log.*.gz"),
            key=lambda p: int(p.stem.split(".")[-1]),
        )

    def clear_logs(self, agent_name: str, keep_current: bool = True) -> None:
        """Clear all logs for agent.

        Args:
            agent_name: Agent name
            keep_current: If True, only delete rotated logs; if False, delete all
        """
        log_dir = self.log_dir / agent_name

        if not log_dir.exists():
            return

        # Delete rotated logs
        for rotated_log in self.list_rotated_logs(agent_name):
            rotated_log.unlink()

        # Optionally delete current log
        if not keep_current:
            log_file = self.get_log_file(agent_name)
            if log_file.exists():
                log_file.unlink()
