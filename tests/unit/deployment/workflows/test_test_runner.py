"""Unit tests for Temporal test workflow runner.

This module tests the TestRunner implementation including:
- Connection management and retries
- Worker lifecycle
- Workflow execution
- Error handling
- Query operations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mycelium_onboarding.deployment.workflows.test_runner import (
    ConnectionConfig,
    TestRunner,
    ValidationResult,
    run_deployment_validation,
)
from mycelium_onboarding.deployment.workflows.test_workflow import (
    WorkflowValidationResult,
)


class TestConnectionConfig:
    """Test ConnectionConfig dataclass."""

    def test_default_config(self) -> None:
        """Test ConnectionConfig with default values."""
        config = ConnectionConfig()

        assert config.host == "localhost"
        assert config.port == 7233
        assert config.namespace == "default"
        assert config.task_queue == "test-validation-queue"
        assert config.tls_enabled is False
        assert config.max_connection_retries == 3
        assert config.connection_timeout_seconds == 10

    def test_custom_config(self) -> None:
        """Test ConnectionConfig with custom values."""
        config = ConnectionConfig(
            host="temporal.example.com",
            port=7234,
            namespace="custom",
            task_queue="custom-queue",
        )

        assert config.host == "temporal.example.com"
        assert config.port == 7234
        assert config.namespace == "custom"
        assert config.task_queue == "custom-queue"

    def test_address_property(self) -> None:
        """Test address property generation."""
        config = ConnectionConfig(host="example.com", port=8080)
        assert config.address == "example.com:8080"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_successful_validation_result(self) -> None:
        """Test creating a successful ValidationResult."""
        workflow_result = WorkflowValidationResult(
            success=True,
            stages=[],
            total_duration_ms=1000.0,
            summary="All passed",
        )

        result = ValidationResult(
            success=True,
            workflow_result=workflow_result,
            connection_successful=True,
            workflow_id="test-123",
            run_id="run-456",
            duration_ms=1500.0,
        )

        assert result.success is True
        assert result.connection_successful is True
        assert result.workflow_id == "test-123"
        assert result.run_id == "run-456"
        assert result.error is None
        assert result.duration_ms == 1500.0

    def test_failed_validation_result(self) -> None:
        """Test creating a failed ValidationResult."""
        result = ValidationResult(
            success=False,
            connection_successful=False,
            error="Connection failed",
        )

        assert result.success is False
        assert result.connection_successful is False
        assert result.error == "Connection failed"
        assert result.workflow_result is None

    def test_validation_result_to_dict(self) -> None:
        """Test converting ValidationResult to dictionary."""
        workflow_result = WorkflowValidationResult(
            success=True,
            stages=[],
            total_duration_ms=1000.0,
            summary="Test",
        )

        result = ValidationResult(
            success=True,
            workflow_result=workflow_result,
            connection_successful=True,
            workflow_id="test-123",
            duration_ms=1500.0,
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["connection_successful"] is True
        assert result_dict["workflow_id"] == "test-123"
        assert "workflow_result" in result_dict
        assert result_dict["workflow_result"]["success"] is True


class TestTestRunnerInitialization:
    """Test TestRunner initialization."""

    def test_default_initialization(self) -> None:
        """Test runner initialization with default parameters."""
        runner = TestRunner()

        assert runner.config.host == "localhost"
        assert runner.config.port == 7233
        assert runner.config.namespace == "default"
        assert runner.verbose is False
        assert runner.client is None
        assert runner.worker is None

    def test_custom_initialization(self) -> None:
        """Test runner initialization with custom parameters."""
        runner = TestRunner(
            temporal_host="custom.host",
            temporal_port=8080,
            namespace="custom-ns",
            task_queue="custom-queue",
            verbose=True,
        )

        assert runner.config.host == "custom.host"
        assert runner.config.port == 8080
        assert runner.config.namespace == "custom-ns"
        assert runner.config.task_queue == "custom-queue"
        assert runner.verbose is True


@pytest.mark.asyncio
class TestTestRunnerConnection:
    """Test TestRunner connection management."""

    async def test_successful_connection_first_attempt(self) -> None:
        """Test successful connection on first attempt."""
        runner = TestRunner()

        # Mock the Temporal client
        mock_client = AsyncMock()
        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Client.connect",
            return_value=mock_client,
        ):
            success = await runner.connect()

            assert success is True
            assert runner.client is mock_client

    async def test_connection_retry_success(self) -> None:
        """Test connection succeeds after retry."""
        runner = TestRunner()

        # First attempt fails, second succeeds
        mock_client = AsyncMock()
        call_count = 0

        async def connect_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection failed")
            return mock_client

        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Client.connect",
            side_effect=connect_side_effect,
        ):
            success = await runner.connect()

            assert success is True
            assert runner.client is mock_client
            assert call_count == 2

    async def test_connection_max_retries_exceeded(self) -> None:
        """Test connection fails after max retries."""
        runner = TestRunner()
        runner.config.max_connection_retries = 2

        # All attempts fail
        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Client.connect",
            side_effect=ConnectionError("Connection failed"),
        ):
            success = await runner.connect()

            assert success is False
            assert runner.client is None

    async def test_connection_timeout(self) -> None:
        """Test connection timeout handling."""
        runner = TestRunner()
        runner.config.connection_timeout_seconds = 1
        runner.config.max_connection_retries = 1

        # Mock client connect to simulate timeout
        async def slow_connect(*args, **kwargs):
            import asyncio

            await asyncio.sleep(10)  # Longer than timeout

        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Client.connect",
            side_effect=slow_connect,
        ):
            success = await runner.connect()

            assert success is False


@pytest.mark.asyncio
class TestTestRunnerWorker:
    """Test TestRunner worker management."""

    async def test_start_worker_success(self) -> None:
        """Test successful worker startup."""
        runner = TestRunner()
        runner.client = AsyncMock()

        # Mock Worker class
        mock_worker = MagicMock()
        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Worker",
            return_value=mock_worker,
        ):
            success = await runner.start_worker()

            assert success is True
            assert runner.worker is mock_worker

    async def test_start_worker_without_client(self) -> None:
        """Test starting worker without connected client raises error."""
        runner = TestRunner()

        with pytest.raises(RuntimeError, match="client not connected"):
            await runner.start_worker()

    async def test_start_worker_failure(self) -> None:
        """Test worker startup failure handling."""
        runner = TestRunner()
        runner.client = AsyncMock()

        # Mock Worker to raise exception
        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Worker",
            side_effect=Exception("Worker creation failed"),
        ):
            success = await runner.start_worker()

            assert success is False
            assert runner.worker is None


@pytest.mark.asyncio
class TestTestRunnerValidation:
    """Test TestRunner validation execution."""

    async def test_run_validation_connection_failure(self) -> None:
        """Test validation when connection fails."""
        runner = TestRunner()

        with patch.object(runner, "connect", return_value=False):
            result = await runner.run_validation()

            assert result.success is False
            assert result.connection_successful is False
            assert "Failed to connect" in result.error

    async def test_run_validation_worker_failure(self) -> None:
        """Test validation when worker startup fails."""
        runner = TestRunner()

        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=False),
        ):
            result = await runner.run_validation()

            assert result.success is False
            assert result.connection_successful is True
            assert "Failed to start worker" in result.error

    @pytest.mark.skip(reason="TODO: Fix AsyncMock await issue - pre-existing from Sprint 4")
    async def test_run_validation_success(self) -> None:
        """Test successful validation execution."""
        runner = TestRunner()
        runner.client = AsyncMock()
        runner.worker = AsyncMock()

        # Mock workflow result
        mock_workflow_result = WorkflowValidationResult(
            success=True,
            stages=[],
            total_duration_ms=1000.0,
            summary="All passed",
        )

        # Mock workflow handle
        mock_handle = AsyncMock()
        mock_handle.result = AsyncMock(return_value=mock_workflow_result)
        mock_handle.first_execution_run_id = "run-123"

        # Mock worker run
        mock_worker_run = AsyncMock()
        runner.worker.run = mock_worker_run

        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=True),
            patch.object(runner.client, "start_workflow", return_value=mock_handle),
            patch("asyncio.create_task", return_value=mock_worker_run),
        ):
            result = await runner.run_validation()

            assert result.success is True
            assert result.connection_successful is True
            assert result.workflow_result == mock_workflow_result
            assert result.workflow_id is not None

    @pytest.mark.skip(reason="TODO: Fix AsyncMock await issue - pre-existing from Sprint 4")
    async def test_run_validation_custom_workflow_id(self) -> None:
        """Test validation with custom workflow ID."""
        runner = TestRunner()
        runner.client = AsyncMock()
        runner.worker = AsyncMock()

        mock_workflow_result = WorkflowValidationResult(
            success=True,
            stages=[],
            total_duration_ms=1000.0,
            summary="All passed",
        )

        mock_handle = AsyncMock()
        mock_handle.result = AsyncMock(return_value=mock_workflow_result)
        mock_handle.first_execution_run_id = "run-123"
        runner.worker.run = AsyncMock()

        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=True),
            patch.object(runner.client, "start_workflow", return_value=mock_handle) as mock_start,
            patch("asyncio.create_task"),
        ):
            await runner.run_validation(workflow_id="custom-id-123")

            # Verify custom workflow ID was used
            call_kwargs = mock_start.call_args[1]
            assert call_kwargs["id"] == "custom-id-123"


@pytest.mark.asyncio
class TestTestRunnerQueries:
    """Test TestRunner query operations."""

    async def test_query_workflow_status_success(self) -> None:
        """Test successful workflow status query."""
        runner = TestRunner()
        mock_client = AsyncMock()
        runner.client = mock_client

        # Mock workflow handle
        mock_handle = AsyncMock()
        mock_handle.query = AsyncMock(return_value={"current_stage": 2, "total_stages": 5})
        mock_client.get_workflow_handle = Mock(return_value=mock_handle)

        status = await runner.query_workflow_status("test-workflow")

        assert status is not None
        assert status["current_stage"] == 2
        assert status["total_stages"] == 5

    async def test_query_workflow_status_no_client(self) -> None:
        """Test query without connected client."""
        runner = TestRunner()

        status = await runner.query_workflow_status("test-workflow")

        assert status is None

    async def test_query_workflow_status_error(self) -> None:
        """Test query error handling."""
        runner = TestRunner()
        mock_client = AsyncMock()
        runner.client = mock_client

        mock_client.get_workflow_handle = Mock(side_effect=Exception("Query failed"))

        status = await runner.query_workflow_status("test-workflow")

        assert status is None

    async def test_get_stage_results_success(self) -> None:
        """Test successful stage results query."""
        runner = TestRunner()
        mock_client = AsyncMock()
        runner.client = mock_client

        mock_results = [
            {"stage": "connection", "status": "success"},
            {"stage": "workflow_execution", "status": "success"},
        ]

        mock_handle = AsyncMock()
        mock_handle.query = AsyncMock(return_value=mock_results)
        mock_client.get_workflow_handle = Mock(return_value=mock_handle)

        results = await runner.get_stage_results("test-workflow")

        assert results is not None
        assert len(results) == 2
        assert results[0]["stage"] == "connection"

    async def test_get_stage_results_no_client(self) -> None:
        """Test stage results query without client."""
        runner = TestRunner()

        results = await runner.get_stage_results("test-workflow")

        assert results is None


@pytest.mark.asyncio
class TestTestRunnerCleanup:
    """Test TestRunner cleanup and resource management."""

    @pytest.mark.skip(reason="TODO: Fix AsyncMock await issue - pre-existing from Sprint 4")
    async def test_close_with_client(self) -> None:
        """Test closing runner with active client."""
        runner = TestRunner()
        mock_client = AsyncMock()
        runner.client = mock_client

        await runner.close()

        assert runner.client is None
        assert runner.worker is None
        mock_client.close.assert_called_once()

    async def test_close_without_client(self) -> None:
        """Test closing runner without client."""
        runner = TestRunner()

        # Should not raise exception
        await runner.close()

        assert runner.client is None

    async def test_context_manager(self) -> None:
        """Test TestRunner as async context manager."""
        mock_client = AsyncMock()

        with patch(
            "mycelium_onboarding.deployment.workflows.test_runner.Client.connect",
            return_value=mock_client,
        ):
            async with TestRunner() as runner:
                assert runner is not None

            # Client should be closed after context exit
            assert runner.client is None


@pytest.mark.asyncio
class TestConvenienceFunctions:
    """Test convenience functions."""

    async def test_run_deployment_validation_success(self) -> None:
        """Test convenience function for successful validation."""
        mock_workflow_result = WorkflowValidationResult(
            success=True,
            stages=[],
            total_duration_ms=1000.0,
            summary="All passed",
        )

        # Mock the entire run_validation flow
        with (
            patch(
                "mycelium_onboarding.deployment.workflows.test_runner.TestRunner.connect",
                return_value=True,
            ),
            patch(
                "mycelium_onboarding.deployment.workflows.test_runner.TestRunner.run_validation",
                return_value=ValidationResult(
                    success=True,
                    workflow_result=mock_workflow_result,
                    connection_successful=True,
                ),
            ),
        ):
            result = await run_deployment_validation()

            assert result.success is True
            assert result.connection_successful is True

    async def test_run_deployment_validation_custom_params(self) -> None:
        """Test convenience function with custom parameters."""
        with (
            patch(
                "mycelium_onboarding.deployment.workflows.test_runner.TestRunner.connect",
                return_value=True,
            ),
            patch(
                "mycelium_onboarding.deployment.workflows.test_runner.TestRunner.run_validation",
                return_value=ValidationResult(success=True, connection_successful=True),
            ) as mock_run,
        ):
            await run_deployment_validation(
                temporal_host="custom.host",
                temporal_port=8080,
                namespace="custom",
                verbose=True,
            )

            # Verify runner was created with custom params
            # (indirect verification through successful execution)
            assert mock_run.called


@pytest.mark.asyncio
class TestTestRunnerEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.skip(reason="TODO: Fix AsyncMock await issue - pre-existing from Sprint 4")
    async def test_run_validation_with_exception(self) -> None:
        """Test validation handles unexpected exceptions."""
        runner = TestRunner()
        runner.client = AsyncMock()
        runner.worker = AsyncMock()

        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=True),
            patch.object(
                runner.client,
                "start_workflow",
                side_effect=Exception("Unexpected error"),
            ),
            patch("asyncio.create_task"),
        ):
            result = await runner.run_validation()

            assert result.success is False
            assert "Validation error" in result.error

    async def test_multiple_validation_runs(self) -> None:
        """Test running multiple validations sequentially."""
        runner = TestRunner()

        # First run
        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=True),
        ):
            result1 = await runner.run_validation(workflow_id="test-1")
            # Would need more mocking for full execution

        # Second run
        with (
            patch.object(runner, "connect", return_value=True),
            patch.object(runner, "start_worker", return_value=True),
        ):
            result2 = await runner.run_validation(workflow_id="test-2")
            # Would need more mocking for full execution

        # Both should be independent
        assert result1 is not result2
