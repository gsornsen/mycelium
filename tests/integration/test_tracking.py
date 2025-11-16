"""Integration tests for coordination tracking functionality.

NOTE: These tests are currently skipped because coordination.state_manager module
(including WorkflowStatus) has not been implemented yet.
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

# Skip entire module - coordination.state_manager not yet implemented
pytestmark = pytest.mark.skip(reason="coordination.state_manager module (WorkflowStatus) not yet implemented")

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

# Conditional imports - avoid import errors when module is skipped
try:
    from coordination.state_manager import WorkflowStatus
    from coordination.tracker import (
        CoordinationEvent,
        CoordinationTracker,
        EventType,
        PerformanceMetrics,
        track_failure,
        track_handoff,
        track_task_execution,
        track_workflow_completion,
    )
except ImportError:
    # Module not yet implemented - define stubs for type hints
    from enum import Enum

    class WorkflowStatus(str, Enum):
        """Stub for WorkflowStatus."""

        PENDING = "pending"

    CoordinationEvent = None  # type: ignore
    CoordinationTracker = None  # type: ignore
    EventType = None  # type: ignore
    PerformanceMetrics = None  # type: ignore
    track_failure = None  # type: ignore
    track_handoff = None  # type: ignore
    track_task_execution = None  # type: ignore
    track_workflow_completion = None  # type: ignore


@dataclass
class SimpleWorkflowState:
    """Simplified workflow state for testing."""

    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TrackerTestHelper:
    """Helper class to provide workflow management on top of tracker."""

    def __init__(self, tracker: CoordinationTracker):
        self.tracker = tracker
        self._workflows: dict[str, SimpleWorkflowState] = {}
        self._agents: dict[str, dict[str, Any]] = {}

    async def start_workflow(
        self, workflow_id: str, workflow_type: str, metadata: dict[str, Any] | None = None
    ) -> SimpleWorkflowState:
        """Start a workflow by tracking a WORKFLOW_STARTED event."""
        event = CoordinationEvent(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            status="running",
            metadata={"workflow_type": workflow_type, **(metadata or {})},
        )
        await self.tracker.track_event(event)

        workflow = SimpleWorkflowState(
            workflow_id=workflow_id, workflow_type=workflow_type, status=WorkflowStatus.RUNNING, metadata=metadata or {}
        )
        self._workflows[workflow_id] = workflow
        return workflow

    async def register_agent(self, agent_id: str, agent_type: str, capabilities: list[str] | None = None) -> None:
        """Register an agent (store in memory for test purposes)."""
        self._agents[agent_id] = {"agent_id": agent_id, "agent_type": agent_type, "capabilities": capabilities or []}

    async def assign_task(self, workflow_id: str, task_id: str, agent_id: str, agent_type: str | None = None) -> None:
        """Assign a task to an agent."""
        if not agent_type and agent_id in self._agents:
            agent_type = self._agents[agent_id]["agent_type"]

        event = CoordinationEvent(
            event_type=EventType.EXECUTION_START,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            agent_type=agent_type or "unknown",
            status="assigned",
        )
        await self.tracker.track_event(event)

    async def complete_task(
        self, workflow_id: str, task_id: str, agent_id: str, agent_type: str | None = None, result: str | None = None
    ) -> None:
        """Complete a task."""
        if not agent_type and agent_id in self._agents:
            agent_type = self._agents[agent_id]["agent_type"]

        await track_task_execution(
            self.tracker,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            agent_type=agent_type or "unknown",
            status="completed",
            result_summary=result,
        )

    async def handoff_task(
        self, workflow_id: str, task_id: str, from_agent: str, to_agent: str, context: dict[str, Any] | None = None
    ) -> None:
        """Hand off a task between agents."""
        from_type = self._agents.get(from_agent, {}).get("agent_type", "unknown")
        to_type = self._agents.get(to_agent, {}).get("agent_type", "unknown")

        await track_handoff(
            self.tracker,
            workflow_id=workflow_id,
            source_agent_id=from_agent,
            source_agent_type=from_type,
            target_agent_id=to_agent,
            target_agent_type=to_type,
            task_id=task_id,
            context=context,
        )

    async def pause_workflow(self, workflow_id: str) -> SimpleWorkflowState | None:
        """Pause a workflow."""
        event = CoordinationEvent(event_type=EventType.WORKFLOW_PAUSED, workflow_id=workflow_id, status="paused")
        await self.tracker.track_event(event)

        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowStatus.PAUSED
        return self._workflows.get(workflow_id)

    async def resume_workflow(self, workflow_id: str) -> SimpleWorkflowState | None:
        """Resume a workflow."""
        event = CoordinationEvent(event_type=EventType.WORKFLOW_RESUMED, workflow_id=workflow_id, status="running")
        await self.tracker.track_event(event)

        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowStatus.RUNNING
        return self._workflows.get(workflow_id)

    async def complete_workflow(self, workflow_id: str) -> SimpleWorkflowState | None:
        """Complete a workflow."""
        event = CoordinationEvent(event_type=EventType.WORKFLOW_COMPLETED, workflow_id=workflow_id, status="completed")
        await self.tracker.track_event(event)

        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = WorkflowStatus.COMPLETED
        return self._workflows.get(workflow_id)

    async def fail_task(self, workflow_id: str, task_id: str, agent_id: str, error: str, retry: bool = False) -> None:
        """Mark a task as failed."""
        agent_type = self._agents.get(agent_id, {}).get("agent_type", "unknown")

        await track_failure(
            self.tracker,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            agent_type=agent_type,
            error_type="TaskError",
            error_message=error,
            attempt=1,
            will_retry=retry,
        )

    async def update_workflow_status(self, workflow_id: str, status: WorkflowStatus) -> SimpleWorkflowState | None:
        """Update workflow status."""
        event_type_map = {
            WorkflowStatus.FAILED: EventType.WORKFLOW_FAILED,
            WorkflowStatus.CANCELLED: EventType.WORKFLOW_CANCELLED,
            WorkflowStatus.COMPLETED: EventType.WORKFLOW_COMPLETED,
            WorkflowStatus.PAUSED: EventType.WORKFLOW_PAUSED,
            WorkflowStatus.RUNNING: EventType.WORKFLOW_RESUMED,
        }

        event_type = event_type_map.get(status, EventType.STATUS_UPDATE)
        event = CoordinationEvent(event_type=event_type, workflow_id=workflow_id, status=status.value)
        await self.tracker.track_event(event)

        if workflow_id in self._workflows:
            self._workflows[workflow_id].status = status
        return self._workflows.get(workflow_id)

    async def list_workflows(self, status: WorkflowStatus | None = None) -> list[SimpleWorkflowState]:
        """List workflows by status."""
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows


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

    @pytest.fixture
    async def helper(self, tracker: CoordinationTracker) -> TrackerTestHelper:
        """Create a test helper with the tracker."""
        return TrackerTestHelper(tracker)

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test complete workflow from start to finish."""
        # Start workflow
        workflow = await helper.start_workflow(
            workflow_id="test-workflow-001",
            workflow_type="deployment",
            metadata={"environment": "staging", "version": "1.0.0"},
        )
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.workflow_type == "deployment"

        # Register agents
        await helper.register_agent(
            agent_id="agent-001",
            agent_type="backend-developer",
            capabilities=["python", "fastapi", "postgresql"],
        )
        await helper.register_agent(
            agent_id="agent-002",
            agent_type="frontend-developer",
            capabilities=["react", "typescript", "tailwind"],
        )

        # Task assignments and executions
        await helper.assign_task(
            workflow_id="test-workflow-001",
            task_id="setup-backend",
            agent_id="agent-001",
        )

        await helper.complete_task(
            workflow_id="test-workflow-001",
            task_id="setup-backend",
            agent_id="agent-001",
            result="Backend API deployed at https://api.staging.example.com",
        )

        # Handoff to frontend developer
        await helper.handoff_task(
            workflow_id="test-workflow-001",
            task_id="integrate-frontend",
            from_agent="agent-001",
            to_agent="agent-002",
            context={"api_url": "https://api.staging.example.com", "api_key": "test-key-123"},
        )

        await helper.assign_task(
            workflow_id="test-workflow-001",
            task_id="integrate-frontend",
            agent_id="agent-002",
        )

        await helper.complete_task(
            workflow_id="test-workflow-001",
            task_id="integrate-frontend",
            agent_id="agent-002",
            result="Frontend deployed at https://staging.example.com",
        )

        # Complete workflow
        final_workflow = await helper.complete_workflow("test-workflow-001")
        assert final_workflow.status == WorkflowStatus.COMPLETED

        # Verify events were tracked
        events = await tracker.get_workflow_events("test-workflow-001")
        assert len(events) > 0

        # Check timeline
        timeline = await tracker.get_workflow_timeline("test-workflow-001")
        assert timeline["total_events"] > 0
        assert timeline["handoff_count"] == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test error tracking and recovery."""
        await helper.start_workflow(workflow_id="error-workflow", workflow_type="test_errors")

        await helper.register_agent(agent_id="error-agent", agent_type="test-agent")

        # Simulate task failure
        await helper.assign_task(
            workflow_id="error-workflow",
            task_id="failing-task",
            agent_id="error-agent",
        )

        await helper.fail_task(
            workflow_id="error-workflow",
            task_id="failing-task",
            agent_id="error-agent",
            error="Connection timeout to external service",
            retry=True,
        )

        # Retry the task
        await helper.assign_task(
            workflow_id="error-workflow",
            task_id="failing-task",
            agent_id="error-agent",
        )

        await helper.complete_task(
            workflow_id="error-workflow",
            task_id="failing-task",
            agent_id="error-agent",
            result="Successfully completed after retry",
        )

        # Check events
        events = await tracker.get_workflow_events("error-workflow")
        failure_events = [e for e in events if e.event_type == EventType.FAILURE]
        assert len(failure_events) == 1

        stats = await tracker.get_statistics(workflow_id="error-workflow")
        assert stats["failure_rate"] > 0

    @pytest.mark.asyncio
    async def test_multi_agent_communication(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test tracking of complex multi-agent interactions."""
        await helper.start_workflow(workflow_id="comm-workflow", workflow_type="communication_test")

        # Register multiple agents
        agents = ["orchestrator", "backend-dev", "frontend-dev", "qa-engineer"]
        for agent in agents:
            await helper.register_agent(agent_id=agent, agent_type=agent.replace("-", "_"))

        # Complex handoff chain
        handoffs = [
            ("orchestrator", "backend-dev", "design-api"),
            ("backend-dev", "frontend-dev", "implement-ui"),
            ("frontend-dev", "qa-engineer", "test-integration"),
            ("qa-engineer", "orchestrator", "report-results"),
        ]

        for from_agent, to_agent, task_id in handoffs:
            await helper.handoff_task(
                workflow_id="comm-workflow",
                task_id=task_id,
                from_agent=from_agent,
                to_agent=to_agent,
            )

        # Get handoff chain
        chain = await tracker.get_handoff_chain("comm-workflow")
        assert len(chain) == 4

    @pytest.mark.asyncio
    async def test_parallel_execution(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test tracking of parallel task execution."""
        await helper.start_workflow(workflow_id="parallel-workflow", workflow_type="parallel_test")

        # Register agents
        agents = ["agent-1", "agent-2", "agent-3"]
        for agent in agents:
            await helper.register_agent(agent_id=agent, agent_type="worker")

        # Start parallel tasks
        tasks = []
        for i, agent in enumerate(agents):
            task_id = f"parallel-task-{i + 1}"
            await helper.assign_task(
                workflow_id="parallel-workflow",
                task_id=task_id,
                agent_id=agent,
            )
            tasks.append((agent, task_id))

        # Complete tasks in different order
        for agent, task_id in reversed(tasks):
            await helper.complete_task(
                workflow_id="parallel-workflow",
                task_id=task_id,
                agent_id=agent,
            )

        # Check timeline
        timeline = await tracker.get_workflow_timeline("parallel-workflow")
        assert timeline["unique_agents"] == 3
        assert timeline["unique_tasks"] == 3

    @pytest.mark.asyncio
    async def test_workflow_pause_resume(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test workflow pause and resume functionality."""
        workflow = await helper.start_workflow(
            workflow_id="pausable-workflow",
            workflow_type="pause_test",
        )
        assert workflow.status == WorkflowStatus.RUNNING

        # Pause workflow
        paused = await helper.pause_workflow("pausable-workflow")
        assert paused.status == WorkflowStatus.PAUSED

        # Resume workflow
        resumed = await helper.resume_workflow("pausable-workflow")
        assert resumed.status == WorkflowStatus.RUNNING

        # Complete workflow
        completed = await helper.complete_workflow("pausable-workflow")
        assert completed.status == WorkflowStatus.COMPLETED

        # Check events
        events = await tracker.get_workflow_events("pausable-workflow")
        event_types = [e.event_type for e in events]
        assert EventType.WORKFLOW_PAUSED in event_types
        assert EventType.WORKFLOW_RESUMED in event_types

    @pytest.mark.asyncio
    async def test_task_dependencies(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test tracking of task dependencies."""
        await helper.start_workflow(workflow_id="dep-workflow", workflow_type="dependency_test")
        await helper.register_agent(agent_id="worker", agent_type="worker")

        # Execute tasks with dependencies
        tasks = [
            ("task-1", None),
            ("task-2", ["task-1"]),
            ("task-3", ["task-1"]),
            ("task-4", ["task-2", "task-3"]),
        ]

        for task_id, deps in tasks:
            metadata = {"dependencies": deps} if deps else {}

            # Track task with dependencies in metadata
            event = CoordinationEvent(
                event_type=EventType.EXECUTION_START,
                workflow_id="dep-workflow",
                task_id=task_id,
                agent_id="worker",
                agent_type="worker",
                status="running",
                metadata=metadata,
            )
            await tracker.track_event(event)

            await helper.complete_task(
                workflow_id="dep-workflow",
                task_id=task_id,
                agent_id="worker",
            )

        # Verify all tasks completed
        events = await tracker.get_workflow_events("dep-workflow")
        completed_tasks = set()
        for e in events:
            if e.event_type == EventType.EXECUTION_END and e.status == "completed":
                completed_tasks.add(e.task_id)
        assert len(completed_tasks) == 4

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test tracking multiple concurrent workflows."""
        workflow_ids = ["concurrent-1", "concurrent-2", "concurrent-3"]

        # Start multiple workflows
        for workflow_id in workflow_ids:
            await helper.start_workflow(workflow_id=workflow_id, workflow_type="concurrent_test")

        # Track events for each workflow
        for workflow_id in workflow_ids:
            event = CoordinationEvent(
                event_type=EventType.EXECUTION_START,
                workflow_id=workflow_id,
                task_id="task-1",
                agent_id="worker",
                agent_type="worker",
                status="running",
            )
            await tracker.track_event(event)

        # Complete workflows in different order
        for workflow_id in reversed(workflow_ids):
            await helper.complete_workflow(workflow_id)

        # Verify each workflow has its own events
        for workflow_id in workflow_ids:
            events = await tracker.get_workflow_events(workflow_id)
            assert len(events) >= 2  # At least start and complete

    @pytest.mark.asyncio
    async def test_statistics_generation(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test statistics calculation."""
        # Create workflows with different statuses
        await helper.start_workflow(
            workflow_id="stats-1",
            workflow_type="stats_test",
        )
        await helper.start_workflow(
            workflow_id="stats-2",
            workflow_type="stats_test",
        )
        await helper.start_workflow(
            workflow_id="stats-3",
            workflow_type="stats_test",
        )

        # Complete one, leave others running
        await helper.complete_workflow("stats-1")

        # Get active workflows
        active = await helper.list_workflows(status=WorkflowStatus.RUNNING)
        assert all(w.status == WorkflowStatus.RUNNING for w in active)
        assert len(active) >= 2  # stats-2 and stats-3

        # Global statistics
        stats = await tracker.get_statistics()
        assert stats["total_events"] > 0
        assert stats["unique_workflows"] >= 3

    @pytest.mark.asyncio
    async def test_event_filtering(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test event filtering capabilities."""
        await helper.start_workflow(
            workflow_id="filter-workflow",
            workflow_type="filter_test",
        )
        await helper.register_agent(agent_id="agent-1", agent_type="type-a")
        await helper.register_agent(agent_id="agent-2", agent_type="type-b")

        # Create various events
        await helper.assign_task(
            workflow_id="filter-workflow",
            task_id="task-1",
            agent_id="agent-1",
        )
        await helper.complete_task(
            workflow_id="filter-workflow",
            task_id="task-1",
            agent_id="agent-1",
        )
        await helper.handoff_task(
            workflow_id="filter-workflow",
            task_id="task-2",
            from_agent="agent-1",
            to_agent="agent-2",
        )

        # Filter by event type
        events = await tracker.get_workflow_events(
            "filter-workflow",
            event_type=EventType.HANDOFF,
        )
        assert all(e.event_type == EventType.HANDOFF for e in events)

        # Filter by agent
        agent_events = await tracker.get_agent_events("agent-1")
        assert all(
            e.agent_id == "agent-1"
            or (hasattr(e, "source_agent") and e.source_agent and e.source_agent.agent_id == "agent-1")
            for e in agent_events
        )

    @pytest.mark.asyncio
    async def test_workflow_recovery(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test workflow recovery after failure."""
        await helper.start_workflow(workflow_id="recovery-workflow", workflow_type="recovery_test")
        await helper.register_agent(agent_id="recovery-agent", agent_type="worker")

        # Simulate workflow failure
        await helper.update_workflow_status(
            "recovery-workflow",
            WorkflowStatus.FAILED,
        )

        # Check workflow status
        updated_workflow = helper._workflows.get("recovery-workflow")
        assert updated_workflow.status == WorkflowStatus.FAILED

        # Attempt recovery by restarting
        await helper.start_workflow(
            workflow_id="recovery-workflow-retry",
            workflow_type="recovery_test",
            metadata={"retry_of": "recovery-workflow"},
        )

        # Complete the retry
        await helper.complete_workflow("recovery-workflow-retry")

        # Verify both workflows exist
        events_original = await tracker.get_workflow_events("recovery-workflow")
        events_retry = await tracker.get_workflow_events("recovery-workflow-retry")
        assert len(events_original) > 0
        assert len(events_retry) > 0

    @pytest.mark.asyncio
    async def test_event_replay(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test event replay for debugging."""
        await helper.start_workflow(workflow_id="replay-workflow", workflow_type="replay_test")

        # Create a sequence of events
        events_to_create = [
            ("task-1", "agent-1", "started"),
            ("task-1", "agent-1", "completed"),
            ("task-2", "agent-2", "started"),
            ("task-2", "agent-2", "failed"),
        ]

        for task_id, agent_id, status in events_to_create:
            if status == "started":
                event_type = EventType.EXECUTION_START
            elif status == "completed":
                event_type = EventType.EXECUTION_END
            else:
                event_type = EventType.FAILURE

            event = CoordinationEvent(
                event_type=event_type,
                workflow_id="replay-workflow",
                task_id=task_id,
                agent_id=agent_id,
                agent_type="worker",
                status=status,
            )
            await tracker.track_event(event)

        # Get timeline for replay
        timeline = await tracker.get_workflow_timeline("replay-workflow")
        assert timeline["total_events"] == 5  # start_workflow + 4 events

        # Verify event order
        events = await tracker.get_workflow_events("replay-workflow")
        # Events should be in chronological order
        assert all(events[i].timestamp <= events[i + 1].timestamp for i in range(len(events) - 1))

    @pytest.mark.asyncio
    async def test_performance_metrics(self, tracker: CoordinationTracker, helper: TrackerTestHelper) -> None:
        """Test performance metrics tracking."""
        await helper.start_workflow(
            workflow_id="perf-workflow",
            workflow_type="performance_test",
        )

        # Track event with performance metrics
        perf = PerformanceMetrics(
            cpu_usage=45.2,
            memory_mb=512.3,
            io_operations=1523,
            network_bytes=1048576,
        )

        event = CoordinationEvent(
            event_type=EventType.EXECUTION_END,
            workflow_id="perf-workflow",
            task_id="heavy-task",
            agent_id="worker",
            agent_type="compute",
            status="completed",
            duration_ms=2543.7,
            performance=perf,
        )
        await tracker.track_event(event)

        # Verify metrics were tracked
        events = await tracker.get_workflow_events("perf-workflow")
        perf_events = [e for e in events if e.performance is not None]
        assert len(perf_events) > 0
        assert perf_events[0].performance.cpu_usage == 45.2


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_database_migration(self) -> None:
        """Test database schema creation and migration."""
        import asyncpg

        # Skip if no database URL
        db_url = os.environ.get("DATABASE_URL", "postgresql://localhost/test_mycelium")
        if "localhost" not in db_url and "127.0.0.1" not in db_url:
            pytest.skip("Database tests only run on local database")

        try:
            # Create connection pool
            pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)

            # Create tracker with database
            tracker = CoordinationTracker(pool=pool)
            helper = TrackerTestHelper(tracker)

            # Initialize (creates tables if needed)
            await tracker.initialize()

            # Test basic operations
            workflow = await helper.start_workflow(
                workflow_id="test-migration-workflow", workflow_type="migration_test"
            )
            assert workflow is not None

            # Track an event
            event = CoordinationEvent(
                event_type=EventType.EXECUTION_START,
                workflow_id="test-migration-workflow",
                task_id="test-task",
                agent_id="test-agent",
                agent_type="test",
                status="running",
            )
            event_id = await tracker.track_event(event)
            assert event_id is not None

            # Query events
            events = await tracker.get_workflow_events("test-migration-workflow")
            assert len(events) >= 1

            # Clean up
            await tracker.delete_workflow_events("test-migration-workflow")
            await tracker.close()
            await pool.close()

        except asyncpg.PostgresError as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        except Exception as e:
            if "connection" in str(e).lower():
                pytest.skip(f"Database connection failed: {e}")
            raise
