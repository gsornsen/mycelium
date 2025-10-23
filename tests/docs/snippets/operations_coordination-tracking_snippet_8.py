# Source: operations/coordination-tracking.md
# Line: 269
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get complete workflow timeline
timeline = await tracker.get_workflow_timeline("workflow-123")

print(f"Total events: {timeline['total_events']}")
print(f"Duration: {timeline['duration_ms']}ms")
print(f"Lifecycle events: {len(timeline['lifecycle'])}")
print(f"Task events: {len(timeline['tasks'])}")
print(f"Handoffs: {len(timeline['handoffs'])}")
print(f"Failures: {len(timeline['failures'])}")