# Source: projects/backlog/OPTION_A_AGENT_USAGE_ANALYTICS.md
# Line: 833
# Valid syntax: True
# Has imports: True
# Has assignments: True

"""Unit tests for UsageAnalyzer."""

import pytest
from datetime import datetime, timezone, timedelta
from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer


@pytest.fixture
def storage_with_usage_data(tmp_path):
    """Create storage with sample usage events."""
    storage = EventStorage(storage_dir=tmp_path)

    # Add sample events
    for i in range(10):
        storage.append_event({
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
            "event_type": "agent_usage",
            "agent_id_hash": "f2f2cbc2",
            "category": "core-development",
            "session_duration_seconds": 1200,
            "effectiveness_score": 4.5,
        })

    return storage


def test_popularity_ranking(storage_with_usage_data):
    """Test popularity ranking calculation."""
    analyzer = UsageAnalyzer(storage_with_usage_data)
    ranking = analyzer.get_popularity_ranking(days=30)

    assert len(ranking) > 0
    assert ranking[0]["usage_count"] == 10
    assert ranking[0]["agent_id_hash"] == "f2f2cbc2"


def test_category_breakdown(storage_with_usage_data):
    """Test category breakdown."""
    analyzer = UsageAnalyzer(storage_with_usage_data)
    breakdown = analyzer.get_category_breakdown(days=30)

    assert "core-development" in breakdown
    assert breakdown["core-development"] == 10


def test_usage_heatmap(storage_with_usage_data):
    """Test heatmap generation."""
    analyzer = UsageAnalyzer(storage_with_usage_data)
    heatmap = analyzer.get_usage_heatmap(days=30)

    assert "monday" in heatmap
    assert all(0 <= hour <= 23 for hours in heatmap.values() for hour in hours.keys())