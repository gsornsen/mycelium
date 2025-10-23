# Source: technical/orchestration-engine.md
# Line: 586
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: positional argument follows keyword argument (<unknown>, line 3)

# Linear dependencies
tasks = [
    TaskDefinition(task_id="A", ...),
    TaskDefinition(task_id="B", dependencies=["A"], ...),
    TaskDefinition(task_id="C", dependencies=["B"], ...),
]