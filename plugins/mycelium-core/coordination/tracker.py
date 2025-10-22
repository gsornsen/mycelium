"""Coordination event tracking system for inter-agent communication logging.

This module implements comprehensive tracking of all coordination events including
handoffs, task executions, workflow state changes, and failures. Events are stored
in PostgreSQL with efficient indexing for history retrieval and analysis.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import jsonschema
from asyncpg import Pool


# Load event schema
SCHEMA_PATH = Path(__file__).parent / "schemas" / "events.json"
with open(SCHEMA_PATH) as f:
    EVENT_SCHEMA = json.load(f)


# Set up structured logging
logger = logging.getLogger(__name__)


class TrackerError(Exception):
    """Base exception for tracker errors."""
    pass


class EventValidationError(TrackerError):
    """Raised when event validation fails."""
    pass


class EventType(str, Enum):
    """Coordination event types."""
    # Handoff events
    HANDOFF = "handoff"

    # Task execution events
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"

    # Failure events
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

    # Task lifecycle events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    TASK_RETRYING = "task_retrying"


@dataclass
class AgentInfo:
    """Agent information for events."""
    agent_id: str
    agent_type: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {"agent_id": self.agent_id, "agent_type": self.agent_type}


@dataclass
class ErrorInfo:
    """Error information for failure events."""
    error_type: str
    message: str
    attempt: int = 0
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "error_type": self.error_type,
            "message": self.message,
            "attempt": self.attempt,
        }
        if self.stack_trace:
            result["stack_trace"] = self.stack_trace
        return result


@dataclass
class PerformanceMetrics:
    """Performance metrics for events."""
    queue_time_ms: Optional[float] = None
    execution_time_ms: Optional[float] = None
    total_time_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CoordinationEvent:
    """Coordination event with all tracking information."""
    event_type: EventType
    workflow_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    source_agent: Optional[AgentInfo] = None
    target_agent: Optional[AgentInfo] = None
    status: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[ErrorInfo] = None
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    performance: Optional[PerformanceMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage/validation."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
        }

        # Add optional fields
        if self.task_id:
            result["task_id"] = self.task_id
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.agent_type:
            result["agent_type"] = self.agent_type
        if self.source_agent:
            result["source_agent"] = self.source_agent.to_dict()
        if self.target_agent:
            result["target_agent"] = self.target_agent.to_dict()
        if self.status:
            result["status"] = self.status
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.error:
            result["error"] = self.error.to_dict()
        if self.metadata:
            result["metadata"] = self.metadata
        if self.context:
            result["context"] = self.context
        if self.performance:
            perf_dict = self.performance.to_dict()
            if perf_dict:
                result["performance"] = perf_dict

        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize event to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class CoordinationTracker:
    """Tracks all coordination events with PostgreSQL persistence.

    Features:
    - Structured event logging with schema validation
    - Efficient indexing for fast queries
    - <5% performance impact on coordination operations
    - <10MB storage per 1000 events (compressed)
    - Query API for history retrieval and analysis
    """

    def __init__(
        self,
        pool: Optional[Pool] = None,
        connection_string: Optional[str] = None,
        enable_validation: bool = True,
    ):
        """Initialize coordination tracker.

        Args:
            pool: Optional existing connection pool
            connection_string: Optional PostgreSQL connection string
            enable_validation: Whether to validate events against schema (default: True)
        """
        if pool is not None:
            self._pool = pool
            self._owns_pool = False
        else:
            self._connection_string = connection_string or "postgresql://localhost:5432/mycelium_registry"
            self._pool: Optional[Pool] = None
            self._owns_pool = True

        self._enable_validation = enable_validation
        self._event_counts: Dict[str, int] = {}  # For performance monitoring

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        if self._pool is None and self._owns_pool:
            self._pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
        await self._ensure_schema()
        logger.info("Coordination tracker initialized")

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool is not None and self._owns_pool:
            await self._pool.close()
            self._pool = None
        logger.info("Coordination tracker closed")

    async def _ensure_schema(self) -> None:
        """Ensure coordination events table exists with proper indexes."""
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

        schema_sql = """
        CREATE TABLE IF NOT EXISTS coordination_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            task_id TEXT,
            timestamp TIMESTAMP NOT NULL,
            agent_id TEXT,
            agent_type TEXT,
            source_agent JSONB,
            target_agent JSONB,
            status TEXT,
            duration_ms REAL,
            error JSONB,
            metadata JSONB,
            context JSONB,
            performance JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- Indexes for efficient queries
        CREATE INDEX IF NOT EXISTS idx_events_workflow ON coordination_events(workflow_id, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_events_task ON coordination_events(task_id, timestamp DESC) WHERE task_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_events_agent ON coordination_events(agent_id, timestamp DESC) WHERE agent_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_events_type ON coordination_events(event_type, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON coordination_events(timestamp DESC);

        -- Composite index for common query patterns
        CREATE INDEX IF NOT EXISTS idx_events_workflow_type ON coordination_events(workflow_id, event_type, timestamp DESC);
        """

        async with self._pool.acquire() as conn:
            await conn.execute(schema_sql)

    def _validate_event(self, event: CoordinationEvent) -> None:
        """Validate event against JSON schema.

        Args:
            event: Event to validate

        Raises:
            EventValidationError: If validation fails
        """
        if not self._enable_validation:
            return

        try:
            event_dict = event.to_dict()
            jsonschema.validate(instance=event_dict, schema=EVENT_SCHEMA)
        except jsonschema.ValidationError as e:
            raise EventValidationError(f"Event validation failed: {e.message}") from e
        except Exception as e:
            raise EventValidationError(f"Event validation error: {str(e)}") from e

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
            raise TrackerError("Tracker not initialized")

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
                    "event_type": event.event_type.value,
                },
            )

            return event.event_id

        except Exception as e:
            logger.error(f"Failed to track event: {str(e)}", exc_info=True)
            raise TrackerError(f"Failed to track event: {str(e)}") from e

    async def get_workflow_events(
        self,
        workflow_id: str,
        event_type: Optional[EventType] = None,
        limit: int = 1000,
    ) -> List[CoordinationEvent]:
        """Retrieve events for a workflow.

        Args:
            workflow_id: Workflow identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of coordination events ordered by timestamp (newest first)
        """
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

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

            return [self._row_to_event(row) for row in rows]

    async def get_task_events(
        self,
        task_id: str,
        limit: int = 100,
    ) -> List[CoordinationEvent]:
        """Retrieve events for a specific task.

        Args:
            task_id: Task identifier
            limit: Maximum number of events to return

        Returns:
            List of coordination events ordered by timestamp
        """
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

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

            return [self._row_to_event(row) for row in rows]

    async def get_agent_events(
        self,
        agent_id: str,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[CoordinationEvent]:
        """Retrieve events for a specific agent.

        Args:
            agent_id: Agent identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of coordination events ordered by timestamp
        """
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

        async with self._pool.acquire() as conn:
            if event_type:
                rows = await conn.fetch(
                    """
                    SELECT * FROM coordination_events
                    WHERE agent_id = $1 AND event_type = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                    """,
                    agent_id,
                    event_type.value,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM coordination_events
                    WHERE agent_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                    """,
                    agent_id,
                    limit,
                )

            return [self._row_to_event(row) for row in rows]

    async def get_handoff_chain(self, workflow_id: str) -> List[CoordinationEvent]:
        """Retrieve complete handoff chain for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of handoff events in chronological order
        """
        return await self.get_workflow_events(
            workflow_id,
            event_type=EventType.HANDOFF,
        )

    async def get_workflow_timeline(
        self,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Get complete timeline of workflow execution.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Timeline with events grouped by task and phase
        """
        events = await self.get_workflow_events(workflow_id)

        # Group events by phase
        lifecycle_events = [e for e in events if e.event_type.value.startswith("workflow_")]
        task_events = [e for e in events if e.event_type.value.startswith("task_")]
        handoff_events = [e for e in events if e.event_type == EventType.HANDOFF]
        failure_events = [e for e in events if e.event_type in (EventType.FAILURE, EventType.RETRY)]

        # Calculate workflow duration
        if events:
            start_event = next((e for e in reversed(events) if e.event_type == EventType.WORKFLOW_STARTED), None)
            end_event = next((e for e in events if e.event_type in (EventType.WORKFLOW_COMPLETED, EventType.WORKFLOW_FAILED)), None)

            duration_ms = None
            if start_event and end_event:
                start_time = datetime.fromisoformat(start_event.timestamp.rstrip("Z"))
                end_time = datetime.fromisoformat(end_event.timestamp.rstrip("Z"))
                duration_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "workflow_id": workflow_id,
                "total_events": len(events),
                "duration_ms": duration_ms,
                "lifecycle": [e.to_dict() for e in lifecycle_events],
                "tasks": [e.to_dict() for e in task_events],
                "handoffs": [e.to_dict() for e in handoff_events],
                "failures": [e.to_dict() for e in failure_events],
            }

        return {
            "workflow_id": workflow_id,
            "total_events": 0,
            "duration_ms": None,
            "lifecycle": [],
            "tasks": [],
            "handoffs": [],
            "failures": [],
        }

    async def get_statistics(
        self,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get tracking statistics.

        Args:
            workflow_id: Optional workflow to filter stats

        Returns:
            Statistics dictionary with event counts and performance metrics
        """
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

        async with self._pool.acquire() as conn:
            if workflow_id:
                # Workflow-specific stats
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT event_type) as event_types,
                        AVG(duration_ms) as avg_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        MIN(timestamp) as first_event,
                        MAX(timestamp) as last_event
                    FROM coordination_events
                    WHERE workflow_id = $1
                    """,
                    workflow_id,
                )

                # Event type breakdown
                type_counts = await conn.fetch(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM coordination_events
                    WHERE workflow_id = $1
                    GROUP BY event_type
                    ORDER BY count DESC
                    """,
                    workflow_id,
                )
            else:
                # Global stats
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT workflow_id) as total_workflows,
                        COUNT(DISTINCT event_type) as event_types,
                        AVG(duration_ms) as avg_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        MIN(timestamp) as first_event,
                        MAX(timestamp) as last_event
                    FROM coordination_events
                    """
                )

                # Event type breakdown
                type_counts = await conn.fetch(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM coordination_events
                    GROUP BY event_type
                    ORDER BY count DESC
                    """
                )

            return {
                "total_events": stats["total_events"],
                "total_workflows": stats.get("total_workflows", 1 if workflow_id else 0),
                "event_types": stats["event_types"],
                "avg_duration_ms": float(stats["avg_duration_ms"]) if stats["avg_duration_ms"] else None,
                "max_duration_ms": float(stats["max_duration_ms"]) if stats["max_duration_ms"] else None,
                "first_event": stats["first_event"].isoformat() + "Z" if stats["first_event"] else None,
                "last_event": stats["last_event"].isoformat() + "Z" if stats["last_event"] else None,
                "event_type_counts": {row["event_type"]: row["count"] for row in type_counts},
            }

    async def delete_workflow_events(self, workflow_id: str) -> int:
        """Delete all events for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Number of events deleted
        """
        if self._pool is None:
            raise TrackerError("Tracker not initialized")

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM coordination_events WHERE workflow_id = $1",
                workflow_id,
            )
            # Extract count from result string "DELETE N"
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Deleted {count} events for workflow {workflow_id}")
            return count

    def _row_to_event(self, row: asyncpg.Record) -> CoordinationEvent:
        """Convert database row to coordination event.

        Args:
            row: Database row

        Returns:
            CoordinationEvent object
        """
        # Parse source/target agents
        source_agent = None
        if row["source_agent"]:
            data = row["source_agent"] if isinstance(row["source_agent"], dict) else json.loads(row["source_agent"])
            source_agent = AgentInfo(**data)

        target_agent = None
        if row["target_agent"]:
            data = row["target_agent"] if isinstance(row["target_agent"], dict) else json.loads(row["target_agent"])
            target_agent = AgentInfo(**data)

        # Parse error
        error = None
        if row["error"]:
            data = row["error"] if isinstance(row["error"], dict) else json.loads(row["error"])
            error = ErrorInfo(**data)

        # Parse performance
        performance = None
        if row["performance"]:
            data = row["performance"] if isinstance(row["performance"], dict) else json.loads(row["performance"])
            performance = PerformanceMetrics(**data)

        # Parse metadata and context
        metadata = row["metadata"] if isinstance(row["metadata"], dict) else (
            json.loads(row["metadata"]) if row["metadata"] else None
        )
        context = row["context"] if isinstance(row["context"], dict) else (
            json.loads(row["context"]) if row["context"] else None
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
            metadata=metadata,
            context=context,
            performance=performance,
        )


# Convenience functions for common tracking operations

async def track_handoff(
    tracker: CoordinationTracker,
    workflow_id: str,
    source_agent_id: str,
    source_agent_type: str,
    target_agent_id: str,
    target_agent_type: str,
    task_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
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
    duration_ms: Optional[float] = None,
    result_summary: Optional[str] = None,
    performance: Optional[PerformanceMetrics] = None,
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
    attempt: int = 1,
    stack_trace: Optional[str] = None,
) -> str:
    """Track a failure event.

    Args:
        tracker: Coordination tracker instance
        workflow_id: Workflow identifier
        task_id: Task identifier
        agent_id: Agent identifier
        agent_type: Agent type
        error_type: Error type
        error_message: Error message
        attempt: Attempt number
        stack_trace: Optional stack trace

    Returns:
        Event ID
    """
    event = CoordinationEvent(
        event_type=EventType.FAILURE,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_id=agent_id,
        agent_type=agent_type,
        status="failed",
        error=ErrorInfo(
            error_type=error_type,
            message=error_message,
            attempt=attempt,
            stack_trace=stack_trace,
        ),
    )
    return await tracker.track_event(event)
