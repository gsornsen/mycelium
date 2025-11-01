"""Metrics analysis engine for Mycelium performance analytics.

Analyzes telemetry events to compute performance statistics including percentiles,
cache hit rates, token savings, and performance trends.

Features:
    - Agent discovery latency percentiles (p50, p95, p99)
    - Cache hit rate analysis
    - Token consumption statistics
    - Performance trend analysis
    - Daily performance grouping

Example:
    >>> from mycelium_analytics.storage import EventStorage
    >>> from mycelium_analytics.metrics import MetricsAnalyzer
    >>> analyzer = MetricsAnalyzer(EventStorage())
    >>> stats = analyzer.get_discovery_stats(days=7)
    >>> stats['overall']['p95_ms']
    18.5

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import statistics
from datetime import datetime, timedelta, timezone
from typing import Any

from mycelium_analytics.storage import EventStorage


class MetricsAnalyzer:
    """Analyzes telemetry events to compute performance metrics.

    Provides statistical analysis of telemetry data including percentile
    calculations, cache performance, token savings, and performance trends.

    Attributes:
        storage: EventStorage backend for reading events

    Example:
        >>> storage = EventStorage()
        >>> analyzer = MetricsAnalyzer(storage)
        >>> stats = analyzer.get_discovery_stats(days=7)
        >>> 'total_operations' in stats
        True
    """

    def __init__(self, storage: EventStorage):
        """Initialize metrics analyzer.

        Args:
            storage: EventStorage backend for reading events

        Example:
            >>> storage = EventStorage()
            >>> analyzer = MetricsAnalyzer(storage)
            >>> analyzer.storage is not None
            True
        """
        self.storage = storage

    def get_discovery_stats(self, days: int = 7) -> dict[str, Any]:
        """Compute agent discovery statistics.

        Analyzes agent_discovery events to compute:
            - p50, p95, p99 latencies for each operation
            - Cache hit rate for get_agent operations
            - Overall latency percentiles
            - Operation frequency distribution

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with discovery statistics:
            {
                "total_operations": int,
                "by_operation": {
                    "list_agents": {
                        "count": int,
                        "p50_ms": float,
                        "p95_ms": float,
                        "p99_ms": float,
                        "avg_ms": float
                    },
                    "get_agent": {
                        "count": int,
                        "p50_ms": float,
                        "p95_ms": float,
                        "p99_ms": float,
                        "avg_ms": float,
                        "cache_hit_rate": float
                    },
                    "search": {...}
                },
                "overall": {
                    "p50_ms": float,
                    "p95_ms": float,
                    "p99_ms": float,
                    "avg_ms": float
                }
            }

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> stats = analyzer.get_discovery_stats(days=7)
            >>> 'total_operations' in stats
            True
            >>> 'by_operation' in stats
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        # Filter for agent_discovery events
        discovery_events = [e for e in events if e.get("event_type") == "agent_discovery"]

        if not discovery_events:
            return {
                "total_operations": 0,
                "by_operation": {},
                "overall": {},
            }

        # Group by operation type
        by_operation: dict[str, list[dict[str, Any]]] = {}
        for event in discovery_events:
            op = event.get("operation", "unknown")
            if op not in by_operation:
                by_operation[op] = []
            by_operation[op].append(event)

        # Compute stats for each operation
        operation_stats = {}
        all_durations = []

        for operation, events_list in by_operation.items():
            durations = [e["duration_ms"] for e in events_list if "duration_ms" in e]
            all_durations.extend(durations)

            stats = {
                "count": len(events_list),
                "p50_ms": self._percentile(durations, 50),
                "p95_ms": self._percentile(durations, 95),
                "p99_ms": self._percentile(durations, 99),
                "avg_ms": (round(statistics.mean(durations), 2) if durations else 0.0),
            }

            # Add cache hit rate for get_agent
            if operation == "get_agent":
                cache_hits = sum(1 for e in events_list if e.get("cache_hit", False))
                stats["cache_hit_rate"] = round((cache_hits / len(events_list)) * 100, 2) if events_list else 0.0

            operation_stats[operation] = stats

        # Overall stats
        overall = {
            "p50_ms": self._percentile(all_durations, 50),
            "p95_ms": self._percentile(all_durations, 95),
            "p99_ms": self._percentile(all_durations, 99),
            "avg_ms": (round(statistics.mean(all_durations), 2) if all_durations else 0.0),
        }

        return {
            "total_operations": len(discovery_events),
            "by_operation": operation_stats,
            "overall": overall,
        }

    def get_token_savings(self, days: int = 7) -> dict[str, Any]:
        """Compute token consumption statistics.

        Analyzes agent_load events to compute:
            - Total agents loaded
            - Total tokens loaded
            - Average tokens per agent
            - Estimated baseline (pre-Phase 1 lazy loading)
            - Token savings from lazy loading

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with token statistics:
            {
                "total_agents_loaded": int,
                "total_tokens_loaded": int,
                "avg_tokens_per_agent": float,
                "estimated_baseline_tokens": int,
                "estimated_savings_tokens": int,
                "savings_percentage": float
            }

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> stats = analyzer.get_token_savings(days=7)
            >>> 'total_agents_loaded' in stats
            True
            >>> 'savings_percentage' in stats
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        # Filter for agent_load events
        load_events = [e for e in events if e.get("event_type") == "agent_load"]

        if not load_events:
            return {
                "total_agents_loaded": 0,
                "total_tokens_loaded": 0,
                "avg_tokens_per_agent": 0.0,
                "estimated_baseline_tokens": 0,
                "estimated_savings_tokens": 0,
                "savings_percentage": 0.0,
            }

        total_tokens = sum(e.get("estimated_tokens", 0) for e in load_events)
        total_agents = len(load_events)
        avg_tokens = total_tokens / total_agents if total_agents > 0 else 0.0

        # Estimate baseline (pre-Phase 1): assume all 119 agents loaded at
        # ~450 tokens each. Phase 1 introduced lazy loading, so now only
        # loaded agents consume tokens.
        total_agents_baseline = 119
        avg_tokens_per_agent_baseline = 450
        estimated_baseline = total_agents_baseline * avg_tokens_per_agent_baseline

        # Actual usage (with lazy loading)
        estimated_savings = estimated_baseline - total_tokens
        savings_percentage = (estimated_savings / estimated_baseline) * 100 if estimated_baseline > 0 else 0.0

        return {
            "total_agents_loaded": total_agents,
            "total_tokens_loaded": total_tokens,
            "avg_tokens_per_agent": round(avg_tokens, 2),
            "estimated_baseline_tokens": estimated_baseline,
            "estimated_savings_tokens": estimated_savings,
            "savings_percentage": round(savings_percentage, 2),
        }

    def get_cache_performance(self, days: int = 7) -> dict[str, Any]:
        """Compute cache performance metrics.

        Analyzes get_agent operations to compute:
            - Total cache lookups
            - Cache hits and misses
            - Hit rate percentage
            - Average latency for hits vs. misses

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with cache statistics:
            {
                "total_lookups": int,
                "cache_hits": int,
                "cache_misses": int,
                "hit_rate_percentage": float,
                "avg_hit_latency_ms": float,
                "avg_miss_latency_ms": float
            }

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> stats = analyzer.get_cache_performance(days=7)
            >>> 'hit_rate_percentage' in stats
            True
            >>> stats['total_lookups'] >= 0
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        # Filter for get_agent operations (only these have cache_hit field)
        get_agent_events = [
            e for e in events if e.get("event_type") == "agent_discovery" and e.get("operation") == "get_agent"
        ]

        if not get_agent_events:
            return {
                "total_lookups": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_percentage": 0.0,
                "avg_hit_latency_ms": 0.0,
                "avg_miss_latency_ms": 0.0,
            }

        hits = [e for e in get_agent_events if e.get("cache_hit", False)]
        misses = [e for e in get_agent_events if not e.get("cache_hit", False)]

        hit_latencies = [e["duration_ms"] for e in hits if "duration_ms" in e]
        miss_latencies = [e["duration_ms"] for e in misses if "duration_ms" in e]

        return {
            "total_lookups": len(get_agent_events),
            "cache_hits": len(hits),
            "cache_misses": len(misses),
            "hit_rate_percentage": (round((len(hits) / len(get_agent_events)) * 100, 2) if get_agent_events else 0.0),
            "avg_hit_latency_ms": (round(statistics.mean(hit_latencies), 2) if hit_latencies else 0.0),
            "avg_miss_latency_ms": (round(statistics.mean(miss_latencies), 2) if miss_latencies else 0.0),
        }

    def get_performance_trends(self, days: int = 7) -> dict[str, Any]:
        """Analyze performance trends over time.

        Groups discovery events by day and analyzes:
            - Daily operation counts
            - Average latency trends
            - Cache hit rate trends
            - Overall trend direction

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with trend data:
            {
                "daily_stats": [
                    {
                        "date": "2025-10-18",
                        "operations": int,
                        "avg_latency_ms": float,
                        "cache_hit_rate": float
                    },
                    ...
                ],
                "trend": "improving" | "stable" | "degrading"
            }

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> trends = analyzer.get_performance_trends(days=7)
            >>> 'daily_stats' in trends
            True
            >>> trends['trend'] in ['improving', 'stable', 'degrading']
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        # Filter discovery events
        discovery_events = [e for e in events if e.get("event_type") == "agent_discovery"]

        if not discovery_events:
            return {"daily_stats": [], "trend": "stable"}

        # Group by date
        by_date: dict[str, list[dict[str, Any]]] = {}
        for event in discovery_events:
            timestamp = event.get("timestamp", "")
            try:
                date = datetime.fromisoformat(timestamp).date().isoformat()
            except (ValueError, AttributeError):
                continue

            if date not in by_date:
                by_date[date] = []
            by_date[date].append(event)

        # Compute daily stats
        daily_stats = []
        for date in sorted(by_date.keys()):
            events_list = by_date[date]
            durations = [e["duration_ms"] for e in events_list if "duration_ms" in e]

            get_agent_events = [e for e in events_list if e.get("operation") == "get_agent"]
            cache_hits = sum(1 for e in get_agent_events if e.get("cache_hit", False))
            cache_hit_rate = (cache_hits / len(get_agent_events)) * 100 if get_agent_events else 0.0

            daily_stats.append(
                {
                    "date": date,
                    "operations": len(events_list),
                    "avg_latency_ms": (round(statistics.mean(durations), 2) if durations else 0.0),
                    "cache_hit_rate": round(cache_hit_rate, 2),
                }
            )

        # Determine trend (compare first half vs second half)
        if len(daily_stats) >= 2:
            midpoint = len(daily_stats) // 2
            # Extract latencies as floats for type safety
            first_half_latencies: list[float] = [float(d["avg_latency_ms"]) for d in daily_stats[:midpoint]]
            second_half_latencies: list[float] = [float(d["avg_latency_ms"]) for d in daily_stats[midpoint:]]

            first_half_avg = statistics.mean(first_half_latencies)
            second_half_avg = statistics.mean(second_half_latencies)

            if second_half_avg < first_half_avg * 0.9:
                trend = "improving"
            elif second_half_avg > first_half_avg * 1.1:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "daily_stats": daily_stats,
            "trend": trend,
        }

    def get_summary_report(self, days: int = 7) -> dict[str, Any]:
        """Generate comprehensive summary report.

        Combines all metrics into a single summary report for easy consumption.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with complete performance summary:
            {
                "report_period_days": int,
                "generated_at": str (ISO timestamp),
                "discovery_stats": {...},
                "token_savings": {...},
                "cache_performance": {...},
                "trends": {...}
            }

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> report = analyzer.get_summary_report(days=7)
            >>> 'discovery_stats' in report
            True
            >>> 'token_savings' in report
            True
        """
        return {
            "report_period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "discovery_stats": self.get_discovery_stats(days),
            "token_savings": self.get_token_savings(days),
            "cache_performance": self.get_cache_performance(days),
            "trends": self.get_performance_trends(days),
        }

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile value.

        Uses linear interpolation between closest ranks for accurate
        percentile calculation.

        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value (rounded to 2 decimals)

        Example:
            >>> analyzer = MetricsAnalyzer(EventStorage())
            >>> analyzer._percentile([1, 2, 3, 4, 5], 50)
            3.0
            >>> analyzer._percentile([1, 2, 3, 4, 5], 95)
            4.8
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return round(sorted_data[int(index)], 2)

        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return round(lower + (upper - lower) * (index - int(index)), 2)
