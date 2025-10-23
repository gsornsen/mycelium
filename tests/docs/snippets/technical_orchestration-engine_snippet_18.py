# Source: technical/orchestration-engine.md
# Line: 534
# Valid syntax: True
# Has imports: False
# Has assignments: True

# List all workflows
all_workflows = await state_manager.list_workflows()

# List by status
running = await state_manager.list_workflows(status=WorkflowStatus.RUNNING)
failed = await state_manager.list_workflows(status=WorkflowStatus.FAILED)

# Limit results
recent = await state_manager.list_workflows(limit=10)
