# Source: guides/coordination-best-practices.md
# Line: 974
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ❌ ANTI-PATTERN: No error handling
workflow = coordinate_workflow(
    steps=[
        {"agent": "...", "task": "..."},
        {"agent": "...", "task": "..."}
    ]
)
# Hope nothing fails!

# ✅ SOLUTION: Comprehensive failure handling
workflow = coordinate_workflow(
    steps=[
        {"agent": "...", "task": "..."},
        {
            "agent": "...",
            "task": "...",
            "depends_on": ["step-0"],
            "fallback": {
                "agent": "...",
                "task": "Fallback action"
            }
        }
    ],
    failure_strategy="fallback"
)

# Monitor and handle failures
try:
    result = workflow
except WorkflowExecutionError as e:
    handle_failure(e)
