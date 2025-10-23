# Source: technical/orchestration-engine.md
# Line: 517
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get current status
state = await orchestrator.get_workflow_status(workflow_id)

print(f"Status: {state.status}")
print(f"Version: {state.version}")
print(f"Started: {state.started_at}")

# Check individual tasks
for task_id, task in state.tasks.items():
    print(f"{task_id}: {task.status}")
    if task.error:
        print(f"  Error: {task.error}")
