# Source: skills/S2-coordination.md
# Line: 363
# Valid syntax: True
# Has imports: False
# Has assignments: True

# 1. Discover review agents
style_agent = await discover_agents("Python code style review", limit=1)
security_agent = await discover_agents("security audit", limit=1)
perf_agent = await discover_agents("performance optimization", limit=1)

# 2. Create workflow
workflow = await coordinate_workflow(
    steps=[
        {
            "agent": style_agent["agents"][0]["id"],
            "task": "Review code style, structure, and best practices",
            "params": {"file": "api/endpoints.py"}
        },
        {
            "agent": security_agent["agents"][0]["id"],
            "task": "Audit for security vulnerabilities",
            "depends_on": ["step-0"],
            "params": {
                "file": "api/endpoints.py",
                "focus": ["authentication", "injection", "validation"]
            }
        },
        {
            "agent": perf_agent["agents"][0]["id"],
            "task": "Analyze performance and suggest optimizations",
            "depends_on": ["step-0", "step-1"],
            "params": {"file": "api/endpoints.py"}
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# 3. Monitor progress
while workflow["status"] != "completed":
    status = await get_workflow_status(workflow["workflow_id"])
    print(f"Progress: {status['progress_percent']}%")
    await asyncio.sleep(2)

# 4. Review results
for result in workflow["results"]:
    print(f"{result['agent']}: {result['output']}")
