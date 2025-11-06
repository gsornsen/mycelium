"""Unit tests for handoff protocol implementation."""

import sys
from pathlib import Path

import pytest

# TODO: These tests need updating to match current API - see tests/unit/TODO.md
pytestmark = pytest.mark.skip(reason="Tests need updating to match current HandoffProtocol API")

# Add plugins directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plugins" / "mycelium-core"))

from coordination.protocol import (  # noqa: E402
    AgentInfo,
    HandoffContext,
    HandoffMessage,
    HandoffMetadata,
    HandoffProtocol,
    HandoffProtocolError,
    HandoffState,
    HandoffValidationError,
    WorkflowProgress,
)


def test_agent_info_creation():
    """Test AgentInfo creation and serialization."""
    agent = AgentInfo(
        agent_id="agent-001",
        agent_type="frontend-developer",
    )

    assert agent.agent_id == "agent-001"
    assert agent.agent_type == "frontend-developer"

    # Test serialization
    serialized = agent.to_dict()
    assert serialized["agent_id"] == "agent-001"
    assert serialized["agent_type"] == "frontend-developer"


def test_workflow_progress_tracking():
    """Test workflow progress calculation."""
    progress = WorkflowProgress(
        completed_steps=["step1", "step2", "step3"],
        pending_steps=["step4", "step5"],
        percentage=60.0,
    )

    assert len(progress.completed_steps) == 3
    assert len(progress.pending_steps) == 2
    assert progress.percentage == 60.0

    # Test blocked state
    blocked_progress = WorkflowProgress(
        total_tasks=5,
        completed_tasks=2,
        failed_tasks=3,
        in_progress_tasks=0,
    )
    assert blocked_progress.is_blocked is True


def test_handoff_metadata_validation():
    """Test HandoffMetadata validation."""
    metadata = HandoffMetadata(
        priority="high",
        deadline="2024-01-01T00:00:00Z",
        tags=["urgent", "customer-facing"],
        dependencies=["task-001", "task-002"],
    )

    assert metadata.priority == "high"
    assert "urgent" in metadata.tags
    assert len(metadata.dependencies) == 2


def test_handoff_context_initialization():
    """Test HandoffContext creation."""
    context = HandoffContext(
        workflow_id="workflow-001",
        task_id="task-001",
        from_agent="agent-001",
        to_agent="agent-002",
        metadata=HandoffMetadata(priority="medium"),
    )

    assert context.workflow_id == "workflow-001"
    assert context.task_id == "task-001"
    assert context.from_agent == "agent-001"
    assert context.to_agent == "agent-002"
    assert context.metadata.priority == "medium"

    # Test state progression
    assert context.state == HandoffState.INITIATED
    assert context.created_at is not None


def test_handoff_message_creation():
    """Test HandoffMessage creation and validation."""
    context = HandoffContext(
        workflow_id="workflow-001",
        task_id="task-001",
        from_agent="agent-001",
        to_agent="agent-002",
    )

    message = HandoffMessage(
        message_id="msg-001",
        context=context,
        payload={"task": "implement feature", "requirements": ["spec1", "spec2"]},
        message_type="task_assignment",
    )

    assert message.message_id == "msg-001"
    assert message.message_type == "task_assignment"
    assert message.payload["task"] == "implement feature"
    assert len(message.payload["requirements"]) == 2

    # Test serialization
    serialized = message.to_json()
    assert isinstance(serialized, str)

    # Test deserialization
    deserialized = HandoffMessage.from_json(serialized)
    assert deserialized.message_id == message.message_id
    assert deserialized.context.workflow_id == context.workflow_id


class TestHandoffProtocol:
    """Test suite for HandoffProtocol."""

    def test_protocol_initialization(self):
        """Test protocol initialization."""
        protocol = HandoffProtocol(protocol_version="1.0.0")
        assert protocol.protocol_version == "1.0.0"
        assert protocol.is_active is True

    def test_initiate_handoff(self):
        """Test handoff initiation."""
        protocol = HandoffProtocol()

        context = protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        assert context.state == HandoffState.INITIATED
        assert context.workflow_id == "workflow-001"
        assert protocol.get_active_handoffs() == 1

    def test_accept_handoff(self):
        """Test handoff acceptance."""
        protocol = HandoffProtocol()

        # Initiate handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        # Accept handoff
        accepted_context = protocol.accept_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            accepting_agent="agent-002",
        )

        assert accepted_context.state == HandoffState.IN_PROGRESS
        assert accepted_context.accepted_at is not None

    def test_reject_handoff(self):
        """Test handoff rejection."""
        protocol = HandoffProtocol()

        # Initiate handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        # Reject handoff
        rejected_context = protocol.reject_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            reason="Agent unavailable",
        )

        assert rejected_context.state == HandoffState.REJECTED
        assert rejected_context.rejection_reason == "Agent unavailable"

    def test_complete_handoff(self):
        """Test handoff completion."""
        protocol = HandoffProtocol()

        # Initiate and accept handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        protocol.accept_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            accepting_agent="agent-002",
        )

        # Complete handoff
        completed_context = protocol.complete_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            result={"status": "success", "output": "task completed"},
        )

        assert completed_context.state == HandoffState.COMPLETED
        assert completed_context.result["status"] == "success"
        assert completed_context.completed_at is not None

    def test_handoff_timeout(self):
        """Test handoff timeout handling."""
        protocol = HandoffProtocol(default_timeout=1)  # 1 second timeout

        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        # Simulate timeout
        import time

        time.sleep(1.1)

        timed_out = protocol.check_timeout(
            workflow_id="workflow-001",
            task_id="task-001",
        )

        assert timed_out is True

        # Get updated context
        updated_context = protocol.get_handoff_context(
            workflow_id="workflow-001",
            task_id="task-001",
        )
        assert updated_context.state == HandoffState.TIMEOUT

    def test_handoff_retry(self):
        """Test handoff retry mechanism."""
        protocol = HandoffProtocol(max_retries=3)

        # Initiate handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        # Simulate failure and retry
        for i in range(3):
            retry_context = protocol.retry_handoff(
                workflow_id="workflow-001",
                task_id="task-001",
            )
            assert retry_context.retry_count == i + 1

        # Max retries reached
        with pytest.raises(HandoffProtocolError, match="Max retries"):
            protocol.retry_handoff(
                workflow_id="workflow-001",
                task_id="task-001",
            )

    def test_invalid_state_transition(self):
        """Test invalid state transitions."""
        protocol = HandoffProtocol()

        # Try to accept non-existent handoff
        with pytest.raises(HandoffValidationError):
            protocol.accept_handoff(
                workflow_id="non-existent",
                task_id="non-existent",
                accepting_agent="agent-001",
            )

        # Complete already completed handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        protocol.accept_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            accepting_agent="agent-002",
        )

        protocol.complete_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            result={"status": "success"},
        )

        # Try to complete again
        with pytest.raises(HandoffProtocolError, match="Invalid state transition"):
            protocol.complete_handoff(
                workflow_id="workflow-001",
                task_id="task-001",
                result={"status": "success"},
            )

    def test_handoff_cancellation(self):
        """Test handoff cancellation."""
        protocol = HandoffProtocol()

        # Initiate handoff
        protocol.initiate_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            from_agent="agent-001",
            to_agent="agent-002",
            payload={"task": "test task"},
        )

        # Cancel handoff
        cancelled_context = protocol.cancel_handoff(
            workflow_id="workflow-001",
            task_id="task-001",
            reason="Task no longer needed",
        )

        assert cancelled_context.state == HandoffState.CANCELLED
        assert cancelled_context.cancellation_reason == "Task no longer needed"

    def test_protocol_metrics(self):
        """Test protocol metrics collection."""
        protocol = HandoffProtocol()

        # Create multiple handoffs
        for i in range(5):
            protocol.initiate_handoff(
                workflow_id=f"workflow-{i}",
                task_id=f"task-{i}",
                from_agent="agent-001",
                to_agent="agent-002",
                payload={"task": f"task {i}"},
            )

        # Accept some
        for i in range(3):
            protocol.accept_handoff(
                workflow_id=f"workflow-{i}",
                task_id=f"task-{i}",
                accepting_agent="agent-002",
            )

        # Complete some
        for i in range(2):
            protocol.complete_handoff(
                workflow_id=f"workflow-{i}",
                task_id=f"task-{i}",
                result={"status": "success"},
            )

        # Get metrics
        metrics = protocol.get_metrics()
        assert metrics["total_handoffs"] == 5
        assert metrics["accepted_handoffs"] == 3
        assert metrics["completed_handoffs"] == 2
        assert metrics["pending_handoffs"] == 3
        assert metrics["success_rate"] == 0.4  # 2/5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
