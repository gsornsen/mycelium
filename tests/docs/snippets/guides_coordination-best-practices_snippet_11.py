# Source: guides/coordination-best-practices.md
# Line: 430
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Idempotent steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "database-admin",
            "task": "Create users table if not exists",
            "params": {"ddl": "CREATE TABLE IF NOT EXISTS users (...)"}
        },
        {
            "agent": "data-loader",
            "task": "Load data with upsert (insert or update)",
            "params": {"mode": "upsert", "key": "user_id"}
        }
    ]
)

# ❌ BAD: Non-idempotent steps
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "database-admin",
            "task": "Create users table",  # Fails if table exists
            "params": {"ddl": "CREATE TABLE users (...)"}
        },
        {
            "agent": "data-loader",
            "task": "Insert all data",  # Fails if data exists
            "params": {"mode": "insert"}
        }
    ]
)
