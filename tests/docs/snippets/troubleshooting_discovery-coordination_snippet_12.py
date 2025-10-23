# Source: troubleshooting/discovery-coordination.md
# Line: 229
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Increase timeout
import os

os.environ["DISCOVERY_TIMEOUT_SECONDS"] = "60"

result = discover_agents("query")

# Solution 2: Check API server
# Restart API server if needed
# Check logs: tail -f logs/discovery-api.log

# Solution 3: Use cached results if available
try:
    result = discover_agents("query")
except DiscoveryTimeoutError:
    # Fallback to previously cached agents
    from plugins.mycelium_core.agent_discovery import get_cached_results
    result = get_cached_results("query")
