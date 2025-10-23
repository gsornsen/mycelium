# Source: guides/coordination-best-practices.md
# Line: 341
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Compressed context with references
context = {
    "database_schema": "file://database/schema.sql",  # Reference
    "slow_queries_log": "file://logs/slow_queries.txt",  # Reference
    "summary": {
        "tables_affected": ["users", "orders", "products"],
        "slowest_query_time_ms": 5000,
        "p95_latency_ms": 1200,
        "daily_query_volume": 1000000
    },
    "sample_queries": [
        "SELECT * FROM users WHERE created_at > ?",  # Example
        "SELECT COUNT(*) FROM orders GROUP BY user_id"  # Example
    ]
}

# ❌ BAD: Embedded large data
context = {
    "schema": read_file("schema.sql"),  # 500KB embedded
    "all_queries": read_file("logs/queries.txt"),  # 50MB embedded
    "every_table": [...]  # Huge array
}