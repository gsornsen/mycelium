# Source: skills/S2-coordination.md
# Line: 614
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Token-aware coordination (M03)
workflow = await coordinate_workflow(
    steps=[...],
    token_budget=10000,  # Total budget
    budget_allocation="proportional"  # Or "equal", "weighted"
)