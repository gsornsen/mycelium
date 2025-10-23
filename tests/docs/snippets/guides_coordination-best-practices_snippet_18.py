# Source: guides/coordination-best-practices.md
# Line: 705
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Comprehensive audit logging
async def audited_workflow(workflow_spec):
    # Log workflow initiation
    audit_log.record({
        "event": "workflow_started",
        "workflow_spec": workflow_spec,
        "user": get_current_user(),
        "timestamp": datetime.now()
    })

    try:
        workflow = coordinate_workflow(**workflow_spec)

        # Log completion
        audit_log.record({
            "event": "workflow_completed",
            "workflow_id": workflow["workflow_id"],
            "duration_ms": workflow["total_duration_ms"],
            "timestamp": datetime.now()
        })

        return workflow

    except Exception as e:
        # Log failure
        audit_log.record({
            "event": "workflow_failed",
            "error": str(e),
            "timestamp": datetime.now()
        })
        raise

# Get audit trail
events = get_coordination_events(workflow_id="wf-123")
for event in events["events"]:
    audit_log.record(event)