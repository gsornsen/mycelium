# Source: technical/orchestration-engine.md
# Line: 70
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class WorkflowState:
    workflow_id: str
    status: WorkflowStatus  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    tasks: Dict[str, TaskState]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    variables: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str]
    version: int
