"""Tests for log management.

Comprehensive test suite for LogManager, LogEntry, and related functionality.
"""

from __future__ import annotations

import gzip
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mycelium.logging import LogEntry, LogManager


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory for testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path to temporary log directory
    """
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def log_manager(temp_log_dir: Path) -> LogManager:
    """Create LogManager instance with temporary directory.

    Args:
        temp_log_dir: Temporary log directory

    Returns:
        LogManager instance
    """
    return LogManager(log_dir=temp_log_dir, max_size_mb=1, max_rotations=3)


class TestLogEntry:
    """Tests for LogEntry dataclass."""

    def test_create_log_entry(self) -> None:
        """Should create LogEntry with all fields."""
        timestamp = datetime.now(timezone.utc)
        entry = LogEntry(
            timestamp=timestamp,
            level="INFO",
            message="Test message",
            agent_name="test-agent",
            metadata={"key": "value"},
        )

        assert entry.timestamp == timestamp
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.agent_name == "test-agent"
        assert entry.metadata == {"key": "value"}

    def test_create_log_entry_without_metadata(self) -> None:
        """Should create LogEntry without metadata."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            message="Test message",
            agent_name="test-agent",
        )

        assert entry.metadata is None

    def test_to_dict(self) -> None:
        """Should convert LogEntry to dictionary."""
        timestamp = datetime.now(timezone.utc)
        entry = LogEntry(
            timestamp=timestamp,
            level="INFO",
            message="Test message",
            agent_name="test-agent",
            metadata={"key": "value"},
        )

        data = entry.to_dict()

        assert data["timestamp"] == timestamp.isoformat()
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["agent_name"] == "test-agent"
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self) -> None:
        """Should create LogEntry from dictionary."""
        timestamp = datetime.now(timezone.utc)
        data = {
            "timestamp": timestamp.isoformat(),
            "level": "INFO",
            "message": "Test message",
            "agent_name": "test-agent",
            "metadata": {"key": "value"},
        }

        entry = LogEntry.from_dict(data)

        assert entry.timestamp == timestamp
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.agent_name == "test-agent"
        assert entry.metadata == {"key": "value"}

    def test_from_dict_without_metadata(self) -> None:
        """Should handle missing metadata in from_dict."""
        timestamp = datetime.now(timezone.utc)
        data = {
            "timestamp": timestamp.isoformat(),
            "level": "INFO",
            "message": "Test message",
            "agent_name": "test-agent",
        }

        entry = LogEntry.from_dict(data)

        assert entry.metadata is None

    def test_format_with_timestamp(self) -> None:
        """Should format log entry with timestamp."""
        entry = LogEntry(
            timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            level="INFO",
            message="Test message",
            agent_name="test-agent",
        )

        formatted = entry.format(include_timestamp=True)

        assert "[2025-01-01 12:00:00]" in formatted
        assert "INFO" in formatted
        assert "[test-agent]" in formatted
        assert "Test message" in formatted

    def test_format_without_timestamp(self) -> None:
        """Should format log entry without timestamp."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            message="Test message",
            agent_name="test-agent",
        )

        formatted = entry.format(include_timestamp=False)

        assert "INFO" in formatted
        assert "[test-agent]" in formatted
        assert "Test message" in formatted

    def test_format_with_metadata(self) -> None:
        """Should include metadata in formatted output."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            message="Test message",
            agent_name="test-agent",
            metadata={"key": "value"},
        )

        formatted = entry.format()

        assert "{'key': 'value'}" in formatted


class TestLogManager:
    """Tests for LogManager class."""

    def test_init_creates_log_directory(self, temp_log_dir: Path) -> None:
        """Should create log directory on initialization."""
        log_dir = temp_log_dir / "custom"
        LogManager(log_dir=log_dir)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_init_uses_default_directory(self) -> None:
        """Should use default directory if none provided."""
        manager = LogManager()

        expected = Path.home() / ".local" / "share" / "mycelium" / "logs"
        assert manager.log_dir == expected

    def test_get_log_file(self, log_manager: LogManager) -> None:
        """Should get log file path for agent."""
        log_file = log_manager.get_log_file("test-agent")

        assert log_file.parent.name == "test-agent"
        assert log_file.name == "test-agent.log"
        assert log_file.parent.exists()

    def test_write_creates_log_file(self, log_manager: LogManager) -> None:
        """Should create log file when writing."""
        log_manager.write(
            agent_name="test-agent",
            level="INFO",
            message="Test message",
        )

        log_file = log_manager.get_log_file("test-agent")

        assert log_file.exists()

    def test_write_appends_jsonl(self, log_manager: LogManager) -> None:
        """Should write JSONL format."""
        log_manager.write(
            agent_name="test-agent",
            level="INFO",
            message="Test message 1",
        )

        log_manager.write(
            agent_name="test-agent",
            level="INFO",
            message="Test message 2",
        )

        log_file = log_manager.get_log_file("test-agent")
        lines = log_file.read_text().strip().split("\n")

        assert len(lines) == 2

        # Validate JSONL format
        for line in lines:
            data = json.loads(line)
            assert "timestamp" in data
            assert "level" in data
            assert "message" in data
            assert "agent_name" in data

    def test_write_with_metadata(self, log_manager: LogManager) -> None:
        """Should write metadata to log entry."""
        log_manager.write(
            agent_name="test-agent",
            level="INFO",
            message="Test message",
            metadata={"key": "value"},
        )

        log_file = log_manager.get_log_file("test-agent")
        data = json.loads(log_file.read_text().strip())

        assert data["metadata"] == {"key": "value"}

    def test_read_returns_log_entries(self, log_manager: LogManager) -> None:
        """Should read log entries from file."""
        log_manager.write("test-agent", "INFO", "Message 1")
        log_manager.write("test-agent", "INFO", "Message 2")
        log_manager.write("test-agent", "INFO", "Message 3")

        entries = log_manager.read("test-agent", lines=10)

        assert len(entries) == 3
        assert all(isinstance(e, LogEntry) for e in entries)
        assert entries[0].message == "Message 1"
        assert entries[1].message == "Message 2"
        assert entries[2].message == "Message 3"

    def test_read_respects_line_limit(self, log_manager: LogManager) -> None:
        """Should only return last N lines."""
        for i in range(10):
            log_manager.write("test-agent", "INFO", f"Message {i}")

        entries = log_manager.read("test-agent", lines=5)

        assert len(entries) == 5
        assert entries[0].message == "Message 5"
        assert entries[-1].message == "Message 9"

    def test_read_nonexistent_agent(self, log_manager: LogManager) -> None:
        """Should return empty list for nonexistent agent."""
        entries = log_manager.read("nonexistent-agent")

        assert entries == []

    def test_read_handles_malformed_json(self, log_manager: LogManager, temp_log_dir: Path) -> None:
        """Should skip malformed JSON lines."""
        log_file = log_manager.get_log_file("test-agent")

        # Write valid entry
        log_manager.write("test-agent", "INFO", "Valid message")

        # Write malformed JSON
        with log_file.open("a") as f:
            f.write("not valid json\n")
            f.write('{"incomplete": \n')

        # Write another valid entry
        log_manager.write("test-agent", "INFO", "Another valid message")

        entries = log_manager.read("test-agent")

        # Should only return valid entries
        assert len(entries) == 2
        assert entries[0].message == "Valid message"
        assert entries[1].message == "Another valid message"

    def test_stream_existing_content(self, log_manager: LogManager) -> None:
        """Should stream existing log content."""
        log_manager.write("test-agent", "INFO", "Message 1")
        log_manager.write("test-agent", "INFO", "Message 2")

        entries = list(log_manager.stream("test-agent", follow=False))

        assert len(entries) == 2
        assert entries[0].message == "Message 1"
        assert entries[1].message == "Message 2"

    def test_stream_creates_file_if_missing(self, log_manager: LogManager) -> None:
        """Should create log file if it doesn't exist."""
        log_file = log_manager.get_log_file("test-agent")

        assert not log_file.exists()

        # Start streaming (non-blocking)
        stream = log_manager.stream("test-agent", follow=False)
        list(stream)

        assert log_file.exists()

    def test_rotate_creates_compressed_backup(self, log_manager: LogManager) -> None:
        """Should create compressed backup when rotating."""
        # Write some content
        log_manager.write("test-agent", "INFO", "Message 1")
        log_manager.write("test-agent", "INFO", "Message 2")

        # Rotate
        log_manager.rotate("test-agent")

        # Check backup exists
        log_file = log_manager.get_log_file("test-agent")
        backup = log_file.parent / "test-agent.log.1.gz"

        assert backup.exists()

        # Verify backup content
        with gzip.open(backup, "rt") as f:
            content = f.read()
            assert "Message 1" in content
            assert "Message 2" in content

    def test_rotate_clears_current_log(self, log_manager: LogManager) -> None:
        """Should clear current log after rotation."""
        log_manager.write("test-agent", "INFO", "Message 1")

        # Rotate
        log_manager.rotate("test-agent")

        # Current log should be empty
        log_file = log_manager.get_log_file("test-agent")
        assert log_file.exists()
        assert log_file.stat().st_size == 0

    def test_rotate_respects_max_rotations(self, log_manager: LogManager) -> None:
        """Should delete old backups beyond max_rotations."""
        # Create multiple rotations
        for i in range(5):
            log_manager.write("test-agent", "INFO", f"Message {i}")
            log_manager.rotate("test-agent")

        log_file = log_manager.get_log_file("test-agent")

        # Should only keep max_rotations backups (3)
        backups = list(log_file.parent.glob("test-agent.log.*.gz"))
        assert len(backups) == 3

        # Verify numbering
        assert (log_file.parent / "test-agent.log.1.gz").exists()
        assert (log_file.parent / "test-agent.log.2.gz").exists()
        assert (log_file.parent / "test-agent.log.3.gz").exists()
        assert not (log_file.parent / "test-agent.log.4.gz").exists()

    def test_auto_rotation_on_size(self, log_manager: LogManager) -> None:
        """Should automatically rotate when file exceeds max size."""
        # Write enough data to trigger rotation (max_size_mb = 1)
        large_message = "x" * 1024  # 1KB message

        for _ in range(1100):  # Write ~1.1MB
            log_manager.write("test-agent", "INFO", large_message)

        # Should have created rotation
        log_file = log_manager.get_log_file("test-agent")
        backups = list(log_file.parent.glob("test-agent.log.*.gz"))

        assert len(backups) >= 1

    def test_get_log_size(self, log_manager: LogManager) -> None:
        """Should return current log file size."""
        log_manager.write("test-agent", "INFO", "Test message")

        size = log_manager.get_log_size("test-agent")

        assert size > 0

    def test_get_log_size_nonexistent(self, log_manager: LogManager) -> None:
        """Should return 0 for nonexistent log."""
        size = log_manager.get_log_size("nonexistent-agent")

        assert size == 0

    def test_list_rotated_logs(self, log_manager: LogManager) -> None:
        """Should list all rotated log files."""
        # Create rotations
        for i in range(3):
            log_manager.write("test-agent", "INFO", f"Message {i}")
            log_manager.rotate("test-agent")

        rotated = log_manager.list_rotated_logs("test-agent")

        assert len(rotated) == 3
        assert all(p.name.endswith(".gz") for p in rotated)

    def test_list_rotated_logs_sorted(self, log_manager: LogManager) -> None:
        """Should return rotated logs sorted by number."""
        # Create rotations
        for i in range(3):
            log_manager.write("test-agent", "INFO", f"Message {i}")
            log_manager.rotate("test-agent")

        rotated = log_manager.list_rotated_logs("test-agent")

        # Should be sorted: .1.gz, .2.gz, .3.gz
        assert rotated[0].name == "test-agent.log.1.gz"
        assert rotated[1].name == "test-agent.log.2.gz"
        assert rotated[2].name == "test-agent.log.3.gz"

    def test_clear_logs_keeps_current(self, log_manager: LogManager) -> None:
        """Should clear rotated logs but keep current."""
        # Create rotations
        for i in range(3):
            log_manager.write("test-agent", "INFO", f"Message {i}")
            log_manager.rotate("test-agent")

        # Write to current log
        log_manager.write("test-agent", "INFO", "Current message")

        # Clear logs (keep current)
        log_manager.clear_logs("test-agent", keep_current=True)

        # Current should exist
        log_file = log_manager.get_log_file("test-agent")
        assert log_file.exists()
        assert log_file.stat().st_size > 0

        # Rotated should be deleted
        rotated = log_manager.list_rotated_logs("test-agent")
        assert len(rotated) == 0

    def test_clear_logs_deletes_all(self, log_manager: LogManager) -> None:
        """Should delete all logs including current."""
        # Create rotations
        for i in range(2):
            log_manager.write("test-agent", "INFO", f"Message {i}")
            log_manager.rotate("test-agent")

        # Write to current log
        log_manager.write("test-agent", "INFO", "Current message")

        # Clear all logs
        log_manager.clear_logs("test-agent", keep_current=False)

        # Current should not exist
        log_file = log_manager.get_log_file("test-agent")
        assert not log_file.exists()

        # Rotated should be deleted
        rotated = log_manager.list_rotated_logs("test-agent")
        assert len(rotated) == 0

    def test_thread_safe_writes(self, log_manager: LogManager) -> None:
        """Should handle concurrent writes safely."""

        def write_logs(thread_id: int) -> None:
            for i in range(100):
                log_manager.write(
                    "test-agent",
                    "INFO",
                    f"Thread {thread_id} message {i}",
                    metadata={"thread": str(thread_id)},
                )

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_logs, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have 500 entries (5 threads * 100 messages)
        entries = log_manager.read("test-agent", lines=1000)
        assert len(entries) == 500

    def test_multiple_agents(self, log_manager: LogManager) -> None:
        """Should handle logs for multiple agents independently."""
        log_manager.write("agent-1", "INFO", "Agent 1 message")
        log_manager.write("agent-2", "INFO", "Agent 2 message")
        log_manager.write("agent-1", "INFO", "Agent 1 another message")

        entries_1 = log_manager.read("agent-1")
        entries_2 = log_manager.read("agent-2")

        assert len(entries_1) == 2
        assert len(entries_2) == 1
        assert all(e.agent_name == "agent-1" for e in entries_1)
        assert all(e.agent_name == "agent-2" for e in entries_2)


class TestLogLevels:
    """Tests for different log levels."""

    def test_info_level(self, log_manager: LogManager) -> None:
        """Should write INFO level logs."""
        log_manager.write("test-agent", "INFO", "Info message")

        entries = log_manager.read("test-agent")
        assert entries[0].level == "INFO"

    def test_warning_level(self, log_manager: LogManager) -> None:
        """Should write WARNING level logs."""
        log_manager.write("test-agent", "WARNING", "Warning message")

        entries = log_manager.read("test-agent")
        assert entries[0].level == "WARNING"

    def test_error_level(self, log_manager: LogManager) -> None:
        """Should write ERROR level logs."""
        log_manager.write("test-agent", "ERROR", "Error message")

        entries = log_manager.read("test-agent")
        assert entries[0].level == "ERROR"

    def test_debug_level(self, log_manager: LogManager) -> None:
        """Should write DEBUG level logs."""
        log_manager.write("test-agent", "DEBUG", "Debug message")

        entries = log_manager.read("test-agent")
        assert entries[0].level == "DEBUG"


class TestIntegration:
    """Integration tests for log management."""

    def test_full_workflow(self, log_manager: LogManager) -> None:
        """Should support full workflow of logging operations."""
        # Write logs
        log_manager.write("test-agent", "INFO", "Starting")
        log_manager.write("test-agent", "INFO", "Processing")
        log_manager.write("test-agent", "ERROR", "Error occurred")
        log_manager.write("test-agent", "INFO", "Recovered")

        # Read logs
        entries = log_manager.read("test-agent")
        assert len(entries) == 4

        # Check size
        size = log_manager.get_log_size("test-agent")
        assert size > 0

        # Rotate
        log_manager.rotate("test-agent")

        # Verify rotation
        rotated = log_manager.list_rotated_logs("test-agent")
        assert len(rotated) == 1

        # Write more logs
        log_manager.write("test-agent", "INFO", "After rotation")

        # Read new logs
        entries = log_manager.read("test-agent")
        assert len(entries) == 1
        assert entries[0].message == "After rotation"

        # Clear logs
        log_manager.clear_logs("test-agent")

        # Verify cleanup
        rotated = log_manager.list_rotated_logs("test-agent")
        assert len(rotated) == 0
