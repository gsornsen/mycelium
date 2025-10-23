# Source: skills/S2-coordination.md
# Line: 627
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Meta-skill orchestration (M04)
workflow = await coordinate_workflow(
    steps=[
        {"skill": "code-analysis", "params": {...}},
        {"skill": "refactoring", "depends_on": ["step-0"]},
        {"skill": "test-generation", "depends_on": ["step-1"]}
    ]
)