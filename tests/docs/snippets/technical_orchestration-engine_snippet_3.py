# Source: technical/orchestration-engine.md
# Line: 110
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class TaskDefinition:
    task_id: str
    agent_id: str
    agent_type: str
    dependencies: List[str] = []
    retry_policy: RetryPolicy = RetryPolicy()
    timeout: Optional[float] = None  # seconds
    allow_failure: bool = False
    metadata: Dict[str, Any] = {}