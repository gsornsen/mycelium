"""Unit tests for MetricsAnalyzer.

Tests:
    - Discovery statistics computation
    - Percentile calculations
    - Token savings analysis
    - Cache performance metrics
    - Performance trends analysis
    - Summary report generation
    - Edge cases (empty data, single data points)

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mycelium_analytics.metrics import MetricsAnalyzer
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


@pytest.fixture
def analyzer(storage):
    """Create MetricsAnalyzer instance for testing."""
    return MetricsAnalyzer(storage)


class TestMetricsAnalyzerBasics:
    """Test basic metrics analyzer functionality."""

    def test_init(self, storage):
        """Test analyzer initialization."""
        analyzer = MetricsAnalyzer(storage)
        assert analyzer.storage is storage

    def test_percentile_calculation(self, analyzer):
        """Test percentile calculation with various inputs."""
        # Simple case: 5 elements
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert analyzer._percentile(data, 0) == 1.0
        assert analyzer._percentile(data, 50) == 3.0
        assert analyzer._percentile(data, 100) == 5.0

        # Test interpolation (p95)
        assert analyzer._percentile(data, 95) == 4.8

        # Single element
        assert analyzer._percentile([42.0], 50) == 42.0

        # Empty list
        assert analyzer._percentile([], 50) == 0.0

    def test_percentile_with_unsorted_data(self, analyzer):
        """Test percentile calculation handles unsorted data."""
        data = [5.0, 1.0, 3.0, 2.0, 4.0]
        assert analyzer._percentile(data, 50) == 3.0
        assert analyzer._percentile(data, 95) == 4.8

    def test_percentile_with_duplicates(self, analyzer):
        """Test percentile calculation with duplicate values."""
        data = [1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0]
        result = analyzer._percentile(data, 50)
        assert isinstance(result, float)
        assert result >= 2.0
        assert result <= 3.0


class TestDiscoveryStats:
    """Test agent discovery statistics computation."""

    def test_get_discovery_stats_empty(self, analyzer):
        """Test discovery stats with no data."""
        stats = analyzer.get_discovery_stats(days=7)
        assert stats["total_operations"] == 0
        assert stats["by_operation"] == {}
        assert stats["overall"] == {}

    def test_get_discovery_stats_basic(self, analyzer, storage):
        """Test basic discovery statistics computation."""
        now = datetime.now(timezone.utc)

        # Add some test events
        events = [
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 42,
            },
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 15.0,
                "cache_hit": False,
                "agent_count": 42,
            },
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "get_agent",
                "duration_ms": 5.0,
                "cache_hit": True,
                "agent_count": 1,
            },
        ]

        for event in events:
            storage.append_event(event)

        stats = analyzer.get_discovery_stats(days=7)

        # Check overall stats
        assert stats["total_operations"] == 3
        assert "overall" in stats
        assert stats["overall"]["p50_ms"] > 0
        assert stats["overall"]["p95_ms"] > 0
        assert stats["overall"]["avg_ms"] > 0

        # Check operation breakdown
        assert "by_operation" in stats
        assert "list_agents" in stats["by_operation"]
        assert stats["by_operation"]["list_agents"]["count"] == 2

    def test_get_discovery_stats_by_operation(self, analyzer, storage):
        """Test discovery stats grouped by operation."""
        now = datetime.now(timezone.utc)

        # Add multiple operations
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "get_agent",
                "duration_ms": 2.0,
                "cache_hit": True,
                "agent_count": 1,
            }
        )
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "search",
                "duration_ms": 8.0,
                "cache_hit": False,
                "agent_count": 5,
            }
        )

        stats = analyzer.get_discovery_stats(days=7)

        assert len(stats["by_operation"]) == 3
        assert "list_agents" in stats["by_operation"]
        assert "get_agent" in stats["by_operation"]
        assert "search" in stats["by_operation"]

    def test_get_discovery_stats_percentiles(self, analyzer, storage):
        """Test percentile calculation in discovery stats."""
        now = datetime.now(timezone.utc)

        # Add events with known durations
        durations = [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0, 50.0, 100.0]
        for duration in durations:
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": duration,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        stats = analyzer.get_discovery_stats(days=7)

        overall = stats["overall"]
        # p50 should be around median (between 5 and 10)
        assert 5.0 <= overall["p50_ms"] <= 10.0
        # p95 should be high (near 100)
        assert overall["p95_ms"] > 50.0
        # p99 should be very high (near 100)
        assert overall["p99_ms"] >= overall["p95_ms"]

    def test_get_discovery_stats_cache_hit_rate(self, analyzer, storage):
        """Test cache hit rate calculation for get_agent operations."""
        now = datetime.now(timezone.utc)

        # Add 7 cache hits and 3 misses (70% hit rate)
        for _i in range(7):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "get_agent",
                    "duration_ms": 1.0,
                    "cache_hit": True,
                    "agent_count": 1,
                }
            )

        for _i in range(3):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "get_agent",
                    "duration_ms": 5.0,
                    "cache_hit": False,
                    "agent_count": 1,
                }
            )

        stats = analyzer.get_discovery_stats(days=7)

        get_agent_stats = stats["by_operation"]["get_agent"]
        assert get_agent_stats["count"] == 10
        assert get_agent_stats["cache_hit_rate"] == 70.0


class TestTokenSavings:
    """Test token consumption statistics."""

    def test_get_token_savings_empty(self, analyzer):
        """Test token savings with no data."""
        stats = analyzer.get_token_savings(days=7)
        assert stats["total_agents_loaded"] == 0
        assert stats["total_tokens_loaded"] == 0
        assert stats["avg_tokens_per_agent"] == 0.0
        assert stats["estimated_baseline_tokens"] == 0
        assert stats["estimated_savings_tokens"] == 0
        assert stats["savings_percentage"] == 0.0

    def test_get_token_savings_basic(self, analyzer, storage):
        """Test basic token savings calculation."""
        now = datetime.now(timezone.utc)

        # Add agent load events
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_load",
                "agent_name_hash": "abc123",
                "estimated_tokens": 450,
            }
        )
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_load",
                "agent_name_hash": "def456",
                "estimated_tokens": 500,
            }
        )

        stats = analyzer.get_token_savings(days=7)

        assert stats["total_agents_loaded"] == 2
        assert stats["total_tokens_loaded"] == 950
        assert stats["avg_tokens_per_agent"] == 475.0

    def test_get_token_savings_phase1_impact(self, analyzer, storage):
        """Test Phase 1 lazy loading savings calculation."""
        now = datetime.now(timezone.utc)

        # Simulate loading only 10 agents (instead of all 119)
        for i in range(10):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_load",
                    "agent_name_hash": f"agent{i}",
                    "estimated_tokens": 450,
                }
            )

        stats = analyzer.get_token_savings(days=7)

        # Total tokens loaded: 10 * 450 = 4,500
        assert stats["total_tokens_loaded"] == 4500

        # Baseline: 119 * 450 = 53,550
        assert stats["estimated_baseline_tokens"] == 53550

        # Savings: 53,550 - 4,500 = 49,050 (91.6%)
        assert stats["estimated_savings_tokens"] == 49050
        assert 91.0 <= stats["savings_percentage"] <= 92.0


class TestCachePerformance:
    """Test cache performance metrics."""

    def test_get_cache_performance_empty(self, analyzer):
        """Test cache performance with no data."""
        stats = analyzer.get_cache_performance(days=7)
        assert stats["total_lookups"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percentage"] == 0.0
        assert stats["avg_hit_latency_ms"] == 0.0
        assert stats["avg_miss_latency_ms"] == 0.0

    def test_get_cache_performance_basic(self, analyzer, storage):
        """Test basic cache performance metrics."""
        now = datetime.now(timezone.utc)

        # Add cache hits (fast)
        for _i in range(8):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "get_agent",
                    "duration_ms": 0.5,
                    "cache_hit": True,
                    "agent_count": 1,
                }
            )

        # Add cache misses (slower)
        for _i in range(2):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "get_agent",
                    "duration_ms": 5.0,
                    "cache_hit": False,
                    "agent_count": 1,
                }
            )

        stats = analyzer.get_cache_performance(days=7)

        assert stats["total_lookups"] == 10
        assert stats["cache_hits"] == 8
        assert stats["cache_misses"] == 2
        assert stats["hit_rate_percentage"] == 80.0
        assert stats["avg_hit_latency_ms"] == 0.5
        assert stats["avg_miss_latency_ms"] == 5.0

    def test_get_cache_performance_hit_rate(self, analyzer, storage):
        """Test cache hit rate calculation accuracy."""
        now = datetime.now(timezone.utc)

        # 100% hit rate
        for _i in range(5):
            storage.append_event(
                {
                    "timestamp": now.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "get_agent",
                    "duration_ms": 1.0,
                    "cache_hit": True,
                    "agent_count": 1,
                }
            )

        stats = analyzer.get_cache_performance(days=7)
        assert stats["hit_rate_percentage"] == 100.0

    def test_get_cache_performance_ignores_other_operations(self, analyzer, storage):
        """Test that cache performance only considers get_agent operations."""
        now = datetime.now(timezone.utc)

        # Add get_agent with cache hit
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "get_agent",
                "duration_ms": 1.0,
                "cache_hit": True,
                "agent_count": 1,
            }
        )

        # Add list_agents (no cache_hit field)
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        stats = analyzer.get_cache_performance(days=7)

        # Only get_agent should be counted
        assert stats["total_lookups"] == 1
        assert stats["cache_hits"] == 1


class TestPerformanceTrends:
    """Test performance trends analysis."""

    def test_get_performance_trends_empty(self, analyzer):
        """Test trends with no data."""
        trends = analyzer.get_performance_trends(days=7)
        assert trends["daily_stats"] == []
        assert trends["trend"] == "stable"

    def test_get_performance_trends_daily_grouping(self, analyzer, storage):
        """Test events grouped by day."""
        # Add events across multiple days
        base_date = datetime.now(timezone.utc)

        for day_offset in range(3):
            event_date = base_date - timedelta(days=day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 10.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        trends = analyzer.get_performance_trends(days=7)

        # Should have 3 days of data
        assert len(trends["daily_stats"]) == 3

        # Each day should have required fields
        for day_stat in trends["daily_stats"]:
            assert "date" in day_stat
            assert "operations" in day_stat
            assert "avg_latency_ms" in day_stat
            assert "cache_hit_rate" in day_stat

    def test_get_performance_trends_improvement(self, analyzer, storage):
        """Test trend detection for improving performance."""
        base_date = datetime.now(timezone.utc)

        # First half: slow (20ms avg)
        for day_offset in range(4):
            event_date = base_date - timedelta(days=7 - day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 20.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        # Second half: fast (5ms avg)
        for day_offset in range(4):
            event_date = base_date - timedelta(days=3 - day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 5.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        trends = analyzer.get_performance_trends(days=7)

        # Should detect improvement
        assert trends["trend"] == "improving"

    def test_get_performance_trends_degradation(self, analyzer, storage):
        """Test trend detection for degrading performance."""
        base_date = datetime.now(timezone.utc)

        # First half: fast (5ms avg)
        for day_offset in range(4):
            event_date = base_date - timedelta(days=7 - day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 5.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        # Second half: slow (20ms avg)
        for day_offset in range(4):
            event_date = base_date - timedelta(days=3 - day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 20.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        trends = analyzer.get_performance_trends(days=7)

        # Should detect degradation
        assert trends["trend"] == "degrading"

    def test_get_performance_trends_stable(self, analyzer, storage):
        """Test trend detection for stable performance."""
        base_date = datetime.now(timezone.utc)

        # Consistent performance across all days
        for day_offset in range(7):
            event_date = base_date - timedelta(days=day_offset)
            storage.append_event(
                {
                    "timestamp": event_date.isoformat(),
                    "event_type": "agent_discovery",
                    "operation": "list_agents",
                    "duration_ms": 10.0,
                    "cache_hit": False,
                    "agent_count": 119,
                }
            )

        trends = analyzer.get_performance_trends(days=7)

        # Should detect stability
        assert trends["trend"] == "stable"


class TestSummaryReport:
    """Test comprehensive summary report generation."""

    def test_get_summary_report_structure(self, analyzer):
        """Test summary report has all required sections."""
        report = analyzer.get_summary_report(days=7)

        assert "report_period_days" in report
        assert "generated_at" in report
        assert "discovery_stats" in report
        assert "token_savings" in report
        assert "cache_performance" in report
        assert "trends" in report

        assert report["report_period_days"] == 7

        # Verify timestamp format
        timestamp = datetime.fromisoformat(report["generated_at"])
        assert timestamp.tzinfo is not None

    def test_get_summary_report_with_data(self, analyzer, storage):
        """Test summary report with real data."""
        now = datetime.now(timezone.utc)

        # Add various events
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_load",
                "agent_name_hash": "abc123",
                "estimated_tokens": 450,
            }
        )

        report = analyzer.get_summary_report(days=7)

        # Verify all sections have data
        assert report["discovery_stats"]["total_operations"] > 0
        assert report["token_savings"]["total_agents_loaded"] > 0

    def test_get_summary_report_custom_period(self, analyzer):
        """Test summary report with custom time period."""
        report = analyzer.get_summary_report(days=30)

        assert report["report_period_days"] == 30


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_events_ignored(self, analyzer, storage):
        """Test that malformed events don't break analysis."""
        now = datetime.now(timezone.utc)

        # Add valid event
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        # Add malformed event (missing duration_ms)
        storage.append_event(
            {
                "timestamp": now.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        stats = analyzer.get_discovery_stats(days=7)

        # Should still process the valid event
        assert stats["total_operations"] == 2  # Both events counted
        # But percentiles only use events with duration_ms
        assert stats["overall"]["avg_ms"] == 10.0

    def test_future_date_filter(self, analyzer, storage):
        """Test that future dates are handled correctly."""
        future = datetime.now(timezone.utc) + timedelta(days=1)

        storage.append_event(
            {
                "timestamp": future.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        # Query for last 7 days should include future event
        stats = analyzer.get_discovery_stats(days=7)
        assert stats["total_operations"] == 1

    def test_old_events_filtered(self, analyzer, storage):
        """Test that events outside time range are filtered."""
        old = datetime.now(timezone.utc) - timedelta(days=30)
        recent = datetime.now(timezone.utc)

        # Add old event
        storage.append_event(
            {
                "timestamp": old.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        # Add recent event
        storage.append_event(
            {
                "timestamp": recent.isoformat(),
                "event_type": "agent_discovery",
                "operation": "list_agents",
                "duration_ms": 10.0,
                "cache_hit": False,
                "agent_count": 119,
            }
        )

        # Query for last 7 days should only get recent event
        stats = analyzer.get_discovery_stats(days=7)
        assert stats["total_operations"] == 1
