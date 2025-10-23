# Source: guides/coordination-best-practices.md
# Line: 615
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Batch similar tasks
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "test-generator",
            "task": "Generate tests for multiple modules",
            "params": {
                "modules": ["auth.py", "api.py", "models.py"],  # Batch
                "coverage_target": 90
            }
        }
    ]
)

# ❌ BAD: Individual workflows for each task
for module in ["auth.py", "api.py", "models.py"]:
    workflow = coordinate_workflow(
        steps=[
            {
                "agent": "test-generator",
                "task": f"Generate tests for {module}",
                "params": {"module": module}
            }
        ]
    )
