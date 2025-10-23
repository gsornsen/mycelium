# Source: guides/coordination-best-practices.md
# Line: 376
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Critical deployment - abort on failure
deployment_workflow = coordinate_workflow(
    steps=[
        {"agent": "build-engineer", "task": "Build application"},
        {"agent": "qa-expert", "task": "Run integration tests"},
        {"agent": "devops-engineer", "task": "Deploy to production"}
    ],
    failure_strategy="abort"  # Critical - stop if any step fails
)

# ✅ GOOD: Best-effort analysis - continue on failure
analysis_workflow = coordinate_workflow(
    steps=[
        {"agent": "code-analyzer", "task": "Analyze code quality"},
        {"agent": "security-scanner", "task": "Security scan"},
        {"agent": "dependency-checker", "task": "Check outdated dependencies"}
    ],
    failure_strategy="continue"  # Non-critical - collect all results
)

# ✅ GOOD: Fallback for production service
service_workflow = coordinate_workflow(
    steps=[
        {
            "agent": "ml-engineer",
            "task": "Deploy new ML model",
            "fallback": {
                "agent": "ml-engineer",
                "task": "Rollback to previous model version"
            }
        }
    ],
    failure_strategy="fallback"
)

# ❌ BAD: Wrong strategy for critical workflow
deployment_workflow = coordinate_workflow(
    steps=[...],
    failure_strategy="continue"  # Dangerous! Could deploy broken code
)
