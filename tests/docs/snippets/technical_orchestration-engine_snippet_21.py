# Source: technical/orchestration-engine.md
# Line: 576
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Avoid single task doing everything
tasks = [
    TaskDefinition(task_id="do_everything", agent_id="agent", agent_type="all-in-one"),
]
