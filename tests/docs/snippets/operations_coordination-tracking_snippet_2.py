# Source: operations/coordination-tracking.md
# Line: 147
# Valid syntax: True
# Has imports: True
# Has assignments: True

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