"""Unit tests for handoff protocol implementation."""

import json

import pytest
from coordination.protocol import (
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
        agent_id="test-agent-1",
        agent_type="backend-developer",
        execution_time=150.5,
    )

    assert agent.agent_id == "test-agent-1"
    assert agent.agent_type == "backend-developer"
    assert agent.execution_time == 150.5

    # Test to_dict
    data = agent.to_dict()
    assert "agent_id" in data
    assert "agent_type" in data
    assert "execution_time" in data


def test_handoff_context_creation():
    """Test HandoffContext creation and serialization."""
    context = HandoffContext(
        task_description="Implement feature X",
        previous_results=[{"agent": "a1", "result": "done"}],
        files=[{"path": "/tmp/test.py", "type": "python"}],
    )

    assert context.task_description == "Implement feature X"
    assert len(context.previous_results) == 1
    assert len(context.files) == 1

    # Test to_dict excludes empty collections
    minimal_context = HandoffContext()
    data = minimal_context.to_dict()
    assert "previous_results" not in data
    assert "conversation_history" not in data


def test_workflow_progress_creation():
    """Test WorkflowProgress creation."""
    progress = WorkflowProgress(
        completed_steps=["step1", "step2"],
        pending_steps=["step3"],
        percentage=66.7,
    )

    assert len(progress.completed_steps) == 2
    assert len(progress.pending_steps) == 1
    assert progress.percentage == 66.7


def test_handoff_state_creation():
    """Test HandoffState creation."""
    progress = WorkflowProgress(completed_steps=["task1"], percentage=50.0)
    state = HandoffState(
        variables={"counter": 5, "mode": "production"},
        progress=progress,
        errors=[{"type": "warning", "message": "Low memory"}],
    )

    assert state.variables["counter"] == 5
    assert state.progress.percentage == 50.0
    assert len(state.errors) == 1


def test_handoff_metadata_creation():
    """Test HandoffMetadata creation."""
    metadata = HandoffMetadata(
        priority="high",
        timeout=30000,
        retry_count=2,
        tags=["urgent", "production"],
    )

    assert metadata.priority == "high"
    assert metadata.timeout == 30000
    assert metadata.retry_count == 2
    assert "urgent" in metadata.tags


def test_handoff_message_creation():
    """Test complete HandoffMessage creation."""
    source = AgentInfo(agent_id="agent-1", agent_type="frontend")
    target = AgentInfo(agent_id="agent-2", agent_type="backend")
    context = HandoffContext(task_description="Build API endpoint")

    message = HandoffMessage(
        source=source,
        target=target,
        context=context,
        workflow_id="workflow-123",
    )

    assert message.source.agent_id == "agent-1"
    assert message.target.agent_id == "agent-2"
    assert message.workflow_id == "workflow-123"
    assert message.version == "1.0"
    assert message.handoff_id is not None


def test_handoff_message_serialization():
    """Test HandoffMessage to_dict and to_json."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext(task_description="Test task")

    message = HandoffMessage(source=source, target=target, context=context)

    # Test to_dict
    data = message.to_dict()
    assert data["version"] == "1.0"
    assert data["source"]["agent_id"] == "src"
    assert data["target"]["agent_id"] == "tgt"
    assert data["context"]["task_description"] == "Test task"

    # Test to_json
    json_str = message.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["source"]["agent_id"] == "src"


def test_handoff_message_deserialization():
    """Test HandoffMessage from_dict and from_json."""
    data = {
        "version": "1.0",
        "handoff_id": "test-handoff-123",
        "workflow_id": "workflow-456",
        "source": {
            "agent_id": "agent-a",
            "agent_type": "type-a",
            "execution_time": 100.0,
        },
        "target": {
            "agent_id": "agent-b",
            "agent_type": "type-b",
        },
        "context": {
            "task_description": "Process data",
            "previous_results": [{"data": "result1"}],
        },
        "state": {
            "variables": {"count": 5},
            "progress": {
                "completed_steps": ["step1"],
                "pending_steps": ["step2", "step3"],
                "percentage": 33.3,
            },
        },
        "metadata": {
            "priority": "normal",
            "tags": ["test"],
        },
        "timestamp": "2025-01-20T10:00:00Z",
    }

    # Test from_dict
    message = HandoffMessage.from_dict(data)
    assert message.handoff_id == "test-handoff-123"
    assert message.source.agent_id == "agent-a"
    assert message.target.agent_id == "agent-b"
    assert message.context.task_description == "Process data"
    assert message.state.variables["count"] == 5
    assert message.state.progress.percentage == 33.3

    # Test from_json
    json_str = json.dumps(data)
    message2 = HandoffMessage.from_json(json_str)
    assert message2.handoff_id == message.handoff_id
    assert message2.source.agent_id == message.source.agent_id


def test_handoff_protocol_validation_success():
    """Test successful handoff validation."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext(task_description="Valid task")

    message = HandoffMessage(source=source, target=target, context=context)

    # Should not raise exception
    HandoffProtocol.validate(message)


def test_handoff_protocol_validation_failure():
    """Test handoff validation with invalid data."""
    # Create message with invalid priority
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext()
    metadata = HandoffMetadata(priority="invalid_priority")  # Invalid value

    message = HandoffMessage(
        source=source, target=target, context=context, metadata=metadata
    )

    # Should raise validation error
    with pytest.raises(HandoffValidationError):
        HandoffProtocol.validate(message)


def test_handoff_protocol_create_handoff():
    """Test HandoffProtocol.create_handoff helper."""
    message = HandoffProtocol.create_handoff(
        source_agent_id="agent-1",
        source_agent_type="frontend",
        target_agent_id="agent-2",
        target_agent_type="backend",
        task_description="Build feature",
        workflow_id="wf-123",
    )

    assert message.source.agent_id == "agent-1"
    assert message.target.agent_id == "agent-2"
    assert message.context.task_description == "Build feature"
    assert message.workflow_id == "wf-123"

    # Verify it's validated
    HandoffProtocol.validate(message)


def test_handoff_protocol_serialize():
    """Test HandoffProtocol.serialize."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext(task_description="Task")

    message = HandoffMessage(source=source, target=target, context=context)

    json_str = HandoffProtocol.serialize(message)
    assert isinstance(json_str, str)

    # Verify it's valid JSON
    parsed = json.loads(json_str)
    assert parsed["source"]["agent_id"] == "src"


def test_handoff_protocol_deserialize():
    """Test HandoffProtocol.deserialize."""
    data = {
        "version": "1.0",
        "source": {"agent_id": "src", "agent_type": "type1"},
        "target": {"agent_id": "tgt", "agent_type": "type2"},
        "context": {"task_description": "Task"},
        "state": {},
        "metadata": {},
        "timestamp": "2025-01-20T10:00:00Z",
    }

    json_str = json.dumps(data)
    message = HandoffProtocol.deserialize(json_str)

    assert message.source.agent_id == "src"
    assert message.target.agent_id == "tgt"


def test_handoff_protocol_deserialize_invalid_json():
    """Test deserialization with invalid JSON."""
    invalid_json = "{invalid json"

    with pytest.raises(HandoffProtocolError, match="Invalid JSON"):
        HandoffProtocol.deserialize(invalid_json)


def test_handoff_protocol_add_result_to_context():
    """Test adding result to handoff context."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext()

    message = HandoffMessage(source=source, target=target, context=context)

    # Add result
    result = {"output": "processed data", "status": "success"}
    updated = HandoffProtocol.add_result_to_context(message, "agent-1", result)

    assert len(updated.context.previous_results) == 1
    assert updated.context.previous_results[0]["agent_id"] == "agent-1"
    assert updated.context.previous_results[0]["result"] == result


def test_handoff_protocol_update_progress():
    """Test updating progress in handoff."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext()

    message = HandoffMessage(source=source, target=target, context=context)

    # Update progress
    updated = HandoffProtocol.update_progress(
        message,
        completed_steps=["step1", "step2"],
        pending_steps=["step3"],
        percentage=66.7,
    )

    assert updated.state.progress is not None
    assert len(updated.state.progress.completed_steps) == 2
    assert updated.state.progress.percentage == 66.7


def test_handoff_protocol_update_progress_clamping():
    """Test progress percentage clamping."""
    source = AgentInfo(agent_id="src", agent_type="type1")
    target = AgentInfo(agent_id="tgt", agent_type="type2")
    context = HandoffContext()

    message = HandoffMessage(source=source, target=target, context=context)

    # Test upper bound clamping
    updated = HandoffProtocol.update_progress(message, percentage=150.0)
    assert updated.state.progress.percentage == 100.0

    # Test lower bound clamping
    updated = HandoffProtocol.update_progress(message, percentage=-10.0)
    assert updated.state.progress.percentage == 0.0


def test_handoff_round_trip():
    """Test complete serialization/deserialization round trip."""
    # Create complex handoff message
    source = AgentInfo(agent_id="agent-1", agent_type="parser", execution_time=150.5)
    target = AgentInfo(agent_id="agent-2", agent_type="validator")

    context = HandoffContext(
        task_description="Parse and validate input",
        previous_results=[
            {"agent": "preprocessor", "data": "cleaned"},
        ],
        files=[{"path": "/tmp/input.json", "type": "json"}],
        user_preferences={"strict_mode": True},
    )

    progress = WorkflowProgress(
        completed_steps=["parse"],
        pending_steps=["validate", "format"],
        percentage=33.3,
    )

    state = HandoffState(
        variables={"record_count": 100, "errors": 0},
        progress=progress,
    )

    metadata = HandoffMetadata(
        priority="high",
        timeout=30000,
        retry_count=1,
        tags=["validation", "critical"],
        correlation_id="corr-123",
    )

    message = HandoffMessage(
        source=source,
        target=target,
        context=context,
        state=state,
        metadata=metadata,
        workflow_id="wf-789",
    )

    # Serialize
    json_str = HandoffProtocol.serialize(message)

    # Deserialize
    restored = HandoffProtocol.deserialize(json_str)

    # Verify all fields preserved
    assert restored.source.agent_id == message.source.agent_id
    assert restored.source.execution_time == message.source.execution_time
    assert restored.target.agent_id == message.target.agent_id
    assert restored.context.task_description == message.context.task_description
    assert len(restored.context.previous_results) == 1
    assert restored.state.variables["record_count"] == 100
    assert restored.state.progress.percentage == 33.3
    assert restored.metadata.priority == "high"
    assert restored.metadata.correlation_id == "corr-123"
    assert restored.workflow_id == "wf-789"


def test_minimal_handoff_message():
    """Test handoff with minimal required fields."""
    data = {
        "version": "1.0",
        "source": {"agent_id": "src", "agent_type": "type1"},
        "target": {"agent_id": "tgt", "agent_type": "type2"},
        "context": {},
        "timestamp": "2025-01-20T10:00:00Z",
    }

    message = HandoffMessage.from_dict(data)
    HandoffProtocol.validate(message)

    assert message.source.agent_id == "src"
    assert message.target.agent_id == "tgt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
