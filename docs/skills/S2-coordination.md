# S2: Coordination Skill

## Overview

The Coordination Skill enables Claude Code to orchestrate complex multi-agent workflows with seamless state management,
dependency resolution, and failure recovery. This skill transforms Claude from executing single-agent tasks into
conducting sophisticated multi-agent collaborations where context and results flow naturally between specialists.

**Status:** Planned (M01 - Week 4-5) **Version:** 1.0.0 (Target) **Dependencies:** Task 1.5 (Handoff Protocol), Task 1.6
(Orchestration Engine), Task 1.7 (Tracking) **Complements:** S1 (Agent Discovery) - Use S1 to find agents, S2 to
coordinate them

## Capabilities

### Core Functions

1. **Workflow Orchestration**

   - Create and execute multi-agent workflows with dependency management
   - Support sequential, parallel, and conditional execution patterns
   - Maintain workflow state with checkpoint and rollback capabilities
   - Monitor real-time progress across all agents

1. **Agent Handoffs**

   - Transfer execution context between agents seamlessly
   - Preserve conversation history and intermediate results
   - Handle nested handoffs for complex delegation patterns
   - Validate handoff completeness before proceeding

1. **State Management**

   - Persist workflow state across agent transitions
   - Support rollback to previous states on failure
   - Enable workflow pause and resume
   - Manage concurrent workflow executions

1. **Coordination Tracking**

   - Log all inter-agent communications with timestamps
   - Track handoff events, state transitions, and outcomes
   - Provide queryable history for debugging and optimization
   - Generate workflow execution reports

## MCP Tools

### `coordinate_workflow`

Execute a multi-agent workflow with dependency management and state tracking.

**Signature:**

```python
async def coordinate_workflow(
    steps: List[Dict],
    execution_mode: str = "sequential",
    failure_strategy: str = "retry",
) -> dict
```

**Parameters:**

- `steps` (array, required): Workflow steps to execute
  - Each step: `{"agent": str, "task": str, "depends_on": List[str], "params": Dict}`
- `execution_mode` (string, optional): "sequential", "parallel", or "conditional" (default: "sequential")
- `failure_strategy` (string, optional): "retry", "fallback", "abort", or "continue" (default: "retry")

**Returns:**

```json
{
  "success": true,
  "workflow_id": "wf-abc-123",
  "status": "completed",
  "steps_completed": 5,
  "steps_total": 5,
  "results": [
    {
      "step": 0,
      "agent": "python-pro",
      "status": "completed",
      "output": "Code review completed with 3 suggestions",
      "duration_ms": 1200
    }
  ],
  "total_duration_ms": 4500,
  "handoffs": 4,
  "metadata": {
    "started_at": "2025-10-21T10:00:00Z",
    "completed_at": "2025-10-21T10:00:04Z",
    "coordinator": "multi-agent-coordinator"
  }
}
```

**Error Handling:**

- `ValueError`: Invalid workflow structure (empty steps, circular dependencies)
- `WorkflowExecutionError`: Step execution failure
- `WorkflowTimeoutError`: Workflow exceeded maximum duration
- `DependencyError`: Unresolved step dependencies

**Examples:**

```python
# Sequential code review workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "python-pro",
            "task": "Review code style and best practices",
            "params": {"file": "api.py"}
        },
        {
            "agent": "security-expert",
            "task": "Security audit focusing on authentication",
            "depends_on": ["step-0"],
            "params": {"file": "api.py"}
        },
        {
            "agent": "performance-optimizer",
            "task": "Performance analysis and recommendations",
            "depends_on": ["step-0"],
            "params": {"file": "api.py"}
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# Parallel data processing workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Process dataset A",
            "params": {"dataset": "customers.csv"}
        },
        {
            "agent": "data-engineer",
            "task": "Process dataset B",
            "params": {"dataset": "orders.csv"}
        },
        {
            "agent": "ml-engineer",
            "task": "Train model on combined data",
            "depends_on": ["step-0", "step-1"],
            "params": {"model_type": "random_forest"}
        }
    ],
    execution_mode="parallel"
)
```

### `handoff_to_agent`

Explicitly handoff execution to another agent with full context preservation.

**Signature:**

```python
async def handoff_to_agent(
    target_agent: str,
    task: str,
    context: Dict = None,
    wait_for_completion: bool = True,
) -> dict
```

**Parameters:**

- `target_agent` (string, required): Agent ID to hand off to
- `task` (string, required): Task description for target agent
- `context` (object, optional): Contextual data to pass (conversation history, files, etc.)
- `wait_for_completion` (boolean, optional): Wait for agent to complete (default: true)

**Returns:**

```json
{
  "success": true,
  "handoff_id": "ho-xyz-789",
  "source_agent": "backend-developer",
  "target_agent": "database-optimizer",
  "status": "completed",
  "result": {
    "message": "Optimized 5 slow queries",
    "details": "Added indexes on user_id and created_at columns",
    "files_modified": ["schema.sql", "migrations/001_add_indexes.sql"]
  },
  "context_preserved": true,
  "duration_ms": 2300,
  "metadata": {
    "handoff_at": "2025-10-21T10:00:00Z",
    "completed_at": "2025-10-21T10:00:02Z"
  }
}
```

**Error Handling:**

- `ValueError`: Invalid agent ID or empty task
- `HandoffError`: Handoff failed or context serialization error
- `AgentUnavailableError`: Target agent not available
- `ContextPreservationError`: Failed to preserve context

**Examples:**

```python
# Simple handoff with context
result = await handoff_to_agent(
    target_agent="security-expert",
    task="Review authentication implementation in auth.py",
    context={
        "files": ["auth.py", "models/user.py"],
        "concerns": ["password hashing", "session management"]
    }
)

# Handoff without waiting
result = await handoff_to_agent(
    target_agent="documentation-specialist",
    task="Update API documentation",
    wait_for_completion=False
)
# Returns immediately with handoff_id for later status check
```

### `get_workflow_status`

Query the status of a running or completed workflow.

**Signature:**

```python
async def get_workflow_status(
    workflow_id: str,
    include_steps: bool = True,
) -> dict
```

**Parameters:**

- `workflow_id` (string, required): Workflow identifier
- `include_steps` (boolean, optional): Include detailed step information (default: true)

**Returns:**

```json
{
  "success": true,
  "workflow_id": "wf-abc-123",
  "status": "in_progress",
  "current_step": 2,
  "steps_completed": 2,
  "steps_total": 5,
  "progress_percent": 40,
  "started_at": "2025-10-21T10:00:00Z",
  "estimated_completion": "2025-10-21T10:00:15Z",
  "steps": [
    {
      "step": 0,
      "agent": "python-pro",
      "status": "completed",
      "started_at": "2025-10-21T10:00:00Z",
      "completed_at": "2025-10-21T10:00:03Z"
    },
    {
      "step": 1,
      "agent": "security-expert",
      "status": "completed",
      "started_at": "2025-10-21T10:00:03Z",
      "completed_at": "2025-10-21T10:00:07Z"
    },
    {
      "step": 2,
      "agent": "performance-optimizer",
      "status": "in_progress",
      "started_at": "2025-10-21T10:00:07Z"
    }
  ],
  "metadata": {
    "execution_mode": "sequential",
    "failure_strategy": "retry",
    "handoffs": 2
  }
}
```

**Error Handling:**

- `ValueError`: Invalid workflow_id
- `WorkflowNotFoundError`: Workflow doesn't exist
- `CoordinationAPIError`: API error retrieving status

**Examples:**

```python
# Check workflow progress
status = await get_workflow_status("wf-abc-123")

if status["status"] == "in_progress":
    print(f"Progress: {status['progress_percent']}%")
    print(f"Current step: {status['current_step']} of {status['steps_total']}")

# Lightweight status check without step details
status = await get_workflow_status("wf-abc-123", include_steps=False)
```

### `get_coordination_events`

Retrieve coordination events for debugging and analysis.

**Signature:**

```python
async def get_coordination_events(
    workflow_id: str = None,
    agent_id: str = None,
    event_type: str = None,
    limit: int = 100,
) -> dict
```

**Parameters:**

- `workflow_id` (string, optional): Filter by workflow
- `agent_id` (string, optional): Filter by agent
- `event_type` (string, optional): Filter by event type ("handoff", "execution", "completion", "failure")
- `limit` (integer, optional): Maximum events to return (default: 100)

**Returns:**

```json
{
  "success": true,
  "events": [
    {
      "event_id": "evt-123",
      "event_type": "handoff",
      "timestamp": "2025-10-21T10:00:03Z",
      "workflow_id": "wf-abc-123",
      "source_agent": "python-pro",
      "target_agent": "security-expert",
      "context_size_bytes": 1024,
      "metadata": {
        "task": "Security review",
        "state_preserved": true
      }
    }
  ],
  "total_count": 15,
  "returned_count": 15,
  "processing_time_ms": 45
}
```

**Examples:**

```python
# Get all events for a workflow
events = await get_coordination_events(workflow_id="wf-abc-123")

# Get handoff events only
events = await get_coordination_events(
    event_type="handoff",
    limit=50
)

# Get events for a specific agent
events = await get_coordination_events(
    agent_id="security-expert",
    limit=20
)
```

## Usage Patterns

### Pattern 1: Sequential Code Review Workflow

When you need multiple specialists to review code in sequence:

```python
# 1. Discover review agents
style_agent = await discover_agents("Python code style review", limit=1)
security_agent = await discover_agents("security audit", limit=1)
perf_agent = await discover_agents("performance optimization", limit=1)

# 2. Create workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": style_agent["agents"][0]["id"],
            "task": "Review code style, structure, and best practices",
            "params": {"file": "api/endpoints.py"}
        },
        {
            "agent": security_agent["agents"][0]["id"],
            "task": "Audit for security vulnerabilities",
            "depends_on": ["step-0"],
            "params": {
                "file": "api/endpoints.py",
                "focus": ["authentication", "injection", "validation"]
            }
        },
        {
            "agent": perf_agent["agents"][0]["id"],
            "task": "Analyze performance and suggest optimizations",
            "depends_on": ["step-0", "step-1"],
            "params": {"file": "api/endpoints.py"}
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# 3. Monitor progress
while workflow["status"] != "completed":
    status = await get_workflow_status(workflow["workflow_id"])
    print(f"Progress: {status['progress_percent']}%")
    await asyncio.sleep(2)

# 4. Review results
for result in workflow["results"]:
    print(f"{result['agent']}: {result['output']}")
```

### Pattern 2: Parallel Data Processing

When independent tasks can run simultaneously:

```python
# Process multiple data sources in parallel
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Clean and validate customer data",
            "params": {"dataset": "customers.csv", "validations": ["email", "phone"]}
        },
        {
            "agent": "data-engineer",
            "task": "Clean and validate order data",
            "params": {"dataset": "orders.csv", "validations": ["amounts", "dates"]}
        },
        {
            "agent": "data-engineer",
            "task": "Clean and validate product data",
            "params": {"dataset": "products.csv", "validations": ["prices", "stock"]}
        },
        {
            "agent": "analytics-expert",
            "task": "Generate insights from cleaned data",
            "depends_on": ["step-0", "step-1", "step-2"],
            "params": {"analysis_types": ["trends", "correlations", "anomalies"]}
        }
    ],
    execution_mode="parallel"  # Steps 0-2 run in parallel
)

print(f"Processed data in {workflow['total_duration_ms']}ms")
print(f"Parallelization saved {workflow['metadata']['time_saved_ms']}ms")
```

### Pattern 3: Dynamic Expert Handoff

When current agent needs specialized help:

```python
# Backend developer needs database expertise
async def optimize_database_queries():
    # 1. Identify slow queries
    slow_queries = analyze_query_performance()

    # 2. Hand off to database expert
    result = await handoff_to_agent(
        target_agent="postgres-pro",
        task="Optimize these slow queries",
        context={
            "queries": slow_queries,
            "schema": "schema.sql",
            "current_indexes": get_current_indexes(),
            "performance_targets": {
                "p95_latency_ms": 100,
                "throughput_qps": 1000
            }
        }
    )

    # 3. Apply recommendations
    apply_optimizations(result["result"]["recommendations"])

    return result
```

### Pattern 4: Conditional Workflow Branching

When workflow path depends on intermediate results:

```python
# Code quality workflow with conditional steps
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "code-analyzer",
            "task": "Analyze code quality metrics",
            "params": {"file": "main.py"}
        },
        {
            "agent": "refactoring-expert",
            "task": "Refactor complex functions",
            "depends_on": ["step-0"],
            "condition": "complexity_score > 10",  # Only run if complex
            "params": {"focus": "reduce_complexity"}
        },
        {
            "agent": "test-generator",
            "task": "Generate missing tests",
            "depends_on": ["step-0"],
            "condition": "coverage < 80",  # Only run if coverage low
            "params": {"target_coverage": 90}
        }
    ],
    execution_mode="conditional"
)
```

### Pattern 5: Failure Recovery with Fallbacks

When workflows need resilience:

```python
# Deployment workflow with automatic fallbacks
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "build-engineer",
            "task": "Build application",
            "params": {"target": "production"}
        },
        {
            "agent": "qa-expert",
            "task": "Run integration tests",
            "depends_on": ["step-0"],
            "params": {"test_suite": "integration"}
        },
        {
            "agent": "devops-engineer",
            "task": "Deploy to production",
            "depends_on": ["step-1"],
            "params": {"environment": "production"},
            "fallback": {
                "agent": "devops-engineer",
                "task": "Deploy to staging instead",
                "params": {"environment": "staging"}
            }
        }
    ],
    failure_strategy="fallback"
)
```

## Performance Characteristics

### Latency Targets

- **coordinate_workflow**: \<500ms overhead per workflow (P95)

  - Orchestration setup: \<100ms
  - State management: \<50ms per transition
  - Dependency resolution: \<50ms

- **handoff_to_agent**: \<500ms total handoff time (P95)

  - Context serialization: \<100ms
  - State transfer: \<200ms
  - Agent initialization: \<200ms

- **get_workflow_status**: \<200ms end-to-end (P95)

  - State query: \<50ms
  - Step aggregation: \<100ms
  - Response formatting: \<50ms

### Retry Behavior

All coordination tools implement automatic retry:

- **Max retries**: 3 attempts per step (configurable)
- **Backoff strategy**: Exponential (1s, 2s, 4s)
- **Retry conditions**: Timeout, transient errors, agent unavailable
- **No retry conditions**: Validation errors, permanent failures

### Resource Usage

- **Memory**: \<50MB per active workflow
- **Network**: ~10KB per handoff message
- **Storage**: ~1KB per coordination event

### Scalability

- **Concurrent workflows**: Up to 50 simultaneous workflows
- **Workflow size**: Up to 20 steps per workflow
- **Event retention**: 30 days (configurable)
- **Query performance**: \<100ms for 1M+ events

## Integration with Other Skills

### S1: Agent Discovery

Coordination depends on discovery to find the right agents:

```python
# Combined discovery + coordination pattern
async def execute_task_with_experts(task_description):
    # 1. Discover appropriate agents
    agents = await discover_agents(task_description, limit=3)

    # 2. Build workflow from discovered agents
    steps = []
    for idx, agent in enumerate(agents["agents"]):
        steps.append({
            "agent": agent["id"],
            "task": f"Handle {task_description} - your specialty",
            "depends_on": [f"step-{idx-1}"] if idx > 0 else []
        })

    # 3. Execute coordinated workflow
    workflow = await coordinate_workflow(steps)

    return workflow
```

### Future: S3 (Token Optimization)

Coordination will integrate token budgets:

```python
# Token-aware coordination (M03)
workflow = await coordinate_workflow(
    steps=[...],
    token_budget=10000,  # Total budget
    budget_allocation="proportional"  # Or "equal", "weighted"
)
```

### Future: S4 (Meta-Skills)

Coordination enables complex skill composition:

```python
# Meta-skill orchestration (M04)
workflow = await coordinate_workflow(
    steps=[
        {"skill": "code-analysis", "params": {...}},
        {"skill": "refactoring", "depends_on": ["step-0"]},
        {"skill": "test-generation", "depends_on": ["step-1"]}
    ]
)
```

## Best Practices

### Workflow Design

**Good workflow structure:**

- Clear dependencies between steps
- Meaningful task descriptions
- Appropriate failure strategies
- Reasonable timeout values

**Example:**

```python
# ✅ Good: Clear dependencies and descriptions
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": "data-engineer",
            "task": "Load and validate customer data from CSV",
            "params": {"file": "customers.csv", "validations": ["email", "phone"]}
        },
        {
            "agent": "ml-engineer",
            "task": "Train churn prediction model using validated data",
            "depends_on": ["step-0"],
            "params": {"model": "random_forest", "features": ["tenure", "usage"]}
        }
    ]
)

# ❌ Bad: Vague tasks, unclear dependencies
workflow = await coordinate_workflow(
    steps=[
        {"agent": "data-engineer", "task": "process data"},
        {"agent": "ml-engineer", "task": "train model"}
    ]
)
```

### Failure Handling

Choose failure strategy based on use case:

- **retry**: Transient failures (network issues, temporary unavailability)
- **fallback**: Alternative approaches available
- **abort**: Critical step that blocks all downstream work
- **continue**: Non-critical step, workflow can proceed

**Example:**

```python
# Critical deployment: abort on failure
workflow = await coordinate_workflow(
    steps=[...],
    failure_strategy="abort"
)

# Best-effort analysis: continue on failure
workflow = await coordinate_workflow(
    steps=[...],
    failure_strategy="continue"
)
```

### Context Management

**Efficient context passing:**

- Include only necessary data
- Use file paths instead of embedding large content
- Compress repetitive information
- Version context schema

**Example:**

```python
# ✅ Good: Minimal, structured context
context = {
    "files": ["auth.py", "models/user.py"],
    "focus_areas": ["password_hashing", "session_management"],
    "standards": {"reference": "OWASP_ASVS_4.0"}
}

# ❌ Bad: Massive, unstructured context
context = {
    "entire_codebase": read_all_files(),  # Too large
    "random_notes": "check security stuff",  # Too vague
}
```

### Monitoring and Debugging

**Track workflow execution:**

```python
# Start workflow
workflow = await coordinate_workflow(steps=[...])
workflow_id = workflow["workflow_id"]

# Monitor progress
async def monitor_workflow(wf_id):
    while True:
        status = await get_workflow_status(wf_id)

        if status["status"] == "completed":
            print(f"✅ Workflow completed in {status['total_duration_ms']}ms")
            break
        elif status["status"] == "failed":
            print(f"❌ Workflow failed at step {status['current_step']}")
            # Get failure events
            events = await get_coordination_events(
                workflow_id=wf_id,
                event_type="failure"
            )
            for event in events["events"]:
                print(f"  Error: {event['metadata']['error']}")
            break
        else:
            print(f"⏳ Progress: {status['progress_percent']}%")
            await asyncio.sleep(1)

await monitor_workflow(workflow_id)
```

## Limitations

### Current Implementation (v1.0.0 Target)

1. **Sequential Execution Primary**: Parallel execution is basic

   - **Mitigation**: Start with sequential, add parallelism in M02
   - **Impact**: Some workflows slower than optimal

1. **Synchronous Handoffs**: Handoffs block until complete

   - **Mitigation**: Use `wait_for_completion=False` for async
   - **Future**: Full async orchestration in M03

1. **Limited Rollback**: Only supports checkpoint-based rollback

   - **Mitigation**: Design workflows with recovery steps
   - **Future**: Full state machine with arbitrary rollback in M04

1. **No Cross-Workflow Dependencies**: Workflows are isolated

   - **Mitigation**: Chain workflows explicitly
   - **Future**: Workflow composition in M04

### Known Edge Cases

1. **Circular Dependencies**: Will be detected and rejected

   - Example: Step A depends on B, B depends on A
   - Solution: Validation prevents workflow creation

1. **Long-Running Workflows**: May timeout

   - Example: Workflow with 50+ steps
   - Solution: Break into smaller workflows or increase timeout

1. **Context Size Limits**: Large contexts may fail serialization

   - Example: Passing 100MB of data
   - Solution: Use file references instead of embedding

## Troubleshooting

### Common Issues

**Issue**: Workflow stuck in "in_progress" status

```
Symptom: get_workflow_status shows no progress
Diagnosis: Agent failed without reporting error, or network issue
Solution: Check coordination events, manually abort workflow, retry
```

**Issue**: Handoff context not preserved

```
Symptom: Target agent doesn't have expected information
Diagnosis: Context serialization failed or schema mismatch
Solution: Validate context structure, check event logs
```

**Issue**: Workflow fails with DependencyError

```
Symptom: "Unresolved dependencies" error
Diagnosis: Invalid step references or circular dependencies
Solution: Review depends_on fields, ensure valid step indices
```

**Issue**: Performance degradation with many workflows

```
Symptom: Coordination becomes slow with 20+ concurrent workflows
Diagnosis: Resource contention or state management overhead
Solution: Reduce concurrency, optimize state persistence
```

### Diagnostic Commands

```python
# Check orchestration system health
from plugins.mycelium_core.coordination import check_coordination_health

health = await check_coordination_health()
print(f"Status: {health['status']}")
print(f"Active workflows: {health['active_workflows']}")
print(f"Queue depth: {health['queue_depth']}")

# Analyze workflow performance
events = await get_coordination_events(workflow_id="wf-abc-123")
total_handoff_time = sum(
    e["metadata"]["duration_ms"]
    for e in events["events"]
    if e["event_type"] == "handoff"
)
print(f"Total handoff overhead: {total_handoff_time}ms")

# Debug failed workflow
workflow_id = "wf-failed-123"
status = await get_workflow_status(workflow_id)
failed_step = status["steps"][status["current_step"]]
print(f"Failed at step {status['current_step']}: {failed_step['agent']}")

events = await get_coordination_events(
    workflow_id=workflow_id,
    event_type="failure"
)
print(f"Failure reason: {events['events'][0]['metadata']['error']}")
```

## Configuration

### Environment Variables

```bash
# Coordination API URL (default: http://localhost:8000)
export COORDINATION_API_URL="http://localhost:8000"

# Maximum concurrent workflows (default: 50)
export MAX_CONCURRENT_WORKFLOWS=50

# Workflow timeout (default: 300 seconds)
export WORKFLOW_TIMEOUT_SECONDS=300

# Event retention (default: 30 days)
export EVENT_RETENTION_DAYS=30
```

### Tool Configuration

Configuration is stored in `plugins/mycelium-core/mcp/config/coordination.json`:

- **Timeout**: 300 seconds per workflow
- **Max retries**: 3 per step
- **Max workflow size**: 20 steps
- **Max concurrent workflows**: 50
- **Event storage**: PostgreSQL with 30-day retention
- **State checkpoints**: Every 5 steps

## Metrics and Monitoring

### Usage Metrics

Track these metrics for optimization:

- Workflow completion rate
- Average workflow duration
- Most common workflow patterns
- Agent utilization rates
- Handoff frequency

### Performance Metrics

Monitor for SLA compliance:

- Workflow latency (P50, P95, P99)
- Handoff overhead
- State persistence time
- Event query performance
- Concurrent workflow capacity

### Quality Metrics

Measure effectiveness:

- Workflow success rate
- Failure recovery rate
- Context preservation accuracy
- User satisfaction with results
- Time saved through coordination

## Version History

### v1.0.0 (Target: 2025-10-21)

**Planned Features:**

- MCP tools: `coordinate_workflow`, `handoff_to_agent`, `get_workflow_status`, `get_coordination_events`
- Sequential workflow execution
- Basic parallel execution
- Retry-based failure recovery
- State management with checkpoints
- Coordination event tracking
- Integration tests and documentation

### Planned Enhancements

**v1.1.0 (M02)**

- Advanced parallel execution patterns
- Conditional workflow branching
- Dynamic workflow modification
- Enhanced failure recovery

**v2.0.0 (M03)**

- Token-aware coordination
- Async workflow execution
- Cross-workflow dependencies
- Advanced state machine

**v3.0.0 (M04)**

- Workflow composition meta-skills
- AI-powered optimization
- Self-healing workflows
- Real-time collaboration

## References

- [M01 Milestone Specification](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md)
- [Task 1.5: Handoff Protocol](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md#task-15-handoff-protocol-implementation)
- [Task 1.6: Orchestration Engine](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md#task-16-workflow-orchestration-engine)
- [Task 1.8: Coordination MCP Tool](/home/gerald/git/mycelium/docs/projects/claude-code-skills/milestones/M01_AGENT_DISCOVERY_SKILLS.md#task-18-coordination-mcp-tool)
- [Handoff Protocol Specification](/home/gerald/git/mycelium/docs/technical/handoff-protocol.md)
- [Orchestration Engine Documentation](/home/gerald/git/mycelium/docs/technical/orchestration-engine.md)

## Support

For issues or questions:

1. Check troubleshooting section above
1. Review coordination events for debugging
1. Check orchestration engine health status
1. Consult technical documentation
1. Report issues with workflow reproduction steps

______________________________________________________________________

**Skill ID**: S2 **Category**: Coordination **Maturity**: Planned **Target Test Coverage**: 90% **Last Updated**:
2025-10-21
