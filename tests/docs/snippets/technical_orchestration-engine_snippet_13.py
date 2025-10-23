# Source: technical/orchestration-engine.md
# Line: 300
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.coordination.orchestrator import TaskExecutionContext

async def my_task_executor(ctx: TaskExecutionContext) -> Dict[str, Any]:
    """
    Task executor function.

    Args:
        ctx: Execution context containing:
            - task_def: TaskDefinition
            - workflow_id: str
            - workflow_context: HandoffContext
            - previous_results: List[Dict] (from dependencies)
            - variables: Dict (workflow variables)

    Returns:
        Result dictionary to be stored in task state
    """
    # Access task definition
    task_id = ctx.task_def.task_id

    # Access results from dependencies
    for prev in ctx.previous_results:
        dep_task_id = prev["task_id"]
        dep_result = prev["result"]
        # Process dependency result

    # Access workflow variables
    config = ctx.variables.get("config", {})

    # Perform task work
    result = await perform_work(ctx)

    return {"output": result, "status": "success"}

# Register executor
orchestrator.register_executor("my-agent-type", my_task_executor)