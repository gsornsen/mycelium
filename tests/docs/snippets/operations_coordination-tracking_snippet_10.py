# Source: operations/coordination-tracking.md
# Line: 301
# Valid syntax: True
# Has imports: True
# Has assignments: True

from coordination.orchestrator import WorkflowOrchestrator
from coordination.state_manager import StateManager
from coordination.tracker import CoordinationTracker

# Initialize components
state_manager = StateManager(pool=pool)
await state_manager.initialize()

tracker = CoordinationTracker(pool=pool)
await tracker.initialize()

orchestrator = WorkflowOrchestrator(state_manager)

# Orchestrator automatically generates tracking events
# You can add custom tracking in task executors:

async def my_task_executor(context):
    # Track task start
    await track_task_execution(
        tracker,
        context.workflow_id,
        context.task_def.task_id,
        context.task_def.agent_id,
        context.task_def.agent_type,
        "running",
    )

    try:
        # Execute task
        result = await do_work()

        # Track success
        await track_task_execution(
            tracker,
            context.workflow_id,
            context.task_def.task_id,
            context.task_def.agent_id,
            context.task_def.agent_type,
            "completed",
            result_summary=result["summary"],
        )

        return result

    except Exception as e:
        # Track failure
        await track_failure(
            tracker,
            context.workflow_id,
            context.task_def.task_id,
            context.task_def.agent_id,
            context.task_def.agent_type,
            type(e).__name__,
            str(e),
        )
        raise
