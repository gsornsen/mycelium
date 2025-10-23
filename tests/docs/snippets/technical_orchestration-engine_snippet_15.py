# Source: technical/orchestration-engine.md
# Line: 410
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class HandoffMessage:
    version: str
    handoff_id: str
    workflow_id: str
    source: AgentInfo
    target: AgentInfo
    context: HandoffContext
    state: HandoffState
    metadata: HandoffMetadata
    timestamp: str