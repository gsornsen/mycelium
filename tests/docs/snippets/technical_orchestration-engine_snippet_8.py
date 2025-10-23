# Source: technical/orchestration-engine.md
# Line: 230
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.coordination.orchestrator import RetryPolicy

task = TaskDefinition(
    task_id="flaky-task",
    agent_id="agent-1",
    agent_type="network-caller",
    retry_policy=RetryPolicy(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
    ),
)
