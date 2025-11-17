"""Integration tests for Temporal test workflow execution."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import socket
import uuid
from datetime import timedelta

import pytest
from temporalio.client import Client
from temporalio.worker import Worker

from mycelium_onboarding.deployment.workflows.test_runner import TestRunner
from mycelium_onboarding.deployment.workflows.test_workflow import (
    TestWorkflow,
    execute_test_activity,
    test_error_handling_activity,
    validate_connection_activity,
    validate_state_persistence_activity,
)

logger = logging.getLogger(__name__)

TEMPORAL_HOST = "localhost"
TEMPORAL_PORT = 7233
TEMPORAL_NAMESPACE = "default"
TEST_TASK_QUEUE = "test-integration-queue"
WORKFLOW_TIMEOUT = 60


def is_temporal_available() -> bool:
    """Check if Temporal server is accessible.

    Returns True if can connect to Temporal gRPC port, False otherwise.
    This allows tests to gracefully skip when Temporal is not available.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((TEMPORAL_HOST, TEMPORAL_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False


# Skip marker for tests that require Temporal
requires_temporal = pytest.mark.skipif(
    not is_temporal_available(),
    reason=f"Temporal server not available at {TEMPORAL_HOST}:{TEMPORAL_PORT}. "
    "This is expected in CI until Tier 2 Temporal setup is implemented.",
)


@pytest.fixture
async def temporal_client() -> Client:
    """Create Temporal client connected to deployed services."""
    client = await Client.connect(
        f"{TEMPORAL_HOST}:{TEMPORAL_PORT}",
        namespace=TEMPORAL_NAMESPACE,
    )
    yield client


@pytest.fixture
async def temporal_worker(temporal_client: Client) -> Worker:
    """Create Temporal worker with test workflow and activities."""
    return Worker(
        temporal_client,
        task_queue=TEST_TASK_QUEUE,
        workflows=[TestWorkflow],
        activities=[
            validate_connection_activity,
            execute_test_activity,
            validate_state_persistence_activity,
            test_error_handling_activity,
        ],
    )


@pytest.fixture
def test_runner() -> TestRunner:
    """Create TestRunner for workflow execution."""
    return TestRunner(
        temporal_host=TEMPORAL_HOST,
        temporal_port=TEMPORAL_PORT,
        namespace=TEMPORAL_NAMESPACE,
        task_queue=TEST_TASK_QUEUE,
        verbose=True,
    )


class TestTemporalConnection:
    """Test connection to deployed Temporal services."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @requires_temporal
    async def test_can_connect_to_temporal(self) -> None:
        """Test that we can connect to Temporal at localhost:7233."""
        client = await Client.connect(
            f"{TEMPORAL_HOST}:{TEMPORAL_PORT}",
            namespace=TEMPORAL_NAMESPACE,
        )

        assert client.workflow_service is not None
        logger.info(f"Successfully connected to Temporal at {TEMPORAL_HOST}:{TEMPORAL_PORT}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @requires_temporal
    async def test_namespace_accessible(self, temporal_client: Client) -> None:
        """Test that default namespace is accessible."""
        assert temporal_client.namespace == TEMPORAL_NAMESPACE
        logger.info(f"Namespace '{TEMPORAL_NAMESPACE}' is accessible")


class TestWorkflowExecution:
    """Test actual workflow execution against deployed services."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @requires_temporal
    async def test_workflow_execution_end_to_end(self, temporal_client: Client, temporal_worker: Worker) -> None:
        """Test complete workflow execution with all 5 stages."""
        workflow_id = f"test-integration-{uuid.uuid4()}"

        worker_task = asyncio.create_task(temporal_worker.run())

        try:
            await asyncio.sleep(2)

            handle = await temporal_client.start_workflow(
                TestWorkflow.run,
                id=workflow_id,
                task_queue=TEST_TASK_QUEUE,
                execution_timeout=timedelta(seconds=WORKFLOW_TIMEOUT),
            )

            logger.info(f"Started workflow: {workflow_id}")

            result = await handle.result()

            # Check result structure
            assert result is not None
            assert hasattr(result, "success")
            assert hasattr(result, "stages")
            assert hasattr(result, "summary")

            # Validate success
            assert result.success is True
            assert len(result.stages) == 5

            # Log stage results
            for i, stage_result in enumerate(result.stages):
                status = stage_result.status
                # Handle both enum and string representations
                if isinstance(status, list):
                    status = "".join(status)
                elif hasattr(status, "value"):
                    status = status.value

                logger.info(f"Stage {i + 1}: status={status}, message={stage_result.message}")

                # Check that stage succeeded (status is 'success' as string or list)
                if isinstance(stage_result.status, list):
                    assert "".join(stage_result.status) == "success"
                else:
                    assert stage_result.status == "success" or stage_result.status.value == "success"

                assert stage_result.error is None

            assert result.total_duration_ms > 0
            logger.info(f"Workflow completed successfully in {result.total_duration_ms:.2f}ms")
            logger.info(f"Summary: {result.summary}")

        finally:
            worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker_task
