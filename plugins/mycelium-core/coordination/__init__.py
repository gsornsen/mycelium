"""Multi-agent workflow coordination and orchestration.

This module provides workflow orchestration capabilities including:
- Sequential and parallel task execution
- Dependency resolution
- State management with persistence
- Failure recovery mechanisms
- Agent handoff protocol
"""

from .orchestrator import WorkflowOrchestrator, WorkflowStatus, TaskStatus
from .state_manager import StateManager, WorkflowState
from .protocol import HandoffProtocol, HandoffMessage

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowStatus",
    "TaskStatus",
    "StateManager",
    "WorkflowState",
    "HandoffProtocol",
    "HandoffMessage",
]
