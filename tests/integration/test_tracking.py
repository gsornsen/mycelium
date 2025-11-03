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
            capabilities=["react", "typescript", "css"],
        )

        # Create tasks
        await tracker.create_task(
            task_id="task-001",
            workflow_id="test-workflow-001",
            task_type="api_development",
            assigned_agent="agent-001",
            dependencies=[],
        )
        await tracker.create_task(
            task_id="task-002",
            workflow_id="test-workflow-001",
            task_type="ui_development",
            assigned_agent="agent-002",
            dependencies=["task-001"],
        )

        # Start first task
        await tracker.update_task_status(task_id="task-001", status=TaskStatus.IN_PROGRESS)

        # Log some events
        await tracker.log_event(
            event_type=EventType.TASK_STARTED,
            agent_id="agent-001",
            task_id="task-001",
            workflow_id="test-workflow-001",
            details={"message": "Starting API development"},
        )

        # Complete first task
        await tracker.update_task_status(
            task_id="task-001",
            status=TaskStatus.COMPLETED,
            result={"endpoints_created": 5, "tests_passed": 10},
        )

        # Start second task
        await tracker.update_task_status(task_id="task-002", status=TaskStatus.IN_PROGRESS)

        # Complete second task
        await tracker.update_task_status(
            task_id="task-002",
            status=TaskStatus.COMPLETED,
            result={"components_created": 3, "pages_built": 2},
        )

        # Complete workflow
        completed_workflow = await tracker.complete_workflow(
            workflow_id="test-workflow-001",
            result={"deployment_url": "https://staging.example.com"},
        )
        assert completed_workflow.status == WorkflowStatus.COMPLETED

        # Verify workflow history
        events = await tracker.get_workflow_events("test-workflow-001")
        assert len(events) > 0
        assert any(e.event_type == EventType.TASK_STARTED for e in events)

    @pytest.mark.asyncio
    async def test_agent_collaboration(self, tracker: CoordinationTracker) -> None:
        """Test multi-agent collaboration tracking."""
        # Register multiple agents
        agents = []
        for i in range(3):
            agent = await tracker.register_agent(
                agent_id=f"agent-{i:03d}",
                agent_type=f"type-{i}",
                capabilities=[f"skill-{i}"],
            )
            agents.append(agent)

        # Create workflow
        await tracker.start_workflow(
            workflow_id="collab-workflow",
            workflow_type="collaborative_task",
            metadata={"team_size": 3},
        )

        # Agents communicate
        for i in range(len(agents)):
            for j in range(len(agents)):
                if i != j:
                    await tracker.log_event(
                        event_type=EventType.AGENT_COMMUNICATION,
                        agent_id=agents[i].agent_id,
                        workflow_id="collab-workflow",
                        details={
                            "to_agent": agents[j].agent_id,
                            "message_type": "coordination",
                        },
                    )

        # Check communication patterns
        events = await tracker.get_workflow_events("collab-workflow")
        comm_events = [e for e in events if e.event_type == EventType.AGENT_COMMUNICATION]
        assert len(comm_events) == 6  # 3 agents, 2 messages each

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, tracker: CoordinationTracker) -> None:
        """Test error tracking and recovery mechanisms."""
        # Start workflow
        await tracker.start_workflow(workflow_id="error-workflow", workflow_type="error_test")

        # Register agent
        await tracker.register_agent(agent_id="error-agent", agent_type="worker")

        # Create task
        await tracker.create_task(
            task_id="error-task",
            workflow_id="error-workflow",
            task_type="risky_operation",
            assigned_agent="error-agent",
        )

        # Task encounters error
        error = await tracker.log_error(
            error_type="RuntimeError",
            message="Database connection failed",
            agent_id="error-agent",
            task_id="error-task",
            workflow_id="error-workflow",
            stack_trace="Traceback...",
            context={"retry_count": 0},
        )
        assert error.error_type == "RuntimeError"
        assert error.resolved is False

        # Retry task
        await tracker.log_event(
            event_type=EventType.TASK_RETRIED,
            agent_id="error-agent",
            task_id="error-task",
            workflow_id="error-workflow",
            details={"retry_attempt": 1},
        )

        # Task succeeds on retry
        await tracker.update_task_status(task_id="error-task", status=TaskStatus.COMPLETED)

        # Mark error as resolved
        await tracker.resolve_error(error.error_id)

        # Verify error was resolved
        errors = await tracker.get_workflow_errors("error-workflow")
        assert len(errors) == 1
        assert errors[0].resolved is True

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
            workflow_id="deploy-2",
            workflow_type="deployment",
            metadata={"env": "staging"},
        )
        await tracker.start_workflow(
            workflow_id="test-1",
            workflow_type="testing",
            metadata={"suite": "unit"},
        )

        # Get workflows by type
        deployments = await tracker.get_workflows_by_type("deployment")
        assert len(deployments) == 2

        tests = await tracker.get_workflows_by_type("testing")
        assert len(tests) == 1

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
        db_path = tmp_path / "test.db"
        tracker = CoordinationTracker(db_path=str(db_path))

        await tracker.initialize()
        # Verify schema version
        schema_version = await tracker.get_schema_version()
        assert schema_version >= 1

        await tracker.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
