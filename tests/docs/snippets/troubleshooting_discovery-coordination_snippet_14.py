# Source: troubleshooting/discovery-coordination.md
# Line: 266
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Check detailed status
status = get_workflow_status(workflow["workflow_id"], include_steps=True)

print(f"Current Step: {status['current_step']}")
print(f"Steps Completed: {status['steps_completed']}/{status['steps_total']}")

# Check which step is stuck
for step in status["steps"]:
    if step["status"] == "in_progress":
        print(f"\nStuck at step {step['step']}:")
        print(f"  Agent: {step['agent']}")
        print(f"  Started: {step['started_at']}")
        print(f"  Duration so far: {calculate_duration(step['started_at'])}s")

# Check coordination events
events = get_coordination_events(
    workflow_id=workflow["workflow_id"],
    limit=50
)

# Look for errors or warnings
for event in events["events"]:
    if event["event_type"] in ["failure", "warning", "timeout"]:
        print(f"\n{event['event_type']}: {event['metadata']}")