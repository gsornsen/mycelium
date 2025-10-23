# Source: troubleshooting/discovery-coordination.md
# Line: 295
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Abort and restart
from plugins.mycelium_core.coordination import abort_workflow

abort_workflow(workflow["workflow_id"], reason="Stuck, restarting")

# Restart with adjusted parameters
workflow = coordinate_workflow(
    steps=[...],
    timeout_per_step_seconds=300  # Increased timeout
)

# Solution 2: Skip problematic step
# If step is optional, mark as skipped and continue
from plugins.mycelium_core.coordination import skip_workflow_step

skip_workflow_step(
    workflow_id=workflow["workflow_id"],
    step_index=2,
    reason="Agent unavailable"
)

# Solution 3: Check agent availability
from plugins.mycelium_core.agent_discovery import check_agent_health

agent_id = status["steps"][status["current_step"]]["agent"]
agent_health = check_agent_health(agent_id)

if not agent_health["available"]:
    print(f"Agent {agent_id} is unavailable")
    # Use alternative agent
