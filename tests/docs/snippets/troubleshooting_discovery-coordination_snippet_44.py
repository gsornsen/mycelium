# Source: troubleshooting/discovery-coordination.md
# Line: 1079
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Benchmark discovery performance
import time

queries = ["Python development", "database optimization", "security audit"]
latencies = []

for query in queries:
    start = time.time()
    result = discover_agents(query)
    latency = (time.time() - start) * 1000
    latencies.append(latency)
    print(f"{query}: {latency:.2f}ms")

print(f"\nP50: {sorted(latencies)[len(latencies)//2]:.2f}ms")
print(f"P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}ms")