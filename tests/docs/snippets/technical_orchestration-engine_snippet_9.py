# Source: technical/orchestration-engine.md
# Line: 248
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Non-critical task that won't abort workflow if it fails
task = TaskDefinition(
    task_id="optional-optimization",
    agent_id="optimizer",
    agent_type="optimizer",
    allow_failure=True,  # Workflow continues even if this fails
)
