# Source: operations/coordination-tracking.md
# Line: 433
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Delete events older than 90 days
async def cleanup_old_events(tracker, days=90):
    async with tracker._pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM coordination_events
            WHERE timestamp < NOW() - INTERVAL '%s days'
            """,
            days,
        )
    print(f"Deleted {result} old events")
