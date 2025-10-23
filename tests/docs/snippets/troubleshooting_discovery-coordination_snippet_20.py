# Source: troubleshooting/discovery-coordination.md
# Line: 448
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Check handoff events
events = get_coordination_events(event_type="handoff", limit=10)

for event in events["events"]:
    if not event["metadata"].get("context_preserved", True):
        print(f"\nHandoff failed to preserve context:")
        print(f"  Source: {event['source_agent']}")
        print(f"  Target: {event['target_agent']}")
        print(f"  Reason: {event['metadata'].get('failure_reason', 'Unknown')}")
        print(f"  Context Size: {event['metadata'].get('context_size_bytes', 0)} bytes")

# Common issues:
# - Context too large (>1MB)
# - Context contains non-serializable objects
# - Context schema mismatch