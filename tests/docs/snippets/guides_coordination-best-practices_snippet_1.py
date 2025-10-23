# Source: guides/coordination-best-practices.md
# Line: 28
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Clear single purpose per step
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-validator",
            "task": "Validate CSV data format and completeness",
            "params": {"file": "data.csv", "schema": "schema.json"}
        },
        {
            "agent": "data-transformer",
            "task": "Transform validated data to JSON format",
            "depends_on": ["step-0"],
            "params": {"input": "data.csv", "output": "data.json"}
        },
        {
            "agent": "data-loader",
            "task": "Load transformed data into PostgreSQL",
            "depends_on": ["step-1"],
            "params": {"file": "data.json", "table": "users"}
        }
    ]
)

# ❌ BAD: Vague, multi-purpose steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Process data",  # Too vague
            "params": {"file": "data.csv"}
        },
        {
            "agent": "backend-developer",
            "task": "Do database stuff",  # Unclear purpose
            "depends_on": ["step-0"]
        }
    ]
)
