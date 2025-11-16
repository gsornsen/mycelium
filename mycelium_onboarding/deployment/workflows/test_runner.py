"""Temporal test workflow runner with connection management.

This module provides a runner that connects to a Temporal server, executes
the test workflow, and collects validation results. It handles connection
errors gracefully and implements retry logic with exponential backoff.

The runner is designed to be used after deploying Temporal + PostgreSQL
to validate that the deployment is working correctly.

Example:
    >>> runner = TestRunner(temporal_host="localhost", temporal_port=7233)
    >>> result = await runner.run_validation()
    >>> print(f"Validation {'passed' if result.success else 'failed'}")
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio.client import Client, WorkflowFailureError
from temporalio.worker import Worker

from mycelium_onboarding.deployment.workflows.test_workflow import (
    TestWorkflow,
    WorkflowValidationResult,
    execute_test_activity,
    test_error_handling_activity,
    validate_connection_activity,
    validate_state_persistence_activity,
)

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Configuration for Temporal server connection.

    Attributes:
        host: Temporal server host
        port: Temporal server port
        namespace: Temporal namespace to use
        task_queue: Task queue name for workers
        tls_enabled: Whether to use TLS for connection
        max_connection_retries: Maximum connection attempts
        connection_timeout_seconds: Timeout for each connection attempt
    """

    host: str = "localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "test-validation-queue"
    tls_enabled: bool = False
    max_connection_retries: int = 3
    connection_timeout_seconds: int = 10

    @property
    def address(self) -> str:
        """Get full Temporal server address."""
        return f"{self.host}:{self.port}"


@dataclass
class ValidationResult:
    """Result from running the test workflow validation.

    Attributes:
        success: Overall validation success
        workflow_result: Detailed workflow validation result
        connection_successful: Whether connection to Temporal succeeded
        workflow_id: ID of the executed workflow
        run_id: Run ID of the workflow execution
        error: Error message if validation failed
        duration_ms: Total validation duration including connection
    """

    success: bool
    workflow_result: WorkflowValidationResult | None = None
    connection_successful: bool = False
    workflow_id: str | None = None
    run_id: str | None = None
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "connection_successful": self.connection_successful,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "workflow_result": self.workflow_result.to_dict() if self.workflow_result else None,
        }


class TestRunner:
    """Runner for Temporal deployment validation workflow.

    This class manages the complete lifecycle of validation testing:
    1. Connect to Temporal server with retry logic
    2. Start a worker to handle activities
    3. Execute the test workflow
    4. Collect and return validation results
    5. Clean up resources

    The runner implements exponential backoff for connection retries and
    handles various failure scenarios gracefully.
    """

    def __init__(
        self,
        temporal_host: str = "localhost",
        temporal_port: int = 7233,
        namespace: str = "default",
        task_queue: str = "test-validation-queue",
        verbose: bool = False,
    ):
        """Initialize test runner.

        Args:
            temporal_host: Temporal server hostname or IP
            temporal_port: Temporal server port
            namespace: Temporal namespace to use
            task_queue: Task queue name for workflow and activities
            verbose: Enable verbose logging
        """
        self.config = ConnectionConfig(
            host=temporal_host,
            port=temporal_port,
            namespace=namespace,
            task_queue=task_queue,
        )
        self.verbose = verbose
        self.client: Client | None = None
        self.worker: Worker | None = None

        # Configure logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    async def connect(self) -> bool:
        """Connect to Temporal server with retry logic.

        Implements exponential backoff for connection retries to handle
        temporary network issues or server startup delays.

        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"Connecting to Temporal server at {self.config.address}")

        for attempt in range(1, self.config.max_connection_retries + 1):
            try:
                # Calculate backoff delay
                if attempt > 1:
                    delay = min(2 ** (attempt - 1), 30)  # Max 30 seconds
                    logger.info(
                        f"Retrying connection in {delay} seconds "
                        f"(attempt {attempt}/{self.config.max_connection_retries})"
                    )
                    await asyncio.sleep(delay)

                # Attempt connection with timeout
                self.client = await asyncio.wait_for(
                    Client.connect(
                        self.config.address,
                        namespace=self.config.namespace,
                    ),
                    timeout=self.config.connection_timeout_seconds,
                )

                logger.info(f"Successfully connected to Temporal server (attempt {attempt})")
                return True

            except asyncio.TimeoutError:
                logger.warning(
                    f"Connection timeout after {self.config.connection_timeout_seconds}s (attempt {attempt})"
                )
                if attempt >= self.config.max_connection_retries:
                    logger.error(f"Failed to connect after {self.config.max_connection_retries} attempts")
                    return False

            except Exception as e:
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt >= self.config.max_connection_retries:
                    logger.error(f"Failed to connect after {self.config.max_connection_retries} attempts: {e}")
                    return False

        return False

    async def start_worker(self) -> bool:
        """Start a worker to handle workflow and activity tasks.

        The worker must be running to process workflow tasks and execute
        activities during validation.

        Returns:
            True if worker started successfully, False otherwise

        Raises:
            RuntimeError: If client is not connected
        """
        if not self.client:
            raise RuntimeError("Cannot start worker: client not connected")

        logger.info(f"Starting worker on task queue: {self.config.task_queue}")

        try:
            # Create worker with all activities
            self.worker = Worker(
                self.client,
                task_queue=self.config.task_queue,
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            )

            logger.info("Worker configured successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            return False

    async def run_validation(
        self,
        workflow_id: str | None = None,
        execution_timeout: int = 60,
    ) -> ValidationResult:
        """Execute the complete validation workflow.

        This is the main entry point for running deployment validation.
        It handles connection, worker startup, workflow execution, and
        result collection.

        Args:
            workflow_id: Optional workflow ID (auto-generated if None)
            execution_timeout: Maximum workflow execution time in seconds

        Returns:
            ValidationResult with complete validation outcome
        """
        logger.info("Starting Temporal deployment validation")
        start_time = asyncio.get_event_loop().time()

        # Step 1: Connect to Temporal
        connection_successful = await self.connect()
        if not connection_successful:
            return ValidationResult(
                success=False,
                connection_successful=False,
                error="Failed to connect to Temporal server",
            )

        # Step 2: Start worker
        worker_started = await self.start_worker()
        if not worker_started:
            return ValidationResult(
                success=False,
                connection_successful=True,
                error="Failed to start worker",
            )

        # Step 3: Execute validation workflow
        try:
            # Run worker in background
            assert self.worker is not None
            worker_task = asyncio.create_task(self.worker.run())

            # Wait for worker to be ready
            await asyncio.sleep(1)

            # Generate workflow ID if not provided
            if not workflow_id:
                import uuid

                workflow_id = f"validation-{uuid.uuid4()}"

            logger.info(f"Executing validation workflow: {workflow_id}")

            # Start workflow
            assert self.client is not None
            handle = await self.client.start_workflow(
                TestWorkflow.run,
                id=workflow_id,
                task_queue=self.config.task_queue,
                execution_timeout=timedelta(seconds=execution_timeout),
            )

            # Wait for workflow to complete
            workflow_result = await handle.result()

            # Calculate total duration
            end_time = asyncio.get_event_loop().time()
            total_duration_ms = (end_time - start_time) * 1000

            # Create success result
            result = ValidationResult(
                success=workflow_result.success,
                workflow_result=workflow_result,
                connection_successful=True,
                workflow_id=workflow_id,
                run_id=handle.first_execution_run_id,
                duration_ms=total_duration_ms,
            )

            logger.info(f"Validation completed: {workflow_result.summary}")
            return result

        except WorkflowFailureError as e:
            logger.error(f"Workflow execution failed: {e}")
            end_time = asyncio.get_event_loop().time()
            return ValidationResult(
                success=False,
                connection_successful=True,
                workflow_id=workflow_id,
                error=f"Workflow failed: {e}",
                duration_ms=(end_time - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            end_time = asyncio.get_event_loop().time()
            return ValidationResult(
                success=False,
                connection_successful=True,
                workflow_id=workflow_id,
                error=f"Validation error: {e}",
                duration_ms=(end_time - start_time) * 1000,
            )

        finally:
            # Clean up worker
            if self.worker:
                worker_task.cancel()
                with suppress(asyncio.CancelledError):
                    await worker_task

    async def query_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Query the status of a running validation workflow.

        Args:
            workflow_id: ID of the workflow to query

        Returns:
            Current stage information or None if query fails
        """
        if not self.client:
            logger.error("Cannot query workflow: client not connected")
            return None

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            current_stage: dict[str, Any] = await handle.query("get_current_stage")
            return current_stage

        except Exception as e:
            logger.error(f"Failed to query workflow status: {e}")
            return None

    async def get_stage_results(self, workflow_id: str) -> list[dict[str, Any]] | None:
        """Get completed stage results from a running workflow.

        Args:
            workflow_id: ID of the workflow to query

        Returns:
            List of completed stage results or None if query fails
        """
        if not self.client:
            logger.error("Cannot get stage results: client not connected")
            return None

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            stage_results: list[dict[str, Any]] = await handle.query("get_stage_results")
            return stage_results

        except Exception as e:
            logger.error(f"Failed to get stage results: {e}")
            return None

    async def close(self) -> None:
        """Close connection to Temporal server and clean up resources."""
        if self.client:
            logger.info("Closing Temporal client connection")
            # Client closes automatically on context exit
            self.client = None
            self.worker = None

    async def __aenter__(self) -> TestRunner:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with cleanup."""
        await self.close()


async def run_deployment_validation(
    temporal_host: str = "localhost",
    temporal_port: int = 7233,
    namespace: str = "default",
    verbose: bool = False,
) -> ValidationResult:
    """Convenience function to run deployment validation.

    This is a simplified interface for running validation without managing
    the TestRunner lifecycle manually.

    Args:
        temporal_host: Temporal server hostname
        temporal_port: Temporal server port
        namespace: Temporal namespace
        verbose: Enable verbose logging

    Returns:
        ValidationResult with validation outcome

    Example:
        >>> result = await run_deployment_validation()
        >>> if result.success:
        ...     print("Deployment validated!")
    """
    async with TestRunner(
        temporal_host=temporal_host,
        temporal_port=temporal_port,
        namespace=namespace,
        verbose=verbose,
    ) as runner:
        return await runner.run_validation()
