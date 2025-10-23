# Source: operations/coordination-tracking.md
# Line: 219
# Valid syntax: True
# Has imports: False
# Has assignments: True

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