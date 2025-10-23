# Source: operations/coordination-tracking.md
# Line: 172
# Valid syntax: True
# Has imports: True
# Has assignments: False

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