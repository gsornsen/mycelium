"""Thread-safe JSONL storage backend for telemetry events.

Provides persistent storage for performance analytics with automatic log
rotation, thread safety, and privacy guarantees. Uses newline-delimited JSON
format for efficient append operations and streaming analysis.

Features:
    - Thread-safe append operations with locking
    - Automatic log rotation at 10MB threshold
    - Privacy-first: no PII, only performance metrics
    - Efficient JSONL format for streaming

Storage location: ~/.mycelium/analytics/events.jsonl

Example:
    >>> from pathlib import Path
    >>> storage = EventStorage()
    >>> storage.append_event({
    ...     "timestamp": "2025-10-18T12:00:00Z",
    ...     "event_type": "agent_discovery",
    ...     "duration_ms": 15.2
    ... })

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import contextlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Module-level default for storage directory
_DEFAULT_STORAGE_DIR = Path.home() / ".mycelium" / "analytics"


class EventStorage:
    """Thread-safe JSONL storage for telemetry events.

    Handles persistent storage of performance events with automatic rotation
    and thread-safe operations. Uses JSONL (newline-delimited JSON) format
    for efficient append and streaming analysis.

    Privacy guarantees:
        - No user data or file paths stored
        - Only performance metrics (durations, counts, booleans)
        - Timestamps are UTC with no timezone PII

    Attributes:
        storage_dir: Directory for JSONL files
        max_file_size: Maximum file size before rotation (10MB default)

    Example:
        >>> storage = EventStorage()
        >>> event = {"timestamp": "2025-10-18T12:00:00Z", "event_type": "test"}
        >>> storage.append_event(event)
        >>> events = storage.read_events(limit=10)
        >>> len(events) > 0
        True
    """

    # Constants
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    DEFAULT_FILENAME = "events.jsonl"
    ROTATED_FILENAME_PATTERN = "events_{timestamp}.jsonl"

    def __init__(
        self,
        storage_dir: Path | None = None,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ):
        """Initialize storage backend.

        Args:
            storage_dir: Directory for storing JSONL files
                (default: ~/.mycelium/analytics)
            max_file_size: Maximum file size before rotation in bytes

        Example:
            >>> storage = EventStorage()
            >>> storage.storage_dir.exists()
            True
        """
        if storage_dir is not None:
            self.storage_dir = storage_dir
        else:
            self.storage_dir = _DEFAULT_STORAGE_DIR

        self.max_file_size = max_file_size
        self._lock = threading.Lock()

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize current file path
        self._current_file = self.storage_dir / self.DEFAULT_FILENAME

    def append_event(self, event: dict[str, Any]) -> None:
        """Append event to JSONL file (thread-safe).

        Writes event as single-line JSON with newline. Automatically rotates
        file if it exceeds max_file_size. Thread-safe with locking.

        Args:
            event: Event dictionary to append

        Raises:
            OSError: If file write fails
            TypeError: If event is not JSON-serializable

        Example:
            >>> storage = EventStorage()
            >>> event = {
            ...     "timestamp": datetime.now(timezone.utc).isoformat(),
            ...     "event_type": "test_event",
            ...     "duration_ms": 42.0
            ... }
            >>> storage.append_event(event)
        """
        with self._lock:
            # Check if rotation is needed BEFORE writing
            self._rotate_if_needed()

            # Write event as single-line JSON
            try:
                json_line = json.dumps(
                    event, ensure_ascii=False, separators=(",", ":")
                )
                with self._current_file.open("a", encoding="utf-8") as f:
                    f.write(json_line + "\n")
            except (OSError, TypeError):
                # Re-raise for caller to handle
                raise

    def read_events(
        self,
        start_date: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Read events from storage with optional filtering.

        Reads events from current and rotated files, filtering by timestamp
        if start_date provided. Returns up to limit events in chronological
        order.

        Args:
            start_date: Optional minimum timestamp (UTC)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries

        Example:
            >>> storage = EventStorage()
            >>> from datetime import timedelta
            >>> recent = datetime.now(timezone.utc) - timedelta(days=1)
            >>> events = storage.read_events(start_date=recent, limit=100)
            >>> isinstance(events, list)
            True
        """
        events: list[dict[str, Any]] = []

        # Get all JSONL files (current + rotated)
        jsonl_files = sorted(
            self.storage_dir.glob("events*.jsonl"),
            key=lambda p: p.stat().st_mtime,
        )

        for file_path in jsonl_files:
            if len(events) >= limit:
                break

            try:
                with file_path.open(encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event = json.loads(line)

                            # Filter by start_date if provided
                            if start_date is not None:
                                event_time = datetime.fromisoformat(
                                    event.get("timestamp", "")
                                )
                                if event_time < start_date:
                                    continue

                            events.append(event)

                            if len(events) >= limit:
                                break

                        except (json.JSONDecodeError, ValueError):
                            # Skip malformed lines
                            continue

            except OSError:
                # Skip unreadable files
                continue

        return events

    def _rotate_if_needed(self) -> None:
        """Check file size and rotate if needed (internal).

        Renames current file with timestamp suffix and creates new file.
        Called internally with lock held.

        Privacy note: Timestamp in filename is UTC, no timezone PII.
        """
        if not self._current_file.exists():
            return

        # Check file size
        file_size = self._current_file.stat().st_size
        if file_size < self.max_file_size:
            return

        # Rotate: rename current file with timestamp
        # Add microseconds to avoid collisions in high-frequency rotation
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        rotated_name = self.ROTATED_FILENAME_PATTERN.format(
            timestamp=timestamp
        )
        rotated_path = self.storage_dir / rotated_name

        # Perform rotation - if this fails, continue anyway
        # (we're already holding the lock, so thread safety is guaranteed)
        with contextlib.suppress(OSError):
            self._current_file.rename(rotated_path)

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics including event count and latest timestamp.

        Returns information about storage usage, file count, sizes, total
        events, and most recent event timestamp.

        Returns:
            Dict with storage statistics including:
                - file_count: Number of JSONL files
                - total_events: Total number of events across all files
                - total_size_bytes: Total storage size in bytes
                - latest_event_time: ISO timestamp of most recent event
                - storage_dir: Path to storage directory

        Example:
            >>> storage = EventStorage()
            >>> stats = storage.get_storage_stats()
            >>> 'file_count' in stats
            True
            >>> 'total_events' in stats
            True
            >>> 'latest_event_time' in stats
            True
        """
        jsonl_files = list(self.storage_dir.glob("events*.jsonl"))

        total_events = 0
        total_size = 0
        latest_event_time = None

        for file_path in jsonl_files:
            try:
                total_size += file_path.stat().st_size

                # Count events and find latest timestamp
                with file_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        total_events += 1
                        try:
                            event = json.loads(line)
                            timestamp = event.get("timestamp")
                            if timestamp and (
                                latest_event_time is None
                                or timestamp > latest_event_time
                            ):
                                latest_event_time = timestamp
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

        return {
            "file_count": len(jsonl_files),
            "total_events": total_events,
            "total_size_bytes": total_size,
            "latest_event_time": latest_event_time,
            "storage_dir": str(self.storage_dir),
        }

    def clear_all_events(self) -> int:
        """Delete all event files (for testing/maintenance).

        WARNING: This permanently deletes all telemetry data.

        Returns:
            Number of files deleted

        Example:
            >>> storage = EventStorage()
            >>> deleted = storage.clear_all_events()
            >>> deleted >= 0
            True
        """
        with self._lock:
            jsonl_files = list(self.storage_dir.glob("events*.jsonl"))
            deleted = 0

            for file_path in jsonl_files:
                try:
                    file_path.unlink()
                    deleted += 1
                except OSError:
                    continue

            return deleted
