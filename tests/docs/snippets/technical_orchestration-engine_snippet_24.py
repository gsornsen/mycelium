# Source: technical/orchestration-engine.md
# Line: 608
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: positional argument follows keyword argument (<unknown>, line 2)

tasks = [
    TaskDefinition(task_id="critical", allow_failure=False, ...),  # Must succeed
    TaskDefinition(task_id="optional", allow_failure=True, ...),  # Nice to have
]