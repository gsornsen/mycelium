"""Integration tests for coordination tracking system.

Tests cover:
- Event tracking and retrieval
- Workflow timeline generation
- Performance impact validation
- Storage efficiency
- Integration with orchestrator
"""

import asyncio

# Import coordination modules
import sys
import time
from pathlib import Path

import asyncpg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

from coordination.tracker import (
    AgentInfo,
    CoordinationEvent,
    CoordinationTracker,
    ErrorInfo,
    EventType,
    PerformanceMetrics,
    track_failure,
    track_handoff,
    track_task_execution,
)

# Test database configuration
TEST_DB_URL = "postgresql://mycelium:mycelium_dev_password@localhost:5432/mycelium_registry"


@pytest.fixture
async def db_pool():
    """Create database connection pool for tests."""
    pool = await asyncpg.create_pool(TEST_DB_URL, min_size=2, max_size=5)
    yield pool
    await pool.close()


@pytest.fixture
async def tracker(db_pool):
    """Create tracker instance for tests."""
    tracker = CoordinationTracker(pool=db_pool)
    await tracker.initialize()

    yield tracker

    # Cleanup: delete test events
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM coordination_events WHERE workflow_id LIKE 'test-%'")

    await tracker.close()


@pytest.fixture
def sample_event():
    """Create sample coordination event."""
    return CoordinationEvent(
        event_type=EventType.HANDOFF,
        workflow_id="test-workflow-001",
        task_id="test-task-001",
        source_agent=AgentInfo("agent-001", "backend-developer"),
        target_agent=AgentInfo("agent-002", "frontend-developer"),
        context={"task_description": "Build REST API"},
        metadata={"priority": "high"},
    )


class TestEventTracking:
    """Test basic event tracking functionality."""

    @pytest.mark.asyncio
    async def test_track_simple_event(self, tracker, sample_event):
        """Test tracking a simple event."""
        event_id = await tracker.track_event(sample_event)

        assert event_id is not None
        assert event_id == sample_event.event_id

        # Verify event was stored
        events = await tracker.get_workflow_events(sample_event.workflow_id)
        assert len(events) == 1
        assert events[0].event_id == event_id
        assert events[0].event_type == EventType.HANDOFF

    @pytest.mark.asyncio
    async def test_track_multiple_events(self, tracker):
        """Test tracking multiple events for same workflow."""
        workflow_id = "test-workflow-002"

        # Track workflow lifecycle
        events_to_track = [
            CoordinationEvent(EventType.WORKFLOW_CREATED, workflow_id),
            CoordinationEvent(EventType.WORKFLOW_STARTED, workflow_id),
            CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id="task-1"),
            CoordinationEvent(EventType.TASK_COMPLETED, workflow_id, task_id="task-1"),
            CoordinationEvent(EventType.WORKFLOW_COMPLETED, workflow_id),
        ]

        for event in events_to_track:
            await tracker.track_event(event)

        # Verify all events stored
        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_event_with_error(self, tracker):
        """Test tracking failure event with error info."""
        workflow_id = "test-workflow-003"

        error_event = CoordinationEvent(
            event_type=EventType.FAILURE,
            workflow_id=workflow_id,
            task_id="failed-task",
            agent_id="agent-001",
            agent_type="backend-developer",
            error=ErrorInfo(
                error_type="TimeoutError",
                message="Task execution timeout",
                attempt=2,
                stack_trace="Stack trace here...",
            ),
        )

        event_id = await tracker.track_event(error_event)

        # Retrieve and verify
        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 1
        assert events[0].error is not None
        assert events[0].error.error_type == "TimeoutError"
        assert events[0].error.attempt == 2

    @pytest.mark.asyncio
    async def test_event_with_performance_metrics(self, tracker):
        """Test tracking event with performance metrics."""
        workflow_id = "test-workflow-004"

        perf_event = CoordinationEvent(
            event_type=EventType.EXECUTION_END,
            workflow_id=workflow_id,
            task_id="perf-task",
            duration_ms=1523.5,
            performance=PerformanceMetrics(
                queue_time_ms=10.5,
                execution_time_ms=1500.0,
                total_time_ms=1523.5,
            ),
        )

        await tracker.track_event(perf_event)

        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 1
        assert events[0].duration_ms == 1523.5
        assert events[0].performance.execution_time_ms == 1500.0


class TestEventRetrieval:
    """Test event retrieval and querying."""

    @pytest.mark.asyncio
    async def test_get_workflow_events(self, tracker):
        """Test retrieving events by workflow ID."""
        workflow_id = "test-workflow-005"

        # Create events
        for i in range(5):
            event = CoordinationEvent(
                event_type=EventType.TASK_STARTED,
                workflow_id=workflow_id,
                task_id=f"task-{i}",
            )
            await tracker.track_event(event)

        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_workflow_events_by_type(self, tracker):
        """Test filtering events by type."""
        workflow_id = "test-workflow-006"

        # Create mixed events
        await tracker.track_event(CoordinationEvent(EventType.WORKFLOW_STARTED, workflow_id))
        await tracker.track_event(CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id="t1"))
        await tracker.track_event(CoordinationEvent(EventType.HANDOFF, workflow_id, task_id="t1"))
        await tracker.track_event(CoordinationEvent(EventType.TASK_COMPLETED, workflow_id, task_id="t1"))

        # Filter by handoff
        handoffs = await tracker.get_workflow_events(workflow_id, event_type=EventType.HANDOFF)
        assert len(handoffs) == 1
        assert handoffs[0].event_type == EventType.HANDOFF

    @pytest.mark.asyncio
    async def test_get_task_events(self, tracker):
        """Test retrieving events by task ID."""
        workflow_id = "test-workflow-007"
        task_id = "specific-task"

        # Create events for specific task
        await tracker.track_event(CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id=task_id))
        await tracker.track_event(CoordinationEvent(EventType.EXECUTION_START, workflow_id, task_id=task_id))
        await tracker.track_event(CoordinationEvent(EventType.EXECUTION_END, workflow_id, task_id=task_id))

        # Also create events for other tasks
        await tracker.track_event(CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id="other-task"))

        events = await tracker.get_task_events(task_id)
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_get_agent_events(self, tracker):
        """Test retrieving events by agent ID."""
        workflow_id = "test-workflow-008"
        agent_id = "test-agent-123"

        # Create events for agent
        await tracker.track_event(
            CoordinationEvent(
                EventType.TASK_STARTED,
                workflow_id,
                agent_id=agent_id,
                agent_type="backend-developer",
            )
        )
        await tracker.track_event(
            CoordinationEvent(
                EventType.TASK_COMPLETED,
                workflow_id,
                agent_id=agent_id,
                agent_type="backend-developer",
            )
        )

        events = await tracker.get_agent_events(agent_id)
        assert len(events) == 2


class TestWorkflowTimeline:
    """Test workflow timeline generation."""

    @pytest.mark.asyncio
    async def test_get_workflow_timeline(self, tracker):
        """Test generating complete workflow timeline."""
        workflow_id = "test-workflow-009"

        # Create complete workflow execution
        events = [
            CoordinationEvent(EventType.WORKFLOW_CREATED, workflow_id),
            CoordinationEvent(EventType.WORKFLOW_STARTED, workflow_id),
            CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id="t1"),
            CoordinationEvent(
                EventType.HANDOFF,
                workflow_id,
                task_id="t1",
                source_agent=AgentInfo("a1", "backend"),
                target_agent=AgentInfo("a2", "frontend"),
            ),
            CoordinationEvent(EventType.TASK_COMPLETED, workflow_id, task_id="t1"),
            CoordinationEvent(EventType.WORKFLOW_COMPLETED, workflow_id),
        ]

        for event in events:
            await tracker.track_event(event)
            await asyncio.sleep(0.01)  # Small delay for ordering

        timeline = await tracker.get_workflow_timeline(workflow_id)

        assert timeline["workflow_id"] == workflow_id
        assert timeline["total_events"] == 6
        assert len(timeline["lifecycle"]) == 3  # Created, started, completed
        assert len(timeline["tasks"]) == 2  # Started, completed
        assert len(timeline["handoffs"]) == 1
        assert timeline["duration_ms"] is not None

    @pytest.mark.asyncio
    async def test_get_handoff_chain(self, tracker):
        """Test retrieving complete handoff chain."""
        workflow_id = "test-workflow-010"

        # Create handoff chain
        handoffs = [
            ("agent-1", "backend", "agent-2", "frontend"),
            ("agent-2", "frontend", "agent-3", "qa"),
            ("agent-3", "qa", "agent-4", "devops"),
        ]

        for src_id, src_type, tgt_id, tgt_type in handoffs:
            event = CoordinationEvent(
                EventType.HANDOFF,
                workflow_id,
                source_agent=AgentInfo(src_id, src_type),
                target_agent=AgentInfo(tgt_id, tgt_type),
            )
            await tracker.track_event(event)

        chain = await tracker.get_handoff_chain(workflow_id)
        assert len(chain) == 3


class TestStatistics:
    """Test statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_workflow_statistics(self, tracker):
        """Test getting statistics for specific workflow."""
        workflow_id = "test-workflow-011"

        # Create events
        for i in range(10):
            await tracker.track_event(
                CoordinationEvent(
                    EventType.TASK_STARTED,
                    workflow_id,
                    task_id=f"task-{i}",
                    duration_ms=100.0 * (i + 1),
                )
            )

        stats = await tracker.get_statistics(workflow_id)

        assert stats["total_events"] == 10
        assert stats["avg_duration_ms"] > 0
        assert stats["max_duration_ms"] == 1000.0
        assert EventType.TASK_STARTED.value in stats["event_type_counts"]

    @pytest.mark.asyncio
    async def test_get_global_statistics(self, tracker):
        """Test getting global statistics."""
        # Create events for multiple workflows
        for w in range(3):
            workflow_id = f"test-workflow-stats-{w}"
            for e in range(5):
                await tracker.track_event(
                    CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id=f"t-{e}")
                )

        stats = await tracker.get_statistics()

        assert stats["total_events"] >= 15
        assert stats["total_workflows"] >= 3


class TestPerformance:
    """Test performance and efficiency."""

    @pytest.mark.asyncio
    async def test_tracking_performance(self, tracker):
        """Test that tracking has minimal performance impact (<5%)."""
        workflow_id = "test-workflow-perf"
        num_events = 100

        # Measure tracking time
        start_time = time.perf_counter()
        for i in range(num_events):
            event = CoordinationEvent(
                EventType.TASK_STARTED,
                workflow_id,
                task_id=f"task-{i}",
            )
            await tracker.track_event(event)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_event = total_time_ms / num_events

        # Should be fast (<10ms per event for reasonable performance)
        assert avg_time_per_event < 10.0, f"Tracking too slow: {avg_time_per_event}ms per event"

        print(f"\nTracking performance: {avg_time_per_event:.2f}ms per event")

    @pytest.mark.asyncio
    async def test_storage_efficiency(self, tracker, db_pool):
        """Test storage size is <10MB per 1000 events."""
        workflow_id = "test-workflow-storage"
        num_events = 100  # Using 100 for faster test, extrapolate to 1000

        # Create events with typical data
        for i in range(num_events):
            event = CoordinationEvent(
                EventType.HANDOFF,
                workflow_id,
                task_id=f"task-{i}",
                source_agent=AgentInfo(f"agent-{i}", "backend-developer"),
                target_agent=AgentInfo(f"agent-{i+1}", "frontend-developer"),
                context={"task_description": "Sample task " * 10},
                metadata={"priority": "normal", "tags": ["test", "sample"]},
            )
            await tracker.track_event(event)

        # Check storage size
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT pg_total_relation_size('coordination_events') as size
                """
            )
            size_bytes = result["size"]

        # Extrapolate to 1000 events
        extrapolated_size_mb = (size_bytes / num_events * 1000) / (1024 * 1024)

        print(f"\nStorage efficiency: {extrapolated_size_mb:.2f}MB per 1000 events (extrapolated)")

        # Should be under 10MB per 1000 events
        assert extrapolated_size_mb < 10.0, f"Storage too large: {extrapolated_size_mb:.2f}MB per 1000 events"

    @pytest.mark.asyncio
    async def test_concurrent_tracking(self, tracker):
        """Test concurrent event tracking."""
        workflow_id = "test-workflow-concurrent"
        num_concurrent = 50

        async def track_event_task(task_id: str):
            event = CoordinationEvent(
                EventType.TASK_STARTED,
                workflow_id,
                task_id=task_id,
            )
            return await tracker.track_event(event)

        # Track events concurrently
        tasks = [track_event_task(f"task-{i}") for i in range(num_concurrent)]
        event_ids = await asyncio.gather(*tasks)

        # Verify all tracked
        assert len(event_ids) == num_concurrent
        assert len(set(event_ids)) == num_concurrent  # All unique

        # Verify in database
        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == num_concurrent


class TestConvenienceFunctions:
    """Test convenience tracking functions."""

    @pytest.mark.asyncio
    async def test_track_handoff(self, tracker):
        """Test track_handoff convenience function."""
        workflow_id = "test-workflow-handoff"

        event_id = await track_handoff(
            tracker,
            workflow_id,
            "agent-1",
            "backend",
            "agent-2",
            "frontend",
            task_id="handoff-task",
            context={"description": "API handoff"},
        )

        assert event_id is not None

        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 1
        assert events[0].event_type == EventType.HANDOFF

    @pytest.mark.asyncio
    async def test_track_task_execution(self, tracker):
        """Test track_task_execution convenience function."""
        workflow_id = "test-workflow-exec"

        # Track start
        start_id = await track_task_execution(
            tracker,
            workflow_id,
            "exec-task",
            "agent-1",
            "backend",
            "running",
        )

        # Track end
        end_id = await track_task_execution(
            tracker,
            workflow_id,
            "exec-task",
            "agent-1",
            "backend",
            "completed",
            duration_ms=1500.0,
            result_summary="Task completed successfully",
        )

        events = await tracker.get_task_events("exec-task")
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_track_failure(self, tracker):
        """Test track_failure convenience function."""
        workflow_id = "test-workflow-fail"

        event_id = await track_failure(
            tracker,
            workflow_id,
            "fail-task",
            "agent-1",
            "backend",
            "RuntimeError",
            "Something went wrong",
            attempt=2,
        )

        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 1
        assert events[0].event_type == EventType.FAILURE
        assert events[0].error.message == "Something went wrong"


class TestDataCleanup:
    """Test data management and cleanup."""

    @pytest.mark.asyncio
    async def test_delete_workflow_events(self, tracker):
        """Test deleting workflow events."""
        workflow_id = "test-workflow-delete"

        # Create events
        for i in range(5):
            await tracker.track_event(
                CoordinationEvent(EventType.TASK_STARTED, workflow_id, task_id=f"t-{i}")
            )

        # Verify created
        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 5

        # Delete
        deleted = await tracker.delete_workflow_events(workflow_id)
        assert deleted == 5

        # Verify deleted
        events = await tracker.get_workflow_events(workflow_id)
        assert len(events) == 0


class TestEventOrdering:
    """Test event ordering and timestamps."""

    @pytest.mark.asyncio
    async def test_events_ordered_by_timestamp(self, tracker):
        """Test that events are returned in chronological order."""
        workflow_id = "test-workflow-order"

        # Create events with delays
        event_ids = []
        for i in range(5):
            event = CoordinationEvent(
                EventType.TASK_STARTED,
                workflow_id,
                task_id=f"task-{i}",
            )
            event_id = await tracker.track_event(event)
            event_ids.append(event_id)
            await asyncio.sleep(0.01)  # Small delay

        # Retrieve events (should be newest first)
        events = await tracker.get_workflow_events(workflow_id)

        # Check ordering (newest first)
        assert events[0].event_id == event_ids[-1]
        assert events[-1].event_id == event_ids[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
