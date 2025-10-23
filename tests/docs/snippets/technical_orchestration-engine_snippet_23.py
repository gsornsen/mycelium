# Source: technical/orchestration-engine.md
# Line: 596
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: positional argument follows keyword argument (<unknown>, line 3)

# C doesn't actually need A's output
tasks = [
    TaskDefinition(task_id="A", ...),
    TaskDefinition(task_id="B", dependencies=["A"], ...),
    TaskDefinition(task_id="C", dependencies=["A", "B"], ...),  # Remove A
]