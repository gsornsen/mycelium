# Source: skills/S2-coordination.md
# Line: 825
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check orchestration system health
from plugins.mycelium_core.coordination import check_coordination_health

health = await check_coordination_health()
print(f"Status: {health['status']}")
print(f"Active workflows: {health['active_workflows']}")
print(f"Queue depth: {health['queue_depth']}")

# Analyze workflow performance
events = await get_coordination_events(workflow_id="wf-abc-123")
total_handoff_time = sum(
    e["metadata"]["duration_ms"]
    for e in events["events"]
    if e["event_type"] == "handoff"
)
print(f"Total handoff overhead: {total_handoff_time}ms")

# Debug failed workflow
workflow_id = "wf-failed-123"
status = await get_workflow_status(workflow_id)
failed_step = status["steps"][status["current_step"]]
print(f"Failed at step {status['current_step']}: {failed_step['agent']}")

events = await get_coordination_events(
    workflow_id=workflow_id,
    event_type="failure"
)
print(f"Failure reason: {events['events'][0]['metadata']['error']}")
