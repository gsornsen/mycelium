"""State management for workflow orchestration with persistence and rollback support.

This module provides state management capabilities for multi-agent workflows,
including state persistence, versioning, and rollback mechanisms.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg
from asyncpg import Pool


class StateManagerError(Exception):
    """Base exception for state manager errors."""

    pass


class StateNotFoundError(StateManagerError):
    """Raised when workflow state is not found."""

    pass


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Individual task execution status."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class TaskState:
    """State of an individual task in the workflow."""

    task_id: str
    agent_id: str
    agent_type: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: str | None = None
    completed_at: str | None = None
    execution_time: float | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    retry_count: int = 0
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskState":
        """Create from dictionary."""
        data = data.copy()
        data["status"] = TaskStatus(data["status"])
        return cls(**data)


@dataclass
class WorkflowState:
    """Complete workflow execution state."""

    workflow_id: str
    status: WorkflowStatus
    tasks: dict[str, TaskState]
    created_at: str
    updated_at: str
    started_at: str | None = None
    completed_at: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "variables": self.variables,
            "metadata": self.metadata,
            "error": self.error,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create from dictionary."""
        data = data.copy()
        data["status"] = WorkflowStatus(data["status"])
        data["tasks"] = {k: TaskState.from_dict(v) for k, v in data["tasks"].items()}
        return cls(**data)


class StateManager:
    """Manages workflow state with persistence and rollback support.

    Provides state persistence to PostgreSQL with versioning and rollback capabilities.
    Supports concurrent workflow execution with isolation.
    """

    def __init__(self, pool: Pool | None = None, connection_string: str | None = None):
        """Initialize state manager.

        Args:
            pool: Optional existing connection pool
            connection_string: Optional PostgreSQL connection string
        """
        if pool is not None:
            self._pool = pool
            self._owns_pool = False
        else:
            self._connection_string = (
                connection_string or "postgresql://localhost:5432/mycelium_registry"
            )
            self._pool: Pool | None = None
            self._owns_pool = True

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        if self._pool is None and self._owns_pool:
            self._pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
        await self._ensure_schema()

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool is not None and self._owns_pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_schema(self) -> None:
        """Ensure workflow state tables exist."""
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        schema_sql = """
        CREATE TABLE IF NOT EXISTS workflow_states (
            workflow_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            variables JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            error TEXT,
            version INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS task_states (
            task_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL
                REFERENCES workflow_states(workflow_id) ON DELETE CASCADE,
            agent_id TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            execution_time REAL,
            result JSONB,
            error JSONB,
            retry_count INTEGER DEFAULT 0,
            dependencies TEXT[] DEFAULT ARRAY[]::TEXT[]
        );

        CREATE INDEX IF NOT EXISTS idx_task_workflow ON task_states(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_task_status ON task_states(status);
        CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_states(status);

        CREATE TABLE IF NOT EXISTS workflow_state_history (
            id SERIAL PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            state_snapshot JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE(workflow_id, version)
        );

        CREATE INDEX IF NOT EXISTS idx_history_workflow
            ON workflow_state_history(workflow_id);
        """

        async with self._pool.acquire() as conn:
            await conn.execute(schema_sql)

    async def create_workflow(
        self,
        workflow_id: str | None = None,
        tasks: list[TaskState] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowState:
        """Create a new workflow state.

        Args:
            workflow_id: Optional workflow ID (generated if not provided)
            tasks: Optional list of task states
            metadata: Optional workflow metadata

        Returns:
            Created workflow state

        Raises:
            StateManagerError: If creation fails
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        workflow_id = workflow_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        tasks_dict = {}
        if tasks:
            for task in tasks:
                tasks_dict[task.task_id] = task

        state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            tasks=tasks_dict,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        await self._persist_state(state)
        await self._save_snapshot(state)
        return state

    async def get_workflow(self, workflow_id: str) -> WorkflowState:
        """Retrieve workflow state.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow state

        Raises:
            StateNotFoundError: If workflow not found
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn:
            # Get workflow
            workflow_row = await conn.fetchrow(
                "SELECT * FROM workflow_states WHERE workflow_id = $1",
                workflow_id,
            )
            if not workflow_row:
                raise StateNotFoundError(f"Workflow {workflow_id} not found")

            # Get tasks
            task_rows = await conn.fetch(
                "SELECT * FROM task_states WHERE workflow_id = $1",
                workflow_id,
            )

            tasks = {}
            for row in task_rows:
                task = TaskState(
                    task_id=row["task_id"],
                    agent_id=row["agent_id"],
                    agent_type=row["agent_type"],
                    status=TaskStatus(row["status"]),
                    started_at=row["started_at"].isoformat() + "Z"
                    if row["started_at"]
                    else None,
                    completed_at=row["completed_at"].isoformat() + "Z"
                    if row["completed_at"]
                    else None,
                    execution_time=row["execution_time"],
                    result=row["result"],
                    error=row["error"],
                    retry_count=row["retry_count"],
                    dependencies=list(row["dependencies"])
                    if row["dependencies"]
                    else [],
                )
                tasks[task.task_id] = task

            return WorkflowState(
                workflow_id=workflow_row["workflow_id"],
                status=WorkflowStatus(workflow_row["status"]),
                tasks=tasks,
                created_at=workflow_row["created_at"].isoformat() + "Z",
                updated_at=workflow_row["updated_at"].isoformat() + "Z",
                started_at=workflow_row["started_at"].isoformat() + "Z"
                if workflow_row["started_at"]
                else None,
                completed_at=workflow_row["completed_at"].isoformat() + "Z"
                if workflow_row["completed_at"]
                else None,
                variables=workflow_row["variables"] or {},
                metadata=workflow_row["metadata"] or {},
                error=workflow_row["error"],
                version=workflow_row["version"],
            )

    async def update_workflow(self, state: WorkflowState) -> WorkflowState:
        """Update workflow state with versioning.

        Args:
            state: Updated workflow state

        Returns:
            Updated workflow state with incremented version

        Raises:
            StateManagerError: If update fails
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        state.updated_at = datetime.utcnow().isoformat() + "Z"
        state.version += 1

        await self._persist_state(state)
        await self._save_snapshot(state)
        return state

    async def update_task(
        self,
        workflow_id: str,
        task_id: str,
        status: TaskStatus | None = None,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        execution_time: float | None = None,
    ) -> WorkflowState:
        """Update individual task state.

        Args:
            workflow_id: Workflow identifier
            task_id: Task identifier
            status: Optional new task status
            result: Optional task result
            error: Optional error information
            execution_time: Optional execution time in milliseconds

        Returns:
            Updated workflow state

        Raises:
            StateNotFoundError: If workflow or task not found
        """
        state = await self.get_workflow(workflow_id)

        if task_id not in state.tasks:
            raise StateNotFoundError(
                f"Task {task_id} not found in workflow {workflow_id}"
            )

        task = state.tasks[task_id]
        now = datetime.utcnow().isoformat() + "Z"

        if status:
            task.status = status
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = now
            elif status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.SKIPPED,
            ):
                task.completed_at = now

        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        if execution_time is not None:
            task.execution_time = execution_time

        return await self.update_workflow(state)

    async def rollback_workflow(self, workflow_id: str, version: int) -> WorkflowState:
        """Rollback workflow to a previous version.

        Args:
            workflow_id: Workflow identifier
            version: Version to rollback to

        Returns:
            Restored workflow state

        Raises:
            StateNotFoundError: If workflow or version not found
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT state_snapshot FROM workflow_state_history "
                "WHERE workflow_id = $1 AND version = $2",
                workflow_id,
                version,
            )

            if not row:
                raise StateNotFoundError(
                    f"Version {version} not found for workflow {workflow_id}"
                )

            state = WorkflowState.from_dict(row["state_snapshot"])
            await self._persist_state(state)
            return state

    async def delete_workflow(self, workflow_id: str) -> None:
        """Delete workflow state.

        Args:
            workflow_id: Workflow identifier
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM workflow_states WHERE workflow_id = $1",
                workflow_id,
            )

    async def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 100,
    ) -> list[WorkflowState]:
        """List workflows with optional status filter.

        Args:
            status: Optional status filter
            limit: Maximum number of workflows to return

        Returns:
            List of workflow states
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT workflow_id FROM workflow_states WHERE status = $1 "
                    "ORDER BY updated_at DESC LIMIT $2",
                    status.value,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT workflow_id FROM workflow_states "
                    "ORDER BY updated_at DESC LIMIT $1",
                    limit,
                )

            workflows = []
            for row in rows:
                try:
                    workflows.append(await self.get_workflow(row["workflow_id"]))
                except StateNotFoundError:
                    continue

            return workflows

    async def _persist_state(self, state: WorkflowState) -> None:
        """Persist workflow state to database.

        Args:
            state: Workflow state to persist
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn, conn.transaction():
            # Upsert workflow
            await conn.execute(
                """
                    INSERT INTO workflow_states (
                        workflow_id, status, created_at, updated_at, started_at,
                        completed_at, variables, metadata, error, version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (workflow_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at,
                        started_at = EXCLUDED.started_at,
                        completed_at = EXCLUDED.completed_at,
                        variables = EXCLUDED.variables,
                        metadata = EXCLUDED.metadata,
                        error = EXCLUDED.error,
                        version = EXCLUDED.version
                    """,
                state.workflow_id,
                state.status.value,
                datetime.fromisoformat(state.created_at.rstrip("Z")),
                datetime.fromisoformat(state.updated_at.rstrip("Z")),
                datetime.fromisoformat(state.started_at.rstrip("Z"))
                if state.started_at
                else None,
                datetime.fromisoformat(state.completed_at.rstrip("Z"))
                if state.completed_at
                else None,
                json.dumps(state.variables),
                json.dumps(state.metadata),
                state.error,
                state.version,
            )

            # Delete existing tasks and re-insert (simpler than complex upsert logic)
            await conn.execute(
                "DELETE FROM task_states WHERE workflow_id = $1",
                state.workflow_id,
            )

            # Insert tasks
            for task in state.tasks.values():
                await conn.execute(
                    """
                        INSERT INTO task_states (
                            task_id, workflow_id, agent_id, agent_type, status,
                            started_at, completed_at, execution_time, result,
                            error, retry_count, dependencies
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        """,
                    task.task_id,
                    state.workflow_id,
                    task.agent_id,
                    task.agent_type,
                    task.status.value,
                    datetime.fromisoformat(task.started_at.rstrip("Z"))
                    if task.started_at
                    else None,
                    datetime.fromisoformat(task.completed_at.rstrip("Z"))
                    if task.completed_at
                    else None,
                    task.execution_time,
                    json.dumps(task.result) if task.result else None,
                    json.dumps(task.error) if task.error else None,
                    task.retry_count,
                    task.dependencies,
                )

    async def _save_snapshot(self, state: WorkflowState) -> None:
        """Save state snapshot for rollback.

        Args:
            state: Workflow state to snapshot
        """
        if self._pool is None:
            raise StateManagerError("State manager not initialized")

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workflow_state_history
                    (workflow_id, version, state_snapshot)
                VALUES ($1, $2, $3)
                ON CONFLICT (workflow_id, version) DO NOTHING
                """,
                state.workflow_id,
                state.version,
                json.dumps(state.to_dict()),
            )
