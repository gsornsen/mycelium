# Source: troubleshooting/discovery-coordination.md
# Line: 703
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check workflow state size
import sys

workflow = coordinate_workflow(steps=[...])
workflow_size = sys.getsizeof(workflow)

print(f"Workflow State Size: {workflow_size / 1024 / 1024:.2f}MB")

# Check context sizes
events = get_coordination_events(workflow_id=workflow["workflow_id"])

for event in events["events"]:
    if event["event_type"] == "handoff":
        context_size = event["metadata"].get("context_size_bytes", 0)
        print(f"Handoff context: {context_size / 1024:.2f}KB")

# If context sizes > 100KB → Contexts too large