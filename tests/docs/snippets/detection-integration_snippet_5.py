# Source: detection-integration.md
# Line: 153
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio

from mycelium_onboarding.detection import detect_all_async


async def async_service_check():
    """Async service availability check."""
    summary = await detect_all_async()

    services = {
        "docker": summary.has_docker,
        "redis": summary.has_redis,
        "postgres": summary.has_postgres,
        "temporal": summary.has_temporal,
        "gpu": summary.has_gpu,
    }

    return services

# Run in async context
services = asyncio.run(async_service_check())
print(f"Available services: {services}")
