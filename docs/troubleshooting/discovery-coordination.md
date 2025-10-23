# Discovery & Coordination Troubleshooting Guide

**Purpose:** Diagnose and resolve common issues with agent discovery and multi-agent coordination

**Last Updated:** 2025-10-21

---

## Quick Diagnosis Flowchart

```
Issue Type?
├── Discovery Issues → Section 1
├── Coordination Issues → Section 2
├── Performance Issues → Section 3
├── Context/Handoff Issues → Section 4
└── System Health Issues → Section 5
```

---

## Section 1: Discovery Issues

### Issue 1.1: No Agents Found

**Symptom:**
```python
result = discover_agents("my query")
# result["agents"] == []
# result["total_count"] == 0
```

**Possible Causes:**

1. **Query too specific**
2. **Confidence threshold too high**
3. **Agent registry empty or not loaded**
4. **Discovery API unreachable**

**Diagnosis:**

```python
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
```

**Solutions:**

```python
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
```

### Issue 1.2: Low Confidence Scores

**Symptom:**
```python
result = discover_agents("machine learning deployment")
# All agents have confidence < 0.5
```

**Possible Causes:**

1. **Query doesn't match agent keywords**
2. **Agent descriptions need updating**
3. **NLP model needs retraining**

**Diagnosis:**

```python
# Check what keywords agents actually have
from plugins.mycelium_core.agent_discovery import get_agent_details

for agent in result["agents"]:
    details = get_agent_details(agent["id"])
    print(f"\n{agent['name']}:")
    print(f"  Keywords: {details['agent']['keywords']}")
    print(f"  Description: {details['agent']['description'][:100]}...")
    print(f"  Confidence: {agent['confidence']}")

# Compare your query terms with agent keywords
```

**Solutions:**

```python
# Solution 1: Use agent's actual keywords
# If agent has keywords: ["ML", "model", "serving"]
# Query: "ML model serving" instead of "machine learning deployment"

# Solution 2: Try multiple query variations
queries = [
    "machine learning deployment",
    "ML model serving",
    "model inference production",
    "deploy ML models"
]

best_result = None
best_confidence = 0

for query in queries:
    result = discover_agents(query, limit=3)
    if result["agents"] and result["agents"][0]["confidence"] > best_confidence:
        best_result = result
        best_confidence = result["agents"][0]["confidence"]

print(f"Best match: {best_result['agents'][0]['name']} ({best_confidence})")

# Solution 3: Request agent description update
# File issue or update agent description to include relevant keywords
```

### Issue 1.3: Wrong Agents Returned

**Symptom:**
```python
result = discover_agents("Python backend development")
# Returns: frontend-developer, data-scientist, devops-engineer
# Expected: backend-developer, python-pro, api-designer
```

**Diagnosis:**

```python
# Check match reasons
for agent in result["agents"]:
    print(f"{agent['name']}: {agent['match_reason']}")

# Example output:
# frontend-developer: Matches keyword 'development'
# data-scientist: Matches keyword 'Python'
# devops-engineer: Matches keyword 'backend'

# The matching is too broad!
```

**Solutions:**

```python
# Solution 1: More specific query
result = discover_agents(
    query="Python backend API development REST FastAPI",
    threshold=0.7  # Higher threshold filters out weak matches
)

# Solution 2: Category filtering
result = discover_agents(
    query="Python development",
    category_filter="backend"  # Limit to backend category
)

# Solution 3: Multi-stage discovery
# Stage 1: Find primary agent
primary = discover_agents("backend development", limit=1)

# Stage 2: Find complementary agents
details = get_agent_details(primary["agents"][0]["id"])
if "Python" in details["agent"]["capabilities"]:
    # This is right agent
    pass
else:
    # Try next agent
    pass
```

### Issue 1.4: Discovery Timeout

**Symptom:**
```python
result = discover_agents("query")
# DiscoveryTimeoutError: Request timed out after 30s
```

**Diagnosis:**

```python
# Check API health
import requests
import time

start = time.time()
try:
    response = requests.get(
        "http://localhost:8000/health",
        timeout=5
    )
    print(f"API Health: {response.json()}")
    print(f"Response Time: {(time.time() - start)*1000}ms")
except requests.exceptions.Timeout:
    print("API not responding")
except requests.exceptions.ConnectionError:
    print("Cannot connect to API")
```

**Solutions:**

```python
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
```

---

## Section 2: Coordination Issues

### Issue 2.1: Workflow Stuck "In Progress"

**Symptom:**
```python
workflow = coordinate_workflow(steps=[...])
time.sleep(60)
status = get_workflow_status(workflow["workflow_id"])
# status["status"] == "in_progress"
# No progress for extended time
```

**Diagnosis:**

```python
# Check detailed status
status = get_workflow_status(workflow["workflow_id"], include_steps=True)

print(f"Current Step: {status['current_step']}")
print(f"Steps Completed: {status['steps_completed']}/{status['steps_total']}")

# Check which step is stuck
for step in status["steps"]:
    if step["status"] == "in_progress":
        print(f"\nStuck at step {step['step']}:")
        print(f"  Agent: {step['agent']}")
        print(f"  Started: {step['started_at']}")
        print(f"  Duration so far: {calculate_duration(step['started_at'])}s")

# Check coordination events
events = get_coordination_events(
    workflow_id=workflow["workflow_id"],
    limit=50
)

# Look for errors or warnings
for event in events["events"]:
    if event["event_type"] in ["failure", "warning", "timeout"]:
        print(f"\n{event['event_type']}: {event['metadata']}")
```

**Solutions:**

```python
# Solution 1: Abort and restart
from plugins.mycelium_core.coordination import abort_workflow

abort_workflow(workflow["workflow_id"], reason="Stuck, restarting")

# Restart with adjusted parameters
workflow = coordinate_workflow(
    steps=[...],
    timeout_per_step_seconds=300  # Increased timeout
)

# Solution 2: Skip problematic step
# If step is optional, mark as skipped and continue
from plugins.mycelium_core.coordination import skip_workflow_step

skip_workflow_step(
    workflow_id=workflow["workflow_id"],
    step_index=2,
    reason="Agent unavailable"
)

# Solution 3: Check agent availability
from plugins.mycelium_core.agent_discovery import check_agent_health

agent_id = status["steps"][status["current_step"]]["agent"]
agent_health = check_agent_health(agent_id)

if not agent_health["available"]:
    print(f"Agent {agent_id} is unavailable")
    # Use alternative agent
```

### Issue 2.2: Workflow Fails Immediately

**Symptom:**
```python
workflow = coordinate_workflow(steps=[...])
# workflow["status"] == "failed"
# workflow["steps_completed"] == 0
```

**Diagnosis:**

```python
# Check failure reason
print(f"Status: {workflow['status']}")

# Get failure events
events = get_coordination_events(
    workflow_id=workflow["workflow_id"],
    event_type="failure"
)

for event in events["events"]:
    print(f"\nFailure at step {event['metadata']['step']}:")
    print(f"  Error: {event['metadata']['error']}")
    print(f"  Details: {event['metadata'].get('details', 'N/A')}")

# Common error types:
# - ValueError: Invalid workflow structure
# - DependencyError: Unresolved dependencies
# - ValidationError: Invalid parameters
```

**Solutions:**

```python
# Solution 1: Validate workflow before execution
def validate_workflow(steps):
    # Check required fields
    for i, step in enumerate(steps):
        if "agent" not in step:
            raise ValueError(f"Step {i} missing 'agent' field")
        if "task" not in step:
            raise ValueError(f"Step {i} missing 'task' field")

    # Check dependencies
    step_ids = {f"step-{i}" for i in range(len(steps))}
    for i, step in enumerate(steps):
        for dep in step.get("depends_on", []):
            if dep not in step_ids:
                raise ValueError(f"Step {i} has invalid dependency: {dep}")

validate_workflow(steps)  # Validate before executing
workflow = coordinate_workflow(steps=steps)

# Solution 2: Fix dependency issues
# Check for circular dependencies
def find_circular_dependencies(steps):
    # Build dependency graph
    graph = {f"step-{i}": step.get("depends_on", [])
             for i, step in enumerate(steps)}

    # Detect cycles
    visited = set()
    path = set()

    def has_cycle(node):
        if node in path:
            return True
        if node in visited:
            return False

        visited.add(node)
        path.add(node)

        for neighbor in graph.get(node, []):
            if has_cycle(neighbor):
                return True

        path.remove(node)
        return False

    for node in graph:
        if has_cycle(node):
            return True

    return False

if find_circular_dependencies(steps):
    print("Circular dependency detected!")
    # Fix dependencies before retrying

# Solution 3: Simplify workflow
# Start with minimal workflow and add steps incrementally
workflow = coordinate_workflow(
    steps=[steps[0]]  # Just first step
)

if workflow["status"] == "completed":
    # First step works, add second
    workflow = coordinate_workflow(
        steps=[steps[0], steps[1]]
    )
    # Continue adding steps
```

### Issue 2.3: Context Not Preserved in Handoff

**Symptom:**
```python
result = handoff_to_agent(
    target_agent="security-expert",
    task="Review auth.py",
    context={"file": "auth.py", "issues": [...]}
)
# result["context_preserved"] == False
# Or target agent doesn't have expected information
```

**Diagnosis:**

```python
# Check handoff events
events = get_coordination_events(event_type="handoff", limit=10)

for event in events["events"]:
    if not event["metadata"].get("context_preserved", True):
        print(f"\nHandoff failed to preserve context:")
        print(f"  Source: {event['source_agent']}")
        print(f"  Target: {event['target_agent']}")
        print(f"  Reason: {event['metadata'].get('failure_reason', 'Unknown')}")
        print(f"  Context Size: {event['metadata'].get('context_size_bytes', 0)} bytes")

# Common issues:
# - Context too large (>1MB)
# - Context contains non-serializable objects
# - Context schema mismatch
```

**Solutions:**

```python
# Solution 1: Reduce context size
# Instead of embedding large data:
context = {
    "full_codebase": read_all_files(),  # Too large!
    "git_history": get_git_log()  # Too large!
}

# Use references:
context = {
    "files": ["auth.py", "models/user.py"],  # File paths only
    "summary": "Authentication system with JWT tokens",
    "known_issues": [
        {"type": "security", "file": "auth.py", "line": 42}
    ]
}

# Solution 2: Validate context is serializable
import json

try:
    json.dumps(context)  # Will fail if not serializable
except TypeError as e:
    print(f"Context not serializable: {e}")
    # Fix non-serializable objects

# Solution 3: Use schema validation
from jsonschema import validate, ValidationError

HANDOFF_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "metadata": {"type": "object"}
    },
    "additionalProperties": False
}

try:
    validate(instance=context, schema=HANDOFF_CONTEXT_SCHEMA)
except ValidationError as e:
    print(f"Invalid context schema: {e}")

# Solution 4: Check handoff result
result = handoff_to_agent(
    target_agent="security-expert",
    task="Review auth.py",
    context=context
)

if not result.get("context_preserved", False):
    print(f"Warning: Context not fully preserved")
    print(f"Reason: {result.get('preservation_status', {})}")
    # Retry with reduced context or different format
```

### Issue 2.4: Handoff Timeout

**Symptom:**
```python
result = handoff_to_agent(target_agent="slow-agent", task="complex task")
# HandoffTimeoutError: Handoff did not complete within 30s
```

**Diagnosis:**

```python
# Check agent performance history
from plugins.mycelium_core.agent_discovery import get_agent_details

details = get_agent_details("slow-agent")
print(f"Average Response Time: {details['agent']['avg_response_time_ms']}ms")

# If avg_response_time_ms > 10000 → Agent is consistently slow

# Check recent handoffs
events = get_coordination_events(
    agent_id="slow-agent",
    event_type="handoff",
    limit=20
)

durations = [e["metadata"]["duration_ms"] for e in events["events"]]
print(f"Handoff durations: p50={percentile(durations, 50)}ms, "
      f"p95={percentile(durations, 95)}ms")
```

**Solutions:**

```python
# Solution 1: Increase timeout
result = handoff_to_agent(
    target_agent="slow-agent",
    task="complex task",
    timeout_seconds=120  # Increased timeout
)

# Solution 2: Async handoff (don't wait)
result = handoff_to_agent(
    target_agent="slow-agent",
    task="complex task",
    wait_for_completion=False  # Returns immediately
)

# Check status later
handoff_id = result["handoff_id"]
time.sleep(60)
status = get_handoff_status(handoff_id)

# Solution 3: Use faster alternative agent
agents = discover_agents("task description", limit=5)

# Filter by response time
fast_agents = [
    a for a in agents["agents"]
    if get_agent_details(a["id"])["agent"]["avg_response_time_ms"] < 5000
]

result = handoff_to_agent(
    target_agent=fast_agents[0]["id"],
    task="complex task"
)
```

---

## Section 3: Performance Issues

### Issue 3.1: Slow Workflow Execution

**Symptom:**
```python
workflow = coordinate_workflow(steps=[...])
# workflow["total_duration_ms"] > expected
# P95 latency exceeds targets
```

**Diagnosis:**

```python
# Analyze workflow performance
workflow_id = workflow["workflow_id"]

# Get detailed timing
events = get_coordination_events(workflow_id=workflow_id)

# Calculate overhead
total_time = workflow["total_duration_ms"]
agent_time = sum(r["duration_ms"] for r in workflow["results"])
coordination_overhead = total_time - agent_time

print(f"Total Time: {total_time}ms")
print(f"Agent Time: {agent_time}ms")
print(f"Coordination Overhead: {coordination_overhead}ms "
      f"({(coordination_overhead/total_time)*100:.1f}%)")

# Breakdown by step
for result in workflow["results"]:
    print(f"\nStep {result['step']}: {result['agent']}")
    print(f"  Duration: {result['duration_ms']}ms")
    print(f"  % of Total: {(result['duration_ms']/total_time)*100:.1f}%")

# Identify bottlenecks
slowest = max(workflow["results"], key=lambda r: r["duration_ms"])
print(f"\nBottleneck: {slowest['agent']} ({slowest['duration_ms']}ms)")
```

**Solutions:**

```python
# Solution 1: Parallelize independent steps
# Before (sequential):
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend", "task": "Build UI"},
        {"agent": "backend", "task": "Build API"},  # Could be parallel!
        {"agent": "database", "task": "Setup DB"},  # Could be parallel!
        {"agent": "integration", "task": "Connect all",
         "depends_on": ["step-0", "step-1", "step-2"]}
    ],
    execution_mode="sequential"
)

# After (parallel):
workflow = coordinate_workflow(
    steps=[
        {"agent": "frontend", "task": "Build UI"},
        {"agent": "backend", "task": "Build API"},
        {"agent": "database", "task": "Setup DB"},
        {"agent": "integration", "task": "Connect all",
         "depends_on": ["step-0", "step-1", "step-2"]}
    ],
    execution_mode="parallel"  # Steps 0-2 run in parallel
)

# Solution 2: Batch similar operations
# Before (multiple workflows):
for file in files:
    coordinate_workflow(steps=[
        {"agent": "analyzer", "task": f"Analyze {file}"}
    ])

# After (single batched workflow):
coordinate_workflow(steps=[
    {"agent": "analyzer", "task": "Analyze all files",
     "params": {"files": files}}
])

# Solution 3: Use faster agents
# Replace slow agent with faster alternative
agents = discover_agents("task description")
details = [get_agent_details(a["id"]) for a in agents["agents"]]

# Sort by speed
sorted_agents = sorted(
    details,
    key=lambda d: d["agent"]["avg_response_time_ms"]
)

fastest = sorted_agents[0]
print(f"Using {fastest['agent']['name']} "
      f"({fastest['agent']['avg_response_time_ms']}ms avg)")
```

### Issue 3.2: High Memory Usage

**Symptom:**
```python
# System monitoring shows high memory usage during workflows
# Memory usage > 500MB per workflow
```

**Diagnosis:**

```python
# Check workflow state size
import sys

workflow = coordinate_workflow(steps=[...])
workflow_size = sys.getsizeof(workflow)

print(f"Workflow State Size: {workflow_size / 1024 / 1024:.2f}MB")

# Check context sizes
events = get_coordination_events(workflow_id=workflow["workflow_id"])

for event in events["events"]:
    if event["event_type"] == "handoff":
        context_size = event["metadata"].get("context_size_bytes", 0)
        print(f"Handoff context: {context_size / 1024:.2f}KB")

# If context sizes > 100KB → Contexts too large
```

**Solutions:**

```python
# Solution 1: Reduce context size
# Before:
context = {
    "entire_file": read_file("large_file.txt"),  # 5MB
    "all_data": load_all_data()  # 10MB
}

# After:
context = {
    "file_path": "large_file.txt",  # Reference
    "data_summary": {
        "row_count": 10000,
        "columns": ["id", "name", "email"],
        "sample": data[:100]  # Small sample
    }
}

# Solution 2: Clear completed workflows
from plugins.mycelium_core.coordination import cleanup_workflows

# Clean up workflows older than 24 hours
cleanup_workflows(older_than_hours=24)

# Solution 3: Use workflow checkpoints
# Enable checkpointing to disk instead of keeping in memory
workflow = coordinate_workflow(
    steps=[...],
    checkpoint_to_disk=True  # Reduces memory usage
)
```

### Issue 3.3: Discovery Cache Misses

**Symptom:**
```python
# Repeated discovery calls have low cache hit rate
# Every call takes 50-100ms instead of <10ms
```

**Diagnosis:**

```python
# Check cache statistics
from plugins.mycelium_core.agent_discovery import get_cache_stats

stats = get_cache_stats()
print(f"Cache Hit Rate: {stats['hit_rate']}%")
print(f"Cache Size: {stats['size']} / {stats['max_size']}")
print(f"Total Queries: {stats['total_queries']}")

# If hit_rate < 50% → Cache not being utilized effectively
```

**Solutions:**

```python
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
```

---

## Section 4: Context & Handoff Issues

### Issue 4.1: Large Context Serialization Failure

**Symptom:**
```python
context = {"large_data": [...]}
result = handoff_to_agent("agent", "task", context=context)
# ContextSerializationError: Context too large to serialize
```

**Solutions:**

```python
# Solution 1: Use file references
# Before:
context = {
    "data": read_large_file()  # 50MB
}

# After:
context = {
    "data_path": "/path/to/large_file.txt",
    "data_format": "CSV",
    "row_count": 1000000
}

# Solution 2: Compress context
import gzip
import json
import base64

def compress_context(context):
    json_data = json.dumps(context).encode('utf-8')
    compressed = gzip.compress(json_data)
    return base64.b64encode(compressed).decode('utf-8')

def decompress_context(compressed):
    decoded = base64.b64decode(compressed.encode('utf-8'))
    decompressed = gzip.decompress(decoded)
    return json.loads(decompressed.decode('utf-8'))

# Use compressed context
compressed = compress_context(large_context)
result = handoff_to_agent(
    "agent",
    "task",
    context={"compressed_data": compressed}
)

# Solution 3: Stream large data
# Instead of passing all at once, stream in chunks
def stream_data_to_agent(agent_id, data_chunks):
    handoff_id = initiate_streaming_handoff(agent_id)

    for chunk in data_chunks:
        send_chunk(handoff_id, chunk)

    finalize_handoff(handoff_id)
```

### Issue 4.2: Context Schema Mismatch

**Symptom:**
```python
result = handoff_to_agent("agent", "task", context={"foo": "bar"})
# Agent expects different context structure
# Agent returns error or incomplete results
```

**Solutions:**

```python
# Solution 1: Validate context against schema
from jsonschema import validate, ValidationError

# Get agent's expected context schema
details = get_agent_details("security-expert")
expected_schema = details["metadata"].get("context_schema")

if expected_schema:
    try:
        validate(instance=context, schema=expected_schema)
    except ValidationError as e:
        print(f"Context validation failed: {e}")
        # Fix context structure before retrying

# Solution 2: Use standard context templates
STANDARD_CONTEXT_TEMPLATES = {
    "code_review": {
        "files": List[str],
        "focus_areas": List[str],
        "standards": str
    },
    "security_audit": {
        "files": List[str],
        "focus_areas": List[str],
        "compliance": str,
        "known_issues": List[Dict]
    },
    # ... more templates
}

# Build context from template
context = build_context_from_template(
    template="security_audit",
    files=["auth.py"],
    focus_areas=["authentication"],
    compliance="OWASP_ASVS_4.0"
)

# Solution 3: Get context example from agent
details = get_agent_details("security-expert")
context_example = details["metadata"].get("context_example")

# Use example as guide for structure
```

---

## Section 5: System Health Issues

### Issue 5.1: Discovery API Unhealthy

**Symptom:**
```python
health = check_discovery_health()
# health["status"] == "unhealthy"
```

**Diagnosis:**

```python
# Check detailed health
print(f"Status: {health['status']}")
print(f"Agent Count: {health['agent_count']}")
print(f"Last Updated: {health.get('last_updated', 'Unknown')}")
print(f"Errors: {health.get('errors', [])}")

# Check API logs
# tail -f logs/discovery-api.log
```

**Solutions:**

```python
# Solution 1: Restart API service
import subprocess
subprocess.run(["systemctl", "restart", "mycelium-discovery-api"])

# Solution 2: Reload registry
from plugins.mycelium_core.agent_discovery import reload_registry

reload_registry(force=True)

# Solution 3: Check database connection
from plugins.mycelium_core.registry import check_database_health

db_health = check_database_health()
if not db_health["connected"]:
    print(f"Database connection failed: {db_health['error']}")
    # Fix database connection

# Solution 4: Rebuild registry
from plugins.mycelium_core.registry import rebuild_registry

rebuild_registry(
    source="plugins/mycelium-core/agents/index.json"
)
```

### Issue 5.2: Coordination Service Unavailable

**Symptom:**
```python
workflow = coordinate_workflow(steps=[...])
# CoordinationServiceError: Service unavailable
```

**Diagnosis:**

```python
# Check coordination service health
from plugins.mycelium_core.coordination import check_coordination_health

health = check_coordination_health()
print(f"Status: {health['status']}")
print(f"Active Workflows: {health.get('active_workflows', 0)}")
print(f"Queue Depth: {health.get('queue_depth', 0)}")
print(f"Errors: {health.get('errors', [])}")

# If queue_depth > 100 → Service overloaded
# If active_workflows > 50 → At capacity
```

**Solutions:**

```python
# Solution 1: Wait for queue to drain
import time

while True:
    health = check_coordination_health()
    if health["queue_depth"] < 10:
        break
    print(f"Waiting for queue to drain: {health['queue_depth']} items")
    time.sleep(5)

workflow = coordinate_workflow(steps=[...])

# Solution 2: Increase service capacity
# In configuration:
# MAX_CONCURRENT_WORKFLOWS=100  # Increase from 50
# WORKER_THREADS=8  # Increase from 4

# Solution 3: Clean up stuck workflows
from plugins.mycelium_core.coordination import cleanup_stuck_workflows

cleanup_stuck_workflows(stuck_for_hours=2)

# Solution 4: Use fallback mode
# If coordination service unavailable, execute steps manually
try:
    workflow = coordinate_workflow(steps=[...])
except CoordinationServiceError:
    # Manual execution fallback
    results = []
    for step in steps:
        result = handoff_to_agent(
            step["agent"],
            step["task"],
            context=step.get("params", {})
        )
        results.append(result)
```

---

## Diagnostic Commands Reference

### Quick Health Check

```bash
# One-command system health check
python -c "
from plugins.mycelium_core.agent_discovery import check_discovery_health
from plugins.mycelium_core.coordination import check_coordination_health

discovery = check_discovery_health()
coordination = check_coordination_health()

print('=== System Health ===')
print(f'Discovery API: {discovery[\"status\"]}')
print(f'Agents: {discovery[\"agent_count\"]}')
print(f'Coordination: {coordination[\"status\"]}')
print(f'Active Workflows: {coordination[\"active_workflows\"]}')
print(f'Queue Depth: {coordination[\"queue_depth\"]}')
"
```

### Performance Benchmarking

```python
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
```

### Event Log Analysis

```python
# Analyze recent coordination events
events = get_coordination_events(limit=1000)

# Count by type
from collections import Counter
event_types = Counter(e["event_type"] for e in events["events"])
print(f"Event Types: {dict(event_types)}")

# Find failures
failures = [e for e in events["events"] if e["event_type"] == "failure"]
print(f"\nFailures: {len(failures)}")
for failure in failures[:5]:
    print(f"  {failure['timestamp']}: {failure['metadata']['error']}")

# Average handoff time
handoffs = [e for e in events["events"] if e["event_type"] == "handoff"]
avg_handoff = sum(e["metadata"]["duration_ms"] for e in handoffs) / len(handoffs)
print(f"\nAverage Handoff Time: {avg_handoff:.2f}ms")
```

---

## Getting Help

### Self-Service Resources

1. **Documentation**
   - [S1: Agent Discovery](/home/gerald/git/mycelium/docs/skills/S1-agent-discovery.md)
   - [S2: Coordination](/home/gerald/git/mycelium/docs/skills/S2-coordination.md)
   - [Quick Start Guide](/home/gerald/git/mycelium/docs/guides/discovery-coordination-quickstart.md)
   - [Best Practices](/home/gerald/git/mycelium/docs/guides/coordination-best-practices.md)

2. **Diagnostic Tools**
   - `check_discovery_health()` - Discovery system health
   - `check_coordination_health()` - Coordination system health
   - `get_coordination_events()` - Event history
   - `get_agent_details()` - Agent information

3. **Logs**
   - Discovery API: `logs/discovery-api.log`
   - Coordination: `logs/coordination.log`
   - Events: `logs/coordination-events.log`

### Escalation Path

If issues persist:

1. **Check system requirements**
   - PostgreSQL 15+ running
   - MCP server active
   - Network connectivity

2. **Collect diagnostics**
   ```bash
   python scripts/collect_diagnostics.py > diagnostics.txt
   ```

3. **Report issue**
   - Issue description
   - Error messages
   - Diagnostic output
   - Reproduction steps

---

**Last Updated:** 2025-10-21
**Version:** 1.0
