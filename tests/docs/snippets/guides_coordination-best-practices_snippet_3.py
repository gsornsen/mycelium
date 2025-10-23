# Source: guides/coordination-best-practices.md
# Line: 121
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Balanced granularity
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "code-analyzer",
            "task": "Analyze code complexity and identify refactoring candidates",
            "params": {"threshold": "complexity > 10"}
        },
        {
            "agent": "refactoring-expert",
            "task": "Refactor complex functions",
            "depends_on": ["step-0"],
            "params": {"focus": "reduce_complexity"}
        },
        {
            "agent": "test-generator",
            "task": "Generate tests for refactored code",
            "depends_on": ["step-1"],
            "params": {"coverage_target": 90}
        }
    ]
)

# ❌ BAD: Too fine-grained (micro-steps)
workflow = coordinate_workflow(
    steps=[
        {"agent": "analyzer", "task": "Load code"},
        {"agent": "analyzer", "task": "Parse AST"},
        {"agent": "analyzer", "task": "Calculate metrics"},
        {"agent": "analyzer", "task": "Format report"},
        {"agent": "refactor", "task": "Find function A"},
        {"agent": "refactor", "task": "Simplify function A"},
        # ... 20 more micro-steps
    ]
)

# ❌ BAD: Too coarse-grained (mega-steps)
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "full-stack-developer",
            "task": "Analyze, refactor, test, and deploy entire codebase",
            "params": {"everything": True}
        }
    ]
)