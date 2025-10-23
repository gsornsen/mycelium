# Source: guides/coordination-best-practices.md
# Line: 516
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Parallel independent tasks
workflow = coordinate_workflow(
    steps=[
        # These can run in parallel
        {
            "agent": "frontend-developer",
            "task": "Build React components"
        },
        {
            "agent": "backend-developer",
            "task": "Implement API endpoints"
        },
        {
            "agent": "database-architect",
            "task": "Design database schema"
        },
        # This waits for all three
        {
            "agent": "integration-engineer",
            "task": "Connect frontend, backend, and database",
            "depends_on": ["step-0", "step-1", "step-2"]
        }
    ],
    execution_mode="parallel"
)

# ❌ BAD: Unnecessary sequential execution
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend-developer", "task": "Build components"},
        {
            "agent": "backend-developer",
            "task": "Implement API",
            "depends_on": ["step-0"]  # Not actually dependent!
        },
        {
            "agent": "database-architect",
            "task": "Design schema",
            "depends_on": ["step-1"]  # Not actually dependent!
        }
    ],
    execution_mode="sequential"
)
