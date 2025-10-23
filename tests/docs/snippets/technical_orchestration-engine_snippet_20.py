# Source: technical/orchestration-engine.md
# Line: 567
# Valid syntax: True
# Has imports: False
# Has assignments: True

tasks = [
    TaskDefinition(task_id="parse", agent_id="parser", agent_type="parser"),
    TaskDefinition(task_id="validate", agent_id="validator", agent_type="validator"),
    TaskDefinition(task_id="transform", agent_id="transformer", agent_type="transformer"),
]