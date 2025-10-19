"""Integration tests for analytics system with agent discovery.

This module tests the complete integration of the analytics system with
the agent discovery pipeline, ensuring telemetry is correctly collected
and analyzed.

Author: @documentation-engineer
Phase: Phase 2 Performance Analytics - Day 3
Date: 2025-10-19
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mycelium_analytics import EventStorage, MetricsAnalyzer, TelemetryCollector
from scripts.agent_discovery import AgentDiscovery


def test_agent_discovery_telemetry_integration(tmp_path):
    """Test that agent discovery generates telemetry events.

    This test verifies the complete integration flow:
    1. Agent discovery operations generate events
    2. Events are stored correctly
    3. Events can be read back
    4. Event structure matches schema
    """
    # Create temp storage
    storage = EventStorage(storage_dir=tmp_path / "analytics")

    # Run agent discovery with telemetry
    index_path = Path("plugins/mycelium-core/agents/index.json")
    if not index_path.exists():
        pytest.skip("Agent index not found (expected in mycelium-core plugin)")

    discovery = AgentDiscovery(index_path)

    # Override telemetry to use temp storage
    discovery.telemetry = TelemetryCollector(storage)

    # Perform operations
    agents = discovery.list_agents()
    assert len(agents) > 0, "Should discover at least some agents"

    # Get specific agent
    agent = discovery.get_agent(agents[0]["id"])
    assert agent is not None, "Should load agent successfully"

    # Search for agents
    results = discovery.search("api")

    # Verify events were recorded
    events = storage.read_events()
    assert len(events) >= 3, "Should have at least 3 events (list, get, search)"

    # Verify event types
    event_types = {e["event_type"] for e in events}
    assert "agent_discovery" in event_types, "Should have agent_discovery events"

    # Verify operations
    operations = {e["operation"] for e in events if e.get("operation")}
    assert "list_agents" in operations, "Should have list_agents operation"
    assert "get_agent" in operations, "Should have get_agent operation"

    # Verify event structure
    for event in events:
        assert "timestamp" in event, "Event should have timestamp"
        assert "event_type" in event, "Event should have event_type"
        # Validate timestamp is ISO 8601 UTC
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        assert timestamp.tzinfo is not None, "Timestamp should have timezone"


def test_metrics_analyzer_with_real_data():
    """Test MetricsAnalyzer with real telemetry data.

    This test verifies that the metrics analyzer can process real
    telemetry data from the default storage location (if it exists).
    """
    storage = EventStorage()
    analyzer = MetricsAnalyzer(storage)

    # Get real metrics (if data exists)
    stats = analyzer.get_discovery_stats(days=7)

    # Verify structure (even if empty)
    assert "total_operations" in stats, "Should have total_operations field"
    assert "by_operation" in stats, "Should have by_operation field"
    assert "overall" in stats, "Should have overall field"

    # If we have data, verify it's well-formed
    if stats["total_operations"] > 0:
        assert "list_agents" in stats["by_operation"] or "get_agent" in stats[
            "by_operation"
        ], "Should have at least one operation type"

        for op_name, op_stats in stats["by_operation"].items():
            assert "count" in op_stats, f"{op_name} should have count"
            assert "avg_ms" in op_stats, f"{op_name} should have avg_ms"
            assert "p50_ms" in op_stats, f"{op_name} should have p50_ms"
            assert "p95_ms" in op_stats, f"{op_name} should have p95_ms"
            assert "p99_ms" in op_stats, f"{op_name} should have p99_ms"


def test_health_check_execution():
    """Test health check report generation.

    This test verifies that the health check report can be generated
    and contains expected sections.
    """
    from scripts.health_check import generate_health_report

    report = generate_health_report(days=7)

    # Verify report structure
    assert (
        "Mycelium Performance Health Check" in report
    ), "Should have health check header"
    assert (
        "AGENT DISCOVERY PERFORMANCE" in report
    ), "Should have discovery performance section"
    assert "CACHE PERFORMANCE" in report, "Should have cache performance section"
    assert "TOKEN SAVINGS" in report, "Should have token savings section"


def test_telemetry_opt_out(tmp_path):
    """Test that telemetry can be disabled via environment variable.

    This test verifies the opt-out mechanism works correctly.
    """
    import os

    # Create temp storage
    storage = EventStorage(storage_dir=tmp_path / "analytics")

    # Disable telemetry
    os.environ["MYCELIUM_TELEMETRY"] = "0"

    try:
        telemetry = TelemetryCollector(storage)

        # Record some events (should be no-ops)
        telemetry.record_agent_discovery(
            operation="list_agents", duration_ms=1.0, agent_count=10
        )
        telemetry.record_agent_load(
            agent_id="test-agent",
            load_time_ms=2.0,
            content_size_bytes=1000,
            estimated_tokens=250,
        )

        # Verify no events were recorded
        events = storage.read_events()
        assert len(events) == 0, "Should not record events when telemetry is disabled"

    finally:
        # Clean up environment
        del os.environ["MYCELIUM_TELEMETRY"]


def test_storage_rotation(tmp_path):
    """Test that storage rotation works correctly.

    This test verifies that large event files are rotated automatically.
    """
    storage = EventStorage(storage_dir=tmp_path / "analytics")

    # Generate events until rotation occurs
    # Rotation threshold is 10MB, so we need to generate enough events
    large_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "test_event",
        "data": "x" * 10000,  # 10KB per event
    }

    # Write 1100 events (11MB worth)
    for i in range(1100):
        storage.append_event(large_event)

    # Check that rotation occurred
    storage_stats = storage.get_storage_stats()
    assert storage_stats["file_count"] > 1, "Should have rotated to multiple files"


def test_end_to_end_analytics_workflow(tmp_path):
    """Test complete end-to-end analytics workflow.

    This test verifies:
    1. Agent operations generate telemetry
    2. Telemetry is stored correctly
    3. Metrics can be analyzed
    4. Reports can be generated
    """
    # Setup temp storage
    storage = EventStorage(storage_dir=tmp_path / "analytics")
    telemetry = TelemetryCollector(storage)
    analyzer = MetricsAnalyzer(storage)

    # Simulate agent discovery operations
    telemetry.record_agent_discovery(
        operation="list_agents", duration_ms=0.08, agent_count=119
    )

    for i in range(10):
        telemetry.record_agent_discovery(
            operation="get_agent", duration_ms=0.03 if i < 8 else 1.2, cache_hit=i < 8
        )

    telemetry.record_agent_discovery(
        operation="search", duration_ms=6.5, agent_count=5
    )

    # Record agent loads
    for i in range(5):
        telemetry.record_agent_load(
            agent_id=f"agent-{i}",
            load_time_ms=1.0 + i * 0.1,
            content_size_bytes=5000,
            estimated_tokens=1250,
        )

    # Analyze metrics
    discovery_stats = analyzer.get_discovery_stats(days=1)
    assert discovery_stats["total_operations"] == 12, "Should have 12 operations"
    assert (
        discovery_stats["by_operation"]["list_agents"]["count"] == 1
    ), "Should have 1 list_agents"
    assert (
        discovery_stats["by_operation"]["get_agent"]["count"] == 10
    ), "Should have 10 get_agent"
    assert (
        discovery_stats["by_operation"]["search"]["count"] == 1
    ), "Should have 1 search"

    # Check cache performance
    cache_perf = analyzer.get_cache_performance(days=1)
    assert cache_perf["cache_hits"] == 8, "Should have 8 cache hits"
    assert cache_perf["cache_misses"] == 2, "Should have 2 cache misses"
    assert cache_perf["hit_rate_percentage"] == 80.0, "Should have 80% hit rate"

    # Check token savings
    token_savings = analyzer.get_token_savings(days=1)
    assert token_savings["total_agents_loaded"] == 5, "Should have loaded 5 agents"
    assert (
        token_savings["total_tokens_loaded"] == 6250
    ), "Should have loaded 6250 tokens"

    # Generate summary report
    summary = analyzer.get_summary_report(days=1)
    assert "discovery_stats" in summary, "Summary should include discovery stats"
    assert "cache_performance" in summary, "Summary should include cache performance"
    assert "token_savings" in summary, "Summary should include token savings"
    assert "trends" in summary, "Summary should include trends"


def test_privacy_guarantees(tmp_path):
    """Test that privacy guarantees are maintained.

    This test verifies:
    1. Agent IDs are hashed
    2. No file paths are recorded
    3. Only UTC timestamps
    4. No PII in events
    """
    storage = EventStorage(storage_dir=tmp_path / "analytics")
    telemetry = TelemetryCollector(storage)

    # Record an agent load with identifiable information
    telemetry.record_agent_load(
        agent_id="01-core-api-designer",  # Real agent ID
        load_time_ms=1.2,
        content_size_bytes=6424,
        estimated_tokens=1606,
    )

    # Read back events
    events = storage.read_events()
    assert len(events) == 1, "Should have 1 event"

    event = events[0]

    # Verify agent ID is hashed
    assert "agent_id" not in event, "Should not contain raw agent_id"
    assert "agent_id_hash" in event, "Should contain hashed agent_id"
    assert len(event["agent_id_hash"]) == 8, "Hash should be 8 characters"
    assert (
        event["agent_id_hash"] != "01-core-api-designer"
    ), "Should not contain raw ID"

    # Verify timestamp is UTC
    timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    assert timestamp.tzinfo is not None, "Should have timezone info"
    assert timestamp.tzinfo == timezone.utc, "Should be UTC timezone"

    # Verify no file paths
    event_str = json.dumps(event)
    assert "/home/" not in event_str, "Should not contain file paths"
    assert "C:\\" not in event_str, "Should not contain Windows paths"

    # Verify only allowed fields
    allowed_fields = {
        "timestamp",
        "event_type",
        "agent_id_hash",
        "load_time_ms",
        "content_size_bytes",
        "estimated_tokens",
    }
    event_fields = set(event.keys())
    assert event_fields.issubset(
        allowed_fields
    ), f"Should only have allowed fields, got extra: {event_fields - allowed_fields}"
