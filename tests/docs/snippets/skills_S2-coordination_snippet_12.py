# Source: skills/S2-coordination.md
# Line: 480
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Code quality workflow with conditional steps
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "code-analyzer",
            "task": "Analyze code quality metrics",
            "params": {"file": "main.py"}
        },
        {
            "agent": "refactoring-expert",
            "task": "Refactor complex functions",
            "depends_on": ["step-0"],
            "condition": "complexity_score > 10",  # Only run if complex
            "params": {"focus": "reduce_complexity"}
        },
        {
            "agent": "test-generator",
            "task": "Generate missing tests",
            "depends_on": ["step-0"],
            "condition": "coverage < 80",  # Only run if coverage low
            "params": {"target_coverage": 90}
        }
    ],
    execution_mode="conditional"
)
