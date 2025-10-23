# Source: skills/S2-coordination.md
# Line: 512
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Deployment workflow with automatic fallbacks
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "build-engineer",
            "task": "Build application",
            "params": {"target": "production"}
        },
        {
            "agent": "qa-expert",
            "task": "Run integration tests",
            "depends_on": ["step-0"],
            "params": {"test_suite": "integration"}
        },
        {
            "agent": "devops-engineer",
            "task": "Deploy to production",
            "depends_on": ["step-1"],
            "params": {"environment": "production"},
            "fallback": {
                "agent": "devops-engineer",
                "task": "Deploy to staging instead",
                "params": {"environment": "staging"}
            }
        }
    ],
    failure_strategy="fallback"
)
