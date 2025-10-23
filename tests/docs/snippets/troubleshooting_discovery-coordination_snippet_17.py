# Source: troubleshooting/discovery-coordination.md
# Line: 339
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Check failure reason
print(f"Status: {workflow['status']}")

# Get failure events
events = get_coordination_events(
    workflow_id=workflow["workflow_id"],
    event_type="failure"
)

for event in events["events"]:
    print(f"\nFailure at step {event['metadata']['step']}:")
    print(f"  Error: {event['metadata']['error']}")
    print(f"  Details: {event['metadata'].get('details', 'N/A')}")

# Common error types:
# - ValueError: Invalid workflow structure
# - DependencyError: Unresolved dependencies
# - ValidationError: Invalid parameters