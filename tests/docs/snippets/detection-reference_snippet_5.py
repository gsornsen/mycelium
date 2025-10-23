# Source: detection-reference.md
# Line: 95
# Valid syntax: True
# Has imports: True
# Has assignments: True

import asyncio

from mycelium_onboarding.detection import detect_all_async


async def main():
    summary = await detect_all_async()
    print(f"Found {len(summary.redis)} Redis instances")

asyncio.run(main())
