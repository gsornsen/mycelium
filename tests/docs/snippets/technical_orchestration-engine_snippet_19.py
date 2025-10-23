# Source: technical/orchestration-engine.md
# Line: 548
# Valid syntax: True
# Has imports: False
# Has assignments: True

# View state history
state = await state_manager.get_workflow(workflow_id)
print(f"Current version: {state.version}")

# Rollback to inspect previous state
for version in range(1, state.version):
    historical = await state_manager.rollback_workflow(workflow_id, version)
    print(f"Version {version}: {historical.status}")

    # Restore to current version
    await state_manager.rollback_workflow(workflow_id, state.version)