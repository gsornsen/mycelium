# Source: guides/discovery-coordination-quickstart.md
# Line: 152
# Valid syntax: True
# Has imports: True
# Has assignments: True

from plugins.mycelium_core.mcp.tools.coordination_tools import coordinate_workflow

# Create a code review workflow
workflow = coordinate_workflow(
    steps=[
        {
            "agent": "python-pro",
            "task": "Review Python code style and best practices",
            "params": {"file": "api/endpoints.py"}
        },
        {
            "agent": "security-expert",
            "task": "Security audit focusing on injection and auth",
            "depends_on": ["step-0"],
            "params": {"file": "api/endpoints.py"}
        },
        {
            "agent": "performance-optimizer",
            "task": "Performance analysis and optimization recommendations",
            "depends_on": ["step-0"],
            "params": {"file": "api/endpoints.py"}
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

print(f"Workflow ID: {workflow['workflow_id']}")
print(f"Status: {workflow['status']}")
print(f"Completed {workflow['steps_completed']}/{workflow['steps_total']} steps")
print(f"Total Duration: {workflow['total_duration_ms']}ms")
print()

# View results
for result in workflow["results"]:
    print(f"{result['agent']}:")
    print(f"  {result['output']}")
    print(f"  (took {result['duration_ms']}ms)")
    print()

# Example output:
# Workflow ID: wf-abc-123
# Status: completed
# Completed 3/3 steps
# Total Duration: 4500ms
#
# python-pro:
#   Found 3 style issues: inconsistent naming, missing docstrings
#   (took 1200ms)
#
# security-expert:
#   Found 1 critical issue: SQL injection vulnerability in search endpoint
#   (took 1800ms)
#
# performance-optimizer:
#   Found 2 optimization opportunities: add caching, use bulk operations
#   (took 1500ms)
