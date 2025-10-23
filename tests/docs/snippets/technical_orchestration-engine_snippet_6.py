# Source: technical/orchestration-engine.md
# Line: 180
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Tasks with no dependencies execute in parallel
tasks = [
    TaskDefinition(task_id="lint", agent_id="linter", agent_type="linter"),
    TaskDefinition(task_id="test", agent_id="tester", agent_type="tester"),
    TaskDefinition(task_id="type_check", agent_id="mypy", agent_type="type-checker"),
]

workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
