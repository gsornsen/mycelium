# Source: troubleshooting/discovery-coordination.md
# Line: 1014
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Wait for queue to drain
import time

while True:
    health = check_coordination_health()
    if health["queue_depth"] < 10:
        break
    print(f"Waiting for queue to drain: {health['queue_depth']} items")
    time.sleep(5)

workflow = coordinate_workflow(steps=[...])

# Solution 2: Increase service capacity
# In configuration:
# MAX_CONCURRENT_WORKFLOWS=100  # Increase from 50
# WORKER_THREADS=8  # Increase from 4

# Solution 3: Clean up stuck workflows
from plugins.mycelium_core.coordination import cleanup_stuck_workflows

cleanup_stuck_workflows(stuck_for_hours=2)

# Solution 4: Use fallback mode
# If coordination service unavailable, execute steps manually
try:
    workflow = coordinate_workflow(steps=[...])
except CoordinationServiceError:
    # Manual execution fallback
    results = []
    for step in steps:
        result = handoff_to_agent(
            step["agent"],
            step["task"],
            context=step.get("params", {})
        )
        results.append(result)
