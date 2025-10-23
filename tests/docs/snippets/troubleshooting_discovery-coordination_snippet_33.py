# Source: troubleshooting/discovery-coordination.md
# Line: 781
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Reuse agents instead of rediscovering
# Before (rediscover each time):
for task in tasks:
    agents = discover_agents("Python development")
    process_task(task, agents["agents"][0])

# After (discover once):
agents = discover_agents("Python development")
python_dev = agents["agents"][0]

for task in tasks:
    process_task(task, python_dev)

# Solution 2: Increase cache size
import os
os.environ["DISCOVERY_CACHE_SIZE"] = "200"  # Default: 100

# Solution 3: Warm up cache
# Pre-populate cache with common queries
common_queries = [
    "Python development",
    "database optimization",
    "security audit",
    "frontend development",
    "API design"
]

for query in common_queries:
    discover_agents(query)  # Warm cache

# Now actual queries will hit cache