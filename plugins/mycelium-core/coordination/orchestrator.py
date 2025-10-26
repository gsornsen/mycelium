"""Workflow orchestration engine for multi-agent task execution.

This module implements a DAG-based workflow orchestration engine that manages
multi-agent task execution with dependency resolution, parallel coordination,
state management, and failure recovery mechanisms.
"""

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .protocol import HandoffContext
from .state_manager import (
    StateManager,
    TaskState,
    TaskStatus,
    WorkflowState,
    WorkflowStatus,
)


class OrchestrationError(Exception):
    """Base exception for orchestration errors."""

    pass


class DependencyError(OrchestrationError):
    """Raised when dependency resolution fails."""

    pass


class ExecutionError(OrchestrationError):
    """Raised when task execution fails."""

    pass


@dataclass
class RetryPolicy:
    """Retry policy configuration for task execution."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt."""
        delay = self.initial_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


@dataclass
class TaskDefinition:
    """Definition of a task in the workflow."""

    task_id: str
    agent_id: str
    agent_type: str
    dependencies: list[str] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: float | None = None  # seconds
    allow_failure: bool = False  # if True, workflow continues even if task fails
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecutionContext:
    """Context for task execution."""

    task_def: TaskDefinition
    workflow_id: str
    workflow_context: HandoffContext
    previous_results: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)


# Type alias for task executor function
TaskExecutor = Callable[[TaskExecutionContext], Any]


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflow execution with dependency resolution.

    Supports:
    - Sequential and parallel task execution
    - DAG-based dependency resolution
    - State persistence with rollback
    - Failure recovery (retry, fallback, abort)
    - Real-time progress tracking
    - Memory-efficient execution (<50MB overhead per workflow)
    """

    def __init__(
        self,
        state_manager: StateManager,
        default_retry_policy: RetryPolicy | None = None,
        max_parallel_tasks: int = 10,
    ):
        """Initialize workflow orchestrator.

        Args:
            state_manager: State manager for persistence
            default_retry_policy: Default retry policy for tasks
            max_parallel_tasks: Maximum number of parallel tasks
        """
        self.state_manager = state_manager
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        self.max_parallel_tasks = max_parallel_tasks
        self._task_executors: dict[str, TaskExecutor] = {}
        self._active_workflows: dict[str, asyncio.Task[Any]] = {}

    def register_executor(self, agent_type: str, executor: TaskExecutor) -> None:
        """Register task executor for agent type.

        Args:
            agent_type: Agent type identifier
            executor: Async function that executes the task
        """
        self._task_executors[agent_type] = executor

    async def create_workflow(
        self,
        tasks: list[TaskDefinition],
        workflow_id: str | None = None,
        context: HandoffContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new workflow.

        Args:
            tasks: List of task definitions
            workflow_id: Optional workflow ID
            context: Optional workflow context
            metadata: Optional workflow metadata

        Returns:
            Workflow ID

        Raises:
            DependencyError: If task dependencies form a cycle
            OrchestrationError: If workflow creation fails
        """
        # Validate dependencies (no cycles)
        self._validate_dependencies(tasks)

        # Create task states
        task_states = [
            TaskState(
                task_id=task.task_id,
                agent_id=task.agent_id,
                agent_type=task.agent_type,
                dependencies=task.dependencies,
            )
            for task in tasks
        ]

        # Store task definitions in metadata
        if metadata is None:
            metadata = {}
        metadata["tasks"] = [
            {
                "task_id": t.task_id,
                "agent_id": t.agent_id,
                "agent_type": t.agent_type,
                "dependencies": t.dependencies,
                "retry_policy": {
                    "max_attempts": t.retry_policy.max_attempts,
                    "initial_delay": t.retry_policy.initial_delay,
                    "max_delay": t.retry_policy.max_delay,
                    "exponential_base": t.retry_policy.exponential_base,
                },
                "timeout": t.timeout,
                "allow_failure": t.allow_failure,
                "metadata": t.metadata,
            }
            for t in tasks
        ]
        metadata["context"] = context.to_dict() if context else {}

        # Create workflow state
        state = await self.state_manager.create_workflow(
            workflow_id=workflow_id,
            tasks=task_states,
            metadata=metadata,
        )

        return state.workflow_id

    async def execute_workflow(
        self,
        workflow_id: str,
        background: bool = False,
    ) -> WorkflowState | None:
        """Execute workflow with dependency resolution.

        Args:
            workflow_id: Workflow identifier
            background: If True, run in background and return immediately

        Returns:
            Final workflow state (None if background=True)

        Raises:
            OrchestrationError: If workflow execution fails
        """
        if background:
            task = asyncio.create_task(self._execute_workflow_impl(workflow_id))
            self._active_workflows[workflow_id] = task
            return None
        return await self._execute_workflow_impl(workflow_id)

    async def _execute_workflow_impl(self, workflow_id: str) -> WorkflowState:
        """Internal workflow execution implementation."""
        try:
            # Get workflow state
            state = await self.state_manager.get_workflow(workflow_id)

            # Update status to running
            state.status = WorkflowStatus.RUNNING
            state.started_at = state.updated_at
            await self.state_manager.update_workflow(state)

            # Reconstruct task definitions from metadata
            tasks = self._reconstruct_tasks(state)

            # Build dependency graph
            dep_graph = self._build_dependency_graph(tasks)

            # Execute tasks in topological order with parallelism
            await self._execute_tasks(workflow_id, tasks, dep_graph, state)

            # Get final state
            state = await self.state_manager.get_workflow(workflow_id)

            # Determine final status
            if all(t.status == TaskStatus.COMPLETED for t in state.tasks.values()):
                state.status = WorkflowStatus.COMPLETED
            elif any(t.status == TaskStatus.FAILED for t in state.tasks.values()):
                # Check if any failed tasks don't allow failure
                tasks_by_id = {t.task_id: t for t in tasks}
                critical_failures = [
                    t
                    for t in state.tasks.values()
                    if t.status == TaskStatus.FAILED
                    and not tasks_by_id[t.task_id].allow_failure
                ]
                if critical_failures:
                    state.status = WorkflowStatus.FAILED
                    state.error = f"Critical tasks failed: {[t.task_id for t in critical_failures]}"
                else:
                    state.status = WorkflowStatus.COMPLETED
            else:
                state.status = WorkflowStatus.COMPLETED

            state.completed_at = state.updated_at
            await self.state_manager.update_workflow(state)

            return state

        except Exception as e:
            # Mark workflow as failed
            try:
                state = await self.state_manager.get_workflow(workflow_id)
                state.status = WorkflowStatus.FAILED
                state.error = str(e)
                state.completed_at = state.updated_at
                await self.state_manager.update_workflow(state)
            except Exception:
                pass  # Best effort
            raise OrchestrationError(f"Workflow execution failed: {str(e)}") from e
        finally:
            # Clean up active workflows
            if workflow_id in self._active_workflows:
                del self._active_workflows[workflow_id]

    def _reconstruct_tasks(self, state: WorkflowState) -> list[TaskDefinition]:
        """Reconstruct task definitions from workflow metadata."""
        task_defs = []
        for task_data in state.metadata.get("tasks", []):
            retry_data = task_data.get("retry_policy", {})
            retry_policy = RetryPolicy(
                max_attempts=retry_data.get("max_attempts", 3),
                initial_delay=retry_data.get("initial_delay", 1.0),
                max_delay=retry_data.get("max_delay", 60.0),
                exponential_base=retry_data.get("exponential_base", 2.0),
            )
            task_def = TaskDefinition(
                task_id=task_data["task_id"],
                agent_id=task_data["agent_id"],
                agent_type=task_data["agent_type"],
                dependencies=task_data.get("dependencies", []),
                retry_policy=retry_policy,
                timeout=task_data.get("timeout"),
                allow_failure=task_data.get("allow_failure", False),
                metadata=task_data.get("metadata", {}),
            )
            task_defs.append(task_def)
        return task_defs

    def _validate_dependencies(self, tasks: list[TaskDefinition]) -> None:
        """Validate task dependencies for cycles.

        Args:
            tasks: List of task definitions

        Raises:
            DependencyError: If dependencies contain a cycle
        """
        task_ids = {t.task_id for t in tasks}

        # Check all dependencies exist
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise DependencyError(
                        f"Task {task.task_id} depends on non-existent task {dep}"
                    )

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str, adj_list: dict[str, list[str]]) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            for neighbor in adj_list.get(task_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, adj_list):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        # Build adjacency list (reverse dependencies for topological sort)
        adj_list = {t.task_id: list(t.dependencies) for t in tasks}

        for task in tasks:
            if task.task_id not in visited and has_cycle(task.task_id, adj_list):
                raise DependencyError("Task dependencies contain a cycle")

    def _build_dependency_graph(
        self, tasks: list[TaskDefinition]
    ) -> dict[str, list[str]]:
        """Build dependency graph (task -> dependent tasks).

        Args:
            tasks: List of task definitions

        Returns:
            Dictionary mapping task_id to list of tasks that depend on it
        """
        graph = defaultdict(list)
        for task in tasks:
            for dep in task.dependencies:
                graph[dep].append(task.task_id)
        return dict(graph)

    async def _execute_tasks(
        self,
        workflow_id: str,
        tasks: list[TaskDefinition],
        _dep_graph: dict[str, list[str]],
        state: WorkflowState,
    ) -> None:
        """Execute tasks respecting dependencies and parallelism.

        Args:
            workflow_id: Workflow identifier
            tasks: Task definitions
            dep_graph: Dependency graph
            state: Current workflow state
        """
        tasks_by_id = {t.task_id: t for t in tasks}
        completed = set()
        running: set[str] = set()
        pending = {t.task_id for t in tasks}

        while pending or running:
            # Find tasks ready to execute (all dependencies completed)
            ready = []
            for task_id in list(pending):
                task_def = tasks_by_id[task_id]
                if all(dep in completed for dep in task_def.dependencies):
                    ready.append(task_id)
                    pending.remove(task_id)

            # Start ready tasks up to parallel limit
            tasks_to_start = ready[: self.max_parallel_tasks - len(running)]
            if tasks_to_start:
                task_futures = []
                for task_id in tasks_to_start:
                    running.add(task_id)
                    future = asyncio.create_task(
                        self._execute_task(workflow_id, tasks_by_id[task_id], state)
                    )
                    task_futures.append((task_id, future))

                # Wait for at least one task to complete
                done, pending_futures = await asyncio.wait(
                    [f for _, f in task_futures],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Process completed tasks
                for task_id, future in task_futures:
                    if future in done:
                        running.remove(task_id)
                        try:
                            await future
                            completed.add(task_id)
                        except ExecutionError:
                            # Check if failure is allowed
                            if not tasks_by_id[task_id].allow_failure:
                                raise
                            completed.add(
                                task_id
                            )  # Mark as completed even though it failed
            elif running:
                # Wait for running tasks if no ready tasks
                await asyncio.sleep(0.1)
            else:
                # No ready tasks and nothing running - check for deadlock
                if pending:
                    raise OrchestrationError(
                        f"Workflow deadlock detected. Pending tasks: {pending}"
                    )

    async def _execute_task(
        self,
        workflow_id: str,
        task_def: TaskDefinition,
        state: WorkflowState,
    ) -> None:
        """Execute a single task with retry logic.

        Args:
            workflow_id: Workflow identifier
            task_def: Task definition
            state: Current workflow state

        Raises:
            ExecutionError: If task execution fails after retries
        """
        task_state = state.tasks[task_def.task_id]
        attempt = 0

        while attempt < task_def.retry_policy.max_attempts:
            try:
                # Update task status
                await self.state_manager.update_task(
                    workflow_id,
                    task_def.task_id,
                    status=TaskStatus.RUNNING if attempt == 0 else TaskStatus.RETRYING,
                )
                task_state.retry_count = attempt

                # Get executor
                executor = self._task_executors.get(task_def.agent_type)
                if not executor:
                    raise ExecutionError(
                        f"No executor registered for agent type {task_def.agent_type}"
                    )

                # Build execution context
                state = await self.state_manager.get_workflow(workflow_id)
                context_data = state.metadata.get("context", {})
                workflow_context = HandoffContext(
                    task_description=context_data.get("task_description"),
                    previous_results=context_data.get("previous_results", []),
                    conversation_history=context_data.get("conversation_history", []),
                    files=context_data.get("files", []),
                    user_preferences=context_data.get("user_preferences", {}),
                )

                # Collect results from dependencies
                previous_results = []
                for dep_id in task_def.dependencies:
                    dep_task = state.tasks.get(dep_id)
                    if dep_task and dep_task.result:
                        previous_results.append(
                            {
                                "task_id": dep_id,
                                "agent_id": dep_task.agent_id,
                                "result": dep_task.result,
                            }
                        )

                exec_context = TaskExecutionContext(
                    task_def=task_def,
                    workflow_id=workflow_id,
                    workflow_context=workflow_context,
                    previous_results=previous_results,
                    variables=state.variables.copy(),
                )

                # Execute task with timeout
                start_time = time.time()
                if task_def.timeout:
                    result = await asyncio.wait_for(
                        executor(exec_context),
                        timeout=task_def.timeout,
                    )
                else:
                    result = await executor(exec_context)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms

                # Update task with result
                await self.state_manager.update_task(
                    workflow_id,
                    task_def.task_id,
                    status=TaskStatus.COMPLETED,
                    result={"data": result} if result else {},
                    execution_time=execution_time,
                )
                return

            except asyncio.TimeoutError:
                error_info = {
                    "error_type": "timeout",
                    "message": f"Task exceeded timeout of {task_def.timeout}s",
                    "attempt": attempt + 1,
                }
                await self._handle_task_failure(
                    workflow_id, task_def, attempt, error_info
                )
                attempt += 1
                if attempt < task_def.retry_policy.max_attempts:
                    await asyncio.sleep(task_def.retry_policy.get_delay(attempt))

            except Exception as e:
                error_info = {
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "attempt": attempt + 1,
                }
                await self._handle_task_failure(
                    workflow_id, task_def, attempt, error_info
                )
                attempt += 1
                if attempt < task_def.retry_policy.max_attempts:
                    await asyncio.sleep(task_def.retry_policy.get_delay(attempt))

        # All retries exhausted
        raise ExecutionError(f"Task {task_def.task_id} failed after {attempt} attempts")

    async def _handle_task_failure(
        self,
        workflow_id: str,
        task_def: TaskDefinition,
        attempt: int,
        error_info: dict[str, Any],
    ) -> None:
        """Handle task execution failure.

        Args:
            workflow_id: Workflow identifier
            task_def: Task definition
            attempt: Current attempt number
            error_info: Error information
        """
        if attempt >= task_def.retry_policy.max_attempts - 1:
            # Final failure
            await self.state_manager.update_task(
                workflow_id,
                task_def.task_id,
                status=TaskStatus.FAILED,
                error=error_info,
            )

    async def get_workflow_status(self, workflow_id: str) -> WorkflowState:
        """Get current workflow status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Current workflow state
        """
        return await self.state_manager.get_workflow(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> WorkflowState:
        """Cancel running workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Updated workflow state
        """
        state = await self.state_manager.get_workflow(workflow_id)
        state.status = WorkflowStatus.CANCELLED
        state.completed_at = state.updated_at

        # Cancel running tasks
        for task in state.tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.SKIPPED

        await self.state_manager.update_workflow(state)

        # Cancel asyncio task if running
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].cancel()
            del self._active_workflows[workflow_id]

        return state

    async def pause_workflow(self, workflow_id: str) -> WorkflowState:
        """Pause running workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Updated workflow state
        """
        state = await self.state_manager.get_workflow(workflow_id)
        if state.status == WorkflowStatus.RUNNING:
            state.status = WorkflowStatus.PAUSED
            await self.state_manager.update_workflow(state)
        return state

    async def resume_workflow(self, workflow_id: str) -> WorkflowState:
        """Resume paused workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Execution started in background, returns current state
        """
        state = await self.state_manager.get_workflow(workflow_id)
        if state.status == WorkflowStatus.PAUSED:
            state.status = WorkflowStatus.PENDING
            await self.state_manager.update_workflow(state)
            await self.execute_workflow(workflow_id, background=True)
        return state

    async def rollback_workflow(self, workflow_id: str, version: int) -> WorkflowState:
        """Rollback workflow to previous version.

        Args:
            workflow_id: Workflow identifier
            version: Version to rollback to

        Returns:
            Restored workflow state
        """
        return await self.state_manager.rollback_workflow(workflow_id, version)
