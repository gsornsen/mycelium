# Source: troubleshooting/discovery-coordination.md
# Line: 558
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Solution 1: Increase timeout
result = handoff_to_agent(
    target_agent="slow-agent",
    task="complex task",
    timeout_seconds=120  # Increased timeout
)

# Solution 2: Async handoff (don't wait)
result = handoff_to_agent(
    target_agent="slow-agent",
    task="complex task",
    wait_for_completion=False  # Returns immediately
)

# Check status later
handoff_id = result["handoff_id"]
time.sleep(60)
status = get_handoff_status(handoff_id)

# Solution 3: Use faster alternative agent
agents = discover_agents("task description", limit=5)

# Filter by response time
fast_agents = [
    a for a in agents["agents"]
    if get_agent_details(a["id"])["agent"]["avg_response_time_ms"] < 5000
]

result = handoff_to_agent(
    target_agent=fast_agents[0]["id"],
    task="complex task"
)
