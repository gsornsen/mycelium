# Source: technical/orchestration-engine.md
# Line: 271
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Start workflow in background
await orchestrator.execute_workflow(workflow_id, background=True)

# Check status later
status = await orchestrator.get_workflow_status(workflow_id)
print(f"Status: {status.status}")
