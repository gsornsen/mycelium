# Source: technical/orchestration-engine.md
# Line: 282
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Pause workflow
await orchestrator.pause_workflow(workflow_id)

# Resume workflow
await orchestrator.resume_workflow(workflow_id)

# Cancel workflow
await orchestrator.cancel_workflow(workflow_id)

# Rollback to previous version
await orchestrator.rollback_workflow(workflow_id, version=1)