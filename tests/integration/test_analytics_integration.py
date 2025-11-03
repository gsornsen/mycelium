"""Integration tests for analytics and monitoring functionality."""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from mycelium_analytics import EventStorage, MetricsAnalyzer, TelemetryCollector
from scripts.agent_discovery import AgentDiscovery
from scripts.health_check import generate_health_report


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics system."""

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

    def test_end_to_end_event_flow(
        self, telemetry_collector: TelemetryCollector, metrics_analyzer: MetricsAnalyzer
    ) -> None:
        """Test complete flow from event collection to analysis."""
        # Collect events
        for i in range(100):
            telemetry_collector.track_event(
                event_type="api_call",
                properties={
                    "endpoint": f"/api/v1/endpoint{i % 5}",
                    "duration_ms": 100 + (i * 10),
                    "status_code": 200 if i % 10 != 0 else 500,
                    "user_id": f"user_{i % 20}",
                },
            )

        # Analyze metrics
        metrics = metrics_analyzer.compute_metrics(event_type="api_call", time_window=timedelta(hours=1))

        # Verify metrics
        assert metrics["total_events"] == 100
        assert metrics["error_rate"] == 0.1  # 10% errors
        assert "p95_duration" in metrics
        assert metrics["unique_users"] == 20

    def test_real_time_monitoring(self, telemetry_collector: TelemetryCollector) -> None:
        """Test real-time event monitoring capabilities."""
        events_received = []

        def event_handler(event: dict[str, Any]) -> None:
            """Handle incoming events."""
            events_received.append(event)

        # Subscribe to events
        telemetry_collector.subscribe("test_event", event_handler)

        # Send events
        for i in range(10):
            telemetry_collector.track_event(event_type="test_event", properties={"index": i})

        # Verify all events received
        assert len(events_received) == 10
        assert all(e["properties"]["index"] == i for i, e in enumerate(events_received))

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, telemetry_collector: TelemetryCollector) -> None:
        """Test handling of concurrent event streams."""

        async def generate_events(source: str, count: int) -> None:
            """Generate events from a source."""
            for i in range(count):
                telemetry_collector.track_event(
                    event_type="concurrent_test",
                    properties={"source": source, "index": i},
                )
                await asyncio.sleep(0.001)

        # Generate events from multiple sources concurrently
        tasks = [generate_events(f"source_{i}", 50) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all events captured
        events = telemetry_collector.get_events(event_type="concurrent_test")
        assert len(events) == 250  # 5 sources * 50 events

        # Verify no event loss
        source_counts = {}
        for event in events:
            source = event["properties"]["source"]
            source_counts[source] = source_counts.get(source, 0) + 1

        assert all(count == 50 for count in source_counts.values())

    def test_metrics_aggregation_pipeline(self, temp_storage: EventStorage, metrics_analyzer: MetricsAnalyzer) -> None:
        """Test metrics aggregation across different dimensions."""
        # Generate diverse events
        event_types = ["api_call", "db_query", "cache_hit", "error"]
        for event_type in event_types:
            for i in range(100):
                temp_storage.store_event(
                    {
                        "event_type": event_type,
                        "timestamp": datetime.now(),
                        "properties": {
                            "duration_ms": 50 + (i * 2),
                            "success": i % 5 != 0,
                            "service": f"service_{i % 3}",
                        },
                    }
                )

        # Aggregate by event type
        type_metrics = metrics_analyzer.aggregate_by_dimension(dimension="event_type", metric="count")
        assert all(type_metrics[et] == 100 for et in event_types)

        # Aggregate by service
        service_metrics = metrics_analyzer.aggregate_by_dimension(dimension="service", metric="avg_duration")
        assert len(service_metrics) == 3

        # Time series aggregation
        time_series = metrics_analyzer.generate_time_series(metric="count", interval="1m")
        assert len(time_series) > 0

    def test_anomaly_detection(self, metrics_analyzer: MetricsAnalyzer) -> None:
        """Test anomaly detection in metrics."""
        # Generate normal baseline
        for i in range(1000):
            metrics_analyzer.storage.store_event(
                {
                    "event_type": "performance",
                    "timestamp": datetime.now() - timedelta(minutes=1000 - i),
                    "properties": {"latency_ms": 100 + (i % 20)},
                }
            )

        # Inject anomalies
        anomaly_times = []
        for i in range(10):
            timestamp = datetime.now() - timedelta(minutes=500 - (i * 50))
            anomaly_times.append(timestamp)
            metrics_analyzer.storage.store_event(
                {
                    "event_type": "performance",
                    "timestamp": timestamp,
                    "properties": {"latency_ms": 1000},  # 10x normal
                }
            )

        # Detect anomalies
        anomalies = metrics_analyzer.detect_anomalies(metric="latency_ms", sensitivity=2.0)

        # Verify anomalies detected
        assert len(anomalies) >= 5  # Should detect at least half
        for anomaly in anomalies:
            assert anomaly["severity"] in ["high", "medium", "low"]
            assert "timestamp" in anomaly
            assert "value" in anomaly

    def test_dashboard_data_generation(self, metrics_analyzer: MetricsAnalyzer) -> None:
        """Test generation of dashboard-ready data."""
        # Generate sample data
        for i in range(24):  # 24 hours of data
            for j in range(60):  # Events per hour
                metrics_analyzer.storage.store_event(
                    {
                        "event_type": "user_action",
                        "timestamp": datetime.now() - timedelta(hours=24 - i, minutes=j),
                        "properties": {
                            "action": ["click", "view", "submit"][j % 3],
                            "page": f"page_{j % 10}",
                            "duration_ms": 100 + (j * 5),
                        },
                    }
                )

        # Generate dashboard data
        dashboard = metrics_analyzer.generate_dashboard_data()

        # Verify dashboard structure
        assert "summary" in dashboard
        assert "time_series" in dashboard
        assert "top_pages" in dashboard
        assert "action_breakdown" in dashboard

        # Verify summary stats
        summary = dashboard["summary"]
        assert summary["total_events"] == 24 * 60
        assert "avg_duration_ms" in summary
        assert "unique_pages" in summary

    def test_data_export_formats(self, temp_storage: EventStorage) -> None:
        """Test exporting data in various formats."""
        # Generate test data
        for i in range(100):
            temp_storage.store_event(
                {
                    "event_type": "test_event",
                    "timestamp": datetime.now(),
                    "properties": {"value": i},
                }
            )

        # Export as JSON
        json_export = temp_storage.export_json(event_type="test_event")
        assert len(json.loads(json_export)) == 100

        # Export as CSV
        csv_export = temp_storage.export_csv(event_type="test_event")
        lines = csv_export.strip().split("\n")
        assert len(lines) == 101  # Header + 100 rows

        # Export as Parquet (if supported)
        if hasattr(temp_storage, "export_parquet"):
            parquet_path = temp_storage.export_parquet(event_type="test_event")
            df = pd.read_parquet(parquet_path)
            assert len(df) == 100

    def test_retention_policy(self, temp_storage: EventStorage) -> None:
        """Test data retention policy enforcement."""
        # Set retention policy to 7 days
        temp_storage.set_retention_policy(days=7)

        # Generate old and new events
        for i in range(100):
            # Old events (should be deleted)
            temp_storage.store_event(
                {
                    "event_type": "old_event",
                    "timestamp": datetime.now() - timedelta(days=10),
                    "properties": {"index": i},
                }
            )
            # Recent events (should be kept)
            temp_storage.store_event(
                {
                    "event_type": "recent_event",
                    "timestamp": datetime.now() - timedelta(days=3),
                    "properties": {"index": i},
                }
            )

        # Apply retention policy
        deleted_count = temp_storage.apply_retention_policy()

        # Verify old events deleted
        assert deleted_count == 100
        old_events = temp_storage.get_events(event_type="old_event")
        assert len(old_events) == 0

        # Verify recent events kept
        recent_events = temp_storage.get_events(event_type="recent_event")
        assert len(recent_events) == 100

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self) -> None:
        """Test health monitoring across system components."""
        with patch("scripts.health_check.check_service_health") as mock_check:
            # Simulate service health checks
            mock_check.side_effect = [
                {"status": "healthy", "latency_ms": 10},
                {"status": "degraded", "latency_ms": 500},
                {"status": "unhealthy", "error": "Connection timeout"},
            ]

            # Generate health report
            report = await generate_health_report(services=["api", "database", "cache"])

            # Verify report structure
            assert report["overall_status"] in ["healthy", "degraded", "unhealthy"]
            assert len(report["services"]) == 3
            assert report["timestamp"]

            # Verify service statuses
            assert report["services"]["api"]["status"] == "healthy"
            assert report["services"]["database"]["status"] == "degraded"
            assert report["services"]["cache"]["status"] == "unhealthy"

    def test_agent_discovery_integration(self) -> None:
        """Test agent discovery and registration."""
        discovery = AgentDiscovery()

        # Register agents
        agents = [
            {"id": "agent-1", "type": "backend", "capabilities": ["python", "api"]},
            {"id": "agent-2", "type": "frontend", "capabilities": ["react", "css"]},
            {"id": "agent-3", "type": "database", "capabilities": ["postgres", "redis"]},
        ]

        for agent in agents:
            discovery.register_agent(**agent)

        # Discover agents by capability
        python_agents = discovery.find_agents_with_capability("python")
        assert len(python_agents) == 1
        assert python_agents[0]["id"] == "agent-1"

        # Discover agents by type
        frontend_agents = discovery.find_agents_by_type("frontend")
        assert len(frontend_agents) == 1
        assert frontend_agents[0]["id"] == "agent-2"

        # Get all agents
        all_agents = discovery.get_all_agents()
        assert len(all_agents) == 3

    def test_performance_benchmarking(self, telemetry_collector: TelemetryCollector) -> None:
        """Test performance benchmarking capabilities."""
        # Benchmark event ingestion
        start_time = time.time()
        events_count = 10000

        for i in range(events_count):
            telemetry_collector.track_event(
                event_type="benchmark",
                properties={"index": i, "data": "x" * 100},
            )

        ingestion_time = time.time() - start_time
        events_per_second = events_count / ingestion_time

        # Verify performance thresholds
        assert events_per_second > 1000  # Should handle >1000 events/sec
        assert ingestion_time < 30  # Should complete within 30 seconds

        # Benchmark query performance
        start_time = time.time()
        retrieved_events = telemetry_collector.get_events(event_type="benchmark", limit=1000)
        query_time = time.time() - start_time

        assert len(retrieved_events) == 1000
        assert query_time < 1.0  # Query should complete within 1 second

    def test_data_consistency(self, temp_storage: EventStorage) -> None:
        """Test data consistency under various operations."""
        # Store events
        original_events = []
        for i in range(100):
            event = {
                "event_type": "consistency_test",
                "timestamp": datetime.now(),
                "properties": {"id": i, "value": f"value_{i}"},
            }
            temp_storage.store_event(event)
            original_events.append(event)

        # Verify all events stored
        stored_events = temp_storage.get_events(event_type="consistency_test")
        assert len(stored_events) == 100

        # Verify data integrity
        for original, stored in zip(original_events, stored_events, strict=False):
            assert stored["properties"]["id"] == original["properties"]["id"]
            assert stored["properties"]["value"] == original["properties"]["value"]

        # Test update operations (if supported)
        if hasattr(temp_storage, "update_event"):
            temp_storage.update_event(
                event_id=stored_events[0]["id"],
                properties={"value": "updated_value"},
            )

            updated_event = temp_storage.get_event(event_id=stored_events[0]["id"])
            assert updated_event["properties"]["value"] == "updated_value"

    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled",
    )
    def test_external_service_integration(self) -> None:
        """Test integration with external monitoring services."""
        # This would test real integrations with services like:
        # - Prometheus
        # - Grafana
        # - DataDog
        # - New Relic
        # etc.
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
