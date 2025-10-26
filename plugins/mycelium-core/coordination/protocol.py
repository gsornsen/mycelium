"""Agent handoff protocol for state transfer between agents.

This module implements a JSON-based protocol for agent-to-agent communication,
enabling seamless state transfer and context preservation across workflow transitions.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

# Load handoff schema
SCHEMA_PATH = Path(__file__).parent / "schemas" / "handoff.json"
with SCHEMA_PATH.open() as f:
    HANDOFF_SCHEMA = json.load(f)


class HandoffProtocolError(Exception):
    """Base exception for handoff protocol errors."""

    pass


class HandoffValidationError(HandoffProtocolError):
    """Raised when handoff message validation fails."""

    pass


@dataclass
class AgentInfo:
    """Agent information for handoff."""

    agent_id: str
    agent_type: str
    execution_time: float | None = None
    requirements: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class HandoffContext:
    """Context information for handoff."""

    task_description: str | None = None
    previous_results: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    files: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding empty collections."""
        result: dict[str, Any] = {}
        if self.task_description:
            result["task_description"] = self.task_description
        if self.previous_results:
            result["previous_results"] = self.previous_results
        if self.conversation_history:
            result["conversation_history"] = self.conversation_history
        if self.files:
            result["files"] = self.files
        if self.user_preferences:
            result["user_preferences"] = self.user_preferences
        return result


@dataclass
class WorkflowProgress:
    """Workflow progress tracking."""

    completed_steps: list[str] = field(default_factory=list)
    pending_steps: list[str] = field(default_factory=list)
    percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HandoffState:
    """Workflow execution state."""

    variables: dict[str, Any] = field(default_factory=dict)
    progress: WorkflowProgress | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {}
        if self.variables:
            result["variables"] = self.variables
        if self.progress:
            result["progress"] = self.progress.to_dict()
        if self.errors:
            result["errors"] = self.errors
        return result


@dataclass
class HandoffMetadata:
    """Handoff metadata for tracking and debugging."""

    priority: str = "normal"
    timeout: int | None = None
    retry_count: int = 0
    tags: list[str] = field(default_factory=list)
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class HandoffMessage:
    """Complete handoff message structure."""

    source: AgentInfo
    target: AgentInfo
    context: HandoffContext
    version: str = "1.0"
    handoff_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str | None = None
    state: HandoffState = field(default_factory=HandoffState)
    metadata: HandoffMetadata = field(default_factory=HandoffMetadata)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert handoff message to dictionary."""
        result = {
            "version": self.version,
            "handoff_id": self.handoff_id,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "context": self.context.to_dict(),
            "state": self.state.to_dict(),
            "metadata": self.metadata.to_dict(),
            "timestamp": self.timestamp,
        }
        # Only include workflow_id if it's not None
        if self.workflow_id is not None:
            result["workflow_id"] = self.workflow_id
        return result

    def to_json(self, indent: int | None = None) -> str:
        """Serialize handoff message to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HandoffMessage":
        """Create handoff message from dictionary."""
        # Parse source
        source_data = data["source"]
        source = AgentInfo(
            agent_id=source_data["agent_id"],
            agent_type=source_data["agent_type"],
            execution_time=source_data.get("execution_time"),
        )

        # Parse target
        target_data = data["target"]
        target = AgentInfo(
            agent_id=target_data["agent_id"],
            agent_type=target_data["agent_type"],
            requirements=target_data.get("requirements"),
        )

        # Parse context
        context_data = data.get("context", {})
        context = HandoffContext(
            task_description=context_data.get("task_description"),
            previous_results=context_data.get("previous_results", []),
            conversation_history=context_data.get("conversation_history", []),
            files=context_data.get("files", []),
            user_preferences=context_data.get("user_preferences", {}),
        )

        # Parse state
        state_data = data.get("state", {})
        progress_data = state_data.get("progress")
        progress = None
        if progress_data:
            progress = WorkflowProgress(
                completed_steps=progress_data.get("completed_steps", []),
                pending_steps=progress_data.get("pending_steps", []),
                percentage=progress_data.get("percentage", 0.0),
            )
        state = HandoffState(
            variables=state_data.get("variables", {}),
            progress=progress,
            errors=state_data.get("errors", []),
        )

        # Parse metadata
        metadata_data = data.get("metadata", {})
        metadata = HandoffMetadata(
            priority=metadata_data.get("priority", "normal"),
            timeout=metadata_data.get("timeout"),
            retry_count=metadata_data.get("retry_count", 0),
            tags=metadata_data.get("tags", []),
            correlation_id=metadata_data.get("correlation_id"),
        )

        return cls(
            version=data.get("version", "1.0"),
            handoff_id=data.get("handoff_id", str(uuid.uuid4())),
            workflow_id=data.get("workflow_id"),
            source=source,
            target=target,
            context=context,
            state=state,
            metadata=metadata,
            timestamp=data.get(
                "timestamp", datetime.now(timezone.utc).isoformat() + "Z"
            ),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "HandoffMessage":
        """Create handoff message from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class HandoffProtocol:
    """Handoff protocol implementation for agent-to-agent communication."""

    @staticmethod
    def validate(message: HandoffMessage) -> None:
        """Validate handoff message against JSON schema.

        Args:
            message: Handoff message to validate

        Raises:
            HandoffValidationError: If validation fails
        """
        try:
            message_dict = message.to_dict()
            jsonschema.validate(instance=message_dict, schema=HANDOFF_SCHEMA)
        except jsonschema.ValidationError as e:
            raise HandoffValidationError(
                f"Handoff validation failed: {e.message}"
            ) from e
        except Exception as e:
            raise HandoffValidationError(f"Handoff validation error: {str(e)}") from e

    @staticmethod
    def create_handoff(
        source_agent_id: str,
        source_agent_type: str,
        target_agent_id: str,
        target_agent_type: str,
        task_description: str | None = None,
        workflow_id: str | None = None,
        context: HandoffContext | None = None,
        state: HandoffState | None = None,
        metadata: HandoffMetadata | None = None,
    ) -> HandoffMessage:
        """Create a new handoff message.

        Args:
            source_agent_id: ID of source agent
            source_agent_type: Type of source agent
            target_agent_id: ID of target agent
            target_agent_type: Type of target agent
            task_description: Optional task description
            workflow_id: Optional workflow ID
            context: Optional handoff context
            state: Optional workflow state
            metadata: Optional metadata

        Returns:
            Validated handoff message

        Raises:
            HandoffValidationError: If created message fails validation
        """
        source = AgentInfo(agent_id=source_agent_id, agent_type=source_agent_type)
        target = AgentInfo(agent_id=target_agent_id, agent_type=target_agent_type)

        if context is None:
            context = HandoffContext(task_description=task_description)
        elif task_description and not context.task_description:
            context.task_description = task_description

        message = HandoffMessage(
            source=source,
            target=target,
            context=context,
            workflow_id=workflow_id,
            state=state or HandoffState(),
            metadata=metadata or HandoffMetadata(),
        )

        # Validate before returning
        HandoffProtocol.validate(message)
        return message

    @staticmethod
    def serialize(message: HandoffMessage) -> str:
        """Serialize handoff message to JSON.

        Args:
            message: Handoff message to serialize

        Returns:
            JSON string representation

        Raises:
            HandoffProtocolError: If serialization fails
        """
        try:
            return message.to_json()
        except Exception as e:
            raise HandoffProtocolError(f"Serialization failed: {str(e)}") from e

    @staticmethod
    def deserialize(json_str: str) -> HandoffMessage:
        """Deserialize JSON to handoff message.

        Args:
            json_str: JSON string to deserialize

        Returns:
            Handoff message object

        Raises:
            HandoffProtocolError: If deserialization fails
            HandoffValidationError: If deserialized message fails validation
        """
        try:
            message = HandoffMessage.from_json(json_str)
            HandoffProtocol.validate(message)
            return message
        except json.JSONDecodeError as e:
            raise HandoffProtocolError(f"Invalid JSON: {str(e)}") from e
        except HandoffValidationError:
            raise
        except Exception as e:
            raise HandoffProtocolError(f"Deserialization failed: {str(e)}") from e

    @staticmethod
    def add_result_to_context(
        message: HandoffMessage,
        agent_id: str,
        result: dict[str, Any],
    ) -> HandoffMessage:
        """Add agent execution result to handoff context.

        Args:
            message: Existing handoff message
            agent_id: ID of agent that produced result
            result: Result data to add

        Returns:
            Updated handoff message
        """
        result_entry = {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "result": result,
        }
        message.context.previous_results.append(result_entry)
        return message

    @staticmethod
    def update_progress(
        message: HandoffMessage,
        completed_steps: list[str] | None = None,
        pending_steps: list[str] | None = None,
        percentage: float | None = None,
    ) -> HandoffMessage:
        """Update workflow progress in handoff message.

        Args:
            message: Handoff message to update
            completed_steps: Completed step names
            pending_steps: Pending step names
            percentage: Progress percentage (0-100)

        Returns:
            Updated handoff message
        """
        if message.state.progress is None:
            message.state.progress = WorkflowProgress()

        if completed_steps is not None:
            message.state.progress.completed_steps = completed_steps
        if pending_steps is not None:
            message.state.progress.pending_steps = pending_steps
        if percentage is not None:
            message.state.progress.percentage = min(100.0, max(0.0, percentage))

        return message
