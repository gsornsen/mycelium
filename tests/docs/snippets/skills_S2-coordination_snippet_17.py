# Source: skills/S2-coordination.md
# Line: 649
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ Good: Clear dependencies and descriptions
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Load and validate customer data from CSV",
            "params": {"file": "customers.csv", "validations": ["email", "phone"]}
        },
        {
            "agent": "ml-engineer",
            "task": "Train churn prediction model using validated data",
            "depends_on": ["step-0"],
            "params": {"model": "random_forest", "features": ["tenure", "usage"]}
        }
    ]
)

# ❌ Bad: Vague tasks, unclear dependencies
workflow = await coordinate_workflow(
    steps=[
        {"agent": "data-engineer", "task": "process data"},
        {"agent": "ml-engineer", "task": "train model"}
    ]
)
