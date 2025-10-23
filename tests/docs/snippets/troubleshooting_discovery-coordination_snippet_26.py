# Source: troubleshooting/discovery-coordination.md
# Line: 608
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Analyze workflow performance
workflow_id = workflow["workflow_id"]

# Get detailed timing
events = get_coordination_events(workflow_id=workflow_id)

# Calculate overhead
total_time = workflow["total_duration_ms"]
agent_time = sum(r["duration_ms"] for r in workflow["results"])
coordination_overhead = total_time - agent_time

print(f"Total Time: {total_time}ms")
print(f"Agent Time: {agent_time}ms")
print(f"Coordination Overhead: {coordination_overhead}ms "
      f"({(coordination_overhead/total_time)*100:.1f}%)")

# Breakdown by step
for result in workflow["results"]:
    print(f"\nStep {result['step']}: {result['agent']}")
    print(f"  Duration: {result['duration_ms']}ms")
    print(f"  % of Total: {(result['duration_ms']/total_time)*100:.1f}%")

# Identify bottlenecks
slowest = max(workflow["results"], key=lambda r: r["duration_ms"])
print(f"\nBottleneck: {slowest['agent']} ({slowest['duration_ms']}ms)")