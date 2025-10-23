# Source: guides/discovery-coordination-quickstart.md
# Line: 383
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Problem: Workflow not progressing
status = get_workflow_status("wf-123")
# status["status"] == "in_progress" for too long

# Solution 1: Check events
events = get_coordination_events(
    workflow_id="wf-123",
    event_type="failure"
)
for event in events["events"]:
    print(f"Error: {event['metadata']}")

# Solution 2: Verify agent availability
from plugins.mycelium_core.agent_discovery import check_discovery_health
health = check_discovery_health()

# Solution 3: Retry with different agent
# Manually abort and restart with fallback agent