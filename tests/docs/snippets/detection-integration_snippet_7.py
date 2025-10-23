# Source: detection-integration.md
# Line: 240
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio
from mycelium_onboarding.detection import detect_all_async

async def load_config():
    """Load application configuration."""
    await asyncio.sleep(1)  # Simulate config loading
    return {"app": "myapp", "version": "1.0"}

async def initialize_database():
    """Initialize database connection."""
    await asyncio.sleep(1)  # Simulate DB init
    return "db_connection"

async def startup_sequence():
    """Run multiple startup tasks concurrently."""
    # Run all tasks in parallel
    config, db, summary = await asyncio.gather(
        load_config(),
        initialize_database(),
        detect_all_async()
    )

    print(f"Config: {config}")
    print(f"Database: {db}")
    print(f"Services: {summary.has_docker}, {summary.has_redis}")

    return config, db, summary

asyncio.run(startup_sequence())