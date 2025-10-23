# Source: technical/orchestration-engine.md
# Line: 618
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Quick operations - fail fast
fast_task = TaskDefinition(
    retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.5)
)

# Network operations - more retries
network_task = TaskDefinition(
    retry_policy=RetryPolicy(max_attempts=5, initial_delay=2.0, max_delay=30.0)
)