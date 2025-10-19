"""Mycelium Analytics - Privacy-first performance telemetry.

Lightweight telemetry system for tracking Mycelium performance metrics
in production use. Local-only storage with privacy guarantees.

Features:
    - Thread-safe JSONL event storage
    - Non-blocking event collection
    - Privacy-first (no PII, paths, or command content)
    - Automatic log rotation
    - Graceful degradation

Example:
    >>> from mycelium_analytics import EventStorage, TelemetryCollector
    >>> storage = EventStorage()
    >>> collector = TelemetryCollector(storage)
    >>> collector.record_agent_discovery(
    ...     operation="list_agents",
    ...     duration_ms=15.2,
    ...     agent_count=42
    ... )

Components:
    - EventStorage: Thread-safe JSONL storage backend
    - TelemetryCollector: Event collection with privacy guarantees
    - MetricsAnalyzer: Performance metrics analysis (Day 2)

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

from mycelium_analytics.metrics import MetricsAnalyzer
from mycelium_analytics.storage import EventStorage
from mycelium_analytics.telemetry import TelemetryCollector

__all__ = [
    "EventStorage",
    "TelemetryCollector",
    "MetricsAnalyzer",
]

__version__ = "0.1.0"
