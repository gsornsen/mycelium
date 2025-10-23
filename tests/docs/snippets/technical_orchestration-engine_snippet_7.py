# Source: technical/orchestration-engine.md
# Line: 194
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Complex dependency pattern:
#     parse
#    /     \
#  analyze  validate
#    \     /
#     merge

tasks = [
    TaskDefinition(task_id="parse", agent_id="p1", agent_type="parser"),
    TaskDefinition(
        task_id="analyze",
        agent_id="a1",
        agent_type="analyzer",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="validate",
        agent_id="v1",
        agent_type="validator",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="merge",
        agent_id="m1",
        agent_type="merger",
        dependencies=["analyze", "validate"],
    ),
]

workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)