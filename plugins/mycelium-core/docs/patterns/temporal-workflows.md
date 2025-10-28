# Temporal Workflow Patterns

## Overview

Temporal workflows provide durable, fault-tolerant execution for long-running ML training pipelines and multi-stage data
processing. This pattern guide covers implementing production-ready workflows with automatic state persistence,
checkpoint recovery, and distributed coordination.

**Use Cases:**

- ML model training (6-48 hour durations)
- Multi-stage data processing pipelines
- Human-in-the-loop approval workflows
- Distributed GPU training coordination
- Scheduled compute optimization

## Prerequisites

### Required Tools

- **temporal-mcp MCP server** - Workflow execution and history queries
- **RedisMCPServer** - State synchronization and metrics publishing
- **Temporal CLI** - Workflow management and debugging

### Dependencies

```python
temporalio>=1.0.0
structlog>=23.0.0
torch>=2.0.0  # For ML training examples
```

### Environment Setup

```bash
# Start Temporal server (local development)
temporal server start-dev

# Or connect to existing Temporal cluster
export TEMPORAL_HOST=temporal.example.com:7233
export TEMPORAL_NAMESPACE=mycelium
```

## Patterns

### Pattern 1: ML Training Workflow with Checkpoint Recovery

**Use Case:** Train voice cloning models with automatic checkpoint/resume on failures

**Implementation:**

```python
# File: podcast_pipeline/workflows/training_workflow.py

from temporalio import workflow
from datetime import timedelta
import structlog

logger = structlog.get_logger(__name__)

@workflow.defn
class VoiceCloneTrainingWorkflow:
    """
    Durable workflow for LoRA fine-tuning of Sesame CSM-1B.

    Execution time: 6-48 hours
    Checkpoints: Every 500 steps
    Recovery: Automatic from last checkpoint
    """

    @workflow.run
    async def run(self, training_config: TrainingConfig) -> TrainingResult:
        """
        Execute complete training pipeline with durable checkpoints.

        Args:
            training_config: Dataset path, hyperparameters, model config

        Returns:
            TrainingResult with final model path, metrics, and artifacts
        """
        workflow_id = workflow.info().workflow_id

        # Stage 1: Data Preparation (Activity - can retry on failure)
        dataset = await workflow.execute_activity(
            prepare_training_dataset,
            args=[training_config.dataset_path],
            start_to_close_timeout=timedelta(hours=1),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=10),
                backoff_coefficient=2.0,
            )
        )

        logger.info("dataset_prepared",
                   workflow_id=workflow_id,
                   num_clips=dataset.num_clips,
                   duration_hours=dataset.duration_hours)

        # Stage 2: Model Initialization (Activity - fast, retry on OOM)
        model_handle = await workflow.execute_activity(
            initialize_model,
            args=[training_config.model_config],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                maximum_attempts=5,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=1.5,
            )
        )

        # Stage 3: Training Loop (Long Activity - checkpoint every 500 steps)
        # Temporal ensures this activity can be interrupted and resumed
        training_result = await workflow.execute_activity(
            train_model_with_checkpoints,
            args=[model_handle, dataset, training_config.hyperparameters],
            start_to_close_timeout=timedelta(hours=48),  # Max training time
            heartbeat_timeout=timedelta(minutes=5),  # Must heartbeat every 5min
            retry_policy=RetryPolicy(
                maximum_attempts=10,  # Training can retry from checkpoint
                initial_interval=timedelta(minutes=1),
                backoff_coefficient=1.2,
            )
        )

        logger.info("training_completed",
                   workflow_id=workflow_id,
                   final_loss=training_result.final_loss,
                   total_steps=training_result.total_steps)

        # Stage 4: Evaluation (Activity - parallel synthesis + metrics)
        eval_metrics = await workflow.execute_activity(
            evaluate_model,
            args=[training_result.model_path, dataset.test_split],
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # Stage 5: Quality Gate - Human Approval
        # Workflow pauses here until signal received
        if training_config.require_approval:
            await workflow.wait_condition(
                lambda: self.approval_received,
                timeout=timedelta(hours=24)  # Must approve within 24h
            )

            if not self.approved:
                raise WorkflowFailureException("Model quality rejected by reviewer")

        # Stage 6: Model Deployment (Activity - copy to serving location)
        deployment_path = await workflow.execute_activity(
            deploy_model,
            args=[training_result.model_path, training_config.deployment_config],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=5)
        )

        return TrainingResult(
            model_path=deployment_path,
            metrics=eval_metrics,
            training_duration=workflow.info().run_duration,
            total_cost_usd=calculate_training_cost(training_result)
        )

    @workflow.signal
    async def approve_model(self, approved: bool, reviewer: str):
        """Signal handler for human approval gate."""
        self.approval_received = True
        self.approved = approved
        self.reviewer = reviewer
```

**Activity Implementation with Checkpoint Recovery:**

```python
# File: podcast_pipeline/workflows/training_activities.py

from temporalio import activity
import torch
from pathlib import Path

@activity.defn
async def train_model_with_checkpoints(
    model_handle: ModelHandle,
    dataset: Dataset,
    hyperparameters: Hyperparameters
) -> TrainingResult:
    """
    Training activity with checkpoint/resume support.

    Temporal guarantees:
    - Activity can be interrupted at any time (worker crash, deployment)
    - On retry, resumes from last saved checkpoint
    - Heartbeat signals activity is alive (must call every <5min)
    """
    checkpoint_dir = Path(f"checkpoints/{activity.info().workflow_id}")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing checkpoint (resume after retry)
    last_checkpoint = find_latest_checkpoint(checkpoint_dir)
    if last_checkpoint:
        logger.info("resuming_from_checkpoint",
                   checkpoint=last_checkpoint.path,
                   step=last_checkpoint.step)
        model, optimizer, scheduler, start_step = load_checkpoint(last_checkpoint)
    else:
        logger.info("starting_training_from_scratch")
        model, optimizer, scheduler = initialize_training(model_handle, hyperparameters)
        start_step = 0

    # Training loop with heartbeat
    for step in range(start_step, hyperparameters.total_steps):
        batch = dataset.get_batch(step)

        # Forward/backward pass
        loss = training_step(model, batch, optimizer, scheduler)

        # Heartbeat every 100 steps (signals activity is alive)
        if step % 100 == 0:
            activity.heartbeat({"step": step, "loss": loss})

        # Save checkpoint every 500 steps
        if step % 500 == 0:
            checkpoint_path = checkpoint_dir / f"step_{step}.pt"
            save_checkpoint(model, optimizer, scheduler, step, checkpoint_path)
            logger.info("checkpoint_saved", step=step, path=checkpoint_path)

        # Publish training metrics to Redis for real-time monitoring
        await publish_training_metrics(step, loss)

    # Final model save
    final_model_path = checkpoint_dir / "final_model.pt"
    torch.save(model.state_dict(), final_model_path)

    return TrainingResult(
        model_path=str(final_model_path),
        final_loss=loss,
        total_steps=hyperparameters.total_steps
    )
```

**Considerations:**

- **Heartbeat Frequency:** Activities >30s must heartbeat to signal liveness
- **Checkpoint Granularity:** Balance checkpoint frequency (every 500 steps) vs storage overhead
- **Timeout Settings:** Set realistic `start_to_close_timeout` for long-running activities (48 hours for training)
- **Retry Policy:** Configure exponential backoff to prevent thundering herd on transient failures

### Pattern 2: Multi-Stage Pipeline with Child Workflows

**Use Case:** Orchestrate multi-speaker podcast generation with parallel training

**Implementation:**

```python
@workflow.defn
class PodcastSynthesisPipelineWorkflow:
    """
    Parent workflow orchestrating multi-speaker podcast generation.

    Child workflows:
    1. VoiceCloneTrainingWorkflow (per speaker)
    2. ScriptProcessingWorkflow (dialogue parsing)
    3. AudioSynthesisWorkflow (multi-speaker generation)
    4. MixingWorkflow (final episode assembly)
    """

    @workflow.run
    async def run(self, podcast_config: PodcastConfig) -> PodcastEpisode:
        # Train each speaker model (parallel child workflows)
        training_tasks = []
        for speaker in podcast_config.speakers:
            child_workflow = workflow.start_child_workflow(
                VoiceCloneTrainingWorkflow.run,
                args=[speaker.training_config],
                id=f"train-{speaker.name}",
                execution_timeout=timedelta(hours=48)
            )
            training_tasks.append(child_workflow)

        # Wait for all training to complete
        speaker_models = await asyncio.gather(*training_tasks)

        logger.info("all_speakers_trained",
                   num_speakers=len(speaker_models))

        # Process script (sequential child workflow)
        dialogue = await workflow.execute_child_workflow(
            ScriptProcessingWorkflow.run,
            args=[podcast_config.script_path],
            id=f"script-{podcast_config.episode_id}"
        )

        # Synthesize audio (child workflow with speaker models)
        audio_segments = await workflow.execute_child_workflow(
            AudioSynthesisWorkflow.run,
            args=[dialogue, speaker_models],
            id=f"synthesis-{podcast_config.episode_id}"
        )

        # Mix final episode (child workflow)
        final_episode = await workflow.execute_child_workflow(
            MixingWorkflow.run,
            args=[audio_segments, podcast_config.mixing_config],
            id=f"mixing-{podcast_config.episode_id}"
        )

        return final_episode
```

**Considerations:**

- **Parallel Execution:** Use `asyncio.gather()` to run independent child workflows concurrently
- **Child Workflow IDs:** Assign deterministic IDs for idempotency and debugging
- **Execution Timeout:** Set timeout per child workflow, not globally
- **Error Propagation:** Child workflow failures propagate to parent unless explicitly caught

### Pattern 3: Saga Pattern for Distributed Training

**Use Case:** Coordinate multi-GPU training with compensating transactions

**Implementation:**

```python
@workflow.defn
class DistributedTrainingWorkflow:
    """
    Saga pattern for distributed training across multiple GPUs.

    If any GPU fails, compensate by:
    1. Releasing all GPU reservations
    2. Saving checkpoint from healthy nodes
    3. Retrying with fewer GPUs or different hardware
    """

    @workflow.run
    async def run(self, training_config: DistributedTrainingConfig):
        reserved_gpus = []

        try:
            # Reserve GPU resources (compensatable)
            for gpu_id in training_config.gpu_ids:
                gpu = await workflow.execute_activity(
                    reserve_gpu,
                    args=[gpu_id],
                    start_to_close_timeout=timedelta(minutes=5)
                )
                reserved_gpus.append(gpu)

            # Initialize distributed training (compensatable)
            dist_handle = await workflow.execute_activity(
                initialize_distributed_training,
                args=[reserved_gpus, training_config],
                start_to_close_timeout=timedelta(minutes=10)
            )

            # Execute training (main saga transaction)
            result = await workflow.execute_activity(
                run_distributed_training,
                args=[dist_handle],
                start_to_close_timeout=timedelta(hours=48),
                heartbeat_timeout=timedelta(minutes=5)
            )

            return result

        except Exception as e:
            logger.error("distributed_training_failed", error=str(e))

            # Compensation: Release all reserved GPUs
            for gpu in reserved_gpus:
                await workflow.execute_activity(
                    release_gpu,
                    args=[gpu],
                    start_to_close_timeout=timedelta(minutes=2)
                )

            # Compensation: Save checkpoint from any healthy nodes
            if dist_handle:
                await workflow.execute_activity(
                    emergency_checkpoint_save,
                    args=[dist_handle],
                    start_to_close_timeout=timedelta(minutes=10)
                )

            raise  # Re-raise to mark workflow as failed
```

**Considerations:**

- **Compensation Order:** Release resources in reverse order of acquisition
- **Partial Completion:** Save progress even when saga fails
- **Idempotency:** Ensure compensation activities are idempotent (can run multiple times safely)
- **Error Context:** Log detailed error information for post-mortem analysis

### Pattern 4: Timer-Based Scheduling

**Use Case:** Schedule training runs during off-peak GPU hours for cost optimization

**Implementation:**

```python
@workflow.defn
class ScheduledTrainingWorkflow:
    """
    Schedule training during off-peak GPU hours (2am-6am).

    Uses Temporal timers to wait until optimal time window.
    """

    @workflow.run
    async def run(self, training_config: TrainingConfig):
        # Calculate next off-peak window
        next_window = calculate_next_off_peak_window()
        now = workflow.now()

        if next_window > now:
            wait_duration = next_window - now
            logger.info("waiting_for_off_peak_window",
                       wait_hours=wait_duration.total_seconds() / 3600)

            # Temporal timer - workflow sleeps but uses no resources
            await asyncio.sleep(wait_duration.total_seconds())

        # Execute training during off-peak window
        result = await workflow.execute_child_workflow(
            VoiceCloneTrainingWorkflow.run,
            args=[training_config]
        )

        return result
```

**Considerations:**

- **Timer Precision:** Temporal timers have ~second precision, not millisecond
- **Resource Efficiency:** Sleeping workflows consume minimal resources
- **Time Zone Handling:** Use UTC internally, convert for display
- **Dynamic Scheduling:** Recalculate windows based on current system load

### Pattern 5: Continue-As-New for Iterative Training

**Use Case:** Hyperparameter sweeps with 100+ training runs without history bloat

**Implementation:**

```python
@workflow.defn
class HyperparameterSweepWorkflow:
    """
    Iterative hyperparameter tuning with continue-as-new.

    Temporal workflows have ~50KB history limit. For 100+ training runs,
    use continue-as-new to start fresh workflow with accumulated results.
    """

    @workflow.run
    async def run(self, sweep_config: SweepConfig, results: List[Result] = None):
        results = results or []

        # Train with current hyperparameters
        current_result = await workflow.execute_child_workflow(
            VoiceCloneTrainingWorkflow.run,
            args=[sweep_config.current_params]
        )
        results.append(current_result)

        # Check if sweep complete
        if sweep_config.is_complete(results):
            best_result = find_best_result(results)
            return best_result

        # Continue as new workflow with updated state
        next_config = sweep_config.next_iteration(results)
        workflow.continue_as_new(next_config, results)
```

**Considerations:**

- **History Limit:** Prevent workflows from exceeding Temporal's history size limit (~50KB)
- **State Transfer:** Only pass essential state to continue-as-new (not full history)
- **Search Termination:** Implement clear stopping criteria to prevent infinite loops
- **Result Persistence:** Store intermediate results in durable storage (Redis, database)

## Querying Workflow Execution History

**Use Case:** Retrieve complete execution details for debugging and monitoring

**Implementation:**

```javascript
// Query workflow history via Temporal MCP
const history = await mcp__temporal_mcp__GetWorkflowHistory({
  workflowId: "voice-clone-training-proj-1",
  runId: "optional-specific-run-id"  // Omit for latest run
});

// History contains every event in workflow execution:
// - WorkflowExecutionStarted
// - ActivityTaskScheduled (for each activity)
// - ActivityTaskStarted
// - ActivityTaskCompleted (or Failed/TimedOut)
// - WorkflowSignalReceived (for approval signals)
// - WorkflowExecutionCompleted

// Example: Extract training progress from activity heartbeats
const trainingHeartbeats = history.events
  .filter(e => e.eventType === "ActivityTaskHeartbeatRecorded")
  .map(e => JSON.parse(e.details));

console.log("Training progress:");
trainingHeartbeats.forEach(hb => {
  console.log(`  Step ${hb.step}: loss = ${hb.loss}`);
});

// Check if workflow is still running
const finalEvent = history.events[history.events.length - 1];
const isComplete = finalEvent.eventType === "WorkflowExecutionCompleted";
const isFailed = finalEvent.eventType === "WorkflowExecutionFailed";
```

## Temporal CLI Integration

**Use Case:** Manage workflows via command line for operations and debugging

**Common Commands:**

```javascript
// Start a new workflow execution
await Bash({
  command: `temporal workflow start \
    --workflow-id voice-clone-training-proj-1 \
    --type VoiceCloneTrainingWorkflow \
    --namespace default \
    --task-queue ml-training-queue \
    --input '${JSON.stringify(trainingConfig)}'`,
  description: "Start voice cloning training workflow"
});

// Query workflow status
const statusResult = await Bash({
  command: `temporal workflow show \
    --workflow-id voice-clone-training-proj-1 \
    --namespace default`,
  description: "Query training workflow status"
});

// Send approval signal to workflow
await Bash({
  command: `temporal workflow signal \
    --workflow-id voice-clone-training-proj-1 \
    --name approve_model \
    --input '{"approved": true, "reviewer": "human-reviewer"}'`,
  description: "Approve trained model"
});

// Cancel long-running workflow
await Bash({
  command: `temporal workflow cancel \
    --workflow-id voice-clone-training-proj-1 \
    --reason "Training taking too long, canceling to try different hyperparameters"`,
  description: "Cancel training workflow"
});
```

## Workflow Testing Strategy

**Unit Testing:**

```python
# File: tests/workflows/test_training_workflow.py

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
import pytest

@pytest.mark.asyncio
async def test_voice_clone_training_workflow():
    """Test complete training workflow execution."""
    async with await WorkflowEnvironment.start_local() as env:
        # Register workflow and activities
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[VoiceCloneTrainingWorkflow],
            activities=[
                prepare_training_dataset,
                initialize_model,
                train_model_with_checkpoints,
                evaluate_model,
                deploy_model
            ]
        )

        async with worker:
            # Execute workflow
            result = await env.client.execute_workflow(
                VoiceCloneTrainingWorkflow.run,
                args=[test_training_config],
                id="test-training-workflow",
                task_queue="test-queue"
            )

            # Verify results
            assert result.model_path.exists()
            assert result.metrics.wer < 0.07  # WER < 7%
            assert result.metrics.cer < 0.03  # CER < 3%

@pytest.mark.asyncio
async def test_training_workflow_recovery_after_failure():
    """Test workflow resumes from checkpoint after activity failure."""
    async with await WorkflowEnvironment.start_local() as env:
        # Inject failure in training activity
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[VoiceCloneTrainingWorkflow],
            activities=[training_activity_that_fails_once]
        )

        async with worker:
            # Workflow should retry and succeed
            result = await env.client.execute_workflow(
                VoiceCloneTrainingWorkflow.run,
                args=[test_training_config],
                id="test-recovery-workflow",
                task_queue="test-queue"
            )

            # Verify checkpoint recovery worked
            assert result.resumed_from_checkpoint
            assert result.checkpoint_step > 0
```

## Best Practices

1. **Always Use Heartbeats for Long Activities** - Activities >30 seconds must heartbeat to signal liveness
1. **Design Idempotent Activities** - Activities can be retried multiple times; ensure side effects are safe
1. **Use Checkpoint/Resume for GPU Training** - Save checkpoints every 500 steps, resume on activity retry
1. **Separate Fast and Slow Activities** - Don't mix quick validation (10s) with training (hours) in same activity
1. **Use Child Workflows for Modularity** - Break complex pipelines into composable child workflows
1. **Version Workflows Carefully** - Use `workflow.get_version()` for backward-compatible schema changes
1. **Set Realistic Timeouts** - Training activities need hours, not minutes; set `start_to_close_timeout` appropriately
1. **Publish Metrics to Redis** - Enable real-time monitoring without querying Temporal history repeatedly
1. **Use Signals for Human Approval** - `workflow.wait_condition()` for manual quality gates
1. **Continue-As-New for Unbounded Loops** - Prevent history bloat in hyperparameter sweeps and long experiments

## Related Agents

- **workflow-orchestrator** (`/home/gerald/git/mycelium/plugins/mycelium-core/agents/09-meta-workflow-orchestrator.md`)
  \- Coordinates multi-agent workflow execution
- **error-coordinator** - Implements retry logic and circuit breakers for workflow failures
- **performance-monitor** - Tracks workflow execution metrics and bottleneck identification
- **context-manager** - Stores workflow state in Redis for real-time access

## References

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://python.temporal.io/)
- [temporal-mcp MCP Server](https://github.com/tmcp/temporal-mcp)
- [Temporal Best Practices](https://docs.temporal.io/dev-guide/temporal-sdk-best-practices)
