"""Integration tests for analytics and monitoring functionality."""

from pathlib import Path

import pytest

from mycelium_analytics import EventStorage, MetricsAnalyzer, TelemetryCollector


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics system using actual API."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> EventStorage:
        """Create temporary event storage."""
        return EventStorage(storage_dir=tmp_path / "events")

    @pytest.fixture
    def telemetry_collector(self, temp_storage: EventStorage) -> TelemetryCollector:
        """Create telemetry collector with temp storage."""
        return TelemetryCollector(storage=temp_storage)

    @pytest.fixture
    def metrics_analyzer(self, temp_storage: EventStorage) -> MetricsAnalyzer:
        """Create metrics analyzer with temp storage."""
        return MetricsAnalyzer(storage=temp_storage)

    def test_agent_discovery_recording(self, telemetry_collector: TelemetryCollector) -> None:
        """Test recording agent discovery operations."""
        # Record discovery operations
        for i in range(10):
            telemetry_collector.record_agent_discovery(
                operation="list_agents", duration_ms=10.0 + (i * 0.5), agent_count=42 + i
            )

        # Verify events were recorded
        events = telemetry_collector.storage.read_events(limit=20)
        assert len(events) == 10
        assert all(e["event_type"] == "agent_discovery" for e in events)

    def test_cache_performance_tracking(
        self, telemetry_collector: TelemetryCollector, metrics_analyzer: MetricsAnalyzer
    ) -> None:
        """Test cache performance analysis."""
        # Record cache hits and misses
        for _i in range(8):
            telemetry_collector.record_agent_discovery(
                operation="get_agent",
                duration_ms=0.8,
                cache_hit=True,
                agent_count=1,
            )
        for _i in range(2):
            telemetry_collector.record_agent_discovery(
                operation="get_agent",
                duration_ms=5.0,
                cache_hit=False,
                agent_count=1,
            )

        # Analyze cache performance
        stats = metrics_analyzer.get_cache_performance(days=1)

        assert stats["total_lookups"] == 10
        assert stats["cache_hits"] == 8
        assert stats["hit_rate_percentage"] == 80.0

    def test_discovery_stats_analysis(
        self, telemetry_collector: TelemetryCollector, metrics_analyzer: MetricsAnalyzer
    ) -> None:
        """Test discovery statistics analysis."""
        # Generate mixed operations
        for _ in range(5):
            telemetry_collector.record_agent_discovery(operation="list_agents", duration_ms=15.0, agent_count=42)
        for i in range(10):
            telemetry_collector.record_agent_discovery(
                operation="get_agent",
                duration_ms=1.0,
                cache_hit=(i % 2 == 0),
                agent_count=1,
            )

        # Get stats
        stats = metrics_analyzer.get_discovery_stats(days=1)

        assert stats["total_operations"] == 15
        assert "list_agents" in stats["by_operation"]
        assert "get_agent" in stats["by_operation"]
        assert stats["by_operation"]["list_agents"]["count"] == 5
        assert stats["by_operation"]["get_agent"]["count"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
