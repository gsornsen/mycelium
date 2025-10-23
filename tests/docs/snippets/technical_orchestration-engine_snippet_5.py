# Source: technical/orchestration-engine.md
# Line: 140
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.coordination import (
    StateManager,
    TaskDefinition,
    WorkflowOrchestrator,
)

# Initialize
state_manager = StateManager()
await state_manager.initialize()
orchestrator = WorkflowOrchestrator(state_manager)

# Define tasks
tasks = [
    TaskDefinition(
        task_id="parse",
        agent_id="parser-1",
        agent_type="python-parser",
    ),
    TaskDefinition(
        task_id="analyze",
        agent_id="analyzer-1",
        agent_type="code-analyzer",
        dependencies=["parse"],
    ),
    TaskDefinition(
        task_id="report",
        agent_id="reporter-1",
        agent_type="report-generator",
        dependencies=["analyze"],
    ),
]

# Create and execute
workflow_id = await orchestrator.create_workflow(tasks)
result = await orchestrator.execute_workflow(workflow_id)
