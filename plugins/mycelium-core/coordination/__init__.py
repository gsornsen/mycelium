"""Multi-agent workflow coordination and orchestration.

This module provides workflow orchestration capabilities including:
- Sequential and parallel task execution
- Dependency resolution
- State management with persistence
- Failure recovery mechanisms
- Agent handoff protocol
- Coordination event tracking
"""

from .orchestrator import WorkflowOrchestrator, WorkflowStatus, TaskStatus
from .state_manager import StateManager, WorkflowState
from .protocol import HandoffProtocol, HandoffMessage
from .tracker import (
    CoordinationTracker,
    CoordinationEvent,
    EventType,
    AgentInfo,
    ErrorInfo,
    PerformanceMetrics,
    track_handoff,
    track_task_execution,
    track_failure,
)

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowStatus",
    "TaskStatus",
    "StateManager",
    "WorkflowState",
    "HandoffProtocol",
    "HandoffMessage",
    "CoordinationTracker",
    "CoordinationEvent",
    "EventType",
    "AgentInfo",
    "ErrorInfo",
    "PerformanceMetrics",
    "track_handoff",
    "track_task_execution",
    "track_failure",
]
