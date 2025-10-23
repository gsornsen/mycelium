# Source: technical/orchestration-engine.md
# Line: 389
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Initial version
state = await state_manager.create_workflow(tasks)
assert state.version == 1

# After update
state.status = WorkflowStatus.RUNNING
updated = await state_manager.update_workflow(state)
assert updated.version == 2

# Rollback to previous version
restored = await state_manager.rollback_workflow(workflow_id, version=1)
assert restored.version == 1
