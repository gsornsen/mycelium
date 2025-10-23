# Source: technical/orchestration-engine.md
# Line: 725
# Valid syntax: False
# Has imports: False
# Has assignments: False

# Syntax error: expected ':' (<unknown>, line 6)

class StateManager:
    def __init__(
        self,
        pool: Optional[Pool] = None,
        connection_string: Optional[str] = None,
    )

    async def initialize() -> None
    async def close() -> None

    async def create_workflow(
        self,
        workflow_id: Optional[str] = None,
        tasks: Optional[List[TaskState]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState

    async def get_workflow(self, workflow_id: str) -> WorkflowState
    async def update_workflow(self, state: WorkflowState) -> WorkflowState
    async def update_task(
        self,
        workflow_id: str,
        task_id: str,
        status: Optional[TaskStatus] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
    ) -> WorkflowState

    async def rollback_workflow(self, workflow_id: str, version: int) -> WorkflowState
    async def delete_workflow(self, workflow_id: str) -> None
    async def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
    ) -> List[WorkflowState]