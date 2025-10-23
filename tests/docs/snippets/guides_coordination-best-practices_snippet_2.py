# Source: guides/coordination-best-practices.md
# Line: 75
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Explicit dependencies with clear reasons
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "backend-developer",
            "task": "Implement API endpoints",
            "params": {"spec": "api-spec.yaml"}
        },
        {
            "agent": "database-architect",
            "task": "Design database schema for API",
            "params": {"entities": ["User", "Order", "Product"]}
        },
        {
            "agent": "backend-developer",
            "task": "Connect API endpoints to database",
            "depends_on": ["step-0", "step-1"],  # Needs both complete
            "params": {"orm": "SQLAlchemy"}
        },
        {
            "agent": "qa-expert",
            "task": "Integration testing of API with database",
            "depends_on": ["step-2"],  # Only needs implementation done
            "params": {"test_cases": "tests/integration/"}
        }
    ]
)

# ❌ BAD: Implicit or missing dependencies
workflow = coordinate_workflow(
    steps=[
        {"agent": "backend-developer", "task": "Implement API"},
        {"agent": "database-architect", "task": "Design schema"},
        {"agent": "backend-developer", "task": "Connect them"},  # Missing depends_on!
        {"agent": "qa-expert", "task": "Test everything"}  # Missing depends_on!
    ]
)