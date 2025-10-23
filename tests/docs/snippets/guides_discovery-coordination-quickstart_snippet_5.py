# Source: guides/discovery-coordination-quickstart.md
# Line: 214
# Valid syntax: True
# Has imports: True
# Has assignments: True

import time

from plugins.mycelium_core.mcp.tools.coordination_tools import get_workflow_status

# Monitor long-running workflow
workflow_id = "wf-abc-123"

while True:
    status = get_workflow_status(workflow_id, include_steps=False)

    if status["status"] == "completed":
        print(f"\n✓ Workflow completed in {status['total_duration_ms']}ms")
        break
    elif status["status"] == "failed":
        print(f"\n✗ Workflow failed at step {status['current_step']}")
        break
    else:
        print(f"Progress: {status['progress_percent']}% (step {status['current_step']}/{status['steps_total']})")
        time.sleep(2)
