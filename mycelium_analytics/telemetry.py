"""Lightweight telemetry event collector for Mycelium performance analytics.

Non-blocking event collection system for tracking agent discovery performance,
token usage, and session metrics. Privacy-first design with graceful degradation.

Features:
    - Non-blocking event recording (fails silently)
    - Integration with AgentDiscovery timing
    - Privacy guarantees (no PII, paths, or command content)
    - Environment variable opt-out support

Example:
    >>> from mycelium_analytics.storage import EventStorage
    >>> storage = EventStorage()
    >>> collector = TelemetryCollector(storage)
    >>> collector.record_agent_discovery(
    ...     operation="list_agents",
    ...     duration_ms=15.2,
    ...     agent_count=42
    ... )

Author: @python-pro
Phase: 2 Performance Analytics
Date: 2025-10-18
"""

import contextlib
import os
from datetime import datetime, timezone
from typing import Any

from mycelium_analytics.storage import EventStorage


class TelemetryCollector:
    """Lightweight telemetry event collector.

    Collects performance metrics for agent discovery operations, session
    management, and token usage. Designed for minimal overhead with
    graceful degradation if storage fails.

    Privacy guarantees:
        - No user data or file paths
        - No command content or agent content
        - Only performance metrics (durations, counts, booleans)
        - Can be disabled via MYCELIUM_TELEMETRY=0

    Attributes:
        storage: EventStorage backend
        enabled: Whether telemetry is enabled

    Example:
        >>> storage = EventStorage()
        >>> collector = TelemetryCollector(storage)
        >>> collector.record_agent_discovery("get_agent", 2.5, cache_hit=True)
    """

    def __init__(self, storage: EventStorage):
        """Initialize telemetry collector.

        Args:
            storage: EventStorage backend for persistence

        Example:
            >>> storage = EventStorage()
            >>> collector = TelemetryCollector(storage)
            >>> collector.enabled
            True
        """
        self.storage = storage

        # Check environment variable for opt-out
        self.enabled = os.getenv("MYCELIUM_TELEMETRY", "1") != "0"

    def record_agent_discovery(
        self,
        operation: str,
        duration_ms: float,
        cache_hit: bool = False,
        agent_count: int = 0,
    ) -> None:
        """Record agent discovery performance metrics.

        Tracks performance of AgentDiscovery operations including list_agents,
        get_agent, and search. Records duration, cache behavior, and result
        counts.

        Args:
            operation: Operation name (e.g., "list_agents", "get_agent", "search")
            duration_ms: Operation duration in milliseconds
            cache_hit: Whether cache was used (for get_agent)
            agent_count: Number of agents returned/found

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_agent_discovery(
            ...     operation="list_agents",
            ...     duration_ms=18.5,
            ...     agent_count=42
            ... )
            >>> collector.record_agent_discovery(
            ...     operation="get_agent",
            ...     duration_ms=0.8,
            ...     cache_hit=True,
            ...     agent_count=1
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_discovery",
            "operation": operation,
            "duration_ms": duration_ms,
            "cache_hit": cache_hit,
            "agent_count": agent_count,
        }
        self._record_event(event)

    def record_session_start(
        self,
        session_type: str,
        initial_tokens: int,
    ) -> None:
        """Record Claude Code session start.

        Tracks session initialization with initial token load. Used to measure
        impact of lazy loading optimizations.

        Args:
            session_type: Type of session (e.g., "full_context", "lazy_loaded")
            initial_tokens: Estimated token count at session start

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_session_start(
            ...     session_type="lazy_loaded",
            ...     initial_tokens=1200
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "session_start",
            "session_type": session_type,
            "initial_tokens": initial_tokens,
        }
        self._record_event(event)

    def record_session_end(
        self,
        session_duration_seconds: float,
        total_tokens_loaded: int,
        agents_loaded: int,
    ) -> None:
        """Record Claude Code session end.

        Tracks session completion with total token usage and agent loading
        statistics. Useful for measuring lazy loading effectiveness.

        Args:
            session_duration_seconds: Total session duration in seconds
            total_tokens_loaded: Total tokens loaded during session
            agents_loaded: Number of agents loaded during session

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_session_end(
            ...     session_duration_seconds=120.5,
            ...     total_tokens_loaded=3500,
            ...     agents_loaded=5
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "session_end",
            "session_duration_seconds": session_duration_seconds,
            "total_tokens_loaded": total_tokens_loaded,
            "agents_loaded": agents_loaded,
        }
        self._record_event(event)

    def record_agent_load(
        self,
        agent_id: str,
        load_time_ms: float,
        content_size_bytes: int,
        estimated_tokens: int,
    ) -> None:
        """Record individual agent content loading.

        Tracks lazy loading of agent markdown content. Agent ID is hashed
        for privacy (no actual agent paths stored).

        Args:
            agent_id: Agent identifier (e.g., "01-core-api-designer")
            load_time_ms: Time to load content in milliseconds
            content_size_bytes: Size of markdown content in bytes
            estimated_tokens: Estimated token count for content

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_agent_load(
            ...     agent_id="01-core-api-designer",
            ...     load_time_ms=3.2,
            ...     content_size_bytes=4582,
            ...     estimated_tokens=1145
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "agent_load",
            "agent_id_hash": self._hash_agent_id(agent_id),
            "load_time_ms": load_time_ms,
            "content_size_bytes": content_size_bytes,
            "estimated_tokens": estimated_tokens,
        }
        self._record_event(event)

    def record_cache_operation(
        self,
        operation: str,
        cache_size: int,
        hit_rate: float,
        evictions: int = 0,
    ) -> None:
        """Record cache performance metrics.

        Tracks AgentCache LRU behavior including hit rate and evictions.
        Useful for tuning cache_size parameter.

        Args:
            operation: Cache operation (e.g., "get", "put", "evict")
            cache_size: Current cache size
            hit_rate: Current cache hit rate percentage (0-100)
            evictions: Number of evictions (for "evict" operation)

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> collector.record_cache_operation(
            ...     operation="get",
            ...     cache_size=45,
            ...     hit_rate=87.5
            ... )
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "cache_operation",
            "operation": operation,
            "cache_size": cache_size,
            "hit_rate": hit_rate,
            "evictions": evictions,
        }
        self._record_event(event)

    def _record_event(self, event: dict[str, Any]) -> None:
        """Internal: record event to storage (non-blocking).

        Fails silently if telemetry is disabled or storage fails. Telemetry
        should never break normal operations.

        Args:
            event: Event dictionary to record
        """
        if not self.enabled:
            return

        with contextlib.suppress(Exception):
            self.storage.append_event(event)
            pass

    @staticmethod
    def _hash_agent_id(agent_id: str) -> str:
        """Hash agent ID for privacy (internal).

        Uses simple hash to anonymize agent IDs while preserving uniqueness
        for analysis. Avoids storing actual file paths or agent names.

        Args:
            agent_id: Agent identifier

        Returns:
            Hashed agent ID (first 8 chars of hex hash)

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> hash1 = collector._hash_agent_id("01-core-api-designer")
            >>> hash2 = collector._hash_agent_id("01-core-api-designer")
            >>> hash1 == hash2
            True
            >>> len(hash1)
            8
        """
        import hashlib

        return hashlib.sha256(agent_id.encode()).hexdigest()[:8]

    def get_enabled_status(self) -> dict[str, Any]:
        """Get telemetry enabled status and configuration.

        Returns:
            Dict with enabled status and configuration

        Example:
            >>> collector = TelemetryCollector(EventStorage())
            >>> status = collector.get_enabled_status()
            >>> 'enabled' in status
            True
        """
        return {
            "enabled": self.enabled,
            "storage_dir": str(self.storage.storage_dir),
            "env_var": os.getenv("MYCELIUM_TELEMETRY", "1"),
        }
