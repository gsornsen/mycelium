---
allowed-tools: Bash(*), Read
description: Multi-agent coordination status check. Shows agent workload, active tasks, and team health. Uses Redis/TaskQueue when available, falls back to markdown coordination files.
argument-hint: [agent-type] [--detailed]
---

# Multi-Agent Team Status

Check current workload and coordination status of Claude Code subagents.

## Context

**Command arguments**: $ARGS

**Detect coordination method**:
```bash
!`
# Check if MCP servers are available
COORDINATION_METHOD="unknown"

if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null 2>&1; then
    echo "Coordination: Redis MCP (preferred)"
    COORDINATION_METHOD="redis"
elif command -v npx &> /dev/null; then
    if npx -y taskqueue-mcp --version &> /dev/null 2>&1; then
        echo "Coordination: TaskQueue MCP (preferred)"
        COORDINATION_METHOD="taskqueue"
    fi
fi

if [ "$COORDINATION_METHOD" = "unknown" ]; then
    echo "Coordination: Markdown files (fallback)"
    COORDINATION_METHOD="markdown"

    # Check for coordination files
    if [ -d ".claude/coordination" ]; then
        echo "Found coordination directory: .claude/coordination/"
        ls -1 .claude/coordination/*.md 2>/dev/null | head -5
    else
        echo "No coordination directory found"
    fi
fi

echo "Method: $COORDINATION_METHOD"
`
```

## Your Task

Provide agent status using the best available coordination method:

### Method 1: Redis MCP (Preferred)

If Redis is available, query agent metrics:

```javascript
// Check agent workload
const agentWorkload = await mcp__RedisMCPServer__hgetall({
  name: "agents:workload"
});

// Check active tasks per agent
const agentTasks = await mcp__RedisMCPServer__hgetall({
  name: "agents:active_tasks"
});

// Check circuit breaker status
const circuitBreakers = await mcp__RedisMCPServer__hgetall({
  name: "agents:circuit-breaker"
});

// Check last heartbeat
const heartbeats = await mcp__RedisMCPServer__hgetall({
  name: "agents:heartbeat"
});
```

**Output format**:
```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

Agent Workload:
  ai-engineer         ████████░░ 85% | 2 active tasks
  data-engineer       ███░░░░░░░ 30% | 1 active task
  ml-engineer         ██████████ 100% | 3 active tasks (at capacity)
  python-pro          ████░░░░░░ 40% | 1 active task
  performance-eng     ░░░░░░░░░░ 0% | available

Circuit Breakers:
  ✅ All agents operational

Task Distribution:
  Total Active: 7 tasks
  Average Load: 51%
  Load Variance: 23% (⚠️ unbalanced)

Last Updated: 2025-10-12 14:30:00
```

### Method 2: TaskQueue MCP (Preferred)

If TaskQueue is available:

```javascript
// List all projects and tasks
const projects = await mcp__taskqueue__list_projects();

for (const project of projects) {
  const tasks = await mcp__taskqueue__list_tasks({
    projectId: project.id
  });

  // Aggregate by agent type from toolRecommendations
}
```

**Output format**:
```
=== Multi-Agent Team Status ===
Coordination Method: TaskQueue MCP

Active Projects: 3

Project: proj-1 (Voice Clone Training)
  - ai-engineer: Training model (in_progress, 4h 23m)
  - data-engineer: Processing dataset (done)

Project: proj-2 (Multi-speaker Podcast)
  - data-engineer: Processing speaker 1 (in_progress, 45m)
  - data-engineer: Processing speaker 2 (in_progress, 38m)
  - data-engineer: Processing speaker 3 (pending)

Project: proj-3 (Model Evaluation)
  - performance-eng: Running benchmarks (in_progress, 12m)

Total Active Tasks: 5
Queue Depth: 1 pending
```

### Method 3: Markdown Coordination (Fallback)

If no MCP servers available, check coordination files:

```bash
# Check for agent status files
ls -1 .claude/coordination/agent-*.md 2>/dev/null

# Read each agent status file
for agent_file in .claude/coordination/agent-*.md; do
  echo "Reading: $agent_file"
  cat "$agent_file"
done

# Check for task status files
ls -1 .claude/coordination/task-*.md 2>/dev/null

for task_file in .claude/coordination/task-*.md; do
  echo "Reading: $task_file"
  cat "$task_file"
done
```

**Markdown file format** (`.claude/coordination/agent-ai-engineer.md`):
```markdown
# Agent: ai-engineer

**Status**: BUSY
**Last Updated**: 2025-10-12T14:30:00Z

## Active Tasks

- Task: train-model (proj-1)
  - Started: 2025-10-12T10:07:00Z
  - Duration: 4h 23m
  - Status: in_progress
  - Progress: 35% (3500/10000 steps)

## Recent Completions

- Task: tune-hyperparameters (proj-3)
  - Completed: 2025-10-12T09:45:00Z
  - Duration: 2h 15m
  - Success: true

## Metrics

- Workload: 85% (high)
- Success Rate: 100%
- Average Duration: 3h 30m
```

**Output format**:
```
=== Multi-Agent Team Status ===
Coordination Method: Markdown files (fallback)

⚠️  Warning: Markdown coordination is ephemeral and may be stale.
   Consider setting up Redis or TaskQueue for real-time coordination.

Agent Status (from files):

ai-engineer: BUSY (updated 5m ago)
  - Active: train-model (4h 23m, 35% complete)

data-engineer: AVAILABLE (updated 15m ago)
  - Last task: process-dataset (completed 15m ago)

ml-engineer: BUSY (updated 2m ago)
  - Active: implement-training-loop (1h 45m)

⚠️  3 agents have no status files (may be idle or not reporting)
```

## Workload Level Indicators

- **0-30%**: 🟢 AVAILABLE - Agent has capacity for new work
- **31-70%**: 🟡 MODERATE - Agent is working but can handle more
- **71-90%**: 🟠 HIGH - Agent is busy, consider routing to others
- **91-100%**: 🔴 AT CAPACITY - No more work should be assigned

## Handling Specific Agent Queries

If user specifies an agent type (e.g., `/team-status ai-engineer`):

1. Filter results to only show that agent
2. Include detailed task breakdown
3. Show historical performance metrics
4. Display recent errors or warnings

Example:
```
=== Agent Status: ai-engineer ===

Current Status: BUSY (85% capacity)

Active Tasks (2):
  1. train-model (proj-1)
     - Started: 4h 23m ago
     - Progress: 35% (3500/10000 steps)
     - Loss: 0.42
     - ETA: 8h remaining

  2. evaluate-checkpoint (proj-3)
     - Started: 45m ago
     - Progress: 70% (evaluation phase)
     - ETA: 15m remaining

Recent History (24h):
  - Completed: 3 tasks
  - Failed: 0 tasks
  - Success Rate: 100%
  - Avg Duration: 3h 30m

Circuit Breaker: ✅ CLOSED (healthy)
Last Heartbeat: 2m ago
```

## Error Scenarios

**No coordination infrastructure**:
```
⚠️  No coordination infrastructure detected

To enable real-time agent coordination:

Option 1 (Recommended): Install Redis
  docker run -d -p 6379:6379 redis:latest

Option 2: Use TaskQueue MCP
  npm install -g taskqueue-mcp

Option 3 (Fallback): Create coordination directory
  mkdir -p .claude/coordination/
  # Agents will create status files here
```

**Stale coordination data**:
```
⚠️  Warning: Some agent status files are stale (>1h old)

Stale agents:
  - ai-engineer: last updated 2h 15m ago
  - ml-engineer: last updated 3h 42m ago

This may indicate:
  - Agents are idle and not updating status
  - Coordination files need manual cleanup
  - Agents terminated unexpectedly

Recommendation: Clear stale files or verify agent health
```

## Coordination File Management

If using markdown fallback, implement cleanup:

```bash
# Remove stale coordination files (>1 hour old)
find .claude/coordination/ -name "*.md" -type f -mmin +60 -delete

# Archive completed task files
mkdir -p .claude/coordination/archive/
find .claude/coordination/ -name "task-*.md" -type f -mtime +1 \
  -exec mv {} .claude/coordination/archive/ \;
```

## Integration with Other Commands

This command integrates with:
- `/infra-check` - Validates coordination infrastructure health
- `/workflow-status` - Shows Temporal workflow progress
- Project-specific commands - Can query task status

## Best Practices

1. **Prefer Redis/TaskQueue over markdown** for real-time coordination
2. **Update agent status regularly** (every 5-10 minutes during active work)
3. **Clean up stale coordination files** to avoid confusion
4. **Use structured formats** (JSON in Redis, YAML in markdown) for consistency
5. **Implement heartbeat mechanisms** to detect silent agent failures
6. **Set TTLs on Redis keys** to auto-expire old status data
7. **Version coordination schemas** to enable evolution over time
