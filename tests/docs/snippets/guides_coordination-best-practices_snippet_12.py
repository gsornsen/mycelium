# Source: guides/coordination-best-practices.md
# Line: 470
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Rich error context
try:
    workflow = coordinate_workflow(steps=[...])
except WorkflowExecutionError as e:
    # Get detailed failure information
    events = get_coordination_events(
        workflow_id=e.workflow_id,
        event_type="failure"
    )

    for event in events["events"]:
        print(f"Failed Step: {event['metadata']['step']}")
        print(f"Agent: {event['metadata']['agent']}")
        print(f"Error: {event['metadata']['error']}")
        print(f"Context: {event['metadata']['context']}")
        print(f"Timestamp: {event['timestamp']}")

        # Log to monitoring system
        logger.error(
            "Workflow step failed",
            extra={
                "workflow_id": e.workflow_id,
                "step": event['metadata']['step'],
                "agent": event['metadata']['agent'],
                "error": event['metadata']['error']
            }
        )

# ❌ BAD: Minimal error handling
try:
    workflow = coordinate_workflow(steps=[...])
except Exception as e:
    print(f"Failed: {e}")  # No context, hard to debug