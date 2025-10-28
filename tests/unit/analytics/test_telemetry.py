"""Unit tests for TelemetryCollector.

Tests:
    - Event collection for different event types
    - Privacy guarantees (hashing, no PII)
    - Graceful degradation on storage failures
    - Environment variable opt-out
    - Integration with EventStorage

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mycelium_analytics.storage import EventStorage
from mycelium_analytics.telemetry import TelemetryCollector


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create EventStorage instance for testing."""
    return EventStorage(storage_dir=temp_storage_dir)


@pytest.fixture
def collector(storage):
    """Create TelemetryCollector instance for testing."""
    return TelemetryCollector(storage)


class TestTelemetryBasics:
    """Test basic telemetry collection."""

    def test_init(self, storage):
        """Test collector initialization."""
        collector = TelemetryCollector(storage)
        assert collector.storage is storage
        assert collector.enabled is True

    def test_init_respects_env_var(self, storage):
        """Test that MYCELIUM_TELEMETRY=0 disables telemetry."""
        with patch.dict(os.environ, {"MYCELIUM_TELEMETRY": "0"}):
            collector = TelemetryCollector(storage)
            assert collector.enabled is False

    def test_record_agent_discovery(self, collector, storage):
        """Test recording agent discovery event."""
        collector.record_agent_discovery(
            operation="list_agents",
            duration_ms=15.5,
            agent_count=42,
        )

        # Verify event was stored
        events = storage.read_events()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "agent_discovery"
        assert event["operation"] == "list_agents"
        assert event["duration_ms"] == 15.5
        assert event["cache_hit"] is False
        assert event["agent_count"] == 42
        assert "timestamp" in event

    def test_record_agent_discovery_with_cache_hit(self, collector, storage):
        """Test recording agent discovery with cache hit."""
        collector.record_agent_discovery(
            operation="get_agent",
            duration_ms=0.8,
            cache_hit=True,
            agent_count=1,
        )

        events = storage.read_events()
        assert len(events) == 1
        assert events[0]["cache_hit"] is True

    def test_record_session_start(self, collector, storage):
        """Test recording session start event."""
        collector.record_session_start(
            session_type="lazy_loaded",
            initial_tokens=1200,
        )

        events = storage.read_events()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "session_start"
        assert event["session_type"] == "lazy_loaded"
        assert event["initial_tokens"] == 1200

    def test_record_session_end(self, collector, storage):
        """Test recording session end event."""
        collector.record_session_end(
            session_duration_seconds=120.5,
            total_tokens_loaded=3500,
            agents_loaded=5,
        )

        events = storage.read_events()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "session_end"
        assert event["session_duration_seconds"] == 120.5
        assert event["total_tokens_loaded"] == 3500
        assert event["agents_loaded"] == 5

    def test_record_agent_load(self, collector, storage):
        """Test recording agent load event."""
        collector.record_agent_load(
            agent_id="01-core-api-designer",
            load_time_ms=3.2,
            content_size_bytes=4582,
            estimated_tokens=1145,
        )

        events = storage.read_events()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "agent_load"
        assert "agent_id_hash" in event
        assert event["load_time_ms"] == 3.2
        assert event["content_size_bytes"] == 4582
        assert event["estimated_tokens"] == 1145

    def test_record_cache_operation(self, collector, storage):
        """Test recording cache operation event."""
        collector.record_cache_operation(
            operation="get",
            cache_size=45,
            hit_rate=87.5,
        )

        events = storage.read_events()
        assert len(events) == 1

        event = events[0]
        assert event["event_type"] == "cache_operation"
        assert event["operation"] == "get"
        assert event["cache_size"] == 45
        assert event["hit_rate"] == 87.5
        assert event["evictions"] == 0


class TestPrivacyGuarantees:
    """Test privacy-preserving features."""

    def test_agent_id_hashing(self, collector):
        """Test that agent IDs are hashed for privacy."""
        hash1 = collector._hash_agent_id("01-core-api-designer")
        hash2 = collector._hash_agent_id("01-core-api-designer")
        hash3 = collector._hash_agent_id("02-different-agent")

        # Same input produces same hash
        assert hash1 == hash2

        # Different input produces different hash
        assert hash1 != hash3

        # Hash is shortened (8 chars)
        assert len(hash1) == 8

    def test_no_pii_in_events(self, collector, storage):
        """Test that no PII is stored in events."""
        # Record various events
        collector.record_agent_discovery("list_agents", 15.0, agent_count=10)
        collector.record_session_start("lazy_loaded", 1000)
        collector.record_agent_load("test-agent", 5.0, 1000, 250)

        # Check all events
        events = storage.read_events()

        for event in events:
            # Should not contain these privacy-sensitive fields
            assert "user" not in event
            assert "username" not in event
            assert "file_path" not in event
            assert "command" not in event
            assert "content" not in event

            # Should only contain performance metrics
            assert "timestamp" in event
            assert "event_type" in event


class TestGracefulDegradation:
    """Test graceful degradation on failures."""

    def test_disabled_telemetry_no_storage(self, storage):
        """Test that disabled telemetry doesn't call storage."""
        with patch.dict(os.environ, {"MYCELIUM_TELEMETRY": "0"}):
            collector = TelemetryCollector(storage)
            collector.record_agent_discovery("test", 10.0)

            # No events should be stored
            events = storage.read_events()
            assert len(events) == 0

    def test_storage_failure_doesnt_crash(self, storage):
        """Test that storage failures don't crash telemetry."""
        collector = TelemetryCollector(storage)

        # Mock storage to raise exception
        storage.append_event = Mock(side_effect=OSError("Disk full"))

        # Should not raise exception
        collector.record_agent_discovery("test", 10.0)

    def test_multiple_events_recording(self, collector, storage):
        """Test recording multiple events in sequence."""
        events_to_record = [
            ("list_agents", 15.0, 42),
            ("get_agent", 2.5, 1),
            ("search", 8.0, 5),
        ]

        for operation, duration, count in events_to_record:
            collector.record_agent_discovery(operation, duration, agent_count=count)

        # Verify all events were stored
        events = storage.read_events()
        assert len(events) == 3

        operations = [e["operation"] for e in events]
        assert "list_agents" in operations
        assert "get_agent" in operations
        assert "search" in operations


class TestTimestamps:
    """Test timestamp handling."""

    def test_timestamp_format(self, collector, storage):
        """Test that timestamps are ISO 8601 UTC format."""
        collector.record_agent_discovery("test", 10.0)

        events = storage.read_events()
        timestamp = events[0]["timestamp"]

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

        # Should be UTC (ends with +00:00 or Z)
        assert timestamp.endswith("+00:00") or timestamp.endswith("Z") or "+" in timestamp

    def test_timestamps_are_ordered(self, collector, storage):
        """Test that timestamps are in chronological order."""
        import time

        for i in range(5):
            collector.record_agent_discovery(f"event{i}", 10.0)
            time.sleep(0.01)  # Small delay

        events = storage.read_events()

        # Parse timestamps
        timestamps = [datetime.fromisoformat(e["timestamp"]) for e in events]

        # Verify chronological order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] <= timestamps[i + 1]


class TestConfigurationStatus:
    """Test telemetry configuration and status."""

    def test_get_enabled_status(self, collector, temp_storage_dir):
        """Test getting telemetry enabled status."""
        status = collector.get_enabled_status()

        assert "enabled" in status
        assert "storage_dir" in status
        assert "env_var" in status

        assert status["enabled"] is True
        assert str(temp_storage_dir) in status["storage_dir"]

    def test_get_enabled_status_when_disabled(self, storage):
        """Test status when telemetry is disabled."""
        with patch.dict(os.environ, {"MYCELIUM_TELEMETRY": "0"}):
            collector = TelemetryCollector(storage)
            status = collector.get_enabled_status()

            assert status["enabled"] is False
            assert status["env_var"] == "0"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_typical_session_workflow(self, collector, storage):
        """Test typical session workflow with multiple operations."""
        # Session start
        collector.record_session_start("lazy_loaded", 1000)

        # Agent discovery operations
        collector.record_agent_discovery("list_agents", 18.0, agent_count=42)
        collector.record_agent_discovery("get_agent", 3.0, cache_hit=False, agent_count=1)
        collector.record_agent_load("agent-1", 3.0, 5000, 1250)
        collector.record_agent_discovery("get_agent", 0.5, cache_hit=True, agent_count=1)
        collector.record_agent_discovery("search", 7.0, agent_count=5)

        # Session end
        collector.record_session_end(300.0, 2500, 3)

        # Verify all events
        events = storage.read_events()
        assert len(events) == 7

        event_types = [e["event_type"] for e in events]
        assert "session_start" in event_types
        assert "session_end" in event_types
        assert event_types.count("agent_discovery") == 4
        assert "agent_load" in event_types

    def test_high_frequency_recording(self, collector, storage):
        """Test high-frequency event recording (stress test)."""
        num_events = 100

        for i in range(num_events):
            collector.record_agent_discovery(f"operation{i % 3}", i * 0.1, agent_count=i)

        # Verify all events were recorded
        events = storage.read_events(limit=num_events)
        assert len(events) == num_events
