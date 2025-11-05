"""Integration tests for coordination tracking functionality."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

from coordination.state_manager import TaskStatus, WorkflowStatus
from coordination.tracker import (
    CoordinationTracker,
    EventType,
)


class TestCoordinationTrackerIntegration:
    """Integration tests for the coordination tracker."""

    @pytest.fixture
    async def tracker(self) -> CoordinationTracker:
        """Create a tracker instance for testing."""
        # Create tracker without database (will use in-memory)
        tracker = CoordinationTracker()
        await tracker.initialize()
        yield tracker
        await tracker.close()

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self, tracker: CoordinationTracker) -> None:
        """Test complete workflow from start to finish."""
        # Start workflow
        workflow = await tracker.start_workflow(
            workflow_id="test-workflow-001",
            workflow_type="deployment",
            metadata={"environment": "staging", "version": "1.0.0"},
        )
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.workflow_type == "deployment"

        # Register agents
        await tracker.register_agent(
            agent_id="agent-001",
            agent_type="backend-developer",
            capabilities=["python", "fastapi", "postgresql"],
        )
        await tracker.register_agent(
            agent_id="agent-002",
            agent_type="frontend-developer",
            capabilities=["typescript", "react", "tailwind"],
        )

        # Create tasks
        backend_task = await tracker.create_task(
            task_id="task-backend-001",
            workflow_id="test-workflow-001",
            task_type="api_development",
            dependencies=[],
            assigned_agent="agent-001",
        )
        assert backend_task.status == TaskStatus.PENDING

        await tracker.create_task(
            task_id="task-frontend-001",
            workflow_id="test-workflow-001",
            task_type="ui_development",
            dependencies=["task-backend-001"],  # Depends on backend
            assigned_agent="agent-002",
        )

        # Execute backend task
        await tracker.update_task_status(task_id="task-backend-001", status=TaskStatus.IN_PROGRESS)
        await tracker.update_task_status(
            task_id="task-backend-001",
            status=TaskStatus.COMPLETED,
            result={"endpoints": 5, "tests": 12},
        )

        # Execute frontend task
        await tracker.update_task_status(task_id="task-frontend-001", status=TaskStatus.IN_PROGRESS)
        await tracker.update_task_status(
            task_id="task-frontend-001",
            status=TaskStatus.COMPLETED,
            result={"components": 8, "tests": 20},
        )

        # Complete workflow
        await tracker.complete_workflow(workflow_id="test-workflow-001")

        # Verify final states
        final_workflow = await tracker.get_workflow("test-workflow-001")
        assert final_workflow.status == WorkflowStatus.COMPLETED

        backend = await tracker.get_task("task-backend-001")
        assert backend.status == TaskStatus.COMPLETED
        assert backend.result["endpoints"] == 5

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, tracker: CoordinationTracker) -> None:
        """Test error scenarios and recovery mechanisms."""
        await tracker.start_workflow(workflow_id="error-workflow", workflow_type="test_errors")

        # Create task that will fail
        await tracker.create_task(
            task_id="failing-task",
            workflow_id="error-workflow",
            task_type="risky_operation",
        )

        # Start and fail task
        await tracker.update_task_status(task_id="failing-task", status=TaskStatus.IN_PROGRESS)
        await tracker.update_task_status(
            task_id="failing-task",
            status=TaskStatus.FAILED,
            error={"message": "Connection timeout", "code": "TIMEOUT_ERROR"},
        )

        # Verify task failed
        failed_task = await tracker.get_task("failing-task")
        assert failed_task.status == TaskStatus.FAILED
        assert failed_task.error["code"] == "TIMEOUT_ERROR"

        # Retry task
        await tracker.update_task_status(task_id="failing-task", status=TaskStatus.IN_PROGRESS)
        await tracker.update_task_status(task_id="failing-task", status=TaskStatus.COMPLETED)

        # Verify recovery
        recovered_task = await tracker.get_task("failing-task")
        assert recovered_task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_agent_communication_flow(self, tracker: CoordinationTracker) -> None:
        """Test inter-agent communication and messaging."""
        # Register communicating agents
        await tracker.register_agent(agent_id="sender", agent_type="producer")
        await tracker.register_agent(agent_id="receiver", agent_type="consumer")

        # Start communication workflow
        await tracker.start_workflow(workflow_id="comm-workflow", workflow_type="communication_test")

        # Log communication events
        await tracker.log_event(
            event_type=EventType.MESSAGE_SENT,
            workflow_id="comm-workflow",
            agent_id="sender",
            details={"to": "receiver", "message_type": "data_request"},
        )

        await tracker.log_event(
            event_type=EventType.MESSAGE_RECEIVED,
            workflow_id="comm-workflow",
            agent_id="receiver",
            details={"from": "sender", "message_type": "data_request"},
        )

        await tracker.log_event(
            event_type=EventType.MESSAGE_SENT,
            workflow_id="comm-workflow",
            agent_id="receiver",
            details={"to": "sender", "message_type": "data_response", "payload_size": 1024},
        )

        # Verify communication flow
        events = await tracker.get_workflow_events("comm-workflow")
        message_events = [e for e in events if "MESSAGE" in e.event_type.name]
        assert len(message_events) >= 3

    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, tracker: CoordinationTracker) -> None:
        """Test parallel task execution and synchronization."""
        await tracker.start_workflow(workflow_id="parallel-workflow", workflow_type="parallel_test")

        # Create parallel tasks
        parallel_tasks = []
        for i in range(5):
            task = await tracker.create_task(
                task_id=f"parallel-task-{i}",
                workflow_id="parallel-workflow",
                task_type="parallel_work",
                dependencies=[],  # No dependencies = can run in parallel
            )
            parallel_tasks.append(task)

        # Start all tasks simultaneously
        for task in parallel_tasks:
            await tracker.update_task_status(task_id=task.task_id, status=TaskStatus.IN_PROGRESS)

        # Complete tasks in random order
        for i in [2, 0, 4, 1, 3]:
            await tracker.update_task_status(
                task_id=f"parallel-task-{i}",
                status=TaskStatus.COMPLETED,
                result={"processed": i * 100},
            )

        # Verify all completed
        for i in range(5):
            task = await tracker.get_task(f"parallel-task-{i}")
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, tracker: CoordinationTracker) -> None:
        """Test valid workflow state transitions."""
        # Start workflow
        workflow = await tracker.start_workflow(
            workflow_id="state-workflow",
            workflow_type="state_test",
        )
        assert workflow.status == WorkflowStatus.RUNNING

        # Pause workflow
        await tracker.pause_workflow(workflow_id="state-workflow")
        paused = await tracker.get_workflow("state-workflow")
        assert paused.status == WorkflowStatus.PAUSED

        # Resume workflow
        await tracker.resume_workflow(workflow_id="state-workflow")
        resumed = await tracker.get_workflow("state-workflow")
        assert resumed.status == WorkflowStatus.RUNNING

        # Complete workflow
        await tracker.complete_workflow(workflow_id="state-workflow")
        completed = await tracker.get_workflow("state-workflow")
        assert completed.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_metrics_collection(self, tracker: CoordinationTracker) -> None:
        """Test metrics collection and aggregation."""
        # Generate activity
        for i in range(5):
            await tracker.start_workflow(
                workflow_id=f"metrics-workflow-{i}",
                workflow_type="metrics_test",
            )
            await tracker.create_task(
                task_id=f"metrics-task-{i}",
                workflow_id=f"metrics-workflow-{i}",
                task_type="computation",
            )
            if i % 2 == 0:
                await tracker.update_task_status(task_id=f"metrics-task-{i}", status=TaskStatus.COMPLETED)

        # Collect metrics
        metrics = await tracker.get_metrics()
        assert metrics.active_workflows >= 5
        assert metrics.total_tasks >= 5
        assert metrics.completed_tasks >= 2

    @pytest.mark.asyncio
    async def test_workflow_dependencies(self, tracker: CoordinationTracker) -> None:
        """Test task dependency management."""
        await tracker.start_workflow(workflow_id="dep-workflow", workflow_type="dependency_test")

        # Create task chain: A -> B -> C
        #                          \-> D
        tasks = {}
        tasks["A"] = await tracker.create_task(
            task_id="task-A",
            workflow_id="dep-workflow",
            task_type="initial",
            dependencies=[],
        )
        tasks["B"] = await tracker.create_task(
            task_id="task-B",
            workflow_id="dep-workflow",
            task_type="middle",
            dependencies=["task-A"],
        )
        tasks["C"] = await tracker.create_task(
            task_id="task-C",
            workflow_id="dep-workflow",
            task_type="final",
            dependencies=["task-B"],
        )
        tasks["D"] = await tracker.create_task(
            task_id="task-D",
            workflow_id="dep-workflow",
            task_type="parallel",
            dependencies=["task-B"],
        )

        # Verify dependencies
        task_b = await tracker.get_task("task-B")
        assert "task-A" in task_b.dependencies

        task_c = await tracker.get_task("task-C")
        assert "task-B" in task_c.dependencies

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, tracker: CoordinationTracker) -> None:
        """Test tracker under concurrent load."""
        workflow_count = 10
        tasks_per_workflow = 5

        async def create_workflow_with_tasks(index: int) -> None:
            """Create a workflow with multiple tasks."""
            workflow_id = f"concurrent-workflow-{index}"
            await tracker.start_workflow(workflow_id=workflow_id, workflow_type="concurrent_test")

            for task_idx in range(tasks_per_workflow):
                await tracker.create_task(
                    task_id=f"task-{index}-{task_idx}",
                    workflow_id=workflow_id,
                    task_type="parallel_work",
                )

        # Create workflows concurrently
        tasks = [create_workflow_with_tasks(i) for i in range(workflow_count)]
        await asyncio.gather(*tasks)

        # Verify all workflows and tasks were created
        metrics = await tracker.get_metrics()
        assert metrics.active_workflows >= workflow_count
        assert metrics.total_tasks >= workflow_count * tasks_per_workflow

    @pytest.mark.asyncio
    async def test_workflow_filtering_and_search(self, tracker: CoordinationTracker) -> None:
        """Test workflow filtering capabilities."""
        # Create workflows of different types
        await tracker.start_workflow(
            workflow_id="deploy-1",
            workflow_type="deployment",
            metadata={"env": "prod"},
        )
        await tracker.start_workflow(
            workflow_id="test-1",
            workflow_type="testing",
            metadata={"env": "staging"},
        )
        await tracker.start_workflow(
            workflow_id="deploy-2",
            workflow_type="deployment",
            metadata={"env": "staging"},
        )

        # Filter by type
        deployments = await tracker.list_workflows(workflow_type="deployment")
        assert len(deployments) >= 2
        assert all(w.workflow_type == "deployment" for w in deployments)

        # Filter by status
        active = await tracker.list_workflows(status=WorkflowStatus.RUNNING)
        assert all(w.status == WorkflowStatus.RUNNING for w in active)

    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self, tracker: CoordinationTracker) -> None:
        """Test agent performance metrics."""
        await tracker.register_agent(
            agent_id="perf-agent",
            agent_type="worker",
            capabilities=["fast_processing"],
        )

        # Agent completes multiple tasks
        for i in range(10):
            task_id = f"perf-task-{i}"
            await tracker.create_task(
                task_id=task_id,
                workflow_id=f"perf-workflow-{i}",
                task_type="computation",
                assigned_agent="perf-agent",
            )

            await tracker.update_task_status(task_id=task_id, status=TaskStatus.IN_PROGRESS)

            # Simulate processing time
            await asyncio.sleep(0.01)

            await tracker.update_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result={"performance": "excellent"},
            )

        # Get agent statistics
        stats = await tracker.get_agent_stats("perf-agent")
        assert stats["tasks_completed"] == 10
        assert stats["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, tracker: CoordinationTracker) -> None:
        """Test workflow timeout detection."""
        # Start workflow with timeout
        await tracker.start_workflow(
            workflow_id="timeout-workflow",
            workflow_type="timeout_test",
            metadata={"timeout_seconds": 1},
        )

        # Create long-running task
        await tracker.create_task(
            task_id="timeout-task",
            workflow_id="timeout-workflow",
            task_type="long_operation",
        )

        await tracker.update_task_status(task_id="timeout-task", status=TaskStatus.IN_PROGRESS)

        # Simulate timeout detection
        await asyncio.sleep(1.1)

        # Mark workflow as timed out
        await tracker.fail_workflow(
            workflow_id="timeout-workflow",
            error={"reason": "timeout", "duration": 1.1},
        )

        # Verify workflow failed
        updated_workflow = await tracker.get_workflow("timeout-workflow")
        assert updated_workflow.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_event_replay_capability(self, tracker: CoordinationTracker) -> None:
        """Test ability to replay workflow events."""
        await tracker.start_workflow(workflow_id="replay-workflow", workflow_type="replay_test")

        # Generate sequence of events
        events_sequence = [
            (EventType.WORKFLOW_STARTED, {"phase": "initialization"}),
            (EventType.AGENT_REGISTERED, {"agent": "worker-1"}),
            (EventType.TASK_CREATED, {"task": "data_processing"}),
            (EventType.TASK_STARTED, {"timestamp": "2024-01-01T00:00:00"}),
            (EventType.TASK_COMPLETED, {"result": "success"}),
            (EventType.WORKFLOW_COMPLETED, {"duration": 60}),
        ]

        for event_type, details in events_sequence:
            await tracker.log_event(
                event_type=event_type,
                workflow_id="replay-workflow",
                details=details,
            )

        # Replay events
        events = await tracker.get_workflow_events("replay-workflow")
        assert len(events) == len(events_sequence)

        # Verify event order
        for i, (expected_type, _) in enumerate(events_sequence):
            assert events[i].event_type == expected_type


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database-specific integration scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("TEST_DATABASE_URL") is None,
        reason="No test database configured",
    )
    async def test_postgresql_integration(self) -> None:
        """Test integration with PostgreSQL."""
        db_url = os.getenv("TEST_DATABASE_URL")
        tracker = CoordinationTracker(db_url=db_url)

        try:
            await tracker.initialize()

            # Test basic operations
            workflow = await tracker.start_workflow(
                workflow_id="pg-test-workflow",
                workflow_type="postgresql_test",
            )
            assert workflow.workflow_id == "pg-test-workflow"

        finally:
            await tracker.close()

    @pytest.mark.asyncio
    async def test_database_migration(self, tmp_path: Path) -> None:
        """Test database schema migration."""
        # Use PostgreSQL connection string (CoordinationTracker uses PostgreSQL, not SQLite)
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mycelium_test")
        tracker = CoordinationTracker(db_url=db_url)

        await tracker.initialize()
        # Verify schema version
        schema_version = await tracker.get_schema_version()
        assert schema_version >= 1

        await tracker.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
