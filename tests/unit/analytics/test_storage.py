"""Unit tests for EventStorage JSONL backend.

Tests:
    - Basic append and read operations
    - Automatic file rotation at size threshold
    - Thread safety with concurrent appends
    - Filtering by start_date
    - Storage statistics
    - Graceful error handling

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import json
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mycelium_analytics.storage import EventStorage


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create EventStorage instance for testing."""
    return EventStorage(storage_dir=temp_storage_dir)


class TestEventStorageBasics:
    """Test basic append and read operations."""

    def test_init_creates_directory(self, temp_storage_dir):
        """Test that storage directory is created on init."""
        storage = EventStorage(storage_dir=temp_storage_dir / "new_dir")
        assert storage.storage_dir.exists()
        assert storage.storage_dir.is_dir()

    def test_append_event(self, storage):
        """Test appending single event to JSONL file."""
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'test_event',
            'duration_ms': 42.0,
        }

        storage.append_event(event)

        # Verify file was created
        jsonl_file = storage.storage_dir / "events.jsonl"
        assert jsonl_file.exists()

        # Verify content
        with open(jsonl_file) as f:
            line = f.readline().strip()
            loaded = json.loads(line)
            assert loaded == event

    def test_append_multiple_events(self, storage):
        """Test appending multiple events."""
        events = [
            {'timestamp': datetime.now(timezone.utc).isoformat(), 'event_type': 'event1'},
            {'timestamp': datetime.now(timezone.utc).isoformat(), 'event_type': 'event2'},
            {'timestamp': datetime.now(timezone.utc).isoformat(), 'event_type': 'event3'},
        ]

        for event in events:
            storage.append_event(event)

        # Verify all events were written
        jsonl_file = storage.storage_dir / "events.jsonl"
        with open(jsonl_file) as f:
            lines = f.readlines()
            assert len(lines) == 3

    def test_read_events(self, storage):
        """Test reading events from storage."""
        events = [
            {'timestamp': datetime.now(timezone.utc).isoformat(), 'event_type': f'event{i}'}
            for i in range(5)
        ]

        for event in events:
            storage.append_event(event)

        # Read all events
        read_events = storage.read_events()
        assert len(read_events) == 5
        assert all(e['event_type'] in [f'event{i}' for i in range(5)] for e in read_events)

    def test_read_events_with_limit(self, storage):
        """Test reading events with limit."""
        for i in range(10):
            storage.append_event({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': f'event{i}',
            })

        # Read with limit
        read_events = storage.read_events(limit=5)
        assert len(read_events) == 5

    def test_read_events_with_start_date(self, storage):
        """Test filtering events by start_date."""
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=2)
        recent_time = now - timedelta(hours=1)

        # Add old event
        storage.append_event({
            'timestamp': old_time.isoformat(),
            'event_type': 'old_event',
        })

        # Add recent event
        storage.append_event({
            'timestamp': recent_time.isoformat(),
            'event_type': 'recent_event',
        })

        # Filter by start_date (1 day ago)
        start_date = now - timedelta(days=1)
        read_events = storage.read_events(start_date=start_date)

        # Should only get recent event
        assert len(read_events) == 1
        assert read_events[0]['event_type'] == 'recent_event'

    def test_read_empty_storage(self, storage):
        """Test reading from empty storage."""
        read_events = storage.read_events()
        assert read_events == []


class TestFileRotation:
    """Test automatic file rotation at size threshold."""

    def test_rotation_at_threshold(self, temp_storage_dir):
        """Test that file rotates when exceeding max_file_size."""
        # Use small threshold for testing (1KB)
        storage = EventStorage(
            storage_dir=temp_storage_dir,
            max_file_size=1024,
        )

        # Write events until rotation
        large_event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'large_event',
            'data': 'x' * 500,  # 500 chars
        }

        # Write 3 events (~1.5KB) to trigger rotation
        for _ in range(3):
            storage.append_event(large_event)

        # Should have rotated file
        jsonl_files = list(temp_storage_dir.glob("events*.jsonl"))
        assert len(jsonl_files) >= 2  # events.jsonl + rotated file

    def test_rotated_filename_format(self, temp_storage_dir):
        """Test that rotated files have timestamp in filename."""
        storage = EventStorage(
            storage_dir=temp_storage_dir,
            max_file_size=500,  # Very small threshold
        )

        # Trigger rotation
        large_event = {'timestamp': datetime.now(timezone.utc).isoformat(), 'data': 'x' * 200}
        for _ in range(5):
            storage.append_event(large_event)

        # Check rotated files
        rotated_files = [f for f in temp_storage_dir.glob("events_*.jsonl")]
        assert len(rotated_files) > 0

        # Verify filename pattern (events_YYYYMMDD_HHMMSS.jsonl)
        for rotated_file in rotated_files:
            assert rotated_file.name.startswith("events_")
            assert rotated_file.name.endswith(".jsonl")

    def test_read_across_rotated_files(self, temp_storage_dir):
        """Test reading events from both current and rotated files."""
        storage = EventStorage(
            storage_dir=temp_storage_dir,
            max_file_size=500,
        )

        # Write events that will cause rotation
        for i in range(10):
            storage.append_event({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': f'event{i}',
                'data': 'x' * 100,
            })

        # Read all events (should read from multiple files)
        read_events = storage.read_events()
        assert len(read_events) == 10


class TestThreadSafety:
    """Test thread safety of concurrent operations."""

    def test_concurrent_appends(self, storage):
        """Test concurrent event appends from multiple threads."""
        num_threads = 10
        events_per_thread = 20

        def append_events(thread_id):
            for i in range(events_per_thread):
                storage.append_event({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'thread_id': thread_id,
                    'event_num': i,
                })

        # Spawn threads
        threads = [
            threading.Thread(target=append_events, args=(tid,))
            for tid in range(num_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all events were written
        read_events = storage.read_events(limit=num_threads * events_per_thread)
        assert len(read_events) == num_threads * events_per_thread

    def test_concurrent_appends_with_rotation(self, temp_storage_dir):
        """Test concurrent appends during file rotation."""
        storage = EventStorage(
            storage_dir=temp_storage_dir,
            max_file_size=2048,  # Small threshold
        )

        num_threads = 5
        events_per_thread = 10

        def append_large_events(thread_id):
            for i in range(events_per_thread):
                storage.append_event({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'thread_id': thread_id,
                    'data': 'x' * 150,  # Large event
                })

        threads = [
            threading.Thread(target=append_large_events, args=(tid,))
            for tid in range(num_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all events were written (across potentially multiple files)
        read_events = storage.read_events(limit=num_threads * events_per_thread)
        assert len(read_events) == num_threads * events_per_thread


class TestStorageStats:
    """Test storage statistics."""

    def test_get_storage_stats(self, storage):
        """Test getting storage statistics."""
        # Add some events
        for i in range(5):
            storage.append_event({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': f'event{i}',
            })

        stats = storage.get_storage_stats()

        # Check new field names
        assert 'file_count' in stats
        assert 'total_events' in stats
        assert 'total_size_bytes' in stats
        assert 'latest_event_time' in stats
        assert 'storage_dir' in stats

        # Validate values
        assert stats['file_count'] >= 1
        assert stats['total_events'] == 5
        assert stats['total_size_bytes'] > 0
        assert stats['latest_event_time'] is not None

    def test_clear_all_events(self, storage):
        """Test clearing all events."""
        # Add events
        for i in range(5):
            storage.append_event({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': f'event{i}',
            })

        # Clear
        deleted = storage.clear_all_events()
        assert deleted >= 1

        # Verify empty
        read_events = storage.read_events()
        assert len(read_events) == 0


class TestErrorHandling:
    """Test graceful error handling."""

    def test_append_non_serializable_event(self, storage):
        """Test handling of non-JSON-serializable events."""
        # Event with non-serializable object
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'bad_data': lambda x: x,  # Not JSON serializable
        }

        with pytest.raises(TypeError):
            storage.append_event(event)

    def test_read_events_with_malformed_lines(self, storage):
        """Test reading with malformed JSON lines."""
        # Write valid event
        storage.append_event({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'valid',
        })

        # Manually write malformed line
        with open(storage.storage_dir / "events.jsonl", 'a') as f:
            f.write("not valid json\n")

        # Write another valid event
        storage.append_event({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': 'valid2',
        })

        # Should skip malformed line and return valid events
        read_events = storage.read_events()
        assert len(read_events) == 2
        assert all(e['event_type'].startswith('valid') for e in read_events)

    def test_read_events_empty_lines(self, storage):
        """Test reading with empty lines (should be skipped)."""
        # Write events with empty lines
        with open(storage.storage_dir / "events.jsonl", 'a') as f:
            f.write('{"event_type": "event1"}\n')
            f.write('\n')
            f.write('{"event_type": "event2"}\n')
            f.write('   \n')
            f.write('{"event_type": "event3"}\n')

        read_events = storage.read_events()
        assert len(read_events) == 3
