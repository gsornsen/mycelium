# Source: api/discovery-quickstart.md
# Line: 333
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio
import aiohttp

async def discover_agents_async(query: str):
    """Async agent discovery."""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/agents/discover",
            json={"query": query, "limit": 10}
        ) as response:
            return await response.json()

# Usage
results = asyncio.run(discover_agents_async("python development"))
print(f"Found {results['total_count']} agents")