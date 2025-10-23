# Source: troubleshooting/discovery-coordination.md
# Line: 949
# Valid syntax: True
# Has imports: False
# Has assignments: False

# Check detailed health
print(f"Status: {health['status']}")
print(f"Agent Count: {health['agent_count']}")
print(f"Last Updated: {health.get('last_updated', 'Unknown')}")
print(f"Errors: {health.get('errors', [])}")

# Check API logs
# tail -f logs/discovery-api.log