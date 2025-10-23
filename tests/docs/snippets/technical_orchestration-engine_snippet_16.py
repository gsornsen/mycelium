# Source: technical/orchestration-engine.md
# Line: 426
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.coordination import HandoffProtocol

message = HandoffProtocol.create_handoff(
    source_agent_id="agent-1",
    source_agent_type="parser",
    target_agent_id="agent-2",
    target_agent_type="analyzer",
    task_description="Analyze parsed code",
    workflow_id=workflow_id,
)

# Validate
HandoffProtocol.validate(message)

# Serialize
json_str = HandoffProtocol.serialize(message)

# Deserialize
restored = HandoffProtocol.deserialize(json_str)
