"""Unit tests for state manager.

NOTE: These tests are currently skipped because coordination.state_manager module
has not been implemented yet. They will be enabled once the module is complete.
"""

import os

import pytest

# Skip entire module - coordination.state_manager not yet implemented
pytestmark = pytest.mark.skip(reason="coordination.state_manager module not yet implemented")

# Set test database URL
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test"
)

# Conditional imports - avoid import errors when module is skipped
try:
    from coordination.state_manager import (
        StateManager,
        StateNotFoundError,
        TaskState,
        TaskStatus,
        WorkflowStatus,
    )
except ImportError:
    # Module not yet implemented - tests will be skipped anyway
    pass


@pytest.fixture
async def state_manager():
    """Create state manager for tests."""
    manager = StateManager()
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_create_workflow(state_manager):
    """Test workflow creation."""
    state = await state_manager.create_workflow()

    assert state.workflow_id is not None
    assert state.status == WorkflowStatus.PENDING
    assert len(state.tasks) == 0
    assert state.version == 1


@pytest.mark.asyncio
async def test_create_workflow_with_tasks(state_manager):
    """Test workflow creation with tasks."""
    tasks = [
        TaskState(task_id="task1", agent_id="agent1", agent_type="type1"),
        TaskState(task_id="task2", agent_id="agent2", agent_type="type2"),
    ]

    state = await state_manager.create_workflow(tasks=tasks)

    assert len(state.tasks) == 2
    assert "task1" in state.tasks
    assert "task2" in state.tasks
    assert state.tasks["task1"].status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_get_workflow(state_manager):
    """Test retrieving workflow state."""
    # Create workflow
    created = await state_manager.create_workflow()

    # Retrieve it
    retrieved = await state_manager.get_workflow(created.workflow_id)

    assert retrieved.workflow_id == created.workflow_id
    assert retrieved.status == created.status
    assert retrieved.version == created.version


@pytest.mark.asyncio
async def test_get_nonexistent_workflow(state_manager):
    """Test retrieving non-existent workflow."""
    with pytest.raises(StateNotFoundError):
        await state_manager.get_workflow("nonexistent-id")


@pytest.mark.asyncio
async def test_update_workflow(state_manager):
    """Test updating workflow state."""
    # Create workflow
    state = await state_manager.create_workflow()
    initial_version = state.version

    # Update status
    state.status = WorkflowStatus.RUNNING
    updated = await state_manager.update_workflow(state)

    assert updated.version == initial_version + 1
    assert updated.status == WorkflowStatus.RUNNING

    # Verify persistence
    retrieved = await state_manager.get_workflow(state.workflow_id)
    assert retrieved.status == WorkflowStatus.RUNNING
    assert retrieved.version == updated.version


@pytest.mark.asyncio
async def test_update_task(state_manager):
    """Test updating individual task state."""
    # Create workflow with task
    tasks = [TaskState(task_id="task1", agent_id="agent1", agent_type="type1")]
    state = await state_manager.create_workflow(tasks=tasks)

    # Update task
    updated_state = await state_manager.update_task(
        state.workflow_id,
        "task1",
        status=TaskStatus.RUNNING,
    )

    assert updated_state.tasks["task1"].status == TaskStatus.RUNNING
    assert updated_state.tasks["task1"].started_at is not None


@pytest.mark.asyncio
async def test_update_task_with_result(state_manager):
    """Test updating task with result."""
    tasks = [TaskState(task_id="task1", agent_id="agent1", agent_type="type1")]
    state = await state_manager.create_workflow(tasks=tasks)

    # Update task with result
    result = {"output": "success", "data": [1, 2, 3]}
    updated_state = await state_manager.update_task(
        state.workflow_id,
        "task1",
        status=TaskStatus.COMPLETED,
        result=result,
        execution_time=150.5,
    )

    task = updated_state.tasks["task1"]
    assert task.status == TaskStatus.COMPLETED
    assert task.result == result
    assert task.execution_time == 150.5
    assert task.completed_at is not None


@pytest.mark.asyncio
async def test_update_nonexistent_task(state_manager):
    """Test updating non-existent task."""
    state = await state_manager.create_workflow()

    with pytest.raises(StateNotFoundError):
        await state_manager.update_task(
            state.workflow_id,
            "nonexistent-task",
            status=TaskStatus.RUNNING,
        )


@pytest.mark.asyncio
async def test_workflow_versioning(state_manager):
    """Test workflow version increments."""
    state = await state_manager.create_workflow()
    assert state.version == 1

    # Multiple updates
    for i in range(5):
        state.status = WorkflowStatus.RUNNING
        state = await state_manager.update_workflow(state)
        assert state.version == i + 2


@pytest.mark.asyncio
async def test_state_snapshot_creation(state_manager):
    """Test state snapshot is saved for rollback."""
    state = await state_manager.create_workflow()
    initial_version = state.version

    # Update several times
    for _ in range(3):
        state.status = WorkflowStatus.RUNNING
        state = await state_manager.update_workflow(state)

    # Verify we can rollback to initial version
    rolled_back = await state_manager.rollback_workflow(state.workflow_id, initial_version)
    assert rolled_back.version == initial_version


@pytest.mark.asyncio
async def test_rollback_workflow(state_manager):
    """Test rolling back workflow to previous version."""
    # Create and update workflow
    tasks = [TaskState(task_id="task1", agent_id="agent1", agent_type="type1")]
    state = await state_manager.create_workflow(tasks=tasks)
    version1 = state.version

    # Update task
    await state_manager.update_task(state.workflow_id, "task1", status=TaskStatus.COMPLETED)
    state = await state_manager.get_workflow(state.workflow_id)
    version2 = state.version

    assert version2 > version1
    assert state.tasks["task1"].status == TaskStatus.COMPLETED

    # Rollback
    rolled_back = await state_manager.rollback_workflow(state.workflow_id, version1)

    assert rolled_back.version == version1
    assert rolled_back.tasks["task1"].status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_rollback_nonexistent_version(state_manager):
    """Test rollback to non-existent version."""
    state = await state_manager.create_workflow()

    with pytest.raises(StateNotFoundError):
        await state_manager.rollback_workflow(state.workflow_id, 999)


@pytest.mark.asyncio
async def test_delete_workflow(state_manager):
    """Test deleting workflow."""
    state = await state_manager.create_workflow()

    # Delete
    await state_manager.delete_workflow(state.workflow_id)

    # Verify deletion
    with pytest.raises(StateNotFoundError):
        await state_manager.get_workflow(state.workflow_id)


@pytest.mark.asyncio
async def test_list_workflows(state_manager):
    """Test listing workflows."""
    # Create multiple workflows
    wf1 = await state_manager.create_workflow()
    wf2 = await state_manager.create_workflow()

    # Update one to running
    wf1.status = WorkflowStatus.RUNNING
    await state_manager.update_workflow(wf1)

    # List all
    all_workflows = await state_manager.list_workflows()
    assert len(all_workflows) >= 2

    # List by status
    running = await state_manager.list_workflows(status=WorkflowStatus.RUNNING)
    assert any(wf.workflow_id == wf1.workflow_id for wf in running)

    pending = await state_manager.list_workflows(status=WorkflowStatus.PENDING)
    assert any(wf.workflow_id == wf2.workflow_id for wf in pending)


@pytest.mark.asyncio
async def test_list_workflows_with_limit(state_manager):
    """Test listing workflows with limit."""
    # Create multiple workflows
    for _ in range(5):
        await state_manager.create_workflow()

    # List with limit
    workflows = await state_manager.list_workflows(limit=2)
    assert len(workflows) <= 2


@pytest.mark.asyncio
async def test_workflow_with_metadata(state_manager):
    """Test workflow with custom metadata."""
    metadata = {
        "user_id": "user-123",
        "project": "mycelium",
        "tags": ["test", "integration"],
    }

    state = await state_manager.create_workflow(metadata=metadata)

    assert state.metadata["user_id"] == "user-123"
    assert state.metadata["project"] == "mycelium"
    assert "test" in state.metadata["tags"]

    # Verify persistence
    retrieved = await state_manager.get_workflow(state.workflow_id)
    assert retrieved.metadata == metadata


@pytest.mark.asyncio
async def test_workflow_variables(state_manager):
    """Test workflow variables persistence."""
    state = await state_manager.create_workflow()

    # Add variables
    state.variables = {
        "counter": 5,
        "mode": "production",
        "config": {"timeout": 30},
    }
    await state_manager.update_workflow(state)

    # Verify persistence
    retrieved = await state_manager.get_workflow(state.workflow_id)
    assert retrieved.variables["counter"] == 5
    assert retrieved.variables["mode"] == "production"
    assert retrieved.variables["config"]["timeout"] == 30


@pytest.mark.asyncio
async def test_task_dependencies_persistence(state_manager):
    """Test task dependencies are persisted."""
    tasks = [
        TaskState(task_id="task1", agent_id="agent1", agent_type="type1"),
        TaskState(
            task_id="task2",
            agent_id="agent2",
            agent_type="type2",
            dependencies=["task1"],
        ),
        TaskState(
            task_id="task3",
            agent_id="agent3",
            agent_type="type3",
            dependencies=["task1", "task2"],
        ),
    ]

    state = await state_manager.create_workflow(tasks=tasks)

    # Verify dependencies persisted
    retrieved = await state_manager.get_workflow(state.workflow_id)
    assert retrieved.tasks["task2"].dependencies == ["task1"]
    assert set(retrieved.tasks["task3"].dependencies) == {"task1", "task2"}


@pytest.mark.asyncio
async def test_task_error_persistence(state_manager):
    """Test task error information is persisted."""
    tasks = [TaskState(task_id="task1", agent_id="agent1", agent_type="type1")]
    state = await state_manager.create_workflow(tasks=tasks)

    # Update task with error
    error_info = {
        "error_type": "ValueError",
        "message": "Invalid input",
        "traceback": "...",
    }

    await state_manager.update_task(
        state.workflow_id,
        "task1",
        status=TaskStatus.FAILED,
        error=error_info,
    )

    # Verify error persisted
    retrieved = await state_manager.get_workflow(state.workflow_id)
    task = retrieved.tasks["task1"]
    assert task.status == TaskStatus.FAILED
    assert task.error["error_type"] == "ValueError"
    assert task.error["message"] == "Invalid input"


@pytest.mark.asyncio
async def test_concurrent_workflow_updates(state_manager):
    """Test concurrent updates to different workflows."""
    import asyncio

    # Create workflows
    wf1 = await state_manager.create_workflow()
    wf2 = await state_manager.create_workflow()

    # Update concurrently
    async def update_workflow(workflow_id, status):
        state = await state_manager.get_workflow(workflow_id)
        state.status = status
        await state_manager.update_workflow(state)

    await asyncio.gather(
        update_workflow(wf1.workflow_id, WorkflowStatus.RUNNING),
        update_workflow(wf2.workflow_id, WorkflowStatus.COMPLETED),
    )

    # Verify both updated correctly
    final1 = await state_manager.get_workflow(wf1.workflow_id)
    final2 = await state_manager.get_workflow(wf2.workflow_id)

    assert final1.status == WorkflowStatus.RUNNING
    assert final2.status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_task_retry_count(state_manager):
    """Test task retry count persistence."""
    tasks = [TaskState(task_id="task1", agent_id="agent1", agent_type="type1")]
    state = await state_manager.create_workflow(tasks=tasks)

    # Simulate retries
    for retry in range(3):
        state = await state_manager.get_workflow(state.workflow_id)
        state.tasks["task1"].retry_count = retry
        await state_manager.update_workflow(state)

    # Verify final retry count
    final = await state_manager.get_workflow(state.workflow_id)
    assert final.tasks["task1"].retry_count == 2


@pytest.mark.asyncio
async def test_workflow_timestamps(state_manager):
    """Test workflow timestamp tracking."""
    import asyncio

    state = await state_manager.create_workflow()

    assert state.created_at is not None
    assert state.updated_at is not None
    assert state.started_at is None
    assert state.completed_at is None

    # Start workflow
    await asyncio.sleep(0.1)
    state.status = WorkflowStatus.RUNNING
    state.started_at = state.updated_at
    state = await state_manager.update_workflow(state)

    assert state.started_at is not None

    # Complete workflow
    await asyncio.sleep(0.1)
    state.status = WorkflowStatus.COMPLETED
    state.completed_at = state.updated_at
    state = await state_manager.update_workflow(state)

    assert state.completed_at is not None
    assert state.completed_at > state.started_at


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
