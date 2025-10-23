# Source: detection-reference.md
# Line: 796
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio
from mycelium_onboarding.detection import detect_all_async

async def check_services():
    summary = await detect_all_async()
    return summary.has_docker and summary.has_redis

# In async context
result = await check_services()