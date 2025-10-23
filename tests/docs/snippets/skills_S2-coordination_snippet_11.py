# Source: skills/S2-coordination.md
# Line: 449
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Backend developer needs database expertise
async def optimize_database_queries():
    # 1. Identify slow queries
    slow_queries = analyze_query_performance()

    # 2. Hand off to database expert
    result = await handoff_to_agent(
        target_agent="postgres-pro",
        task="Optimize these slow queries",
        context={
            "queries": slow_queries,
            "schema": "schema.sql",
            "current_indexes": get_current_indexes(),
            "performance_targets": {
                "p95_latency_ms": 100,
                "throughput_qps": 1000
            }
        }
    )

    # 3. Apply recommendations
    apply_optimizations(result["result"]["recommendations"])

    return result