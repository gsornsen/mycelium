# Multi-Agent Coordination Patterns

This guide demonstrates practical coordination patterns using the mycelium multi-agent system with Redis MCP and
TaskQueue MCP.

## Table of Contents

1. [Pattern 1: Parallel Agent Invocation](#pattern-1-parallel-agent-invocation)
1. [Pattern 2: Event-Driven Coordination](#pattern-2-event-driven-coordination)
1. [Pattern 3: Shared State Management](#pattern-3-shared-state-management)
1. [Pattern 4: Work Queue Distribution](#pattern-4-work-queue-distribution)
1. [Pattern 5: Agent Status Tracking](#pattern-5-agent-status-tracking)

______________________________________________________________________

## Pattern 1: Parallel Agent Invocation

**Use Case:** User requests a feature that requires multiple specialists working in parallel.

**Example Request:** "Implement user authentication with tests and documentation"

### Coordinator Response Pattern

```markdown
The coordinator should invoke multiple agents in parallel using the Task tool:

1. Task tool: Invoke python-pro agent
   - Prompt: "Implement user authentication in auth.py with password hashing and JWT tokens"

2. Task tool: Invoke test-automator agent
   - Prompt: "Create integration tests for user authentication including login, logout, token refresh"

3. Task tool: Invoke documentation-engineer agent
   - Prompt: "Document authentication API endpoints and usage examples"

All three agents work in parallel. Expected 3x speedup vs sequential.
```

### Redis State Tracking

```python
# Coordinator tracks agent states
mcp__RedisMCPServer__hset("agents:python-pro", "status", "busy")
mcp__RedisMCPServer__hset("agents:python-pro", "task", "implement_auth")
mcp__RedisMCPServer__hset("agents:python-pro", "started_at", "2025-11-12T10:00:00Z")

mcp__RedisMCPServer__hset("agents:test-automator", "status", "busy")
mcp__RedisMCPServer__hset("agents:test-automator", "task", "test_auth")

mcp__RedisMCPServer__hset("agents:doc-engineer", "status", "busy")
mcp__RedisMCPServer__hset("agents:doc-engineer", "task", "document_auth")
```

### Expected Outcome

- 3 agents work simultaneously
- Each agent produces specialized output
- Coordinator synthesizes results into unified response
- User gets complete feature (code + tests + docs) in parallel time

______________________________________________________________________

## Pattern 2: Event-Driven Coordination

**Use Case:** Agents need to react to events from other agents.

**Example Scenario:** Test agent waits for implementation completion before running tests.

### Publishing Events

```python
# Python-pro agent completes implementation
mcp__RedisMCPServer__publish(
    "events:task:completed",
    '{"agent": "python-pro", "task": "implement_auth", "status": "success", "files": ["auth.py"]}'
)
```

### Subscribing to Events

```python
# Test-automator subscribes to completion events
mcp__RedisMCPServer__subscribe("events:task:completed")

# When event received, test-automator starts testing
# Extract files from event, run tests on those files
```

### Event Types

Common event channels:

- `events:task:completed` - Agent finished task
- `events:task:failed` - Agent encountered error
- `events:context:updated` - Shared context changed
- `events:coordination:required` - Multiple agents need sync

______________________________________________________________________

## Pattern 3: Shared State Management

**Use Case:** Multiple agents need access to shared project context.

### Storing Context

```python
# Coordinator stores project context
context = {
    "project": "neurite",
    "status": "in_progress",
    "phase": "implementation",
    "active_agents": ["python-pro", "test-automator"],
    "completed_features": ["auth", "data-model"],
    "pending_features": ["api-endpoints", "frontend"]
}

mcp__RedisMCPServer__hset("context:project:neurite", "status", "in_progress")
mcp__RedisMCPServer__hset("context:project:neurite", "phase", "implementation")
mcp__RedisMCPServer__hset("context:project:neurite", "active_agents", "3")
```

### Querying Context

```python
# Any agent can query current context
status = mcp__RedisMCPServer__hget("context:project:neurite", "status")
phase = mcp__RedisMCPServer__hget("context:project:neurite", "phase")

# Agent adapts behavior based on context
if phase == "implementation":
    # Focus on building features
elif phase == "testing":
    # Focus on test coverage
elif phase == "optimization":
    # Focus on performance
```

### Context Updates

```python
# Agent updates context after completing milestone
mcp__RedisMCPServer__hset("context:project:neurite", "completed_features", "auth,data-model,api-endpoints")
mcp__RedisMCPServer__hset("context:project:neurite", "phase", "testing")

# Publish event about context change
mcp__RedisMCPServer__publish(
    "events:context:updated",
    '{"project": "neurite", "phase": "testing", "reason": "features_complete"}'
)
```

______________________________________________________________________

## Pattern 4: Work Queue Distribution

**Use Case:** Distribute many small tasks across available agents.

### Queuing Tasks

```python
# Task distributor adds tasks to queue
tasks = [
    "implement_user_login",
    "implement_user_logout",
    "implement_password_reset",
    "implement_profile_update",
    "implement_email_verification"
]

for task in tasks:
    mcp__RedisMCPServer__rpush("queue:pending_tasks", task)
```

### Agents Pull Tasks

```python
# Worker agents pull tasks from queue
while True:
    task = mcp__RedisMCPServer__lpop("queue:pending_tasks")
    if not task:
        break  # Queue empty

    # Process task
    result = process_task(task)

    # Report completion
    mcp__RedisMCPServer__rpush("queue:completed_tasks", task)
    mcp__RedisMCPServer__publish(
        "events:task:completed",
        f'{{"task": "{task}", "agent": "python-pro", "status": "success"}}'
    )
```

### Monitoring Queue

```python
# Coordinator monitors queue status
pending_count = mcp__RedisMCPServer__llen("queue:pending_tasks")
completed_count = mcp__RedisMCPServer__llen("queue:completed_tasks")
in_progress_count = active_agents

progress_percent = (completed_count / total_tasks) * 100
```

______________________________________________________________________

## Pattern 5: Agent Status Tracking

**Use Case:** Monitor which agents are busy, what they're working on, and system health.

### Tracking Agent States

```python
# Coordinator tracks all active agents
agents = {
    "python-pro": {
        "status": "busy",
        "task": "implement_auth",
        "started_at": "2025-11-12T10:00:00Z",
        "progress": "50%"
    },
    "test-automator": {
        "status": "idle",
        "last_task": "test_data_model",
        "completed_at": "2025-11-12T09:55:00Z"
    },
    "doc-engineer": {
        "status": "busy",
        "task": "document_api",
        "started_at": "2025-11-12T10:05:00Z",
        "progress": "25%"
    }
}

# Store each agent's state
for agent_name, state in agents.items():
    for key, value in state.items():
        mcp__RedisMCPServer__hset(f"agents:{agent_name}", key, str(value))
```

### Querying Agent Status

```python
# Get status of specific agent
python_pro_status = mcp__RedisMCPServer__hgetall("agents:python-pro")

# Scan all agent keys
all_agent_keys = mcp__RedisMCPServer__scan_all_keys("agents:*")

# Count busy vs idle agents
busy_count = 0
idle_count = 0
for key in all_agent_keys:
    status = mcp__RedisMCPServer__hget(key, "status")
    if status == "busy":
        busy_count += 1
    elif status == "idle":
        idle_count += 1

# Report system utilization
utilization = (busy_count / (busy_count + idle_count)) * 100
```

### Health Monitoring

```python
# Detect stalled agents (busy for too long)
import time
current_time = time.time()

for key in all_agent_keys:
    status = mcp__RedisMCPServer__hget(key, "status")
    started_at = mcp__RedisMCPServer__hget(key, "started_at")

    if status == "busy" and started_at:
        started_timestamp = parse_iso_time(started_at)
        elapsed = current_time - started_timestamp

        if elapsed > 600:  # 10 minutes
            agent_name = key.split(":")[1]
            # Publish alert
            mcp__RedisMCPServer__publish(
                "events:agent:stalled",
                f'{{"agent": "{agent_name}", "elapsed_seconds": {elapsed}}}'
            )
```

______________________________________________________________________

## Complete Example: Feature Development Workflow

Here's a complete example combining multiple patterns:

### User Request

"Implement a REST API for user management with full CRUD operations, tests, and documentation"

### Coordinator Response

```python
# 1. Store project context
mcp__RedisMCPServer__hset("context:project:user-api", "status", "in_progress")
mcp__RedisMCPServer__hset("context:project:user-api", "phase", "design")
mcp__RedisMCPServer__hset("context:project:user-api", "started_at", "2025-11-12T10:00:00Z")

# 2. Break down into tasks
tasks = [
    "design_user_model",
    "implement_create_user",
    "implement_read_user",
    "implement_update_user",
    "implement_delete_user",
    "implement_list_users"
]

for task in tasks:
    mcp__RedisMCPServer__rpush("queue:api_tasks", task)

# 3. Invoke specialist agents in parallel
# Task tool: python-pro for implementation
# Task tool: api-designer for API spec
# Task tool: database-administrator for schema

# 4. Track agent states
mcp__RedisMCPServer__hset("agents:python-pro", "status", "busy")
mcp__RedisMCPServer__hset("agents:python-pro", "task", "implement_user_crud")
mcp__RedisMCPServer__hset("agents:api-designer", "status", "busy")
mcp__RedisMCPServer__hset("agents:api-designer", "task", "design_openapi_spec")

# 5. Subscribe to completion events
mcp__RedisMCPServer__subscribe("events:task:completed")

# 6. When implementation complete, start testing phase
# (Triggered by event)

# 7. Update project context
mcp__RedisMCPServer__hset("context:project:user-api", "phase", "testing")

# 8. Invoke test-automator agent
# Task tool: test-automator for comprehensive tests

# 9. When tests pass, start documentation
mcp__RedisMCPServer__hset("context:project:user-api", "phase", "documentation")

# 10. Invoke documentation-engineer
# Task tool: documentation-engineer for API docs

# 11. Final synthesis and delivery
mcp__RedisMCPServer__hset("context:project:user-api", "status", "completed")
mcp__RedisMCPServer__publish(
    "events:project:completed",
    '{"project": "user-api", "features": 6, "agents": 5, "duration": "15min"}'
)
```

______________________________________________________________________

## Monitoring Coordination

Use `/team-status` slash command to monitor real-time coordination:

```bash
# View active agents and their tasks
/team-status

# View detailed coordination metrics
/team-status --detailed
```

Redis keys to monitor:

- `agents:*` - Agent states
- `queue:*` - Work queues
- `context:*` - Project contexts
- `events:*` - Event streams (via SUBSCRIBE)

______________________________________________________________________

## Best Practices

1. **Always use Task tool for parallel invocation** - Don't implement yourself
1. **Track agent states in Redis** - Enables monitoring and debugging
1. **Use event-driven patterns** - Loose coupling, better scalability
1. **Store shared context** - Prevents redundant queries
1. **Monitor queue depths** - Detect bottlenecks early
1. **Set timeouts** - Detect stalled agents
1. **Log all coordination** - Audit trail for debugging

______________________________________________________________________

## Troubleshooting

### Problem: Agent not coordinating, doing work itself

**Cause:** Agent doesn't have Task tool or doesn't know to use it

**Fix:** Check agent's `tools:` line includes `Task`

### Problem: Redis operations failing

**Cause:** MCP tools not declared or Redis not running

**Fix:**

1. Check agent has `mcp__RedisMCPServer__*` tools
1. Verify Redis running: `redis-cli ping`

### Problem: No parallel speedup

**Cause:** Coordinator invoking agents sequentially

**Fix:** Use multiple Task tool calls in single message

### Problem: Agents not seeing shared state

**Cause:** Wrong Redis key names or namespace

**Fix:** Use consistent key patterns: `context:project:*`, `agents:*`, `queue:*`

______________________________________________________________________

## Next Steps

1. Run smoke tests: `./scripts/smoke_test_coordination.sh`
1. Try example patterns with real agents
1. Monitor Redis with: `redis-cli monitor`
1. Check `/team-status` during coordination
1. Review coordination metrics after completion
