# Source: guides/coordination-best-practices.md
# Line: 568
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Reuse discovered agents
async def code_review_pipeline(files):
    # Discover agents once
    reviewer = discover_agents("code review", limit=1)["agents"][0]
    security = discover_agents("security audit", limit=1)["agents"][0]

    # Reuse for multiple files
    results = []
    for file in files:
        workflow = coordinate_workflow(
            steps=[
                {"agent": reviewer["id"], "task": f"Review {file}"},
                {
                    "agent": security["id"],
                    "task": f"Security scan {file}",
                    "depends_on": ["step-0"]
                }
            ]
        )
        results.append(workflow)

    return results

# ❌ BAD: Rediscover agents for each file
async def code_review_pipeline(files):
    results = []
    for file in files:
        # Wasteful rediscovery
        reviewer = discover_agents("code review")["agents"][0]
        security = discover_agents("security audit")["agents"][0]

        workflow = coordinate_workflow(
            steps=[
                {"agent": reviewer["id"], "task": f"Review {file}"},
                {"agent": security["id"], "task": f"Security scan {file}"}
            ]
        )
        results.append(workflow)
