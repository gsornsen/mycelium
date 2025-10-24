"""Multi-agent workflow coordination and orchestration.

This module provides workflow orchestration capabilities including:
- Sequential and parallel task execution
- Dependency resolution
- State management with persistence
- Failure recovery mechanisms
- Agent handoff protocol
- Coordination event tracking
"""

from .orchestrator import TaskStatus, WorkflowOrchestrator, WorkflowStatus
from .protocol import HandoffMessage, HandoffProtocol
from .state_manager import StateManager, WorkflowState
from .tracker import (
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
