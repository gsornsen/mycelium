# Source: guides/discovery-coordination-quickstart.md
# Line: 481
# Valid syntax: True
# Has imports: True
# Has assignments: False

from plugins.mycelium_core.mcp.tools.discovery_tools import (
    discover_agents,
    get_agent_details
)

from plugins.mycelium_core.mcp.tools.coordination_tools import (
    coordinate_workflow,
    handoff_to_agent,
    get_workflow_status,
    get_coordination_events
)