# Dual-Mode Coordination Pattern

This document defines the dual-mode coordination pattern used across Claude Code projects: Redis/TaskQueue preferred, markdown fallback.

## Overview

Claude Code agents need to coordinate complex, multi-step workflows. This pattern provides two coordination modes:

1. **Preferred: Redis/TaskQueue MCP** - Real-time, durable, distributed coordination
2. **Fallback: Markdown Files** - Ephemeral, filesystem-based coordination

## Design Principles

### 1. Auto-Detection

Always detect available coordination infrastructure before choosing a mode:

```bash
# Bash detection pattern
COORDINATION_MODE="unknown"

if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null 2>&1; then
    COORDINATION_MODE="redis"
elif command -v npx &> /dev/null; then
    if npx -y taskqueue-mcp --version &> /dev/null 2>&1; then
        COORDINATION_MODE="taskqueue"
    fi
fi

if [ "$COORDINATION_MODE" = "unknown" ]; then
    COORDINATION_MODE="markdown"
    mkdir -p .claude/coordination/
fi
```

```javascript
// JavaScript detection pattern
async function detectCoordinationMode() {
  // Try Redis first
  try {
    await mcp__RedisMCPServer__ping();
    return 'redis';
  } catch (e) {
    // Redis not available
  }

  // Try TaskQueue
  try {
    await mcp__taskqueue__list_projects();
    return 'taskqueue';
  } catch (e) {
    // TaskQueue not available
  }

  // Fallback to markdown
  return 'markdown';
}
```

### 2. Graceful Degradation

Each coordination mode provides the same logical operations with different implementations:

| Operation | Redis MCP | TaskQueue MCP | Markdown Fallback |
|-----------|-----------|---------------|-------------------|
| Store state | `json_set()` | Create task metadata | Write `.md` file |
| Read state | `json_get()` | Read task | Read `.md` file |
| Update state | `json_set(path)` | Update task status | Overwrite `.md` file |
| List entities | `keys()` | `list_tasks()` | `ls *.md` |
| Publish event | `publish()` | Create task with webhook | Update `.md` + timestamp |
| Subscribe to events | `subscribe()` | Poll task status | Watch `.md` files |

### 3. Consistent Data Structures

Use the same data structures across all modes:

**Agent Status Structure**:
```json
{
  "agent_type": "ai-engineer",
  "status": "busy",
  "last_updated": "2025-10-12T14:30:00Z",
  "active_tasks": [
    {
      "task_id": "task-123",
      "title": "Train model",
      "started_at": "2025-10-12T10:00:00Z",
      "progress": 0.35
    }
  ],
  "metrics": {
    "workload_pct": 85,
    "success_rate": 1.0,
    "avg_duration_sec": 12600
  }
}
```

**Task Status Structure**:
```json
{
  "task_id": "task-123",
  "project_id": "proj-1",
  "title": "Train model on Alice dataset",
  "status": "in_progress",
  "assigned_agent": "ai-engineer",
  "created_at": "2025-10-12T09:55:00Z",
  "started_at": "2025-10-12T10:00:00Z",
  "updated_at": "2025-10-12T14:30:00Z",
  "progress": 0.35,
  "metadata": {
    "step": 3500,
    "total_steps": 10000,
    "loss": 0.42
  }
}
```

## Implementation Patterns

### Pattern 1: State Storage

**Redis Mode**:
```javascript
// Store agent status
await mcp__RedisMCPServer__json_set({
  name: "agents:status:ai-engineer",
  path: "$",
  value: agentStatus
});

// Set TTL for auto-expiry
await mcp__RedisMCPServer__expire({
  name: "agents:status:ai-engineer",
  expire_seconds: 3600  // 1 hour
});
```

**TaskQueue Mode**:
```javascript
// Store as task metadata
await mcp__taskqueue__create_task({
  projectId: "coordination",
  title: "Agent Status: ai-engineer",
  description: JSON.stringify(agentStatus),
  metadata: {
    type: "agent_status",
    agent: "ai-engineer"
  }
});
```

**Markdown Mode**:
```bash
# Store as markdown file
cat > .claude/coordination/agent-ai-engineer.md <<EOF
# Agent: ai-engineer

**Status**: BUSY
**Last Updated**: $(date -Iseconds)

## Active Tasks

- Task: train-model (proj-1)
  - Started: 2025-10-12T10:00:00Z
  - Progress: 35% (3500/10000 steps)

## Metrics

- Workload: 85%
- Success Rate: 100%
EOF
```

### Pattern 2: State Retrieval

**Redis Mode**:
```javascript
// Retrieve agent status
const status = await mcp__RedisMCPServer__json_get({
  name: "agents:status:ai-engineer",
  path: "$"
});
```

**TaskQueue Mode**:
```javascript
// Find agent status task
const tasks = await mcp__taskqueue__list_tasks({
  projectId: "coordination"
});

const agentTask = tasks.find(t =>
  t.metadata?.type === "agent_status" &&
  t.metadata?.agent === "ai-engineer"
);

const status = JSON.parse(agentTask.description);
```

**Markdown Mode**:
```bash
# Read markdown file
if [ -f ".claude/coordination/agent-ai-engineer.md" ]; then
  cat .claude/coordination/agent-ai-engineer.md

  # Check staleness
  FILE_AGE=$(($(date +%s) - $(stat -c %Y .claude/coordination/agent-ai-engineer.md)))
  if [ $FILE_AGE -gt 3600 ]; then
    echo "⚠️  Status file is stale ($(($FILE_AGE / 60)) minutes old)"
  fi
fi
```

### Pattern 3: Event Publishing

**Redis Mode**:
```javascript
// Publish event to channel
await mcp__RedisMCPServer__publish({
  channel: "training:events",
  message: JSON.stringify({
    event: "checkpoint_saved",
    workflow_id: "train-123",
    step: 3500,
    timestamp: new Date().toISOString()
  })
});

// Also store event in history
await mcp__RedisMCPServer__lpush({
  name: "events:training:history",
  value: JSON.stringify(event)
});
```

**TaskQueue Mode**:
```javascript
// Create event task
await mcp__taskqueue__create_task({
  projectId: "events",
  title: "Event: checkpoint_saved",
  description: JSON.stringify(event),
  metadata: {
    type: "event",
    channel: "training:events"
  }
});
```

**Markdown Mode**:
```bash
# Append event to log file
cat >> .claude/coordination/events-training.md <<EOF

## Event: checkpoint_saved
**Time**: $(date -Iseconds)
**Workflow**: train-123
**Step**: 3500
EOF

# Keep only recent events (last 100)
tail -100 .claude/coordination/events-training.md > \
  .claude/coordination/events-training.md.tmp
mv .claude/coordination/events-training.md.tmp \
  .claude/coordination/events-training.md
```

### Pattern 4: Listing Entities

**Redis Mode**:
```javascript
// List all agent status keys
const agentKeys = await mcp__RedisMCPServer__keys({
  pattern: "agents:status:*"
});

// Retrieve all statuses
const statuses = [];
for (const key of agentKeys) {
  const status = await mcp__RedisMCPServer__json_get({
    name: key,
    path: "$"
  });
  statuses.push(status);
}
```

**TaskQueue Mode**:
```javascript
// List all agent status tasks
const tasks = await mcp__taskqueue__list_tasks({
  projectId: "coordination"
});

const agentStatuses = tasks
  .filter(t => t.metadata?.type === "agent_status")
  .map(t => JSON.parse(t.description));
```

**Markdown Mode**:
```bash
# List all agent status files
for file in .claude/coordination/agent-*.md; do
  if [ -f "$file" ]; then
    agent_name=$(basename "$file" .md | sed 's/^agent-//')
    echo "Agent: $agent_name"

    # Extract status
    status=$(grep -oP '^\*\*Status\*\*:\s*\K\w+' "$file")
    echo "  Status: $status"

    # Check age
    age=$(($(date +%s) - $(stat -c %Y "$file")))
    echo "  Updated: $((age / 60))m ago"
    echo ""
  fi
done
```

## Advantages and Limitations

### Redis Mode

**Advantages**:
- ✅ Real-time updates via pub/sub
- ✅ Atomic operations with transactions
- ✅ TTL for automatic cleanup
- ✅ Rich data structures (JSON, hashes, lists)
- ✅ High performance (sub-millisecond latency)
- ✅ Distributed access (multiple processes/machines)

**Limitations**:
- ❌ Requires Redis server installation
- ❌ Additional infrastructure to manage
- ❌ Memory-based (need persistence configuration)
- ❌ Network dependency

**Best for**: Production systems, real-time coordination, multi-machine setups

### TaskQueue Mode

**Advantages**:
- ✅ Task-centric coordination model
- ✅ Structured task metadata
- ✅ Built-in status tracking
- ✅ Integration with MCP ecosystem
- ✅ No additional server required (uses npx)

**Limitations**:
- ❌ No pub/sub (must poll)
- ❌ Limited to task-based operations
- ❌ Slower than Redis
- ❌ Requires Node.js/npm

**Best for**: Task-driven workflows, projects already using TaskQueue MCP

### Markdown Mode

**Advantages**:
- ✅ Zero infrastructure required
- ✅ Human-readable (can edit manually)
- ✅ Version control friendly (git-trackable)
- ✅ No dependencies
- ✅ Simple to implement
- ✅ Cross-platform (just filesystem)

**Limitations**:
- ❌ No real-time updates (must poll files)
- ❌ Race conditions possible (concurrent writes)
- ❌ No automatic cleanup (files accumulate)
- ❌ Limited query capabilities
- ❌ Single-machine only
- ❌ Can become stale

**Best for**: Development environments, simple projects, offline work, git-tracked state

## Migration Path

Start with markdown fallback, migrate to Redis as project grows:

1. **Week 1**: Use markdown for initial development
2. **Week 2-4**: When coordination becomes complex, install Redis
3. **Week 4+**: Migrate to Redis, keep markdown as backup

Migration script:
```bash
#!/bin/bash
# Migrate markdown coordination to Redis

echo "Migrating coordination state to Redis..."

# Migrate agent statuses
for file in .claude/coordination/agent-*.md; do
  agent=$(basename "$file" .md | sed 's/^agent-//')

  # Parse markdown and create JSON
  # (simplified - would need proper parser)
  status=$(grep -oP '^\*\*Status\*\*:\s*\K\w+' "$file")

  # Store in Redis
  redis-cli SET "agents:status:$agent" "{\"status\": \"$status\"}"

  echo "  Migrated: $agent"
done

echo "Migration complete!"
```

## Testing Dual-Mode Code

Write tests that work in both modes:

```python
import pytest
from unittest.mock import patch, MagicMock

class TestCoordination:
    @pytest.fixture(params=["redis", "taskqueue", "markdown"])
    def coordination_mode(self, request):
        return request.param

    async def test_store_agent_status(self, coordination_mode):
        status = {
            "agent_type": "ai-engineer",
            "status": "busy",
            "last_updated": "2025-10-12T14:30:00Z"
        }

        if coordination_mode == "redis":
            # Test Redis path
            with patch("mcp__RedisMCPServer__json_set") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called

        elif coordination_mode == "taskqueue":
            # Test TaskQueue path
            with patch("mcp__taskqueue__create_task") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called

        elif coordination_mode == "markdown":
            # Test markdown path
            with patch("builtins.open") as mock:
                await store_agent_status("ai-engineer", status)
                assert mock.called
```

## Best Practices

1. **Always auto-detect** - Don't hardcode coordination mode
2. **Fail gracefully** - Fallback to markdown if preferred mode unavailable
3. **Use consistent structures** - Same JSON schema across all modes
4. **Clean up stale data** - Implement TTLs or periodic cleanup
5. **Document mode choice** - Log which coordination mode is active
6. **Test all modes** - Use parameterized tests
7. **Version data structures** - Include schema version in stored data
8. **Handle concurrency** - Use locks in markdown mode
9. **Monitor coordination health** - Track success/failure rates
10. **Plan migration** - Design for eventual Redis upgrade

## Example: Complete Dual-Mode Implementation

```javascript
// coordination.js - Abstraction layer

class CoordinationClient {
  constructor() {
    this.mode = null;
  }

  async initialize() {
    // Auto-detect mode
    try {
      await mcp__RedisMCPServer__ping();
      this.mode = 'redis';
      console.log('Coordination mode: Redis (preferred)');
    } catch (e) {
      try {
        await mcp__taskqueue__list_projects();
        this.mode = 'taskqueue';
        console.log('Coordination mode: TaskQueue');
      } catch (e) {
        this.mode = 'markdown';
        console.log('Coordination mode: Markdown (fallback)');
      }
    }
  }

  async storeAgentStatus(agent, status) {
    switch (this.mode) {
      case 'redis':
        return this._storeRedis(agent, status);
      case 'taskqueue':
        return this._storeTaskQueue(agent, status);
      case 'markdown':
        return this._storeMarkdown(agent, status);
    }
  }

  async _storeRedis(agent, status) {
    await mcp__RedisMCPServer__json_set({
      name: `agents:status:${agent}`,
      path: "$",
      value: status
    });
  }

  async _storeTaskQueue(agent, status) {
    await mcp__taskqueue__create_task({
      projectId: "coordination",
      title: `Agent Status: ${agent}`,
      description: JSON.stringify(status)
    });
  }

  async _storeMarkdown(agent, status) {
    const fs = require('fs').promises;
    await fs.mkdir('.claude/coordination', { recursive: true });
    await fs.writeFile(
      `.claude/coordination/agent-${agent}.md`,
      `# Agent: ${agent}\n\nStatus: ${status.status}\n` +
      `Updated: ${status.last_updated}\n`
    );
  }
}

// Usage
const client = new CoordinationClient();
await client.initialize();
await client.storeAgentStatus('ai-engineer', {
  status: 'busy',
  last_updated: new Date().toISOString()
});
```

## Related Documentation

- [Redis MCP Integration](./redis-mcp-integration.md) - Redis-specific patterns
- [TaskQueue Coordination](./taskqueue-coordination.md) - TaskQueue-specific patterns
- [Markdown State Management](./markdown-state.md) - Markdown file patterns
- [Agent Coordination Overview](./agent-coordination-overview.md) - High-level coordination

---

**Maintained by**: Claude Code Extensibility Team
**Last Updated**: 2025-10-12
