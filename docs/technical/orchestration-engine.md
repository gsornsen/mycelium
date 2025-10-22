# Workflow Orchestration Engine

## Overview

The Workflow Orchestration Engine is a core component of the Mycelium multi-agent coordination system, providing robust workflow execution capabilities with dependency resolution, state management, and failure recovery mechanisms.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                  WorkflowOrchestrator                    │
│  - DAG-based execution                                   │
│  - Dependency resolution                                 │
│  - Parallel task coordination                            │
│  - Failure recovery                                      │
└──────────────┬──────────────────────────────────────────┘
               │
               ├─────────────────┐
               │                 │
      ┌────────▼────────┐  ┌────▼─────────────┐
      │  StateManager   │  │ HandoffProtocol  │
      │  - Persistence  │  │ - State transfer │
      │  - Rollback     │  │ - Validation     │
      │  - Versioning   │  │ - Serialization  │
      └─────────────────┘  └──────────────────┘
               │
      ┌────────▼────────┐
      │   PostgreSQL    │
      │  - workflow_states
      │  - task_states  │
      │  - state_history│
      └─────────────────┘
```

### Key Features

1. **DAG-Based Execution**
   - Tasks organized as Directed Acyclic Graph
   - Automatic topological sorting
   - Cycle detection at creation time

2. **Dependency Resolution**
   - Prerequisite validation
   - Ordering constraints enforcement
   - Dynamic ready-task detection

3. **Parallel Coordination**
   - Independent tasks execute concurrently
   - Configurable parallelism limits
   - Resource-aware scheduling

4. **State Management**
   - Persistent state storage
   - Version tracking for rollback
   - Atomic updates with transactions

5. **Failure Recovery**
   - Configurable retry policies
   - Exponential backoff
   - Graceful degradation with allow_failure

## Data Models

### WorkflowState

Represents the complete state of a workflow execution.

```python
@dataclass
class WorkflowState:
    workflow_id: str
    status: WorkflowStatus  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    tasks: Dict[str, TaskState]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    variables: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str]
    version: int
```

### TaskState

Represents the state of an individual task.

```python
@dataclass
class TaskState:
    task_id: str
    agent_id: str
    agent_type: str
    status: TaskStatus  # PENDING, READY, RUNNING, COMPLETED, FAILED, SKIPPED
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_time: Optional[float]  # milliseconds
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    retry_count: int
    dependencies: List[str]
```

### TaskDefinition

Defines a task for workflow creation.

```python
@dataclass
class TaskDefinition:
    task_id: str
    agent_id: str
    agent_type: str
    dependencies: List[str] = []
    retry_policy: RetryPolicy = RetryPolicy()
    timeout: Optional[float] = None  # seconds
    allow_failure: bool = False
    metadata: Dict[str, Any] = {}
```

### RetryPolicy

Configures retry behavior for task execution.

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
```

## Usage Examples

### Creating a Sequential Workflow

```python
from plugins.mycelium_core.coordination import (
    WorkflowOrchestrator,
    StateManager,
    TaskDefinition,
)

# Initialize
state_manager = StateManager()
await state_manager.initialize()
orchestrator = WorkflowOrchestrator(state_manager)

# Define tasks
tasks = [
    TaskDefinition(
        task_id="parse",
        agent_id="parser-1",
        agent_type="python-parser",
    ),
    TaskDefinition(
        task_id="analyze",
        agent_id="analyzer-1",
        agent_type="code-analyzer",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="report",
        agent_id="reporter-1",
        agent_type="report-generator",
        dependencies=["analyze"],
    ),
]

# Create and execute
workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
```

### Creating a Parallel Workflow

```python
# Tasks with no dependencies execute in parallel
tasks = [
    TaskDefinition(task_id="lint", agent_id="linter", agent_type="linter"),
    TaskDefinition(task_id="test", agent_id="tester", agent_type="tester"),
    TaskDefinition(task_id="type_check", agent_id="mypy", agent_type="type-checker"),
]

workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
```

### Diamond Dependency Pattern

```python
# Complex dependency pattern:
#     parse
#    /     \
#  analyze  validate
#    \     /
#     merge

tasks = [
    TaskDefinition(task_id="parse", agent_id="p1", agent_type="parser"),
    TaskDefinition(
        task_id="analyze",
        agent_id="a1",
        agent_type="analyzer",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="validate",
        agent_id="v1",
        agent_type="validator",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="merge",
        agent_id="m1",
        agent_type="merger",
        dependencies=["analyze", "validate"],
    ),
]

workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
```

### Custom Retry Policy

```python
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
```

### Allow Task Failure

```python
# Non-critical task that won't abort workflow if it fails
task = TaskDefinition(
    task_id="optional-optimization",
    agent_id="optimizer",
    agent_type="optimizer",
    allow_failure=True,  # Workflow continues even if this fails
)
```

### Timeout Configuration

```python
task = TaskDefinition(
    task_id="bounded-task",
    agent_id="agent-1",
    agent_type="slow-processor",
    timeout=30.0,  # 30 second timeout
)
```

### Background Execution

```python
# Start workflow in background
await orchestrator.execute_workflow(workflow_id, background=True)

# Check status later
status = await orchestrator.get_workflow_status(workflow_id)
print(f"Status: {status.status}")
```

### Workflow Control Operations

```python
# Pause workflow
await orchestrator.pause_workflow(workflow_id)

# Resume workflow
await orchestrator.resume_workflow(workflow_id)

# Cancel workflow
await orchestrator.cancel_workflow(workflow_id)

# Rollback to previous version
await orchestrator.rollback_workflow(workflow_id, version=1)
```

## Task Executor Registration

Executors are async functions that perform the actual task work.

```python
from plugins.mycelium_core.coordination.orchestrator import TaskExecutionContext

async def my_task_executor(ctx: TaskExecutionContext) -> Dict[str, Any]:
    """
    Task executor function.

    Args:
        ctx: Execution context containing:
            - task_def: TaskDefinition
            - workflow_id: str
            - workflow_context: HandoffContext
            - previous_results: List[Dict] (from dependencies)
            - variables: Dict (workflow variables)

    Returns:
        Result dictionary to be stored in task state
    """
    # Access task definition
    task_id = ctx.task_def.task_id

    # Access results from dependencies
    for prev in ctx.previous_results:
        dep_task_id = prev["task_id"]
        dep_result = prev["result"]
        # Process dependency result

    # Access workflow variables
    config = ctx.variables.get("config", {})

    # Perform task work
    result = await perform_work(ctx)

    return {"output": result, "status": "success"}

# Register executor
orchestrator.register_executor("my-agent-type", my_task_executor)
```

## State Persistence

### Database Schema

```sql
-- Workflow states
CREATE TABLE workflow_states (
    workflow_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    variables JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    error TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

-- Task states
CREATE TABLE task_states (
    task_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflow_states(workflow_id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time REAL,
    result JSONB,
    error JSONB,
    retry_count INTEGER DEFAULT 0,
    dependencies TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- State history for rollback
CREATE TABLE workflow_state_history (
    id SERIAL PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    state_snapshot JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(workflow_id, version)
);
```

### Versioning

Every workflow update increments the version number and saves a snapshot to history:

```python
# Initial version
state = await state_manager.create_workflow(tasks)
assert state.version == 1

# After update
state.status = WorkflowStatus.RUNNING
updated = await state_manager.update_workflow(state)
assert updated.version == 2

# Rollback to previous version
restored = await state_manager.rollback_workflow(workflow_id, version=1)
assert restored.version == 1
```

## Handoff Protocol

The orchestration engine uses the handoff protocol for agent-to-agent communication.

### HandoffMessage Structure

```python
@dataclass
class HandoffMessage:
    version: str
    handoff_id: str
    workflow_id: str
    source: AgentInfo
    target: AgentInfo
    context: HandoffContext
    state: HandoffState
    metadata: HandoffMetadata
    timestamp: str
```

### Creating Handoff Messages

```python
from plugins.mycelium_core.coordination import HandoffProtocol

message = HandoffProtocol.create_handoff(
    source_agent_id="agent-1",
    source_agent_type="parser",
    target_agent_id="agent-2",
    target_agent_type="analyzer",
    task_description="Analyze parsed code",
    workflow_id=workflow_id,
)

# Validate
HandoffProtocol.validate(message)

# Serialize
json_str = HandoffProtocol.serialize(message)

# Deserialize
restored = HandoffProtocol.deserialize(json_str)
```

## Performance Characteristics

### Memory Overhead

- **Target:** <50MB per workflow
- **Achieved:** ~1MB per 100 tasks
- State stored in PostgreSQL, not memory
- Only active task data kept in memory

### Execution Performance

- **Sequential tasks:** Latency = sum of task execution times
- **Parallel tasks:** Latency ≈ longest task execution time
- **Dependency resolution:** O(V + E) where V = tasks, E = dependencies
- **State updates:** <10ms per update (PostgreSQL)

### Scalability

- **Concurrent workflows:** 50+ simultaneous workflows tested
- **Tasks per workflow:** Tested up to 100 tasks
- **Parallel task limit:** Configurable (default: 10)
- **Database connections:** Pooled (2-10 connections)

## Error Handling

### Exception Hierarchy

```
OrchestrationError (base)
├── DependencyError
│   ├── Circular dependency detected
│   └── Missing dependency
└── ExecutionError
    ├── Task execution failed
    ├── Timeout exceeded
    └── No executor registered
```

### Failure Scenarios

1. **Task Execution Failure**
   - Retry with exponential backoff
   - Mark as FAILED after max attempts
   - Abort workflow if allow_failure=False

2. **Task Timeout**
   - Cancel execution
   - Count as failed attempt
   - Retry if attempts remaining

3. **Dependency Cycle**
   - Detected at workflow creation
   - DependencyError raised
   - Workflow not created

4. **Missing Executor**
   - ExecutionError when task starts
   - Workflow marked as FAILED
   - Clear error message with agent_type

5. **Database Error**
   - StateManagerError raised
   - Automatic retry with connection pool
   - Graceful degradation

## Monitoring and Debugging

### Workflow Status Tracking

```python
# Get current status
state = await orchestrator.get_workflow_status(workflow_id)

print(f"Status: {state.status}")
print(f"Version: {state.version}")
print(f"Started: {state.started_at}")

# Check individual tasks
for task_id, task in state.tasks.items():
    print(f"{task_id}: {task.status}")
    if task.error:
        print(f"  Error: {task.error}")
```

### Listing Workflows

```python
# List all workflows
all_workflows = await state_manager.list_workflows()

# List by status
running = await state_manager.list_workflows(status=WorkflowStatus.RUNNING)
failed = await state_manager.list_workflows(status=WorkflowStatus.FAILED)

# Limit results
recent = await state_manager.list_workflows(limit=10)
```

### State History

```python
# View state history
state = await state_manager.get_workflow(workflow_id)
print(f"Current version: {state.version}")

# Rollback to inspect previous state
for version in range(1, state.version):
    historical = await state_manager.rollback_workflow(workflow_id, version)
    print(f"Version {version}: {historical.status}")

    # Restore to current version
    await state_manager.rollback_workflow(workflow_id, state.version)
```

## Best Practices

### 1. Task Granularity

**Good:** Fine-grained tasks with clear responsibilities
```python
tasks = [
    TaskDefinition(task_id="parse", agent_id="parser", agent_type="parser"),
    TaskDefinition(task_id="validate", agent_id="validator", agent_type="validator"),
    TaskDefinition(task_id="transform", agent_id="transformer", agent_type="transformer"),
]
```

**Bad:** Monolithic tasks
```python
# Avoid single task doing everything
tasks = [
    TaskDefinition(task_id="do_everything", agent_id="agent", agent_type="all-in-one"),
]
```

### 2. Dependency Design

**Good:** Clear dependency chain
```python
# Linear dependencies
tasks = [
    TaskDefinition(task_id="A", ...),
    TaskDefinition(task_id="B", dependencies=["A"], ...),
    TaskDefinition(task_id="C", dependencies=["B"], ...),
]
```

**Bad:** Unnecessary dependencies
```python
# C doesn't actually need A's output
tasks = [
    TaskDefinition(task_id="A", ...),
    TaskDefinition(task_id="B", dependencies=["A"], ...),
    TaskDefinition(task_id="C", dependencies=["A", "B"], ...),  # Remove A
]
```

### 3. Error Handling

**Good:** Appropriate allow_failure usage
```python
tasks = [
    TaskDefinition(task_id="critical", allow_failure=False, ...),  # Must succeed
    TaskDefinition(task_id="optional", allow_failure=True, ...),  # Nice to have
]
```

### 4. Retry Configuration

**Good:** Tuned retry policies
```python
# Quick operations - fail fast
fast_task = TaskDefinition(
    retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.5)
)

# Network operations - more retries
network_task = TaskDefinition(
    retry_policy=RetryPolicy(max_attempts=5, initial_delay=2.0, max_delay=30.0)
)
```

### 5. Resource Management

**Good:** Cleanup in finally block
```python
state_manager = StateManager()
try:
    await state_manager.initialize()
    # Use state manager
finally:
    await state_manager.close()
```

## Troubleshooting

### Workflow Stuck in RUNNING

**Symptom:** Workflow status remains RUNNING indefinitely

**Causes:**
1. Task executor hung
2. Database connection lost
3. Uncaught exception in executor

**Solutions:**
- Check task timeouts are configured
- Review executor logs for errors
- Cancel and restart workflow

### High Memory Usage

**Symptom:** Memory usage exceeds 50MB per workflow

**Causes:**
1. Large task results stored in state
2. Too many parallel tasks
3. Memory leak in executor

**Solutions:**
- Store large results externally (S3, filesystem)
- Reduce max_parallel_tasks
- Profile executor for memory leaks

### Slow Workflow Execution

**Symptom:** Workflows taking longer than expected

**Causes:**
1. Tasks executing sequentially instead of parallel
2. Inefficient dependency graph
3. Database performance issues

**Solutions:**
- Review task dependencies
- Optimize dependency graph for parallelism
- Add database indexes
- Increase connection pool size

## API Reference

### WorkflowOrchestrator

```python
class WorkflowOrchestrator:
    def __init__(
        self,
        state_manager: StateManager,
        default_retry_policy: Optional[RetryPolicy] = None,
        max_parallel_tasks: int = 10,
    )

    def register_executor(self, agent_type: str, executor: TaskExecutor) -> None

    async def create_workflow(
        self,
        tasks: List[TaskDefinition],
        workflow_id: Optional[str] = None,
        context: Optional[HandoffContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str

    async def execute_workflow(
        self,
        workflow_id: str,
        background: bool = False,
    ) -> Optional[WorkflowState]

    async def get_workflow_status(self, workflow_id: str) -> WorkflowState
    async def cancel_workflow(self, workflow_id: str) -> WorkflowState
    async def pause_workflow(self, workflow_id: str) -> WorkflowState
    async def resume_workflow(self, workflow_id: str) -> WorkflowState
    async def rollback_workflow(self, workflow_id: str, version: int) -> WorkflowState
```

### StateManager

```python
class StateManager:
    def __init__(
        self,
        pool: Optional[Pool] = None,
        connection_string: Optional[str] = None,
    )

    async def initialize() -> None
    async def close() -> None

    async def create_workflow(
        self,
        workflow_id: Optional[str] = None,
        tasks: Optional[List[TaskState]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState

    async def get_workflow(self, workflow_id: str) -> WorkflowState
    async def update_workflow(self, state: WorkflowState) -> WorkflowState
    async def update_task(
        self,
        workflow_id: str,
        task_id: str,
        status: Optional[TaskStatus] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
    ) -> WorkflowState

    async def rollback_workflow(self, workflow_id: str, version: int) -> WorkflowState
    async def delete_workflow(self, workflow_id: str) -> None
    async def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
    ) -> List[WorkflowState]
```

## Version History

- **1.0** (2025-01-20): Initial implementation
  - DAG-based execution
  - Dependency resolution
  - State persistence
  - Retry mechanisms
  - Handoff protocol integration

## Future Enhancements

1. **Conditional Execution**
   - Execute tasks based on runtime conditions
   - Skip branches based on results

2. **Sub-workflows**
   - Nest workflows for modularity
   - Reusable workflow templates

3. **Event-Driven Triggers**
   - Start workflows on external events
   - Webhook integration

4. **Distributed Execution**
   - Execute tasks across multiple nodes
   - Task affinity and placement

5. **Advanced Monitoring**
   - Real-time progress tracking
   - Performance metrics collection
   - Alerting on failures

## References

- [Handoff Protocol Specification](./handoff-protocol.md)
- [State Management Guide](./state-management.md)
- [Multi-Agent Coordination Best Practices](../guides/coordination-best-practices.md)
