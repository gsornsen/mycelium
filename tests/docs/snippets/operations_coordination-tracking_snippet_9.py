# Source: operations/coordination-tracking.md
# Line: 283
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Workflow-specific statistics
stats = await tracker.get_statistics("workflow-123")
print(f"Total events: {stats['total_events']}")
print(f"Event types: {stats['event_types']}")
print(f"Average duration: {stats['avg_duration_ms']}ms")
print(f"Event type breakdown: {stats['event_type_counts']}")

# Global statistics
global_stats = await tracker.get_statistics()
print(f"Total workflows tracked: {global_stats['total_workflows']}")
print(f"Total events: {global_stats['total_events']}")