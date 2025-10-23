# Source: troubleshooting/discovery-coordination.md
# Line: 535
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check agent performance history
from plugins.mycelium_core.agent_discovery import get_agent_details

details = get_agent_details("slow-agent")
print(f"Average Response Time: {details['agent']['avg_response_time_ms']}ms")

# If avg_response_time_ms > 10000 → Agent is consistently slow

# Check recent handoffs
events = get_coordination_events(
    agent_id="slow-agent",
    event_type="handoff",
    limit=20
)

durations = [e["metadata"]["duration_ms"] for e in events["events"]]
print(f"Handoff durations: p50={percentile(durations, 50)}ms, "
      f"p95={percentile(durations, 95)}ms")