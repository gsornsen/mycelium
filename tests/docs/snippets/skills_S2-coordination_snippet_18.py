# Source: skills/S2-coordination.md
# Line: 686
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Critical deployment: abort on failure
workflow = await coordinate_workflow(
    steps=[...],
    failure_strategy="abort"
)

# Best-effort analysis: continue on failure
workflow = await coordinate_workflow(
    steps=[...],
    failure_strategy="continue"
)
