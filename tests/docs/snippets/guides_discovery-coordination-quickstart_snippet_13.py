# Source: guides/discovery-coordination-quickstart.md
# Line: 465
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Run workflow
coordinate_workflow(steps, execution_mode="sequential")

# Handoff
handoff_to_agent(target_agent, task, context={})

# Monitor
get_workflow_status(workflow_id)

# Debug
get_coordination_events(workflow_id)