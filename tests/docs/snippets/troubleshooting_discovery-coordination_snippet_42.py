# Source: troubleshooting/discovery-coordination.md
# Line: 998
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check coordination service health
from plugins.mycelium_core.coordination import check_coordination_health

health = check_coordination_health()
print(f"Status: {health['status']}")
print(f"Active Workflows: {health.get('active_workflows', 0)}")
print(f"Queue Depth: {health.get('queue_depth', 0)}")
print(f"Errors: {health.get('errors', [])}")

# If queue_depth > 100 → Service overloaded
# If active_workflows > 50 → At capacity