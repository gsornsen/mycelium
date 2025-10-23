# Source: projects/backlog/OPTION_A_AGENT_USAGE_ANALYTICS.md
# Line: 245
# Valid syntax: True
# Has imports: True
# Has assignments: True

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