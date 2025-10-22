# Coordination Module

Multi-agent workflow orchestration and coordination for Mycelium.

## Overview

The coordination module provides the infrastructure for orchestrating complex multi-agent workflows with:

- **DAG-based execution** - Tasks organized as directed acyclic graphs
- **Dependency resolution** - Automatic ordering and prerequisite validation
- **Parallel coordination** - Independent tasks execute concurrently
- **State management** - Persistent state with versioning and rollback
- **Failure recovery** - Configurable retry policies with exponential backoff
- **Handoff protocol** - Structured agent-to-agent communication

## Quick Start

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

# Register task executors
async def my_task(ctx):
    return {"result": "success"}

orchestrator.register_executor("my-agent-type", my_task)

# Define workflow
tasks = [
    TaskDefinition(task_id="task1", agent_id="agent1", agent_type="my-agent-type"),
    TaskDefinition(
        task_id="task2",
        agent_id="agent2",
        agent_type="my-agent-type",
        dependencies=["task1"],
    ),
]

# Execute
workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)

print(f"Workflow {result.status}: {result.workflow_id}")
```

## Components

### WorkflowOrchestrator

Main orchestration engine that manages workflow execution.

**Key Features:**
- Sequential and parallel task execution
- Dependency resolution with cycle detection
- Retry policies with exponential backoff
- Timeout handling
- Background execution
- Pause/resume/cancel operations

**Usage:**
```python
orchestrator = WorkflowOrchestrator(
    state_manager=state_manager,
    max_parallel_tasks=10,
)

# Register executors
orchestrator.register_executor("parser", parser_executor)
orchestrator.register_executor("analyzer", analyzer_executor)

# Create and execute
workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
```

### StateManager

Manages workflow state persistence with PostgreSQL backend.

**Key Features:**
- Workflow and task state persistence
- Version tracking for rollback
- Atomic updates with transactions
- Query capabilities

**Usage:**
```python
state_manager = StateManager(
    connection_string="postgresql://localhost/mycelium_registry"
)
await state_manager.initialize()

# Get workflow state
state = await state_manager.get_workflow(workflow_id)

# Update task
await state_manager.update_task(
    workflow_id,
    task_id,
    status=TaskStatus.COMPLETED,
    result={"data": "result"},
)

# Rollback
await state_manager.rollback_workflow(workflow_id, version=1)
```

### HandoffProtocol

Structured protocol for agent-to-agent communication.

**Key Features:**
- JSON schema validation
- Context preservation
- Progress tracking
- Metadata support

**Usage:**
```python
from plugins.mycelium_core.coordination import HandoffProtocol

# Create handoff message
message = HandoffProtocol.create_handoff(
    source_agent_id="agent-1",
    source_agent_type="parser",
    target_agent_id="agent-2",
    target_agent_type="analyzer",
    task_description="Analyze code",
)

# Validate
HandoffProtocol.validate(message)

# Serialize
json_str = HandoffProtocol.serialize(message)

# Deserialize
restored = HandoffProtocol.deserialize(json_str)
```

## Workflow Patterns

### Sequential Execution

Tasks execute one after another:

```python
tasks = [
    TaskDefinition(task_id="A", agent_id="a1", agent_type="type1"),
    TaskDefinition(task_id="B", agent_id="b1", agent_type="type2", dependencies=["A"]),
    TaskDefinition(task_id="C", agent_id="c1", agent_type="type3", dependencies=["B"]),
]
```

### Parallel Execution

Independent tasks execute concurrently:

```python
tasks = [
    TaskDefinition(task_id="A", agent_id="a1", agent_type="type1"),
    TaskDefinition(task_id="B", agent_id="b1", agent_type="type2"),
    TaskDefinition(task_id="C", agent_id="c1", agent_type="type3"),
]
```

### Diamond Pattern

Fan-out and fan-in:

```python
#     A
#    / \
#   B   C
#    \ /
#     D

tasks = [
    TaskDefinition(task_id="A", ...),
    TaskDefinition(task_id="B", dependencies=["A"], ...),
    TaskDefinition(task_id="C", dependencies=["A"], ...),
    TaskDefinition(task_id="D", dependencies=["B", "C"], ...),
]
```

## Configuration

### Retry Policy

Configure retry behavior per task:

```python
from plugins.mycelium_core.coordination.orchestrator import RetryPolicy

task = TaskDefinition(
    task_id="task1",
    agent_id="agent1",
    agent_type="type1",
    retry_policy=RetryPolicy(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
    ),
)
```

### Timeout

Set execution timeout:

```python
task = TaskDefinition(
    task_id="task1",
    agent_id="agent1",
    agent_type="type1",
    timeout=30.0,  # 30 seconds
)
```

### Allow Failure

Allow non-critical tasks to fail:

```python
task = TaskDefinition(
    task_id="optional-task",
    agent_id="agent1",
    agent_type="type1",
    allow_failure=True,  # Workflow continues if this fails
)
```

## Task Executors

Task executors are async functions that perform the actual work:

```python
from plugins.mycelium_core.coordination.orchestrator import TaskExecutionContext

async def my_executor(ctx: TaskExecutionContext) -> Dict[str, Any]:
    """
    Args:
        ctx: Execution context with:
            - task_def: TaskDefinition
            - workflow_id: str
            - workflow_context: HandoffContext
            - previous_results: List[Dict]
            - variables: Dict

    Returns:
        Result dictionary
    """
    # Access task info
    task_id = ctx.task_def.task_id

    # Access dependency results
    for prev in ctx.previous_results:
        dep_result = prev["result"]
        # Use dependency result

    # Perform work
    result = await do_work()

    return {"output": result}
```

## Error Handling

### Exception Types

- `OrchestrationError` - Base orchestration exception
- `DependencyError` - Dependency resolution failure
- `ExecutionError` - Task execution failure
- `StateManagerError` - State persistence error
- `HandoffValidationError` - Handoff message validation error

### Handling Failures

```python
from plugins.mycelium_core.coordination import OrchestrationError

try:
    result = await orchestrator.execute_workflow(workflow_id)
except OrchestrationError as e:
    print(f"Workflow failed: {e}")

    # Check final state
    state = await orchestrator.get_workflow_status(workflow_id)
    for task_id, task in state.tasks.items():
        if task.status == TaskStatus.FAILED:
            print(f"Task {task_id} failed: {task.error}")
```

## Performance

### Memory Overhead

- Target: <50MB per workflow
- Achieved: ~1MB per 100 tasks
- State stored in database, not memory

### Execution Performance

- Sequential: Sum of task execution times
- Parallel: ≈ Longest task execution time
- State updates: <10ms per update

### Scalability

- Concurrent workflows: 50+
- Tasks per workflow: 100+
- Parallel task limit: Configurable (default: 10)

## Testing

### Unit Tests

```bash
pytest tests/unit/coordination/ -v
```

### Integration Tests

```bash
# Requires PostgreSQL
pytest tests/integration/test_orchestration.py -v
```

### Test Coverage

Target: >85%

```bash
pytest --cov=plugins.mycelium_core.coordination --cov-report=html
```

## Database Schema

The module uses PostgreSQL with three main tables:

- `workflow_states` - Workflow metadata and status
- `task_states` - Individual task states
- `workflow_state_history` - Snapshots for rollback

See [orchestration-engine.md](../../../docs/technical/orchestration-engine.md) for complete schema.

## Documentation

- [Orchestration Engine Architecture](../../../docs/technical/orchestration-engine.md)
- [Handoff Protocol Specification](../../../docs/technical/handoff-protocol.md)
- [Coordination Best Practices](../../../docs/guides/coordination-best-practices.md)

## Examples

See `tests/integration/test_orchestration.py` for comprehensive examples:

- Sequential workflows
- Parallel execution
- Complex dependencies
- Retry mechanisms
- Failure handling
- State persistence
- Rollback operations

## Requirements

- Python 3.11+
- PostgreSQL 12+
- asyncpg
- jsonschema

## License

Part of the Mycelium project.
