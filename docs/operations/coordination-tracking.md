# Coordination Tracking System - Operations Guide

**Version:** 1.0 **Last Updated:** 2025-10-21 **Owners:** Backend Team

## Overview

The Coordination Tracking System provides comprehensive logging and monitoring of all inter-agent communications,
workflow executions, and coordination events in the Mycelium multi-agent system.

### Key Features

- **Complete Event History**: Track all coordination events including handoffs, executions, failures, and state changes
- **High Performance**: \<5% overhead on coordination operations
- **Efficient Storage**: \<10MB per 1000 events with PostgreSQL compression
- **Flexible Querying**: Rich query API for history retrieval and analysis
- **Structured Logging**: JSON-based event schema with validation
- **Real-time Monitoring**: Statistics and metrics for operational insights

### Architecture

```
┌─────────────────────────────────────────────────────┐
│          Workflow Orchestrator                       │
│  (generates coordination events)                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│          Coordination Tracker                        │
│  - Event validation                                  │
│  - PostgreSQL persistence                            │
│  - Query API                                         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│          PostgreSQL Database                         │
│  coordination_events table                           │
│  - Indexed by workflow_id, agent_id, timestamp       │
│  - JSONB columns for flexible data                   │
└─────────────────────────────────────────────────────┘
```

## Event Types

The system tracks the following event types:

### Handoff Events

- **`handoff`**: Agent-to-agent state transfer

### Task Execution Events

- **`execution_start`**: Task execution begins
- **`execution_end`**: Task execution completes

### Failure Events

- **`failure`**: Task or operation failure
- **`retry`**: Retry attempt after failure

### Workflow Lifecycle Events

- **`workflow_created`**: New workflow created
- **`workflow_started`**: Workflow execution begins
- **`workflow_completed`**: Workflow completes successfully
- **`workflow_failed`**: Workflow fails
- **`workflow_cancelled`**: Workflow cancelled by user
- **`workflow_paused`**: Workflow paused
- **`workflow_resumed`**: Workflow resumed from pause

### Task Lifecycle Events

- **`task_created`**: New task added to workflow
- **`task_started`**: Task begins execution
- **`task_completed`**: Task completes successfully
- **`task_failed`**: Task fails
- **`task_skipped`**: Task skipped (dependency failure with allow_failure=true)
- **`task_retrying`**: Task retry in progress

## Event Schema

Each event includes:

```json
{
  "event_id": "uuid",
  "event_type": "handoff|execution_start|...",
  "workflow_id": "workflow-identifier",
  "task_id": "task-identifier (optional)",
  "timestamp": "2025-10-21T10:30:00.000Z",
  "agent_id": "agent-identifier (optional)",
  "agent_type": "backend-developer (optional)",
  "source_agent": {
    "agent_id": "source-agent-id",
    "agent_type": "source-agent-type"
  },
  "target_agent": {
    "agent_id": "target-agent-id",
    "agent_type": "target-agent-type"
  },
  "status": "running|completed|failed|...",
  "duration_ms": 1523.5,
  "error": {
    "error_type": "TimeoutError",
    "message": "Task execution timeout",
    "attempt": 2,
    "stack_trace": "..."
  },
  "metadata": {
    "priority": "high",
    "tags": ["api", "database"]
  },
  "context": {
    "task_description": "Build REST API endpoints",
    "result_summary": "Created 5 endpoints",
    "variables": {"api_version": "v1"}
  },
  "performance": {
    "queue_time_ms": 10.5,
    "execution_time_ms": 1500.0,
    "total_time_ms": 1523.5
  }
}
```

## Usage

### Initialization

```python
from coordination.tracker import CoordinationTracker
import asyncpg

# Create database connection pool
pool = await asyncpg.create_pool(
    "postgresql://localhost:5432/mycelium_registry",
    min_size=2,
    max_size=10,
)

# Initialize tracker
tracker = CoordinationTracker(pool=pool)
await tracker.initialize()
```

### Tracking Events

#### Manual Event Creation

```python
from coordination.tracker import (
    CoordinationEvent,
    EventType,
    AgentInfo,
    ErrorInfo,
    PerformanceMetrics,
)

# Create handoff event
event = CoordinationEvent(
    event_type=EventType.HANDOFF,
    workflow_id="workflow-123",
    task_id="task-456",
    source_agent=AgentInfo("agent-001", "backend-developer"),
    target_agent=AgentInfo("agent-002", "frontend-developer"),
    context={"task_description": "Build REST API"},
    metadata={"priority": "high"},
)

event_id = await tracker.track_event(event)
```

#### Convenience Functions

```python
from coordination.tracker import (
    track_handoff,
    track_task_execution,
    track_failure,
)

# Track handoff
await track_handoff(
    tracker,
    workflow_id="workflow-123",
    source_agent_id="agent-001",
    source_agent_type="backend-developer",
    target_agent_id="agent-002",
    target_agent_type="frontend-developer",
    task_id="task-456",
)

# Track task execution
await track_task_execution(
    tracker,
    workflow_id="workflow-123",
    task_id="task-456",
    agent_id="agent-001",
    agent_type="backend-developer",
    status="completed",
    duration_ms=1523.5,
    result_summary="API endpoints created",
)

# Track failure
await track_failure(
    tracker,
    workflow_id="workflow-123",
    task_id="task-456",
    agent_id="agent-001",
    agent_type="backend-developer",
    error_type="TimeoutError",
    error_message="Task execution timeout",
    attempt=2,
)
```

### Querying Events

#### Get Workflow Events

```python
# Get all events for workflow
events = await tracker.get_workflow_events("workflow-123")

# Filter by event type
handoffs = await tracker.get_workflow_events(
    "workflow-123",
    event_type=EventType.HANDOFF,
)

# Limit results
recent_events = await tracker.get_workflow_events(
    "workflow-123",
    limit=50,
)
```

#### Get Task Events

```python
# Get all events for specific task
task_events = await tracker.get_task_events("task-456")
```

#### Get Agent Events

```python
# Get all events for agent
agent_events = await tracker.get_agent_events("agent-001")

# Filter by event type
agent_failures = await tracker.get_agent_events(
    "agent-001",
    event_type=EventType.FAILURE,
)
```

#### Get Handoff Chain

```python
# Get complete handoff chain for workflow
handoff_chain = await tracker.get_handoff_chain("workflow-123")

# Analyze handoff sequence
for i, handoff in enumerate(handoff_chain):
    print(f"Handoff {i+1}: {handoff.source_agent.agent_type} → {handoff.target_agent.agent_type}")
```

#### Get Workflow Timeline

```python
# Get complete workflow timeline
timeline = await tracker.get_workflow_timeline("workflow-123")

print(f"Total events: {timeline['total_events']}")
print(f"Duration: {timeline['duration_ms']}ms")
print(f"Lifecycle events: {len(timeline['lifecycle'])}")
print(f"Task events: {len(timeline['tasks'])}")
print(f"Handoffs: {len(timeline['handoffs'])}")
print(f"Failures: {len(timeline['failures'])}")
```

### Statistics and Monitoring

```python
# Workflow-specific statistics
stats = await tracker.get_statistics("workflow-123")
print(f"Total events: {stats['total_events']}")
print(f"Event types: {stats['event_types']}")
print(f"Average duration: {stats['avg_duration_ms']}ms")
print(f"Event type breakdown: {stats['event_type_counts']}")

# Global statistics
global_stats = await tracker.get_statistics()
print(f"Total workflows tracked: {global_stats['total_workflows']}")
print(f"Total events: {global_stats['total_events']}")
```

## Integration with Orchestrator

The tracker integrates seamlessly with the workflow orchestrator:

```python
from coordination.orchestrator import WorkflowOrchestrator
from coordination.state_manager import StateManager
from coordination.tracker import CoordinationTracker

# Initialize components
state_manager = StateManager(pool=pool)
await state_manager.initialize()

tracker = CoordinationTracker(pool=pool)
await tracker.initialize()

orchestrator = WorkflowOrchestrator(state_manager)

# Orchestrator automatically generates tracking events
# You can add custom tracking in task executors:

async def my_task_executor(context):
    # Track task start
    await track_task_execution(
        tracker,
        context.workflow_id,
        context.task_def.task_id,
        context.task_def.agent_id,
        context.task_def.agent_type,
        "running",
    )

    try:
        # Execute task
        result = await do_work()

        # Track success
        await track_task_execution(
            tracker,
            context.workflow_id,
            context.task_def.task_id,
            context.task_def.agent_id,
            context.task_def.agent_type,
            "completed",
            result_summary=result["summary"],
        )

        return result

    except Exception as e:
        # Track failure
        await track_failure(
            tracker,
            context.workflow_id,
            context.task_def.task_id,
            context.task_def.agent_id,
            context.task_def.agent_type,
            type(e).__name__,
            str(e),
        )
        raise
```

## Performance Characteristics

### Tracking Overhead

- **Target**: \<5% performance impact
- **Measured**: ~2-3% overhead on coordination operations
- **Async operations**: Non-blocking persistence

### Storage Efficiency

- **Target**: \<10MB per 1000 events
- **Measured**: ~6-8MB per 1000 events (with JSONB compression)
- **Retention**: Configurable (default: 90 days)

### Query Performance

- **Workflow events**: \<10ms for typical workflow (100-500 events)
- **Agent events**: \<20ms for active agent (1000+ events)
- **Timeline generation**: \<50ms for complex workflow

### Database Indexes

Optimized indexes ensure fast queries:

```sql
-- Primary queries
CREATE INDEX idx_events_workflow ON coordination_events(workflow_id, timestamp DESC);
CREATE INDEX idx_events_task ON coordination_events(task_id, timestamp DESC);
CREATE INDEX idx_events_agent ON coordination_events(agent_id, timestamp DESC);

-- Composite queries
CREATE INDEX idx_events_workflow_type ON coordination_events(workflow_id, event_type, timestamp DESC);
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Event Rate**: Events per second

   ```python
   stats = await tracker.get_statistics()
   event_rate = stats['total_events'] / time_window_seconds
   ```

1. **Failure Rate**: Percentage of failure events

   ```python
   failure_count = stats['event_type_counts'].get('failure', 0)
   failure_rate = failure_count / stats['total_events'] * 100
   ```

1. **Storage Growth**: Database size over time

   ```sql
   SELECT pg_total_relation_size('coordination_events') / 1024 / 1024 as size_mb;
   ```

1. **Query Performance**: Average query time

   ```python
   # Use PostgreSQL query stats
   SELECT query, mean_exec_time
   FROM pg_stat_statements
   WHERE query LIKE '%coordination_events%';
   ```

### Alerting Thresholds

- **High Failure Rate**: >10% failure events in last hour
- **Storage Growth**: >1GB/day unexpected growth
- **Query Slowdown**: P95 query time >100ms
- **Event Backlog**: >1000 events waiting to be processed

## Maintenance

### Data Retention

Configure retention policy:

```python
# Delete events older than 90 days
async def cleanup_old_events(tracker, days=90):
    async with tracker._pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM coordination_events
            WHERE timestamp < NOW() - INTERVAL '%s days'
            """,
            days,
        )
    print(f"Deleted {result} old events")
```

### Backup and Recovery

```bash
# Backup coordination events
pg_dump -h localhost -U mycelium -d mycelium_registry \
    -t coordination_events > coordination_events_backup.sql

# Restore
psql -h localhost -U mycelium -d mycelium_registry \
    < coordination_events_backup.sql
```

### Vacuum and Analyze

```sql
-- Regular maintenance
VACUUM ANALYZE coordination_events;

-- Full vacuum if needed
VACUUM FULL coordination_events;
```

## Troubleshooting

### High Storage Usage

**Symptom**: Database size growing faster than expected

**Solutions**:

1. Check event volume: `SELECT COUNT(*), event_type FROM coordination_events GROUP BY event_type`
1. Reduce retention period
1. Archive old events to cold storage
1. Check for duplicate events

### Slow Queries

**Symptom**: Query performance degraded

**Solutions**:

1. Check index usage: `EXPLAIN ANALYZE SELECT ...`
1. Update statistics: `ANALYZE coordination_events`
1. Rebuild indexes: `REINDEX TABLE coordination_events`
1. Add missing indexes for specific query patterns

### Missing Events

**Symptom**: Expected events not appearing in history

**Solutions**:

1. Check validation errors in logs
1. Verify tracker is initialized
1. Check database connection
1. Verify workflow/task IDs are correct

### Performance Impact

**Symptom**: Coordination operations slowed by tracking

**Solutions**:

1. Disable validation for performance: `CoordinationTracker(enable_validation=False)`
1. Increase connection pool size
1. Use async/await properly to avoid blocking
1. Consider batching events (for very high volume)

## Security Considerations

### Data Privacy

The tracking system stores:

- ✅ **Safe**: Event metadata, timestamps, agent IDs, workflow IDs
- ✅ **Safe**: Task descriptions and result summaries
- ⚠️ **Caution**: Context variables (may contain sensitive data)
- ❌ **Avoid**: User credentials, API keys, PII

### Access Control

Ensure proper database permissions:

```sql
-- Read-only access for analytics
GRANT SELECT ON coordination_events TO analytics_user;

-- Full access for coordination system
GRANT ALL ON coordination_events TO mycelium_app;
```

### Audit Logging

Track who accesses coordination history:

```python
# Add audit logging to queries
logger.info(
    f"User {user_id} accessed workflow events",
    extra={"workflow_id": workflow_id, "user_id": user_id}
)
```

## Best Practices

1. **Track Meaningful Events**: Don't over-track; focus on coordination points
1. **Use Structured Context**: Include relevant context but avoid large payloads
1. **Monitor Performance**: Track overhead and optimize if needed
1. **Clean Up Regularly**: Implement retention policies
1. **Index Appropriately**: Add indexes for your query patterns
1. **Validate Critical Events**: Enable validation for production
1. **Use Convenience Functions**: Prefer helper functions for common operations
1. **Handle Errors Gracefully**: Don't let tracking failures break workflows

## Future Enhancements

Planned features:

- **Event Streaming**: Real-time event streams via WebSocket
- **Analytics Dashboard**: Visual workflow analytics
- **Anomaly Detection**: ML-based detection of unusual patterns
- **Event Replay**: Replay workflows from event history
- **Cross-Workflow Analysis**: Track patterns across multiple workflows

## Support

For issues or questions:

- **Documentation**: `/docs/operations/coordination-tracking.md`
- **Code**: `/plugins/mycelium-core/coordination/tracker.py`
- **Tests**: `/tests/integration/test_tracking.py`
- **Team**: backend-developer team

## References

- [Workflow Orchestration Engine](../technical/orchestration-engine.md)
- [Handoff Protocol](../technical/handoff-protocol.md)
- [State Management](../technical/state-management.md)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/performance-tips.html)
