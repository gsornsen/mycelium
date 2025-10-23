# Source: guides/coordination-best-practices.md
# Line: 902
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: invalid decimal literal (<unknown>, line 12)

# ❌ ANTI-PATTERN: Monolithic workflow
workflow = coordinate_workflow(
    steps=[
        # 50 steps covering entire application lifecycle
        {"agent": "...", "task": "..."},
        # ...
        {"agent": "...", "task": "..."}
    ]
)

# ✅ SOLUTION: Compose smaller workflows
frontend_workflow = coordinate_workflow(steps=[...5_frontend_steps])
backend_workflow = coordinate_workflow(steps=[...5_backend_steps])
deployment_workflow = coordinate_workflow(steps=[...3_deployment_steps])

# Compose results
full_result = {
    "frontend": frontend_workflow,
    "backend": backend_workflow,
    "deployment": deployment_workflow
}