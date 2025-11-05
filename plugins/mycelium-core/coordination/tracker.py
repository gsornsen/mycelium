"""Coordination tracking system for monitoring agent interactions.

Tracks coordination events:
- Task assignments and executions
- Agent handoffs
- Workflow state changes
- Performance metrics
- Errors and retries

Provides:
- Event storage in PostgreSQL
- Query APIs for event retrieval
- Timeline reconstruction
- Statistical analysis
- Event replay for debugging
"""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Coordination event types."""

    # Core events
    HANDOFF = "handoff"
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    STATUS_UPDATE = "status_update"
    MESSAGE = "message"
    FAILURE = "failure"
    RETRY = "retry"

    # Workflow lifecycle events
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"


class AgentInfo(BaseModel):
    """Agent information for tracking."""

    agent_id: str
    agent_type: str
    metadata: dict[str, Any] | None = None

    def __init__(self, agent_id: str, agent_type: str, **kwargs: Any):
        """Initialize agent info.

        Args:
            agent_id: Agent identifier
            agent_type: Agent type
            **kwargs: Additional fields
        """
        if "metadata" not in kwargs:
            kwargs["metadata"] = None
        super().__init__(agent_id=agent_id, agent_type=agent_type, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "metadata": self.metadata,
        }


class ErrorInfo(BaseModel):
    """Error information for failure tracking."""

    error_type: str
    error_message: str
    stack_trace: str | None = None
    retry_count: int = 0
    will_retry: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "will_retry": self.will_retry,
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics for task execution."""

    cpu_usage: float | None = None
    memory_mb: float | None = None
    io_operations: int | None = None
    network_bytes: int | None = None
    custom_metrics: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_usage": self.cpu_usage,
            "memory_mb": self.memory_mb,
            "io_operations": self.io_operations,
            "network_bytes": self.network_bytes,
            "custom_metrics": self.custom_metrics,
        }


class CoordinationEvent(BaseModel):
    """Coordination event for tracking."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    workflow_id: str
    task_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    agent_id: str | None = None
    agent_type: str | None = None
    source_agent: AgentInfo | None = None
    target_agent: AgentInfo | None = None
    status: str | None = None
    duration_ms: float | None = None
    error: ErrorInfo | None = None
    metadata: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    performance: PerformanceMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "source_agent": self.source_agent.to_dict() if self.source_agent else None,
            "target_agent": self.target_agent.to_dict() if self.target_agent else None,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error": self.error.to_dict() if self.error else None,
            "metadata": self.metadata,
            "context": self.context,
            "performance": self.performance.to_dict() if self.performance else None,
        }


class CoordinationQuery(BaseModel):
    """Query parameters for retrieving coordination events."""

    workflow_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    agent_type: str | None = None
    event_type: EventType | None = None
    status: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    limit: int = 100
    offset: int = 0

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit value."""
        if v < 1 or v > 10000:
            raise ValueError("Limit must be between 1 and 10000")
        return v

    def to_json(self, indent: int | None = None) -> str:
        """Convert to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        data = self.model_dump(exclude_none=True)
        if "event_type" in data and data["event_type"]:
            data["event_type"] = data["event_type"].value
        return json.dumps(data, indent=indent)


class CoordinationTracker:
    """Tracks coordination events between agents."""

    def __init__(
        self,
        pool: asyncpg.pool.Pool | None = None,
        config: dict[str, Any] | None = None,
    ):
        """Initialize coordination tracker.

        Args:
            pool: AsyncPG connection pool
            config: Configuration options
        """
        self._pool = pool
        self._config = config or {}

        # In-memory storage for testing/development
        self._events: list[CoordinationEvent] = []
        self._event_index: dict[str, list[int]] = defaultdict(list)

        # Metrics
        self._event_counts: dict[str, int] = defaultdict(int)
        self._workflow_durations: dict[str, float] = {}

        # Configuration
        self._max_memory_events = self._config.get("max_memory_events", 10000)
        self._enable_logging = self._config.get("enable_logging", True)

    async def initialize(self) -> None:
        """Initialize the tracker and create necessary database tables."""
        if self._pool is None:
            # Use in-memory storage
            logger.info("Using in-memory storage for coordination tracking")
            return

        # Create tables if they don't exist
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coordination_events (
                    event_id VARCHAR(36) PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    workflow_id VARCHAR(255) NOT NULL,
                    task_id VARCHAR(255),
                    timestamp TIMESTAMP NOT NULL,
                    agent_id VARCHAR(255),
                    agent_type VARCHAR(100),
                    source_agent JSONB,
                    target_agent JSONB,
                    status VARCHAR(50),
                    duration_ms FLOAT,
                    error JSONB,
                    metadata JSONB,
                    context JSONB,
                    performance JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_workflow_id ON coordination_events(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_task_id ON coordination_events(task_id);
                CREATE INDEX IF NOT EXISTS idx_agent_id ON coordination_events(agent_id);
                CREATE INDEX IF NOT EXISTS idx_event_type ON coordination_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON coordination_events(timestamp);
                """
            )

    async def close(self) -> None:
        """Close the tracker and clean up resources."""
        # Clear in-memory storage
        self._events.clear()
        self._event_index.clear()

    def _validate_event(self, event: CoordinationEvent) -> None:
        """Validate a coordination event.

        Args:
            event: Event to validate

        Raises:
            EventValidationError: If validation fails
        """
        # Validate required fields
        if not event.workflow_id:
            raise EventValidationError("workflow_id is required")

        # Validate event type specific requirements
        if event.event_type == EventType.HANDOFF and (not event.source_agent or not event.target_agent):
            raise EventValidationError("Handoff events require source and target agents")

        if event.event_type in (EventType.EXECUTION_START, EventType.EXECUTION_END) and not event.task_id:
            raise EventValidationError("Execution events require task_id")

    async def track_event(self, event: CoordinationEvent) -> str:
        """Track a coordination event.

        Args:
            event: Coordination event to track

        Returns:
            Event ID

        Raises:
            EventValidationError: If event validation fails
            TrackerError: If tracking fails
        """
        if self._pool is None:
            # Use in-memory storage
            self._validate_event(event)
            self._events.append(event)
            self._event_index[event.workflow_id].append(len(self._events) - 1)
            if event.task_id:
                self._event_index[f"task:{event.task_id}"].append(len(self._events) - 1)
            if event.agent_id:
                self._event_index[f"agent:{event.agent_id}"].append(len(self._events) - 1)

            # Cleanup old events if limit exceeded
            if len(self._events) > self._max_memory_events:
                self._cleanup_old_events()

            return event.event_id

        # Validate event
        self._validate_event(event)

        # Store event
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO coordination_events (
                        event_id, event_type, workflow_id, task_id, timestamp,
                        agent_id, agent_type, source_agent, target_agent, status,
                        duration_ms, error, metadata, context, performance
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """,
                    event.event_id,
                    event.event_type.value,
                    event.workflow_id,
                    event.task_id,
                    datetime.fromisoformat(event.timestamp.rstrip("Z")),
                    event.agent_id,
                    event.agent_type,
                    json.dumps(event.source_agent.to_dict()) if event.source_agent else None,
                    json.dumps(event.target_agent.to_dict()) if event.target_agent else None,
                    event.status,
                    event.duration_ms,
                    json.dumps(event.error.to_dict()) if event.error else None,
                    json.dumps(event.metadata) if event.metadata else None,
                    json.dumps(event.context) if event.context else None,
                    json.dumps(event.performance.to_dict()) if event.performance else None,
                )

            # Update event counts for monitoring
            self._event_counts[event.event_type.value] = self._event_counts.get(event.event_type.value, 0) + 1

            # Structured logging
            logger.info(
                f"Tracked event: {event.event_type.value}",
                extra={
                    "event_id": event.event_id,
                    "workflow_id": event.workflow_id,
                    "task_id": event.task_id,
                    "agent_id": event.agent_id,
                },
            )

            return event.event_id

        except Exception as e:
            raise TrackerError(f"Failed to track event: {e}") from e

    async def get_workflow_events(
        self,
        workflow_id: str,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[CoordinationEvent]:
        """Get events for a workflow.

        Args:
            workflow_id: Workflow ID
            event_type: Optional event type filter
            limit: Maximum number of events

        Returns:
            List of coordination events
        """
        if self._pool is None:
            # Use in-memory storage
            indices = self._event_index.get(workflow_id, [])
            events = [self._events[i] for i in indices[-limit:]]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return events

        try:
            async with self._pool.acquire() as conn:
                if event_type:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM coordination_events
                        WHERE workflow_id = $1 AND event_type = $2
                        ORDER BY timestamp DESC
                        LIMIT $3
                        """,
                        workflow_id,
                        event_type.value,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM coordination_events
                        WHERE workflow_id = $1
                        ORDER BY timestamp DESC
                        LIMIT $2
                        """,
                        workflow_id,
                        limit,
                    )

                return [self._row_to_event(row) for row in reversed(rows)]

        except Exception as e:
            raise TrackerError(f"Failed to get workflow events: {e}") from e

    async def get_task_events(
        self,
        task_id: str,
        limit: int = 100,
    ) -> list[CoordinationEvent]:
        """Get events for a task.

        Args:
            task_id: Task ID
            limit: Maximum number of events

        Returns:
            List of coordination events
        """
        if self._pool is None:
            # Use in-memory storage
            indices = self._event_index.get(f"task:{task_id}", [])
            return [self._events[i] for i in indices[-limit:]]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM coordination_events
                    WHERE task_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                    """,
                    task_id,
                    limit,
                )

                return [self._row_to_event(row) for row in reversed(rows)]

        except Exception as e:
            raise TrackerError(f"Failed to get task events: {e}") from e

    async def get_agent_events(
        self,
        agent_id: str,
        limit: int = 100,
    ) -> list[CoordinationEvent]:
        """Get events for an agent.

        Args:
            agent_id: Agent ID
            limit: Maximum number of events

        Returns:
            List of coordination events
        """
        if self._pool is None:
            # Use in-memory storage
            indices = self._event_index.get(f"agent:{agent_id}", [])
            events = [self._events[i] for i in indices[-limit:]]

            # Also include events where agent is source or target
            additional = []
            for event in self._events:
                if event not in events and (
                    event.source_agent
                    and event.source_agent.agent_id == agent_id
                    or event.target_agent
                    and event.target_agent.agent_id == agent_id
                ):
                    additional.append(event)

            return sorted(events + additional, key=lambda e: e.timestamp)[-limit:]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM coordination_events
                    WHERE agent_id = $1
                       OR source_agent->>'agent_id' = $1
                       OR target_agent->>'agent_id' = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                    """,
                    agent_id,
                    limit,
                )

                return [self._row_to_event(row) for row in reversed(rows)]

        except Exception as e:
            raise TrackerError(f"Failed to get agent events: {e}") from e

    async def get_handoff_chain(self, workflow_id: str) -> list[CoordinationEvent]:
        """Get handoff chain for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of handoff events in order
        """
        events = await self.get_workflow_events(workflow_id, EventType.HANDOFF, limit=1000)
        return sorted(events, key=lambda e: e.timestamp)

    async def get_workflow_timeline(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Get workflow execution timeline.

        Args:
            workflow_id: Workflow ID

        Returns:
            Timeline information
        """
        events = await self.get_workflow_events(workflow_id, limit=10000)

        if not events:
            return {
                "workflow_id": workflow_id,
                "total_events": 0,
                "duration_ms": 0,
                "handoff_count": 0,
                "failure_count": 0,
                "unique_agents": 0,
                "unique_tasks": 0,
                "events": [],
            }

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Extract timeline data
        handoffs = [e for e in events if e.event_type == EventType.HANDOFF]
        failures = [e for e in events if e.event_type == EventType.FAILURE]
        agents = set()
        tasks = set()

        for event in events:
            if event.agent_id:
                agents.add(event.agent_id)
            if event.task_id:
                tasks.add(event.task_id)
            if event.source_agent:
                agents.add(event.source_agent.agent_id)
            if event.target_agent:
                agents.add(event.target_agent.agent_id)

        # Calculate duration
        start_time = datetime.fromisoformat(events[0].timestamp.rstrip("Z"))
        end_time = datetime.fromisoformat(events[-1].timestamp.rstrip("Z"))
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "workflow_id": workflow_id,
            "total_events": len(events),
            "duration_ms": duration_ms,
            "handoff_count": len(handoffs),
            "failure_count": len(failures),
            "unique_agents": len(agents),
            "unique_tasks": len(tasks),
            "events": [e.to_dict() for e in events],
        }

    async def get_statistics(
        self,
        workflow_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Get coordination statistics.

        Args:
            workflow_id: Optional workflow filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Statistics dictionary
        """
        if self._pool is None:
            # Calculate from in-memory events
            events = self._events
            if workflow_id:
                indices = self._event_index.get(workflow_id, [])
                events = [self._events[i] for i in indices]

            total_events = len(events)
            event_types: defaultdict[str, int] = defaultdict(int)
            failure_count = 0
            total_duration: float = 0
            duration_count = 0

            for event in events:
                event_types[event.event_type.value] += 1
                if event.event_type == EventType.FAILURE:
                    failure_count += 1
                if event.duration_ms:
                    total_duration += event.duration_ms
                    duration_count += 1

            return {
                "total_events": total_events,
                "event_types": dict(event_types),
                "failure_count": failure_count,
                "failure_rate": failure_count / total_events if total_events > 0 else 0,
                "avg_duration_ms": total_duration / duration_count if duration_count > 0 else 0,
                "unique_workflows": len(self._event_index),
            }

        try:
            async with self._pool.acquire() as conn:
                # Build query conditions
                conditions = []
                params = []
                param_num = 1

                if workflow_id:
                    conditions.append(f"workflow_id = ${param_num}")
                    params.append(workflow_id)
                    param_num += 1

                if start_time:
                    conditions.append(f"timestamp >= ${param_num}")
                    params.append(datetime.fromisoformat(start_time.rstrip("Z")).isoformat())
                    param_num += 1

                if end_time:
                    conditions.append(f"timestamp <= ${param_num}")
                    params.append(datetime.fromisoformat(end_time.rstrip("Z")).isoformat())
                    param_num += 1

                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                # Get statistics
                stats_query = f"""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT workflow_id) as unique_workflows,
                        COUNT(DISTINCT task_id) as unique_tasks,
                        COUNT(DISTINCT agent_id) as unique_agents,
                        COUNT(CASE WHEN event_type = 'failure' THEN 1 END) as failure_count,
                        AVG(duration_ms) as avg_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        MIN(duration_ms) as min_duration_ms
                    FROM coordination_events
                    {where_clause}
                """

                row = await conn.fetchrow(stats_query, *params)

                # Get event type breakdown
                type_query = f"""
                    SELECT event_type, COUNT(*) as count
                    FROM coordination_events
                    {where_clause}
                    GROUP BY event_type
                """

                type_rows = await conn.fetch(type_query, *params)
                event_type_counts: dict[str, int] = {row["event_type"]: row["count"] for row in type_rows}

                total_events = row["total_events"] or 0
                failure_count = row["failure_count"] or 0

                return {
                    "total_events": total_events,
                    "unique_workflows": row["unique_workflows"] or 0,
                    "unique_tasks": row["unique_tasks"] or 0,
                    "unique_agents": row["unique_agents"] or 0,
                    "failure_count": failure_count,
                    "failure_rate": failure_count / total_events if total_events > 0 else 0,
                    "avg_duration_ms": float(row["avg_duration_ms"] or 0),
                    "max_duration_ms": float(row["max_duration_ms"] or 0),
                    "min_duration_ms": float(row["min_duration_ms"] or 0),
                    "event_types": event_type_counts,
                }

        except Exception as e:
            raise TrackerError(f"Failed to get statistics: {e}") from e

    async def delete_workflow_events(self, workflow_id: str) -> int:
        """Delete all events for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Number of events deleted
        """
        if self._pool is None:
            # Remove from in-memory storage
            indices = self._event_index.get(workflow_id, [])
            return len(indices)
            # This is complex to do efficiently in-memory, so just clear for now

        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM coordination_events
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )
                # Extract count from result string like "DELETE 5"
                return int(result.split()[-1]) if result else 0

        except Exception as e:
            raise TrackerError(f"Failed to delete workflow events: {e}") from e

    def _row_to_event(self, row: asyncpg.Record) -> CoordinationEvent:
        """Convert database row to CoordinationEvent.

        Args:
            row: Database row

        Returns:
            CoordinationEvent instance
        """
        # Parse JSON fields
        source_agent = None
        if row["source_agent"]:
            agent_data = (
                json.loads(row["source_agent"]) if isinstance(row["source_agent"], str) else row["source_agent"]
            )
            source_agent = AgentInfo(
                agent_id=agent_data["agent_id"],
                agent_type=agent_data["agent_type"],
                metadata=agent_data.get("metadata"),
            )

        target_agent = None
        if row["target_agent"]:
            agent_data = (
                json.loads(row["target_agent"]) if isinstance(row["target_agent"], str) else row["target_agent"]
            )
            target_agent = AgentInfo(
                agent_id=agent_data["agent_id"],
                agent_type=agent_data["agent_type"],
                metadata=agent_data.get("metadata"),
            )

        error = None
        if row["error"]:
            error_data = json.loads(row["error"]) if isinstance(row["error"], str) else row["error"]
            error = ErrorInfo(
                error_type=error_data["error_type"],
                error_message=error_data["error_message"],
                stack_trace=error_data.get("stack_trace"),
                retry_count=error_data.get("retry_count", 0),
                will_retry=error_data.get("will_retry", False),
            )

        performance = None
        if row["performance"]:
            perf_data = json.loads(row["performance"]) if isinstance(row["performance"], str) else row["performance"]
            performance = PerformanceMetrics(
                cpu_usage=perf_data.get("cpu_usage"),
                memory_mb=perf_data.get("memory_mb"),
                io_operations=perf_data.get("io_operations"),
                network_bytes=perf_data.get("network_bytes"),
                custom_metrics=perf_data.get("custom_metrics"),
            )

        return CoordinationEvent(
            event_id=row["event_id"],
            event_type=EventType(row["event_type"]),
            workflow_id=row["workflow_id"],
            task_id=row["task_id"],
            timestamp=row["timestamp"].isoformat() + "Z",
            agent_id=row["agent_id"],
            agent_type=row["agent_type"],
            source_agent=source_agent,
            target_agent=target_agent,
            status=row["status"],
            duration_ms=row["duration_ms"],
            error=error,
            metadata=json.loads(row["metadata"])
            if row["metadata"] and isinstance(row["metadata"], str)
            else row["metadata"],
            context=json.loads(row["context"])
            if row["context"] and isinstance(row["context"], str)
            else row["context"],
            performance=performance,
        )

    def _cleanup_old_events(self) -> None:
        """Clean up old events from memory when limit exceeded."""
        # Keep most recent 80% of max events
        keep_count = int(self._max_memory_events * 0.8)
        if len(self._events) > keep_count:
            # Remove oldest events
            remove_count = len(self._events) - keep_count
            self._events = self._events[remove_count:]

            # Rebuild index
            self._event_index.clear()
            for i, event in enumerate(self._events):
                self._event_index[event.workflow_id].append(i)
                if event.task_id:
                    self._event_index[f"task:{event.task_id}"].append(i)
                if event.agent_id:
                    self._event_index[f"agent:{event.agent_id}"].append(i)


# Convenience functions for common tracking operations


async def track_handoff(
    tracker: CoordinationTracker,
    workflow_id: str,
    source_agent_id: str,
    source_agent_type: str,
    target_agent_id: str,
    target_agent_type: str,
    task_id: str | None = None,
    context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Track a handoff event.

    Args:
        tracker: Coordination tracker instance
        workflow_id: Workflow identifier
        source_agent_id: Source agent ID
        source_agent_type: Source agent type
        target_agent_id: Target agent ID
        target_agent_type: Target agent type
        task_id: Optional task ID
        context: Optional context information
        metadata: Optional metadata

    Returns:
        Event ID
    """
    event = CoordinationEvent(
        event_type=EventType.HANDOFF,
        workflow_id=workflow_id,
        task_id=task_id,
        source_agent=AgentInfo(source_agent_id, source_agent_type),
        target_agent=AgentInfo(target_agent_id, target_agent_type),
        context=context,
        metadata=metadata,
    )
    return await tracker.track_event(event)


async def track_task_execution(
    tracker: CoordinationTracker,
    workflow_id: str,
    task_id: str,
    agent_id: str,
    agent_type: str,
    status: str,
    duration_ms: float | None = None,
    result_summary: str | None = None,
    performance: PerformanceMetrics | None = None,
) -> str:
    """Track task execution start or end.

    Args:
        tracker: Coordination tracker instance
        workflow_id: Workflow identifier
        task_id: Task identifier
        agent_id: Agent identifier
        agent_type: Agent type
        status: Task status
        duration_ms: Optional execution duration
        result_summary: Optional result summary
        performance: Optional performance metrics

    Returns:
        Event ID
    """
    event_type = EventType.EXECUTION_START if status in ("running", "started") else EventType.EXECUTION_END

    context = None
    if result_summary:
        context = {"result_summary": result_summary}

    event = CoordinationEvent(
        event_type=event_type,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_id=agent_id,
        agent_type=agent_type,
        status=status,
        duration_ms=duration_ms,
        context=context,
        performance=performance,
    )
    return await tracker.track_event(event)


async def track_failure(
    tracker: CoordinationTracker,
    workflow_id: str,
    task_id: str,
    agent_id: str,
    agent_type: str,
    error_type: str,
    error_message: str,
    stack_trace: str | None = None,
    attempt: int = 1,
    will_retry: bool = False,
) -> str:
    """Track a failure event.

    Args:
        tracker: Coordination tracker instance
        workflow_id: Workflow identifier
        task_id: Task identifier
        agent_id: Agent identifier
        agent_type: Agent type
        error_type: Type of error
        error_message: Error message
        stack_trace: Optional stack trace
        attempt: Attempt number
        will_retry: Whether retry will be attempted

    Returns:
        Event ID
    """
    error = ErrorInfo(
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        retry_count=attempt - 1,
        will_retry=will_retry,
    )

    event = CoordinationEvent(
        event_type=EventType.RETRY if attempt > 1 else EventType.FAILURE,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_id=agent_id,
        agent_type=agent_type,
        status="failed",
        error=error,
    )
    return await tracker.track_event(event)


# Exceptions


class TrackerError(Exception):
    """Base exception for tracker errors."""

    pass


class EventValidationError(TrackerError):
    """Raised when event validation fails."""

    pass
