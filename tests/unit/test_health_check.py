"""Tests for health check report generation.

Tests the health check script's ability to format and display performance
metrics from telemetry data.

Author: @cli-developer
Phase: 2 Performance Analytics - Day 2
Date: 2025-10-18
"""

import pytest
from datetime import datetime, timezone, timedelta

from scripts.health_check import format_duration, generate_health_report, status_icon


def test_format_duration_sub_millisecond():
    """Test duration formatting for sub-millisecond values."""
    assert format_duration(0.05) == "0.05ms"
    assert format_duration(0.99) == "0.99ms"


def test_format_duration_milliseconds():
    """Test duration formatting for millisecond values."""
    assert format_duration(1.5) == "1.5ms"
    assert format_duration(42.0) == "42.0ms"
    assert format_duration(999.9) == "999.9ms"


def test_format_duration_seconds():
    """Test duration formatting for second values."""
    assert format_duration(1000) == "1.00s"
    assert format_duration(1500) == "1.50s"
    assert format_duration(5000) == "5.00s"


def test_status_icon_lower_is_better_pass():
    """Test status icon when lower is better and value passes."""
    # Value well below target
    assert status_icon(5, 10, lower_is_better=True) == "✅"
    assert status_icon(1, 10, lower_is_better=True) == "✅"


def test_status_icon_lower_is_better_warn():
    """Test status icon when lower is better and value warns."""
    # Value slightly above target but within 1.5x
    assert status_icon(12, 10, lower_is_better=True) == "⚠️"
    assert status_icon(14, 10, lower_is_better=True) == "⚠️"


def test_status_icon_lower_is_better_fail():
    """Test status icon when lower is better and value fails."""
    # Value above 1.5x target
    assert status_icon(20, 10, lower_is_better=True) == "❌"
    assert status_icon(50, 10, lower_is_better=True) == "❌"


def test_status_icon_higher_is_better_pass():
    """Test status icon when higher is better and value passes."""
    # Value above target
    assert status_icon(85, 80, lower_is_better=False) == "✅"
    assert status_icon(95, 80, lower_is_better=False) == "✅"


def test_status_icon_higher_is_better_warn():
    """Test status icon when higher is better and value warns."""
    # Value slightly below target but within 0.75x
    assert status_icon(65, 80, lower_is_better=False) == "⚠️"
    assert status_icon(70, 80, lower_is_better=False) == "⚠️"


def test_status_icon_higher_is_better_fail():
    """Test status icon when higher is better and value fails."""
    # Value below 0.75x target
    assert status_icon(50, 80, lower_is_better=False) == "❌"
    assert status_icon(40, 80, lower_is_better=False) == "❌"


def test_generate_health_report_empty_data():
    """Test health report generation with no telemetry data."""
    report = generate_health_report(days=7)

    # Should still generate a report structure
    assert "Mycelium Performance Health Check" in report
    assert "AGENT DISCOVERY PERFORMANCE" in report
    assert "CACHE PERFORMANCE" in report
    assert "TOKEN SAVINGS" in report
    assert "PERFORMANCE TREND" in report
    assert "STORAGE HEALTH" in report


def test_generate_health_report_structure():
    """Test that health report has expected structure."""
    report = generate_health_report(days=7)

    # Check for major sections
    assert "📊 AGENT DISCOVERY PERFORMANCE" in report
    assert "⚡ CACHE PERFORMANCE" in report
    assert "💾 TOKEN SAVINGS" in report
    assert "📈 PERFORMANCE TREND" in report
    assert "🗄️  STORAGE HEALTH" in report
    assert "💡 Tips:" in report

    # Check for box drawing characters
    assert "╔═" in report
    assert "╚═" in report
    assert "━" in report


def test_generate_health_report_days_parameter():
    """Test that days parameter is reflected in report."""
    report_7 = generate_health_report(days=7)
    report_30 = generate_health_report(days=30)

    assert "Last 7 Days" in report_7
    assert "Last 30 Days" in report_30


def test_generate_health_report_no_exceptions():
    """Test that report generation doesn't raise exceptions."""
    try:
        report = generate_health_report(days=7)
        assert isinstance(report, str)
        assert len(report) > 0
    except Exception as e:
        pytest.fail(f"Health report generation raised exception: {e}")


def test_generate_health_report_tips_section():
    """Test that tips section is included."""
    report = generate_health_report(days=7)

    assert "💡 Tips:" in report
    # Should have at least one tip line
    assert "Run `uv run python -m mycelium_analytics report`" in report


def test_generate_health_report_storage_section():
    """Test that storage section displays file/event counts."""
    report = generate_health_report(days=7)

    # Should show storage stats
    assert "Event Files:" in report
    assert "Total Events:" in report
    assert "Storage Size:" in report


def test_format_duration_edge_cases():
    """Test duration formatting edge cases."""
    assert format_duration(0.0) == "0.00ms"
    assert format_duration(1.0) == "1.0ms"
    assert format_duration(999.99) == "1000.0ms"


def test_status_icon_exact_target():
    """Test status icon when value equals target."""
    # Lower is better: equal to target should fail (not below)
    assert status_icon(10, 10, lower_is_better=True) == "⚠️"

    # Higher is better: equal to target should fail (not above)
    assert status_icon(80, 80, lower_is_better=False) == "⚠️"


def test_generate_health_report_unicode_support():
    """Test that report includes expected Unicode characters."""
    report = generate_health_report(days=7)

    # Check for emojis
    assert "🔍" in report  # Magnifying glass
    assert "📊" in report  # Bar chart
    assert "⚡" in report  # Lightning bolt
    assert "💾" in report  # Floppy disk
    assert "📈" in report  # Chart increasing
    assert "🗄️" in report  # File cabinet
    assert "💡" in report  # Light bulb

    # Check for box drawing
    assert "╔" in report
    assert "╚" in report
    assert "═" in report
    assert "━" in report
