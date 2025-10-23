# Source: operations/coordination-tracking.md
# Line: 258
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Get complete handoff chain for workflow
handoff_chain = await tracker.get_handoff_chain("workflow-123")

# Analyze handoff sequence
for i, handoff in enumerate(handoff_chain):
    print(f"Handoff {i+1}: {handoff.source_agent.agent_type} → {handoff.target_agent.agent_type}")
