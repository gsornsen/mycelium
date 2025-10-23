# Source: operations/coordination-tracking.md
# Line: 127
# Valid syntax: True
# Has imports: True
# Has assignments: True

from coordination.tracker import CoordinationTracker
import asyncpg

# Create database connection pool
pool = await asyncpg.create_pool(
    "postgresql://localhost:5432/mycelium_registry",
    min_size=2,
    max_size=10,
)

# Initialize tracker
tracker = CoordinationTracker(pool=pool)
await tracker.initialize()