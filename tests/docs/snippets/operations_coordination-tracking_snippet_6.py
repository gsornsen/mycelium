# Source: operations/coordination-tracking.md
# Line: 245
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get all events for agent
agent_events = await tracker.get_agent_events("agent-001")

# Filter by event type
agent_failures = await tracker.get_agent_events(
    "agent-001",
    event_type=EventType.FAILURE,
)
