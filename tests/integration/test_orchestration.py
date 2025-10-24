"""Integration tests for workflow orchestration engine.

Tests cover:
- Sequential workflow execution
- Parallel task coordination
- Dependency resolution
- State persistence and rollback
- Failure recovery mechanisms
- Multi-agent workflows (3+ agents)
"""

import asyncio
import os
from typing import Any

import pytest

# Set test database URL
os.environ["DATABASE_URL"] = "postgresql://localhost:5432/mycelium_test"

from coordination import (
    HandoffContext,
    StateManager,
    TaskStatus,
    WorkflowOrchestrator,
    WorkflowStatus,
)
from coordination.orchestrator import (
    DependencyError,
    OrchestrationError,
    RetryPolicy,
    TaskDefinition,
    TaskExecutionContext,
)


@pytest.fixture
async def state_manager():
    """Create state manager for tests."""
    manager = StateManager()
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
async def orchestrator(state_manager):
    """Create orchestrator for tests."""
    return WorkflowOrchestrator(state_manager)


@pytest.mark.asyncio
async def test_sequential_workflow(orchestrator):
    """Test sequential workflow with dependency chain."""
    results = []

    async def task_a(ctx: TaskExecutionContext) -> dict[str, Any]:
        results.append("A")
        await asyncio.sleep(0.1)
        return {"output": "A completed"}

    async def task_b(ctx: TaskExecutionContext) -> dict[str, Any]:
        results.append("B")
        # Verify task A result is available
        assert len(ctx.previous_results) == 1
        assert ctx.previous_results[0]["task_id"] == "task_a"
        return {"output": "B completed"}

    async def task_c(ctx: TaskExecutionContext) -> dict[str, Any]:
        results.append("C")
        # Verify both A and B results available
        assert len(ctx.previous_results) == 2
        return {"output": "C completed"}

    # Register executors
    orchestrator.register_executor("agent_a", task_a)
    orchestrator.register_executor("agent_b", task_b)
    orchestrator.register_executor("agent_c", task_c)

    # Define tasks: A -> B -> C
    tasks = [
        TaskDefinition(task_id="task_a", agent_id="agent_a", agent_type="agent_a"),
        TaskDefinition(
            task_id="task_b",
            agent_id="agent_b",
            agent_type="agent_b",
            dependencies=["task_a"],
        ),
        TaskDefinition(
            task_id="task_c",
            agent_id="agent_c",
            agent_type="agent_c",
            dependencies=["task_a", "task_b"],
        ),
    ]

    # Create and execute workflow
    workflow_id = await orchestrator.create_workflow(tasks)
    final_state = await orchestrator.execute_workflow(workflow_id)

    # Verify execution
    assert final_state.status == WorkflowStatus.COMPLETED
    assert results == ["A", "B", "C"]
    assert all(t.status == TaskStatus.COMPLETED for t in final_state.tasks.values())


@pytest.mark.asyncio
async def test_parallel_workflow(orchestrator):
    """Test parallel execution of independent tasks."""
    execution_times = {}

    async def parallel_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        task_id = ctx.task_def.task_id
        execution_times[task_id] = asyncio.get_event_loop().time()
        await asyncio.sleep(0.2)
        return {"output": f"{task_id} completed"}

    # Register executor
    orchestrator.register_executor("parallel_agent", parallel_task)

    # Define parallel tasks (no dependencies)
    tasks = [
        TaskDefinition(
            task_id=f"task_{i}",
            agent_id=f"agent_{i}",
            agent_type="parallel_agent",
        )
        for i in range(5)
    ]

    # Create and execute workflow
    workflow_id = await orchestrator.create_workflow(tasks)
    start_time = asyncio.get_event_loop().time()
    final_state = await orchestrator.execute_workflow(workflow_id)
    total_time = asyncio.get_event_loop().time() - start_time

    # Verify parallel execution (should complete in ~0.2s, not 1.0s)
    assert final_state.status == WorkflowStatus.COMPLETED
    assert total_time < 0.5  # With parallelism
    assert len(execution_times) == 5

    # Verify all tasks started around the same time (within 0.1s)
    start_times = list(execution_times.values())
    time_spread = max(start_times) - min(start_times)
    assert time_spread < 0.2


@pytest.mark.asyncio
async def test_dependency_resolution(orchestrator):
    """Test complex dependency resolution with diamond pattern."""
    execution_order = []

    async def tracked_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        task_id = ctx.task_def.task_id
        execution_order.append(task_id)
        await asyncio.sleep(0.05)
        return {"output": f"{task_id} done"}

    # Register executor
    orchestrator.register_executor("test_agent", tracked_task)

    # Diamond dependency pattern:
    #     A
    #    / \
    #   B   C
    #    \ /
    #     D
    tasks = [
        TaskDefinition(task_id="A", agent_id="a", agent_type="test_agent"),
        TaskDefinition(
            task_id="B",
            agent_id="b",
            agent_type="test_agent",
            dependencies=["A"],
        ),
        TaskDefinition(
            task_id="C",
            agent_id="c",
            agent_type="test_agent",
            dependencies=["A"],
        ),
        TaskDefinition(
            task_id="D",
            agent_id="d",
            agent_type="test_agent",
            dependencies=["B", "C"],
        ),
    ]

    # Create and execute
    workflow_id = await orchestrator.create_workflow(tasks)
    final_state = await orchestrator.execute_workflow(workflow_id)

    # Verify execution order
    assert final_state.status == WorkflowStatus.COMPLETED
    assert execution_order[0] == "A"  # A must be first
    assert execution_order[-1] == "D"  # D must be last
    assert set(execution_order[1:3]) == {"B", "C"}  # B and C in middle (either order)


@pytest.mark.asyncio
async def test_cycle_detection(orchestrator):
    """Test that circular dependencies are detected."""
    tasks = [
        TaskDefinition(
            task_id="A",
            agent_id="a",
            agent_type="test",
            dependencies=["C"],
        ),
        TaskDefinition(
            task_id="B",
            agent_id="b",
            agent_type="test",
            dependencies=["A"],
        ),
        TaskDefinition(
            task_id="C",
            agent_id="c",
            agent_type="test",
            dependencies=["B"],
        ),
    ]

    # Should raise DependencyError
    with pytest.raises(DependencyError, match="cycle"):
        await orchestrator.create_workflow(tasks)


@pytest.mark.asyncio
async def test_retry_mechanism(orchestrator):
    """Test task retry with exponential backoff."""
    attempt_count = 0

    async def failing_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Simulated failure")
        return {"output": "Success after retries"}

    orchestrator.register_executor("flaky_agent", failing_task)

    tasks = [
        TaskDefinition(
            task_id="task_1",
            agent_id="agent_1",
            agent_type="flaky_agent",
            retry_policy=RetryPolicy(max_attempts=3, initial_delay=0.05),
        )
    ]

    workflow_id = await orchestrator.create_workflow(tasks)
    final_state = await orchestrator.execute_workflow(workflow_id)

    # Verify successful completion after retries
    assert final_state.status == WorkflowStatus.COMPLETED
    assert attempt_count == 3
    assert final_state.tasks["task_1"].retry_count == 2


@pytest.mark.asyncio
async def test_failure_recovery_with_allow_failure(orchestrator):
    """Test workflow continuation when task allows failure."""

    async def success_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        return {"output": "success"}

    async def failing_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        raise ValueError("Intentional failure")

    orchestrator.register_executor("success_agent", success_task)
    orchestrator.register_executor("failing_agent", failing_task)

    tasks = [
        TaskDefinition(
            task_id="task_1",
            agent_id="agent_1",
            agent_type="success_agent",
        ),
        TaskDefinition(
            task_id="task_2",
            agent_id="agent_2",
            agent_type="failing_agent",
            dependencies=["task_1"],
            allow_failure=True,  # Allow this task to fail
            retry_policy=RetryPolicy(max_attempts=1),
        ),
        TaskDefinition(
            task_id="task_3",
            agent_id="agent_3",
            agent_type="success_agent",
            dependencies=["task_1", "task_2"],
        ),
    ]

    workflow_id = await orchestrator.create_workflow(tasks)
    final_state = await orchestrator.execute_workflow(workflow_id)

    # Workflow should complete despite task_2 failure
    assert final_state.status == WorkflowStatus.COMPLETED
    assert final_state.tasks["task_1"].status == TaskStatus.COMPLETED
    assert final_state.tasks["task_2"].status == TaskStatus.FAILED
    assert final_state.tasks["task_3"].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_critical_task_failure_aborts_workflow(orchestrator):
    """Test workflow abort when critical task fails."""

    async def success_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        return {"output": "success"}

    async def failing_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        raise ValueError("Critical failure")

    orchestrator.register_executor("success_agent", success_task)
    orchestrator.register_executor("failing_agent", failing_task)

    tasks = [
        TaskDefinition(
            task_id="task_1",
            agent_id="agent_1",
            agent_type="failing_agent",
            allow_failure=False,  # Critical task
            retry_policy=RetryPolicy(max_attempts=1),
        ),
        TaskDefinition(
            task_id="task_2",
            agent_id="agent_2",
            agent_type="success_agent",
            dependencies=["task_1"],
        ),
    ]

    workflow_id = await orchestrator.create_workflow(tasks)

    with pytest.raises(OrchestrationError):
        await orchestrator.execute_workflow(workflow_id)

    # Verify workflow marked as failed
    final_state = await orchestrator.get_workflow_status(workflow_id)
    assert final_state.status == WorkflowStatus.FAILED
    assert final_state.tasks["task_1"].status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_state_persistence(orchestrator, state_manager):
    """Test state persistence and retrieval."""

    async def simple_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        return {"data": f"Result from {ctx.task_def.task_id}"}

    orchestrator.register_executor("test_agent", simple_task)

    tasks = [
        TaskDefinition(task_id="task_1", agent_id="agent_1", agent_type="test_agent"),
        TaskDefinition(
            task_id="task_2",
            agent_id="agent_2",
            agent_type="test_agent",
            dependencies=["task_1"],
        ),
    ]

    # Create workflow
    workflow_id = await orchestrator.create_workflow(tasks)

    # Retrieve state before execution
    state = await state_manager.get_workflow(workflow_id)
    assert state.status == WorkflowStatus.PENDING
    assert len(state.tasks) == 2

    # Execute workflow
    await orchestrator.execute_workflow(workflow_id)

    # Retrieve final state
    final_state = await state_manager.get_workflow(workflow_id)
    assert final_state.status == WorkflowStatus.COMPLETED
    assert all(t.status == TaskStatus.COMPLETED for t in final_state.tasks.values())
    assert all(t.result is not None for t in final_state.tasks.values())


@pytest.mark.asyncio
async def test_state_rollback(orchestrator, state_manager):
    """Test rollback to previous workflow version."""

    async def simple_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        return {"data": "result"}

    orchestrator.register_executor("test_agent", simple_task)

    tasks = [
        TaskDefinition(task_id="task_1", agent_id="agent_1", agent_type="test_agent"),
    ]

    workflow_id = await orchestrator.create_workflow(tasks)
    initial_version = (await state_manager.get_workflow(workflow_id)).version

    # Execute workflow
    await orchestrator.execute_workflow(workflow_id)
    final_version = (await state_manager.get_workflow(workflow_id)).version

    assert final_version > initial_version

    # Rollback to initial version
    rolled_back_state = await orchestrator.rollback_workflow(
        workflow_id, initial_version
    )
    assert rolled_back_state.version == initial_version
    assert rolled_back_state.status == WorkflowStatus.PENDING


@pytest.mark.asyncio
async def test_multi_agent_workflow(orchestrator):
    """Test complex multi-agent workflow with 5+ agents."""
    execution_log = []

    async def agent_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        agent_type = ctx.task_def.agent_type
        execution_log.append(agent_type)
        await asyncio.sleep(0.05)

        # Simulate different agent behaviors
        return {
            "agent": agent_type,
            "processed": True,
            "dependencies_count": len(ctx.previous_results),
        }

    # Register multiple agent types
    for agent_type in ["parser", "analyzer", "validator", "optimizer", "reporter"]:
        orchestrator.register_executor(agent_type, agent_task)

    # Complex workflow:
    # parser -> analyzer -> validator -> optimizer -> reporter
    #            \-> validator2 -/
    tasks = [
        TaskDefinition(task_id="parse", agent_id="p1", agent_type="parser"),
        TaskDefinition(
            task_id="analyze",
            agent_id="a1",
            agent_type="analyzer",
            dependencies=["parse"],
        ),
        TaskDefinition(
            task_id="validate1",
            agent_id="v1",
            agent_type="validator",
            dependencies=["analyze"],
        ),
        TaskDefinition(
            task_id="validate2",
            agent_id="v2",
            agent_type="validator",
            dependencies=["analyze"],
        ),
        TaskDefinition(
            task_id="optimize",
            agent_id="o1",
            agent_type="optimizer",
            dependencies=["validate1", "validate2"],
        ),
        TaskDefinition(
            task_id="report",
            agent_id="r1",
            agent_type="reporter",
            dependencies=["optimize"],
        ),
    ]

    workflow_id = await orchestrator.create_workflow(tasks)
    final_state = await orchestrator.execute_workflow(workflow_id)

    # Verify completion
    assert final_state.status == WorkflowStatus.COMPLETED
    assert len(execution_log) == 6
    assert execution_log[0] == "parser"
    assert execution_log[-1] == "reporter"

    # Verify dependency handling
    reporter_task = final_state.tasks["report"]
    assert reporter_task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_timeout_handling(orchestrator):
    """Test task timeout and recovery."""

    async def slow_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        await asyncio.sleep(1.0)  # Will timeout
        return {"output": "should not reach here"}

    orchestrator.register_executor("slow_agent", slow_task)

    tasks = [
        TaskDefinition(
            task_id="task_1",
            agent_id="agent_1",
            agent_type="slow_agent",
            timeout=0.2,  # 200ms timeout
            retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.05),
        )
    ]

    workflow_id = await orchestrator.create_workflow(tasks)

    with pytest.raises(OrchestrationError):
        await orchestrator.execute_workflow(workflow_id)

    # Verify task failed due to timeout
    final_state = await orchestrator.get_workflow_status(workflow_id)
    assert final_state.tasks["task_1"].status == TaskStatus.FAILED
    assert final_state.tasks["task_1"].error["error_type"] == "timeout"


@pytest.mark.asyncio
async def test_workflow_cancellation(orchestrator):
    """Test workflow cancellation."""

    async def long_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        await asyncio.sleep(5.0)
        return {"output": "completed"}

    orchestrator.register_executor("long_agent", long_task)

    tasks = [
        TaskDefinition(task_id="task_1", agent_id="agent_1", agent_type="long_agent")
    ]

    workflow_id = await orchestrator.create_workflow(tasks)

    # Start workflow in background
    await orchestrator.execute_workflow(workflow_id, background=True)
    await asyncio.sleep(0.2)  # Let it start

    # Cancel workflow
    final_state = await orchestrator.cancel_workflow(workflow_id)

    assert final_state.status == WorkflowStatus.CANCELLED


@pytest.mark.asyncio
async def test_memory_overhead(orchestrator):
    """Test memory overhead remains under 50MB per workflow."""
    import sys

    async def lightweight_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        return {"data": "result"}

    orchestrator.register_executor("test_agent", lightweight_task)

    # Create workflow with many tasks
    tasks = [
        TaskDefinition(
            task_id=f"task_{i}",
            agent_id=f"agent_{i}",
            agent_type="test_agent",
        )
        for i in range(100)
    ]

    # Measure memory before
    import gc
    gc.collect()

    workflow_id = await orchestrator.create_workflow(tasks)
    initial_state = await orchestrator.get_workflow_status(workflow_id)

    # Get approximate memory size of workflow state
    state_size = sys.getsizeof(initial_state.to_dict())

    # Verify memory overhead is reasonable
    # Full state should be well under 50MB even with 100 tasks
    assert state_size < 1_000_000  # 1MB for 100 tasks is reasonable


@pytest.mark.asyncio
async def test_context_preservation(orchestrator):
    """Test context preservation across handoffs."""
    context_checks = []

    async def context_aware_task(ctx: TaskExecutionContext) -> dict[str, Any]:
        context_checks.append({
            "task_id": ctx.task_def.task_id,
            "has_description": ctx.workflow_context.task_description is not None,
            "prev_results_count": len(ctx.previous_results),
        })
        return {"output": f"Processed by {ctx.task_def.task_id}"}

    orchestrator.register_executor("test_agent", context_aware_task)

    # Create workflow with context
    context = HandoffContext(
        task_description="Multi-step data processing workflow",
        user_preferences={"format": "json"},
    )

    tasks = [
        TaskDefinition(task_id="task_1", agent_id="agent_1", agent_type="test_agent"),
        TaskDefinition(
            task_id="task_2",
            agent_id="agent_2",
            agent_type="test_agent",
            dependencies=["task_1"],
        ),
        TaskDefinition(
            task_id="task_3",
            agent_id="agent_3",
            agent_type="test_agent",
            dependencies=["task_2"],
        ),
    ]

    workflow_id = await orchestrator.create_workflow(tasks, context=context)
    await orchestrator.execute_workflow(workflow_id)

    # Verify context preservation
    assert len(context_checks) == 3
    assert all(check["has_description"] for check in context_checks)
    assert context_checks[0]["prev_results_count"] == 0
    assert context_checks[1]["prev_results_count"] == 1
    assert context_checks[2]["prev_results_count"] == 1  # Only immediate dependency


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
