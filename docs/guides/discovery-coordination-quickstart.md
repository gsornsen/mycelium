# Discovery & Coordination Quick Start Guide

**Goal:** Get productive with agent discovery and multi-agent coordination in under 15 minutes

**Prerequisites:** M01 completed, MCP server running, Mycelium environment configured

______________________________________________________________________

## Step 1: Verify Setup (2 minutes)

### Check System Health

```bash
# Verify Mycelium is running
cd /home/gerald/git/mycelium
./bin/mycelium-switch development

# Check registry populated
python -c "
from plugins.mycelium_core.agent_discovery import check_discovery_health
health = check_discovery_health()
print(f'Agent Registry: {health[\"agent_count\"]} agents')
print(f'Discovery API: {health[\"status\"]}')
"

# Expected output:
# Agent Registry: 130+ agents
# Discovery API: healthy
```

### Verify MCP Tools Available

```bash
# List available MCP tools
python -c "
from mcp import list_tools
tools = list_tools()
discovery_tools = [t for t in tools if 'discover' in t.name or 'coordinate' in t.name]
print('\\n'.join([f'✓ {t.name}' for t in discovery_tools]))
"

# Expected tools:
# ✓ discover_agents
# ✓ get_agent_details
# ✓ coordinate_workflow
# ✓ handoff_to_agent
# ✓ get_workflow_status
# ✓ get_coordination_events
```

______________________________________________________________________

## Step 2: Agent Discovery Basics (3 minutes)

### Find an Agent for a Task

**Scenario:** You need help optimizing a slow API endpoint.

```python
from plugins.mycelium_core.mcp.tools.discovery_tools import discover_agents

# Natural language query
result = discover_agents(
    query="optimize slow API performance and reduce latency",
    limit=5
)

# View results
for agent in result["agents"]:
    print(f"{agent['name']} (confidence: {agent['confidence']})")
    print(f"  → {agent['reason']}")
    print()

# Example output:
# Performance Engineer (confidence: 0.94)
#   → Matches keywords: API, performance, latency
#
# API Designer (confidence: 0.89)
#   → Matches keywords: API, optimization
#
# Backend Developer (confidence: 0.82)
#   → Matches keywords: API
```

### Get Detailed Agent Information

```python
from plugins.mycelium_core.mcp.tools.discovery_tools import get_agent_details

# Get full details on top match
agent_id = result["agents"][0]["id"]
details = get_agent_details(agent_id)

print(f"Agent: {details['agent']['name']}")
print(f"Capabilities: {', '.join(details['agent']['capabilities'])}")
print(f"Tools: {', '.join(details['agent']['tools'])}")
print(f"Success Rate: {details['agent']['success_rate']*100}%")

# Example output:
# Agent: Performance Engineer
# Capabilities: Performance profiling, Load testing, Query optimization
# Tools: pytest-benchmark, locust, py-spy
# Success Rate: 95%
```

______________________________________________________________________

## Step 3: Simple Handoff (3 minutes)

### Hand Off Work to a Specialist

**Scenario:** You're a backend developer who needs database help.

```python
from plugins.mycelium_core.mcp.tools.coordination_tools import handoff_to_agent

# Hand off to database specialist
result = handoff_to_agent(
    target_agent="postgres-pro",
    task="Optimize slow queries in user_analytics table",
    context={
        "schema": "database/schema.sql",
        "slow_queries": [
            "SELECT * FROM user_analytics WHERE created_at > NOW() - INTERVAL '7 days'",
            "SELECT user_id, COUNT(*) FROM events GROUP BY user_id"
        ],
        "performance_targets": {
            "p95_latency_ms": 100,
            "queries_per_second": 1000
        }
    }
)

print(f"Handoff Status: {result['status']}")
print(f"Result: {result['result']['message']}")
print(f"Duration: {result['duration_ms']}ms")

# Example output:
# Handoff Status: completed
# Result: Optimized 2 slow queries - added indexes, rewrote GROUP BY
# Duration: 2300ms
```

______________________________________________________________________

## Step 4: Multi-Agent Workflow (4 minutes)

### Coordinate Multiple Agents

**Scenario:** Comprehensive code review requiring multiple specialists.

```python
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
```

### Monitor Workflow Progress

```python
from plugins.mycelium_core.mcp.tools.coordination_tools import get_workflow_status
import time

# Monitor long-running workflow
workflow_id = "wf-abc-123"

while True:
    status = get_workflow_status(workflow_id, include_steps=False)

    if status["status"] == "completed":
        print(f"\n✓ Workflow completed in {status['total_duration_ms']}ms")
        break
    elif status["status"] == "failed":
        print(f"\n✗ Workflow failed at step {status['current_step']}")
        break
    else:
        print(f"Progress: {status['progress_percent']}% (step {status['current_step']}/{status['steps_total']})")
        time.sleep(2)
```

______________________________________________________________________

## Step 5: Real-World Example (3 minutes)

### Complete Workflow: API Development

**Scenario:** Build a new REST API endpoint from scratch using multiple agents.

```python
from plugins.mycelium_core.mcp.tools.discovery_tools import discover_agents
from plugins.mycelium_core.mcp.tools.coordination_tools import coordinate_workflow

# 1. Discover agents for each phase
design_agents = discover_agents("API design REST best practices", limit=1)
backend_agents = discover_agents("Python FastAPI development", limit=1)
db_agents = discover_agents("PostgreSQL database schema design", limit=1)
test_agents = discover_agents("API testing integration tests", limit=1)

# 2. Build workflow
workflow = coordinate_workflow(
    steps=[
        {
            "agent": design_agents["agents"][0]["id"],
            "task": "Design REST API for user management (CRUD operations)",
            "params": {
                "requirements": ["create user", "update user", "delete user", "list users"],
                "standards": "REST best practices, OpenAPI 3.0"
            }
        },
        {
            "agent": db_agents["agents"][0]["id"],
            "task": "Design database schema for user management",
            "depends_on": ["step-0"],
            "params": {
                "tables": ["users", "user_profiles"],
                "requirements": ["email uniqueness", "soft deletes"]
            }
        },
        {
            "agent": backend_agents["agents"][0]["id"],
            "task": "Implement API endpoints based on design",
            "depends_on": ["step-0", "step-1"],
            "params": {
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "include": ["validation", "error handling"]
            }
        },
        {
            "agent": test_agents["agents"][0]["id"],
            "task": "Create integration tests for API endpoints",
            "depends_on": ["step-2"],
            "params": {
                "test_framework": "pytest",
                "coverage_target": 90
            }
        }
    ],
    execution_mode="sequential",
    failure_strategy="retry"
)

# 3. Review deliverables
print("API Development Workflow Complete!")
print(f"Duration: {workflow['total_duration_ms']/1000:.1f}s")
print(f"Agents involved: {len(workflow['results'])}")
print()

for step in workflow["results"]:
    print(f"✓ {step['agent']}: {step['output']}")
```

______________________________________________________________________

## Common Patterns Cheat Sheet

### Discovery Patterns

```python
# Generic search
agents = discover_agents("your task description")

# Category-specific search
agents = discover_agents(
    "database optimization",
    category_filter="infrastructure"
)

# High-confidence matches only
agents = discover_agents(
    "security audit",
    threshold=0.8,
    limit=3
)
```

### Coordination Patterns

```python
# Sequential workflow (one after another)
workflow = coordinate_workflow(
    steps=[step1, step2, step3],
    execution_mode="sequential"
)

# Parallel workflow (independent tasks)
workflow = coordinate_workflow(
    steps=[task_a, task_b, task_c, merge_step],
    execution_mode="parallel"
)

# Explicit handoff
result = handoff_to_agent(
    target_agent="specialist-id",
    task="specific task",
    context={"relevant": "data"}
)

# Check status
status = get_workflow_status(workflow_id)

# Review history
events = get_coordination_events(workflow_id=workflow_id)
```

______________________________________________________________________

## Troubleshooting

### Discovery Not Finding Agents

```python
# Problem: Empty results
result = discover_agents("very specific niche task")
# result["agents"] == []

# Solution 1: Broaden query
result = discover_agents("general category task")

# Solution 2: Lower threshold
result = discover_agents("specific task", threshold=0.4)

# Solution 3: Check all categories
result = discover_agents("task", limit=20)
```

### Workflow Stuck or Failing

```python
# Problem: Workflow not progressing
status = get_workflow_status("wf-123")
# status["status"] == "in_progress" for too long

# Solution 1: Check events
events = get_coordination_events(
    workflow_id="wf-123",
    event_type="failure"
)
for event in events["events"]:
    print(f"Error: {event['metadata']}")

# Solution 2: Verify agent availability
from plugins.mycelium_core.agent_discovery import check_discovery_health
health = check_discovery_health()

# Solution 3: Retry with different agent
# Manually abort and restart with fallback agent
```

### Context Not Preserved in Handoff

```python
# Problem: Target agent missing context
result = handoff_to_agent("agent", "task", context=large_object)
# result["context_preserved"] == False

# Solution: Use file references instead
result = handoff_to_agent(
    "agent",
    "task",
    context={
        "files": ["path/to/data.json"],  # Reference, not embed
        "summary": "key points only"  # Small, structured
    }
)
```

______________________________________________________________________

## Next Steps

### Explore Advanced Features

1. **Conditional Workflows**: Dynamic branching based on results
1. **Failure Recovery**: Fallback strategies and retry policies
1. **Event Analysis**: Use coordination events for optimization
1. **Performance Tuning**: Monitor and optimize workflow efficiency

### Read More Documentation

- [S1: Agent Discovery Documentation](/home/gerald/git/mycelium/docs/skills/S1-agent-discovery.md)
- [S2: Coordination Documentation](/home/gerald/git/mycelium/docs/skills/S2-coordination.md)
- [Coordination Best Practices](/home/gerald/git/mycelium/docs/guides/coordination-best-practices.md)
- [Troubleshooting Guide](/home/gerald/git/mycelium/docs/troubleshooting/discovery-coordination.md)

### Practice Exercises

Try these scenarios to build proficiency:

1. **Exercise 1**: Find and coordinate agents to review a codebase
1. **Exercise 2**: Build a parallel data processing workflow
1. **Exercise 3**: Create a deployment pipeline with failure recovery
1. **Exercise 4**: Analyze coordination events to optimize a workflow

______________________________________________________________________

## Quick Reference Card

### Discovery

```python
# Find agents
discover_agents(query, limit=5, threshold=0.6)

# Get details
get_agent_details(agent_id)
```

### Coordination

```python
# Run workflow
coordinate_workflow(steps, execution_mode="sequential")

# Handoff
handoff_to_agent(target_agent, task, context={})

# Monitor
get_workflow_status(workflow_id)

# Debug
get_coordination_events(workflow_id)
```

### Import Paths

```python
from plugins.mycelium_core.mcp.tools.discovery_tools import (
    discover_agents,
    get_agent_details
)

from plugins.mycelium_core.mcp.tools.coordination_tools import (
    coordinate_workflow,
    handoff_to_agent,
    get_workflow_status,
    get_coordination_events
)
```

______________________________________________________________________

**Congratulations!** You're now ready to leverage agent discovery and multi-agent coordination in your workflows.

**Time to Proficiency:** ≤ 15 minutes **Last Updated:** 2025-10-21
