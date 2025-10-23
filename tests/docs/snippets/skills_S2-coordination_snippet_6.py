# Source: skills/S2-coordination.md
# Line: 281
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Check workflow progress
status = await get_workflow_status("wf-abc-123")

if status["status"] == "in_progress":
    print(f"Progress: {status['progress_percent']}%")
    print(f"Current step: {status['current_step']} of {status['steps_total']}")

# Lightweight status check without step details
status = await get_workflow_status("wf-abc-123", include_steps=False)