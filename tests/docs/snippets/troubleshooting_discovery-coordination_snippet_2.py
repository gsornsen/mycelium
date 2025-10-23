# Source: troubleshooting/discovery-coordination.md
# Line: 42
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Step 1: Check registry health
from plugins.mycelium_core.agent_discovery import check_discovery_health

health = check_discovery_health()
print(f"Agent Count: {health['agent_count']}")
print(f"API Status: {health['status']}")

# If agent_count == 0 → Registry not loaded
# If status != 'healthy' → API issue

# Step 2: Try broader query with lower threshold
result = discover_agents(
    query="general category",  # Broader
    threshold=0.3,  # Lower
    limit=20  # More results
)

# Step 3: Check if any agents match at all
result = discover_agents(query="agent", limit=100, threshold=0.0)
print(f"Found {len(result['agents'])} agents total")
