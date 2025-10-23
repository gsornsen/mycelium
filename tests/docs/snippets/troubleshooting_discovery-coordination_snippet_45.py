# Source: troubleshooting/discovery-coordination.md
# Line: 1099
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Analyze recent coordination events
events = get_coordination_events(limit=1000)

# Count by type
from collections import Counter

event_types = Counter(e["event_type"] for e in events["events"])
print(f"Event Types: {dict(event_types)}")

# Find failures
failures = [e for e in events["events"] if e["event_type"] == "failure"]
print(f"\nFailures: {len(failures)}")
for failure in failures[:5]:
    print(f"  {failure['timestamp']}: {failure['metadata']['error']}")

# Average handoff time
handoffs = [e for e in events["events"] if e["event_type"] == "handoff"]
avg_handoff = sum(e["metadata"]["duration_ms"] for e in handoffs) / len(handoffs)
print(f"\nAverage Handoff Time: {avg_handoff:.2f}ms")
