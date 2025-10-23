# Source: guides/discovery-coordination-quickstart.md
# Line: 114
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.mcp.tools.coordination_tools import handoff_to_agent

# Hand off to database specialist
result = handoff_to_agent(
    target_agent="postgres-pro",
    task="Optimize slow queries in user_analytics table",
    context={
        "schema": "database/schema.sql",
        "slow_queries": [
            "SELECT * FROM user_analytics WHERE created_at > NOW() - INTERVAL '7 days'",
            "SELECT user_id, COUNT(*) FROM events GROUP BY user_id"
        ],
        "performance_targets": {
            "p95_latency_ms": 100,
            "queries_per_second": 1000
        }
    }
)

print(f"Handoff Status: {result['status']}")
print(f"Result: {result['result']['message']}")
print(f"Duration: {result['duration_ms']}ms")

# Example output:
# Handoff Status: completed
# Result: Optimized 2 slow queries - added indexes, rewrote GROUP BY
# Duration: 2300ms