# Source: guides/discovery-coordination-quickstart.md
# Line: 333
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Sequential workflow (one after another)
workflow = coordinate_workflow(
    steps=[step1, step2, step3],
    execution_mode="sequential"
)

# Parallel workflow (independent tasks)
workflow = coordinate_workflow(
    steps=[task_a, task_b, task_c, merge_step],
    execution_mode="parallel"
)

# Explicit handoff
result = handoff_to_agent(
    target_agent="specialist-id",
    task="specific task",
    context={"relevant": "data"}
)

# Check status
status = get_workflow_status(workflow_id)

# Review history
events = get_coordination_events(workflow_id=workflow_id)