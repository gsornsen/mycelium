# Source: troubleshooting/discovery-coordination.md
# Line: 638
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Solution 1: Parallelize independent steps
# Before (sequential):
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend", "task": "Build UI"},
        {"agent": "backend", "task": "Build API"},  # Could be parallel!
        {"agent": "database", "task": "Setup DB"},  # Could be parallel!
        {"agent": "integration", "task": "Connect all",
         "depends_on": ["step-0", "step-1", "step-2"]}
    ],
    execution_mode="sequential"
)

# After (parallel):
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend", "task": "Build UI"},
        {"agent": "backend", "task": "Build API"},
        {"agent": "database", "task": "Setup DB"},
        {"agent": "integration", "task": "Connect all",
         "depends_on": ["step-0", "step-1", "step-2"]}
    ],
    execution_mode="parallel"  # Steps 0-2 run in parallel
)

# Solution 2: Batch similar operations
# Before (multiple workflows):
for file in files:
    coordinate_workflow(steps=[
        {"agent": "analyzer", "task": f"Analyze {file}"}
    ])

# After (single batched workflow):
coordinate_workflow(steps=[
    {"agent": "analyzer", "task": "Analyze all files",
     "params": {"files": files}}
])

# Solution 3: Use faster agents
# Replace slow agent with faster alternative
agents = discover_agents("task description")
details = [get_agent_details(a["id"]) for a in agents["agents"]]

# Sort by speed
sorted_agents = sorted(
    details,
    key=lambda d: d["agent"]["avg_response_time_ms"]
)

fastest = sorted_agents[0]
print(f"Using {fastest['agent']['name']} "
      f"({fastest['agent']['avg_response_time_ms']}ms avg)")
