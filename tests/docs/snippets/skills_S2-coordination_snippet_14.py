# Source: skills/S2-coordination.md
# Line: 589
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Combined discovery + coordination pattern
async def execute_task_with_experts(task_description):
    # 1. Discover appropriate agents
    agents = await discover_agents(task_description, limit=3)

    # 2. Build workflow from discovered agents
    steps = []
    for idx, agent in enumerate(agents["agents"]):
        steps.append({
            "agent": agent["id"],
            "task": f"Handle {task_description} - your specialty",
            "depends_on": [f"step-{idx-1}"] if idx > 0 else []
        })

    # 3. Execute coordinated workflow
    workflow = await coordinate_workflow(steps)

    return workflow
