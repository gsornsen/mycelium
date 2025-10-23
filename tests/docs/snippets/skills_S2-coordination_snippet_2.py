# Source: skills/S2-coordination.md
# Line: 96
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Sequential code review workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "python-pro",
            "task": "Review code style and best practices",
            "params": {"file": "api.py"}
        },
        {
            "agent": "security-expert",
            "task": "Security audit focusing on authentication",
            "depends_on": ["step-0"],
            "params": {"file": "api.py"}
        },
        {
            "agent": "performance-optimizer",
            "task": "Performance analysis and recommendations",
            "depends_on": ["step-0"],
            "params": {"file": "api.py"}
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# Parallel data processing workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Process dataset A",
            "params": {"dataset": "customers.csv"}
        },
        {
            "agent": "data-engineer",
            "task": "Process dataset B",
            "params": {"dataset": "orders.csv"}
        },
        {
            "agent": "ml-engineer",
            "task": "Train model on combined data",
            "depends_on": ["step-0", "step-1"],
            "params": {"model_type": "random_forest"}
        }
    ],
    execution_mode="parallel"
)
