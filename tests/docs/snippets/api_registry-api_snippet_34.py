# Source: api/registry-api.md
# Line: 647
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time

from plugins.mycelium_core.registry import AgentRegistry


async def benchmark_queries():
    async with AgentRegistry() as registry:
        # Benchmark get_agent_by_id
        start = time.time()
        await registry.get_agent_by_id("01-core-backend-developer")
        duration = (time.time() - start) * 1000
        print(f"get_agent_by_id: {duration:.2f}ms")

        # Benchmark search
        start = time.time()
        await registry.search_agents("backend")
        duration = (time.time() - start) * 1000
        print(f"search_agents: {duration:.2f}ms")

        # Health check
        health = await registry.health_check()
        print(f"Health: {health['status']}")
        print(f"Agents: {health['agent_count']}")
        print(f"DB size: {health['database_size']}")

import asyncio

asyncio.run(benchmark_queries())
