"""Unit tests for Temporal test workflow.

This module tests the TestWorkflow implementation including:
- Individual activity execution
- Stage result tracking
- Error handling
- State persistence
- Query handlers
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mycelium_onboarding.deployment.workflows.test_workflow import (
    StageResult,
    TestWorkflow,
    ValidationStage,
    ValidationStatus,
    WorkflowValidationResult,
    execute_test_activity,
    test_error_handling_activity,
    validate_connection_activity,
    validate_state_persistence_activity,
)


class TestValidationEnums:
    """Test validation stage and status enums."""

    def test_validation_stage_values(self) -> None:
        """Test ValidationStage enum has expected values."""
        assert ValidationStage.CONNECTION.value == "connection"
        assert ValidationStage.WORKFLOW_EXECUTION.value == "workflow_execution"
        assert ValidationStage.ACTIVITY_EXECUTION.value == "activity_execution"
        assert ValidationStage.STATE_PERSISTENCE.value == "state_persistence"
        assert ValidationStage.ERROR_HANDLING.value == "error_handling"

    def test_validation_status_values(self) -> None:
        """Test ValidationStatus enum has expected values."""
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.IN_PROGRESS.value == "in_progress"
        assert ValidationStatus.SUCCESS.value == "success"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.SKIPPED.value == "skipped"


class TestStageResult:
    """Test StageResult dataclass."""

    def test_stage_result_creation(self) -> None:
        """Test creating a StageResult instance."""
        result = StageResult(
            stage=ValidationStage.CONNECTION,
            status=ValidationStatus.SUCCESS,
            message="Connection successful",
            duration_ms=100.5,
        )

        assert result.stage == ValidationStage.CONNECTION
        assert result.status == ValidationStatus.SUCCESS
        assert result.message == "Connection successful"
        assert result.duration_ms == 100.5
        assert result.details is None
        assert result.error is None

    def test_stage_result_with_details(self) -> None:
        """Test StageResult with additional details."""
        details = {"connected": True, "timestamp": "2024-01-01"}
        result = StageResult(
            stage=ValidationStage.CONNECTION,
            status=ValidationStatus.SUCCESS,
            message="Connected",
            duration_ms=50.0,
            details=details,
        )

        assert result.details == details

    def test_stage_result_with_error(self) -> None:
        """Test StageResult with error information."""
        result = StageResult(
            stage=ValidationStage.CONNECTION,
            status=ValidationStatus.FAILED,
            message="Connection failed",
            duration_ms=1000.0,
            error="Connection timeout",
        )

        assert result.status == ValidationStatus.FAILED
        assert result.error == "Connection timeout"

    def test_stage_result_to_dict(self) -> None:
        """Test converting StageResult to dictionary."""
        result = StageResult(
            stage=ValidationStage.ACTIVITY_EXECUTION,
            status=ValidationStatus.SUCCESS,
            message="Activity completed",
            duration_ms=75.5,
            details={"test": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["stage"] == "activity_execution"
        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Activity completed"
        assert result_dict["duration_ms"] == 75.5
        assert result_dict["details"] == {"test": "value"}
        assert result_dict["error"] is None


class TestWorkflowValidationResult:
    """Test WorkflowValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """Test creating a WorkflowValidationResult."""
        stages = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            )
        ]

        result = WorkflowValidationResult(
            success=True,
            stages=stages,
            total_duration_ms=500.0,
            summary="All stages passed",
        )

        assert result.success is True
        assert len(result.stages) == 1
        assert result.total_duration_ms == 500.0
        assert result.summary == "All stages passed"

    def test_get_failed_stages_empty(self) -> None:
        """Test getting failed stages when all succeeded."""
        stages = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            )
        ]

        result = WorkflowValidationResult(
            success=True,
            stages=stages,
            total_duration_ms=500.0,
            summary="All passed",
        )

        failed = result.get_failed_stages()
        assert len(failed) == 0

    def test_get_failed_stages_with_failures(self) -> None:
        """Test getting failed stages when some failed."""
        stages = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            ),
            StageResult(
                stage=ValidationStage.ACTIVITY_EXECUTION,
                status=ValidationStatus.FAILED,
                message="Failed",
                duration_ms=200.0,
                error="Test error",
            ),
        ]

        result = WorkflowValidationResult(
            success=False,
            stages=stages,
            total_duration_ms=500.0,
            summary="Some failures",
        )

        failed = result.get_failed_stages()
        assert len(failed) == 1
        assert failed[0].stage == ValidationStage.ACTIVITY_EXECUTION

    def test_validation_result_to_dict(self) -> None:
        """Test converting validation result to dictionary."""
        stages = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            )
        ]

        result = WorkflowValidationResult(
            success=True,
            stages=stages,
            total_duration_ms=500.0,
            summary="Test summary",
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert len(result_dict["stages"]) == 1
        assert result_dict["total_duration_ms"] == 500.0
        assert result_dict["summary"] == "Test summary"


class TestActivities:
    """Test activity functions."""

    @pytest.mark.asyncio
    async def test_validate_connection_activity(self) -> None:
        """Test connection validation activity."""
        result = await validate_connection_activity()

        assert result["connected"] is True
        assert result["activity_execution"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_execute_test_activity(self) -> None:
        """Test activity execution with input/output."""
        test_input = "test-data"
        result = await execute_test_activity(test_input)

        assert result["input_received"] == test_input
        assert "Processed:" in result["output"]
        assert "activity_id" in result
        assert "attempt" in result

    @pytest.mark.asyncio
    async def test_validate_state_persistence_activity(self) -> None:
        """Test state persistence validation activity."""
        workflow_id = "test-workflow-123"
        test_value = 42

        result = await validate_state_persistence_activity(workflow_id, test_value)

        assert result["workflow_id"] == workflow_id
        assert result["state_persisted"] is True
        assert result["test_value_verified"] == test_value

    @pytest.mark.asyncio
    async def test_error_handling_activity_success_first_attempt(self) -> None:
        """Test error handling activity succeeding on first attempt."""
        result = await test_error_handling_activity(should_fail=False, attempt_limit=3)

        assert result["retry_tested"] is False
        assert result["attempts_made"] >= 1

    @pytest.mark.asyncio
    async def test_error_handling_activity_failure(self) -> None:
        """Test error handling activity intentional failure."""
        with pytest.raises(ValueError, match="Test failure"):
            await test_error_handling_activity(should_fail=True, attempt_limit=5)


@pytest.mark.asyncio
class TestWorkflowExecution:
    """Test TestWorkflow execution in Temporal test environment."""

    @pytest.mark.skip(reason="TODO: Fix Temporal workflow testing issues - pre-existing from Sprint 4")
    async def test_workflow_successful_execution(self) -> None:
        """Test complete workflow execution with all stages passing."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Create worker
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            ):
                # Execute workflow
                result = await env.client.execute_workflow(
                    TestWorkflow.run,
                    id="test-workflow-1",
                    task_queue="test-queue",
                    execution_timeout=timedelta(seconds=60),
                )

                # Verify results
                assert isinstance(result, WorkflowValidationResult)
                assert result.success is True
                assert len(result.stages) == 5
                assert all(stage.status == ValidationStatus.SUCCESS for stage in result.stages)
                assert result.total_duration_ms > 0

    @pytest.mark.skip(reason="TODO: Fix Temporal workflow testing issues - pre-existing from Sprint 4")
    async def test_workflow_stage_ordering(self) -> None:
        """Test that workflow stages execute in correct order."""
        async with (
            await WorkflowEnvironment.start_time_skipping() as env,
            Worker(
                env.client,
                task_queue="test-queue",
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            ),
        ):
            result = await env.client.execute_workflow(
                TestWorkflow.run,
                id="test-workflow-2",
                task_queue="test-queue",
                execution_timeout=timedelta(seconds=60),
            )

            # Verify stage order
            expected_order = [
                ValidationStage.CONNECTION,
                ValidationStage.WORKFLOW_EXECUTION,
                ValidationStage.ACTIVITY_EXECUTION,
                ValidationStage.STATE_PERSISTENCE,
                ValidationStage.ERROR_HANDLING,
            ]

            for i, stage in enumerate(result.stages):
                assert stage.stage == expected_order[i]

    async def test_workflow_query_current_stage(self) -> None:
        """Test querying current stage during execution."""
        async with (
            await WorkflowEnvironment.start_time_skipping() as env,
            Worker(
                env.client,
                task_queue="test-queue",
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            ),
        ):
            # Start workflow
            handle = await env.client.start_workflow(
                TestWorkflow.run,
                id="test-workflow-3",
                task_queue="test-queue",
                execution_timeout=timedelta(seconds=60),
            )

            # Wait for completion
            await handle.result()

            # Query current stage
            stage_info = await handle.query("get_current_stage")
            assert "current_stage" in stage_info
            assert stage_info["total_stages"] == 5
            assert stage_info["completed_stages"] == 5

    async def test_workflow_query_stage_results(self) -> None:
        """Test querying stage results during execution."""
        async with (
            await WorkflowEnvironment.start_time_skipping() as env,
            Worker(
                env.client,
                task_queue="test-queue",
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            ),
        ):
            # Start workflow
            handle = await env.client.start_workflow(
                TestWorkflow.run,
                id="test-workflow-4",
                task_queue="test-queue",
                execution_timeout=timedelta(seconds=60),
            )

            # Wait for completion
            await handle.result()

            # Query stage results
            stage_results = await handle.query("get_stage_results")
            assert isinstance(stage_results, list)
            assert len(stage_results) == 5
            assert all(isinstance(stage, dict) for stage in stage_results)


class TestWorkflowSummaryGeneration:
    """Test workflow summary generation logic."""

    def test_generate_summary_all_success(self) -> None:
        """Test summary generation when all stages succeed."""
        workflow = TestWorkflow()
        workflow.stage_results = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            ),
            StageResult(
                stage=ValidationStage.WORKFLOW_EXECUTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            ),
        ]

        summary = workflow._generate_summary(success=True)

        assert "passed successfully" in summary.lower()
        assert "2" in summary

    def test_generate_summary_with_failures(self) -> None:
        """Test summary generation when some stages fail."""
        workflow = TestWorkflow()
        workflow.stage_results = [
            StageResult(
                stage=ValidationStage.CONNECTION,
                status=ValidationStatus.SUCCESS,
                message="Success",
                duration_ms=100.0,
            ),
            StageResult(
                stage=ValidationStage.ACTIVITY_EXECUTION,
                status=ValidationStatus.FAILED,
                message="Failed",
                duration_ms=100.0,
                error="Test error",
            ),
        ]

        summary = workflow._generate_summary(success=False)

        assert "1 failures" in summary.lower() or "1 failure" in summary.lower()
        assert "1" in summary
        assert "passed" in summary.lower()


class TestWorkflowEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.skip(reason="TODO: Fix Temporal workflow testing issues - pre-existing from Sprint 4")
    @pytest.mark.asyncio
    async def test_workflow_with_activity_retry(self) -> None:
        """Test workflow handles activity retries correctly."""
        async with (
            await WorkflowEnvironment.start_time_skipping() as env,
            Worker(
                env.client,
                task_queue="test-queue",
                workflows=[TestWorkflow],
                activities=[
                    validate_connection_activity,
                    execute_test_activity,
                    validate_state_persistence_activity,
                    test_error_handling_activity,
                ],
            ),
        ):
            # Execute workflow - error handling activity will retry
            result = await env.client.execute_workflow(
                TestWorkflow.run,
                id="test-workflow-retry",
                task_queue="test-queue",
                execution_timeout=timedelta(seconds=60),
            )

            # Verify error handling stage succeeded after retries
            error_stage = next(s for s in result.stages if s.stage == ValidationStage.ERROR_HANDLING)
            assert error_stage.status == ValidationStatus.SUCCESS
