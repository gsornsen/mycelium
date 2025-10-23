# Source: troubleshooting/discovery-coordination.md
# Line: 67
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Broaden query
# Instead of: "PostgreSQL 15.2 pg_stat_statements performance tuning"
# Try: "database optimization" or "PostgreSQL performance"

# Solution 2: Lower threshold
result = discover_agents(query="your query", threshold=0.4)

# Solution 3: Reload registry
from plugins.mycelium_core.agent_discovery import reload_registry

reload_registry()

# Solution 4: Check API configuration
import os

print(f"Discovery API URL: {os.getenv('DISCOVERY_API_URL')}")
# Default should be: http://localhost:8000
