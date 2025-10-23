# Source: troubleshooting/discovery-coordination.md
# Line: 767
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Check cache statistics
from plugins.mycelium_core.agent_discovery import get_cache_stats

stats = get_cache_stats()
print(f"Cache Hit Rate: {stats['hit_rate']}%")
print(f"Cache Size: {stats['size']} / {stats['max_size']}")
print(f"Total Queries: {stats['total_queries']}")

# If hit_rate < 50% → Cache not being utilized effectively
