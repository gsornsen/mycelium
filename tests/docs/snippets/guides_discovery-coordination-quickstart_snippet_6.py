# Source: guides/discovery-coordination-quickstart.md
# Line: 243
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.mcp.tools.coordination_tools import coordinate_workflow
from plugins.mycelium_core.mcp.tools.discovery_tools import discover_agents

# 1. Discover agents for each phase
design_agents = discover_agents("API design REST best practices", limit=1)
backend_agents = discover_agents("Python FastAPI development", limit=1)
db_agents = discover_agents("PostgreSQL database schema design", limit=1)
test_agents = discover_agents("API testing integration tests", limit=1)

# 2. Build workflow
workflow = coordinate_workflow(
    steps=[
        {
            "agent": design_agents["agents"][0]["id"],
            "task": "Design REST API for user management (CRUD operations)",
            "params": {
                "requirements": ["create user", "update user", "delete user", "list users"],
                "standards": "REST best practices, OpenAPI 3.0"
            }
        },
        {
            "agent": db_agents["agents"][0]["id"],
            "task": "Design database schema for user management",
            "depends_on": ["step-0"],
            "params": {
                "tables": ["users", "user_profiles"],
                "requirements": ["email uniqueness", "soft deletes"]
            }
        },
        {
            "agent": backend_agents["agents"][0]["id"],
            "task": "Implement API endpoints based on design",
            "depends_on": ["step-0", "step-1"],
            "params": {
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "include": ["validation", "error handling"]
            }
        },
        {
            "agent": test_agents["agents"][0]["id"],
            "task": "Create integration tests for API endpoints",
            "depends_on": ["step-2"],
            "params": {
                "test_framework": "pytest",
                "coverage_target": 90
            }
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# 3. Review deliverables
print("API Development Workflow Complete!")
print(f"Duration: {workflow['total_duration_ms']/1000:.1f}s")
print(f"Agents involved: {len(workflow['results'])}")
print()

for step in workflow["results"]:
    print(f"✓ {step['agent']}: {step['output']}")
