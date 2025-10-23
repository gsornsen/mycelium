# Source: guides/coordination-best-practices.md
# Line: 205
# Valid syntax: True
# Has imports: False
# Has assignments: True

# ✅ GOOD: Multi-stage discovery
async def find_optimal_team(task_description):
    # Stage 1: Find primary agent
    primary = discover_agents(task_description, limit=1)

    # Stage 2: Get primary agent's details to understand needs
    details = get_agent_details(primary["agents"][0]["id"])

    # Stage 3: Find complementary agents based on dependencies
    team = [primary["agents"][0]]
    for dependency in details["metadata"]["dependencies"]:
        agent = discover_agents(f"{dependency} specialist", limit=1)
        team.append(agent["agents"][0])

    return team

# ❌ BAD: One-shot discovery without refinement
agents = discover_agents("complex task requiring multiple specialists")
# Hope for the best with top 5 results