# Option A: Agent Usage Analytics

**Status**: Draft Backlog **Author**: @claude-code-developer + @project-manager **Created**: 2025-10-18 **Estimated
Effort**: 2-3 days (1 senior developer) **Complexity**: Low **Dependencies**: Phase 2 Performance Analytics (completed)

______________________________________________________________________

## Executive Summary

Extend the existing `mycelium_analytics` system to track **agent usage patterns** including popularity ranking, usage
frequency, category breakdown, and unused agent detection. Provides data-driven insights for agent portfolio
optimization and recommendation system improvements.

**Value Proposition**:

- Identify most/least used agents for optimization efforts
- Detect "zombie agents" (zero usage in 30 days)
- Understand usage patterns by time-of-day and category
- Inform smart agent suggestion algorithms (Option C)

______________________________________________________________________

## Technical Architecture

### System Context

This feature **extends** the existing analytics infrastructure:

- Builds on `EventStorage` (JSONL storage, thread-safe)
- Extends `TelemetryCollector` with new event types
- Adds `UsageAnalyzer` class to `metrics.py`
- Integrates with `AgentDiscovery` for seamless tracking

### Component Diagram

```
┌─────────────────────────────────────────────┐
│   AgentDiscovery (scripts/agent_discovery.py)│
│   - get_agent()                              │
│   - list_agents()                            │
│   - search()                                 │
└─────────────────┬───────────────────────────┘
                  │
                  ↓ record_agent_usage()
┌─────────────────────────────────────────────┐
│   TelemetryCollector (NEW METHOD)            │
│   - record_agent_usage()                     │
│   - record_agent_effectiveness()             │
└─────────────────┬───────────────────────────┘
                  │
                  ↓ append_event()
┌─────────────────────────────────────────────┐
│   EventStorage (EXISTING)                    │
│   - events.jsonl (JSONL format)              │
└─────────────────┬───────────────────────────┘
                  │
                  ↓ read_events()
┌─────────────────────────────────────────────┐
│   UsageAnalyzer (NEW CLASS)                  │
│   - get_popularity_ranking()                 │
│   - get_category_breakdown()                 │
│   - get_unused_agents()                      │
│   - get_usage_heatmap()                      │
└─────────────────────────────────────────────┘
```

______________________________________________________________________

## Data Schema

### Event Type: `agent_usage`

```json
{
  "timestamp": "2025-10-19T12:00:00Z",
  "event_type": "agent_usage",
  "agent_id_hash": "f2f2cbc2",
  "session_id_hash": "a1b2c3d4",
  "context_type": "manual|suggested|auto",
  "invocation_method": "direct|search|category_filter",
  "category": "core-development",
  "keywords": ["api", "design"],
  "session_duration_seconds": 1200,
  "tasks_completed": 3,
  "effectiveness_score": 4.5
}
```

**Privacy Guarantees**:

- Agent IDs are **hashed** (SHA-256, first 8 chars)
- Session IDs are **hashed**
- No file paths, command content, or PII
- Timestamps are UTC (no timezone PII)

### Event Type: `agent_effectiveness` (Optional User Feedback)

```json
{
  "timestamp": "2025-10-19T12:30:00Z",
  "event_type": "agent_effectiveness",
  "agent_id_hash": "f2f2cbc2",
  "session_id_hash": "a1b2c3d4",
  "rating": 5,
  "feedback_type": "helpful|unhelpful|suggested_improvement",
  "task_success": true
}
```

______________________________________________________________________

## Implementation Details

### Phase 1: Extend Telemetry (Day 1)

**File**: `/home/gerald/git/mycelium/mycelium_analytics/telemetry.py`

```python
class TelemetryCollector:
    """Existing class - add new methods."""

    def record_agent_usage(
        self,
        agent_id: str,
        session_id: str,
        context_type: str,
        invocation_method: str,
        category: str,
        keywords: list[str],
        session_duration_seconds: float | None = None,
        tasks_completed: int | None = None,
        effectiveness_score: float | None = None,
    ) -> None:
        """Track agent usage patterns.

        Args:
            agent_id: Agent identifier (e.g., "01-core-api-designer")
            session_id: Unique session identifier
            context_type: How agent was invoked:
                - "manual": User explicitly invoked
                - "suggested": System suggested, user accepted
                - "auto": Automatically invoked by orchestrator
            invocation_method: Discovery method:
                - "direct": User typed agent name
                - "search": Found via search()
                - "category_filter": Found via list_agents(category=...)
            category: Agent category (from index.json)
            keywords: Agent keywords (from index.json)
            session_duration_seconds: How long agent was active
            tasks_completed: Number of tasks completed (if trackable)
            effectiveness_score: User feedback score (1-5, optional)

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_agent_usage(
            ...     agent_id="01-core-api-designer",
            ...     session_id="session-abc123",
            ...     context_type="manual",
            ...     invocation_method="search",
            ...     category="core-development",
            ...     keywords=["api", "design", "rest"],
            ...     session_duration_seconds=1200,
            ...     tasks_completed=3,
            ...     effectiveness_score=4.5
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_usage",
            "agent_id_hash": self._hash_agent_id(agent_id),
            "session_id_hash": self._hash_session_id(session_id),
            "context_type": context_type,
            "invocation_method": invocation_method,
            "category": category,
            "keywords": keywords,
        }

        # Add optional fields if provided
        if session_duration_seconds is not None:
            event["session_duration_seconds"] = session_duration_seconds
        if tasks_completed is not None:
            event["tasks_completed"] = tasks_completed
        if effectiveness_score is not None:
            event["effectiveness_score"] = effectiveness_score

        self._record_event(event)

    def record_agent_effectiveness(
        self,
        agent_id: str,
        session_id: str,
        rating: int,
        feedback_type: str,
        task_success: bool,
    ) -> None:
        """Track user feedback on agent effectiveness.

        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            rating: User rating (1-5 scale)
            feedback_type: Type of feedback:
                - "helpful": Agent was helpful
                - "unhelpful": Agent was not helpful
                - "suggested_improvement": User has suggestions
            task_success: Whether task was successfully completed

        Example:
            >>> collector.record_agent_effectiveness(
            ...     agent_id="01-core-api-designer",
            ...     session_id="session-abc123",
            ...     rating=5,
            ...     feedback_type="helpful",
            ...     task_success=True
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_effectiveness",
            "agent_id_hash": self._hash_agent_id(agent_id),
            "session_id_hash": self._hash_session_id(session_id),
            "rating": rating,
            "feedback_type": feedback_type,
            "task_success": task_success,
        }
        self._record_event(event)

    @staticmethod
    def _hash_session_id(session_id: str) -> str:
        """Hash session ID for privacy (internal).

        Args:
            session_id: Session identifier

        Returns:
            Hashed session ID (first 8 chars of hex hash)
        """
        import hashlib
        return hashlib.sha256(session_id.encode()).hexdigest()[:8]
```

### Phase 2: Usage Analyzer (Day 2)

**File**: `/home/gerald/git/mycelium/mycelium_analytics/metrics.py`

```python
class UsageAnalyzer:
    """Analyzes agent usage patterns from telemetry events.

    Provides insights into agent popularity, category breakdown, unused
    agents, and usage patterns over time.

    Attributes:
        storage: EventStorage backend for reading events

    Example:
        >>> storage = EventStorage()
        >>> analyzer = UsageAnalyzer(storage)
        >>> ranking = analyzer.get_popularity_ranking(days=30)
        >>> len(ranking) > 0
        True
    """

    def __init__(self, storage: EventStorage):
        """Initialize usage analyzer.

        Args:
            storage: EventStorage backend for reading events
        """
        self.storage = storage

    def get_popularity_ranking(
        self,
        days: int = 30,
        min_usage: int = 1
    ) -> list[dict[str, Any]]:
        """Rank agents by usage frequency.

        Returns agents sorted by usage count (descending) with usage
        statistics including total invocations, average session duration,
        and average effectiveness score.

        Args:
            days: Number of days to analyze (default: 30)
            min_usage: Minimum usage count to include (default: 1)

        Returns:
            List of agent usage dictionaries:
            [
                {
                    "agent_id_hash": "f2f2cbc2",
                    "usage_count": 142,
                    "avg_session_duration_seconds": 1200.5,
                    "avg_effectiveness_score": 4.3,
                    "category": "core-development",
                    "last_used": "2025-10-19T12:00:00Z"
                },
                ...
            ]

        Example:
            >>> analyzer = UsageAnalyzer(EventStorage())
            >>> ranking = analyzer.get_popularity_ranking(days=30)
            >>> ranking[0]['usage_count'] >= ranking[-1]['usage_count']
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        # Filter agent_usage events
        usage_events = [
            e for e in events if e.get("event_type") == "agent_usage"
        ]

        # Group by agent_id_hash
        by_agent: dict[str, list[dict[str, Any]]] = {}
        for event in usage_events:
            agent_hash = event.get("agent_id_hash", "unknown")
            if agent_hash not in by_agent:
                by_agent[agent_hash] = []
            by_agent[agent_hash].append(event)

        # Compute stats for each agent
        ranking = []
        for agent_hash, agent_events in by_agent.items():
            usage_count = len(agent_events)
            if usage_count < min_usage:
                continue

            # Average session duration
            durations = [
                e["session_duration_seconds"]
                for e in agent_events
                if "session_duration_seconds" in e
            ]
            avg_duration = statistics.mean(durations) if durations else 0.0

            # Average effectiveness score
            scores = [
                e["effectiveness_score"]
                for e in agent_events
                if "effectiveness_score" in e
            ]
            avg_score = statistics.mean(scores) if scores else None

            # Last used timestamp
            timestamps = [
                e.get("timestamp", "")
                for e in agent_events
                if "timestamp" in e
            ]
            last_used = max(timestamps) if timestamps else None

            # Category (most common in events)
            categories = [e.get("category") for e in agent_events if "category" in e]
            category = max(set(categories), key=categories.count) if categories else "unknown"

            ranking.append({
                "agent_id_hash": agent_hash,
                "usage_count": usage_count,
                "avg_session_duration_seconds": round(avg_duration, 2),
                "avg_effectiveness_score": round(avg_score, 2) if avg_score else None,
                "category": category,
                "last_used": last_used,
            })

        # Sort by usage_count (descending)
        ranking.sort(key=lambda x: x["usage_count"], reverse=True)

        return ranking

    def get_category_breakdown(self, days: int = 30) -> dict[str, int]:
        """Get usage count breakdown by category.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary mapping category to usage count:
            {
                "core-development": 342,
                "infrastructure": 128,
                "frontend": 95,
                ...
            }

        Example:
            >>> analyzer = UsageAnalyzer(EventStorage())
            >>> breakdown = analyzer.get_category_breakdown(days=30)
            >>> isinstance(breakdown, dict)
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        usage_events = [
            e for e in events if e.get("event_type") == "agent_usage"
        ]

        # Count by category
        category_counts: dict[str, int] = {}
        for event in usage_events:
            category = event.get("category", "uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Sort by count (descending)
        sorted_categories = dict(
            sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        )

        return sorted_categories

    def get_unused_agents(
        self,
        days: int = 30,
        discovery: 'AgentDiscovery' | None = None
    ) -> list[dict[str, Any]]:
        """Find agents with zero usage in time period.

        Compares all available agents (from AgentDiscovery) against usage
        events to identify "zombie agents" with no usage.

        Args:
            days: Number of days to check (default: 30)
            discovery: Optional AgentDiscovery instance for full agent list
                If None, returns only agent hashes without metadata

        Returns:
            List of unused agent dictionaries:
            [
                {
                    "agent_id": "01-unused-agent",
                    "agent_id_hash": "abc12345",
                    "category": "data-science",
                    "keywords": ["ml", "training"],
                    "days_since_last_use": 45
                },
                ...
            ]

        Example:
            >>> analyzer = UsageAnalyzer(EventStorage())
            >>> from scripts.agent_discovery import AgentDiscovery
            >>> discovery = AgentDiscovery(Path("plugins/mycelium-core/agents/index.json"))
            >>> unused = analyzer.get_unused_agents(days=30, discovery=discovery)
            >>> all(u['days_since_last_use'] >= 30 for u in unused)
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(limit=100000)  # All events, not just recent

        # Get all used agent hashes (ever)
        used_hashes = set()
        for event in events:
            if event.get("event_type") == "agent_usage":
                used_hashes.add(event.get("agent_id_hash"))

        # If discovery provided, compare against full agent list
        if discovery is not None:
            all_agents = discovery.list_agents()
            unused = []

            for agent in all_agents:
                agent_id = agent.get("id", "")
                agent_hash = self._hash_agent_id(agent_id)

                if agent_hash not in used_hashes:
                    # Never used
                    unused.append({
                        "agent_id": agent_id,
                        "agent_id_hash": agent_hash,
                        "category": agent.get("category", "unknown"),
                        "keywords": agent.get("keywords", []),
                        "days_since_last_use": float("inf"),  # Never used
                    })
                else:
                    # Check if used recently
                    recent_events = [
                        e for e in events
                        if e.get("event_type") == "agent_usage"
                        and e.get("agent_id_hash") == agent_hash
                    ]

                    if not recent_events:
                        continue

                    # Get most recent usage
                    timestamps = [
                        datetime.fromisoformat(e.get("timestamp", ""))
                        for e in recent_events
                        if "timestamp" in e
                    ]

                    if not timestamps:
                        continue

                    last_used = max(timestamps)
                    days_since = (datetime.now(timezone.utc) - last_used).days

                    if days_since >= days:
                        unused.append({
                            "agent_id": agent_id,
                            "agent_id_hash": agent_hash,
                            "category": agent.get("category", "unknown"),
                            "keywords": agent.get("keywords", []),
                            "days_since_last_use": days_since,
                        })

            return unused

        # No discovery provided - return hashes only
        all_hashes_in_storage = set()
        for event in events:
            if event.get("event_type") == "agent_usage":
                all_hashes_in_storage.add(event.get("agent_id_hash"))

        # No way to determine unused without discovery
        return []

    def get_usage_heatmap(self, days: int = 30) -> dict[str, dict[int, int]]:
        """Generate usage heatmap by day-of-week and hour-of-day.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Nested dictionary with usage counts:
            {
                "monday": {0: 5, 1: 2, ..., 23: 12},
                "tuesday": {0: 3, 1: 8, ..., 23: 6},
                ...
            }

            Outer keys: day names (lowercase)
            Inner keys: hours (0-23)
            Values: usage counts

        Example:
            >>> analyzer = UsageAnalyzer(EventStorage())
            >>> heatmap = analyzer.get_usage_heatmap(days=30)
            >>> 'monday' in heatmap
            True
            >>> all(0 <= hour <= 23 for hours in heatmap.values() for hour in hours.keys())
            True
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.storage.read_events(start_date=start_date, limit=100000)

        usage_events = [
            e for e in events if e.get("event_type") == "agent_usage"
        ]

        # Initialize heatmap
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        heatmap: dict[str, dict[int, int]] = {
            day: {hour: 0 for hour in range(24)}
            for day in days_of_week
        }

        # Count by day and hour
        for event in usage_events:
            timestamp_str = event.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                day_name = days_of_week[timestamp.weekday()]
                hour = timestamp.hour
                heatmap[day_name][hour] += 1
            except (ValueError, IndexError):
                continue

        return heatmap

    @staticmethod
    def _hash_agent_id(agent_id: str) -> str:
        """Hash agent ID for privacy (matches TelemetryCollector)."""
        import hashlib
        return hashlib.sha256(agent_id.encode()).hexdigest()[:8]


# Extend MetricsAnalyzer to include usage stats in summary
class MetricsAnalyzer:
    """Existing class - add method to include usage stats."""

    def get_usage_stats(self, days: int = 30) -> dict[str, Any]:
        """Get comprehensive usage statistics.

        Combines popularity ranking, category breakdown, unused agents,
        and usage heatmap into single report.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with usage statistics:
            {
                "popularity_ranking": [...],
                "category_breakdown": {...},
                "unused_agents": [...],
                "usage_heatmap": {...}
            }
        """
        usage_analyzer = UsageAnalyzer(self.storage)

        return {
            "popularity_ranking": usage_analyzer.get_popularity_ranking(days),
            "category_breakdown": usage_analyzer.get_category_breakdown(days),
            "usage_heatmap": usage_analyzer.get_usage_heatmap(days),
        }
```

### Phase 3: CLI Integration (Day 3)

**File**: `/home/gerald/git/mycelium/scripts/agent_stats.py` (NEW)

```python
#!/usr/bin/env python3
"""CLI tool for viewing agent usage analytics.

Provides command-line interface to usage statistics including popularity
ranking, category breakdown, and unused agent detection.

Usage:
    # Show top 10 most used agents
    python scripts/agent_stats.py popularity --days 30 --limit 10

    # Show category breakdown
    python scripts/agent_stats.py categories --days 30

    # Find unused agents
    python scripts/agent_stats.py unused --days 30

    # Show usage heatmap
    python scripts/agent_stats.py heatmap --days 7

Author: @claude-code-developer
Date: 2025-10-18
"""

import argparse
from pathlib import Path
from mycelium_analytics import EventStorage
from mycelium_analytics.metrics import UsageAnalyzer
from scripts.agent_discovery import AgentDiscovery


def cmd_popularity(args):
    """Show popularity ranking."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    ranking = analyzer.get_popularity_ranking(
        days=args.days,
        min_usage=args.min_usage
    )

    print(f"\n=== Top {args.limit} Most Used Agents (Last {args.days} Days) ===\n")

    for i, agent in enumerate(ranking[:args.limit], 1):
        print(f"{i}. Agent {agent['agent_id_hash']}")
        print(f"   Category: {agent['category']}")
        print(f"   Usage: {agent['usage_count']} times")
        print(f"   Avg Session: {agent['avg_session_duration_seconds']:.1f}s")
        if agent['avg_effectiveness_score']:
            print(f"   Avg Rating: {agent['avg_effectiveness_score']:.1f}/5.0")
        print(f"   Last Used: {agent['last_used']}")
        print()


def cmd_categories(args):
    """Show category breakdown."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    breakdown = analyzer.get_category_breakdown(days=args.days)

    print(f"\n=== Usage by Category (Last {args.days} Days) ===\n")

    total = sum(breakdown.values())
    for category, count in breakdown.items():
        percentage = (count / total * 100) if total > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{category:30s} {count:4d} ({percentage:5.1f}%) {bar}")


def cmd_unused(args):
    """Find unused agents."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    # Load agent discovery
    index_path = Path("plugins/mycelium-core/agents/index.json")
    if not index_path.exists():
        print(f"Error: Index not found at {index_path}")
        return

    discovery = AgentDiscovery(index_path)
    unused = analyzer.get_unused_agents(days=args.days, discovery=discovery)

    print(f"\n=== Unused Agents (Last {args.days} Days) ===\n")
    print(f"Found {len(unused)} agents with no recent usage\n")

    for agent in unused[:args.limit]:
        print(f"• {agent['agent_id']}")
        print(f"  Category: {agent['category']}")
        print(f"  Keywords: {', '.join(agent['keywords'][:5])}")
        days_since = agent['days_since_last_use']
        if days_since == float("inf"):
            print(f"  Status: Never used")
        else:
            print(f"  Last Used: {days_since} days ago")
        print()


def cmd_heatmap(args):
    """Show usage heatmap."""
    storage = EventStorage()
    analyzer = UsageAnalyzer(storage)

    heatmap = analyzer.get_usage_heatmap(days=args.days)

    print(f"\n=== Usage Heatmap (Last {args.days} Days) ===\n")
    print("Hour distribution by day of week:\n")

    # Print header
    print("Day       ", end="")
    for hour in [0, 6, 12, 18]:
        print(f"{hour:>4}h", end=" ")
    print()

    # Print heatmap rows
    for day, hours in heatmap.items():
        print(f"{day.capitalize():10s}", end="")
        for hour in [0, 6, 12, 18]:
            count = hours[hour]
            if count == 0:
                symbol = "·"
            elif count < 10:
                symbol = "░"
            elif count < 30:
                symbol = "▒"
            else:
                symbol = "█"
            print(f"  {symbol}  ", end=" ")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Agent usage analytics CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Popularity command
    pop_parser = subparsers.add_parser("popularity", help="Show popularity ranking")
    pop_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    pop_parser.add_argument("--limit", type=int, default=10, help="Number to show")
    pop_parser.add_argument("--min-usage", type=int, default=1, help="Min usage count")

    # Categories command
    cat_parser = subparsers.add_parser("categories", help="Show category breakdown")
    cat_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Unused command
    unused_parser = subparsers.add_parser("unused", help="Find unused agents")
    unused_parser.add_argument("--days", type=int, default=30, help="Days to check")
    unused_parser.add_argument("--limit", type=int, default=20, help="Max to show")

    # Heatmap command
    heat_parser = subparsers.add_parser("heatmap", help="Show usage heatmap")
    heat_parser.add_argument("--days", type=int, default=7, help="Days to analyze")

    args = parser.parse_args()

    if args.command == "popularity":
        cmd_popularity(args)
    elif args.command == "categories":
        cmd_categories(args)
    elif args.command == "unused":
        cmd_unused(args)
    elif args.command == "heatmap":
        cmd_heatmap(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Integration with AgentDiscovery**:

Modify `/home/gerald/git/mycelium/scripts/agent_discovery.py` to track usage:

```python
class AgentDiscovery:
    """Existing class - add usage tracking to get_agent()."""

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details (lazy load content).

        MODIFIED: Now tracks usage via telemetry.
        """
        start_time = time.perf_counter()
        self._stats['total_lookups'] += 1

        # ... existing cache check code ...

        # NEW: Track usage event (if telemetry available)
        if self.telemetry and agent_full:
            # Generate session ID (use thread ID for now)
            import threading
            session_id = f"session-{threading.get_ident()}"

            self.telemetry.record_agent_usage(
                agent_id=agent_id,
                session_id=session_id,
                context_type="manual",  # Assume manual for now
                invocation_method="direct",  # Direct get_agent() call
                category=agent_meta.get("category", "unknown"),
                keywords=agent_meta.get("keywords", []),
            )

        return agent_full
```

______________________________________________________________________

## Testing Strategy

### Unit Tests

**File**: `/home/gerald/git/mycelium/tests/unit/analytics/test_usage_analyzer.py`

```python
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
```

### Integration Tests

Test CLI commands work end-to-end:

```bash
# Generate sample data
python scripts/generate_sample_usage.py --events 100

# Test CLI commands
python scripts/agent_stats.py popularity --days 30 --limit 10
python scripts/agent_stats.py categories --days 30
python scripts/agent_stats.py unused --days 30
python scripts/agent_stats.py heatmap --days 7
```

______________________________________________________________________

## Implementation Timeline

### Day 1: Telemetry Extension

- **Morning**: Add `record_agent_usage()` to `TelemetryCollector`
- **Afternoon**: Add `record_agent_effectiveness()` method
- **End of Day**: Unit tests for new methods (100% coverage)

### Day 2: Usage Analyzer

- **Morning**: Implement `UsageAnalyzer` class with all methods
- **Afternoon**: Integrate with `AgentDiscovery.get_agent()`
- **End of Day**: Unit tests for analyzer (100% coverage)

### Day 3: CLI + Testing

- **Morning**: Build `agent_stats.py` CLI tool
- **Afternoon**: Integration testing + documentation
- **End of Day**: Demo to team, gather feedback

**Total**: 2-3 days for 1 senior Python developer

______________________________________________________________________

## Effort Estimate

**Complexity**: Low (extends existing system)

**Team Composition**:

- 1x @python-pro (lead developer)

**Breakdown**:

- Code implementation: 1.5 days
- Testing (unit + integration): 0.5 days
- Documentation: 0.5 days
- Code review + polish: 0.5 days

**Total**: 2.5 - 3 days

______________________________________________________________________

## Dependencies

**Required**:

- Phase 2 Performance Analytics (✅ Complete)
- `EventStorage` with JSONL backend (✅ Complete)
- `TelemetryCollector` infrastructure (✅ Complete)
- `AgentDiscovery` with lazy loading (✅ Complete)

**Optional**:

- Option C (Smart Agent Suggestions) benefits from this data
- Future ML models can train on usage patterns

______________________________________________________________________

## Success Metrics

**Acceptance Criteria**:

1. ✅ Popularity ranking returns top agents by usage count
1. ✅ Category breakdown shows usage distribution
1. ✅ Unused agent detection identifies zombie agents
1. ✅ Usage heatmap displays day/hour patterns
1. ✅ CLI tool provides all 4 commands
1. ✅ 100% test coverage (unit + integration)
1. ✅ \<20ms for analytics queries (p95)

**Performance Targets**:

- `get_popularity_ranking()`: p95 \< 50ms
- `get_category_breakdown()`: p95 \< 20ms
- `get_unused_agents()`: p95 \< 100ms (involves AgentDiscovery)
- `get_usage_heatmap()`: p95 \< 30ms

______________________________________________________________________

## Future Enhancements

**Phase 2 (Optional)**:

- Real-time usage dashboard (web UI)
- Slack/Discord notifications for unused agents
- Automatic agent deprecation recommendations
- Integration with Option C (recommendation engine)
- A/B testing framework for agent improvements

______________________________________________________________________

## Risk Assessment

**Technical Risks**: LOW

- Extends proven analytics infrastructure
- No external dependencies beyond stdlib
- Simple data structures (dicts, lists)

**Blockers**: NONE

- All dependencies complete (Phase 2)

**Mitigation**:

- Graceful degradation if telemetry fails
- Privacy-first design (hashed IDs)
- Thread-safe storage operations

______________________________________________________________________

## Conclusion

Option A provides **high value** at **low cost** by extending the existing analytics system to track agent usage
patterns. The implementation is straightforward (2-3 days), low risk, and provides immediate insights for optimization
efforts and smart agent suggestions (Option C).

**Recommendation**: **APPROVED for Sprint Planning**

______________________________________________________________________

**Next Steps**:

1. Approve backlog item
1. Add to sprint planning
1. Assign to @python-pro
1. Coordinate with @project-manager for tracking
