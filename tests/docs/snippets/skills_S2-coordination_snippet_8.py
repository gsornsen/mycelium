# Source: skills/S2-coordination.md
# Line: 340
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get all events for a workflow
events = await get_coordination_events(workflow_id="wf-abc-123")

# Get handoff events only
events = await get_coordination_events(
    event_type="handoff",
    limit=50
)

# Get events for a specific agent
events = await get_coordination_events(
    agent_id="security-expert",
    limit=20
)
