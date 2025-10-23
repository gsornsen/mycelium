# Source: technical/orchestration-engine.md
# Line: 90
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class TaskState:
    task_id: str
    agent_id: str
    agent_type: str
    status: TaskStatus  # PENDING, READY, RUNNING, COMPLETED, FAILED, SKIPPED
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_time: Optional[float]  # milliseconds
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    retry_count: int
    dependencies: List[str]
