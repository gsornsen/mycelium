# Source: technical/orchestration-engine.md
# Line: 260
# Valid syntax: True
# Has imports: False
# Has assignments: True

task = TaskDefinition(
    task_id="bounded-task",
    agent_id="agent-1",
    agent_type="slow-processor",
    timeout=30.0,  # 30 second timeout
)
