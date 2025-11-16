---
allowed-tools: Bash(redis-cli:*), Read, Glob, mcp__RedisMCPServer__*
description: Multi-agent coordination status check. Shows agent workload, active tasks, and team health with formatted progress bars and statistics.
argument-hint: [agent-type]
---

# Multi-Agent Team Status

Check current workload and coordination status of Claude Code subagents with formatted visualization.

## Context

**Command arguments**: $ARGS

**Coordination Method**: Redis MCP with JSON serialization and datetime handling

## Your Task

Display formatted team status using Redis coordination data with proper JSON parsing:

### Implementation

1. **Parse command arguments** to determine display mode:

   - No arguments: Show overview of all agents
   - Agent type specified: Show detailed view of that agent

1. **Query Redis with JSON parsing**:

   - Get all agent statuses from `agents:status` hash
   - Get heartbeat data from `agents:heartbeat` hash
   - Parse JSON values using the pattern from RedisCoordinationHelper
   - Restore datetime fields (fields ending in `_at` or containing `timestamp`)

1. **Display formatted output** matching these patterns:

### Overview Mode (No Arguments)

```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

Agent Workload:
  project-manager      ██████████ 100% | 1 active task
  platform-engineer    ██████████ 100% | 1 active task
  ai-engineer          ████████░░ 80% | 2 active tasks
  data-engineer        ████░░░░░░ 40% | 1 active task
  python-pro           ░░░░░░░░░░ 0% | available

Task Distribution:
  Total Active: 5 tasks
  Average Load: 64%
  Load Variance: 35% (⚠️ unbalanced)

Heartbeat Status:
  ✅ All agents reporting healthy

Last Updated: 2025-11-07 20:45:30
```

**Progress Bar Format**:

- 10 blocks: `█` for used capacity, `░` for available
- Calculate blocks: `Math.round(workload / 10)`
- Show percentage and task count
- Add "(at capacity)" warning if workload >= 100

**Workload Indicators**:

- 0%: "available"
- 1-100%: "N active task(s)"
- ≥100%: "N active tasks (at capacity)"

**Balance Status**:

- Variance \< 20%: "✅ balanced"
- Variance ≥ 20%: "⚠️ unbalanced"

**Heartbeat Freshness**:

- Age ≤ 60 minutes: Healthy
- Age > 60 minutes: Warn with specific age (Xh Ym or Ym format)

### Detailed Mode (Agent Type Argument)

When user specifies agent type (e.g., `/team-status project-manager`):

```
=== Agent Status: project-manager ===

Current Status: BUSY (100% capacity)

Active Tasks (1):
  1. smart-onboarding-coordination
     - Progress: 45%
     - Duration: 2h 15m
     - Description: Coordinating Smart Onboarding implementation

Recent History (from status data):
  - Current workload: 100%
  - Task count: 1
  - Last updated: 5m ago

Circuit Breaker: ✅ CLOSED (healthy)
Last Heartbeat: 5m ago
```

**Task Display**:

- Show task ID or name
- Display progress if available
- Calculate duration from `started_at` if present
- Show description if available

**Heartbeat Age Calculation**:

- Compare timestamp to current time
- Format as "Xh Ym" (hours + minutes) or "Ym" (minutes only)
- Warn if age > 60 minutes

### JSON Parsing Logic

Implement this parsing pattern (from RedisCoordinationHelper):

```python
def parse_redis_value(raw_value: str) -> dict:
    """Parse Redis value with JSON deserialization and datetime restoration."""
    try:
        parsed = json.loads(raw_value)

        # Handle non-dict values (wrap in dict)
        if not isinstance(parsed, dict):
            return {"value": parsed}

        # Restore datetime fields
        for key, value in parsed.items():
            if isinstance(value, str) and (key.endswith("_at") or "timestamp" in key.lower()):
                try:
                    # Convert ISO format string to datetime
                    parsed[key] = datetime.fromisoformat(value)
                except ValueError:
                    # Not a valid datetime, keep as string
                    pass

        return parsed

    except json.JSONDecodeError:
        # Not JSON, return as plain value
        return {"value": raw_value}
```

### Statistics Calculations

**Load Variance** (standard deviation):

```python
def calculate_variance(workload_values: list[int]) -> float:
    """Calculate standard deviation of workload values."""
    if not workload_values:
        return 0.0

    mean = sum(workload_values) / len(workload_values)
    squared_diffs = [(val - mean) ** 2 for val in workload_values]
    variance = sum(squared_diffs) / len(workload_values)

    return variance ** 0.5  # Standard deviation
```

**Duration Formatting**:

```python
def format_duration(start_time: datetime) -> str:
    """Format duration from start time to now."""
    delta = datetime.now() - start_time

    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
```

### Error Handling

**No Redis Connection**:

```
⚠️  No coordination infrastructure detected

To enable real-time agent coordination:

Option 1 (Recommended): Deploy Redis Stack
  mycelium deploy start --yes

Option 2: Create coordination directory
  mkdir -p .claude/coordination/
  # Agents will create status files here
```

**Empty Redis Data**:

```
⚠️  No agents currently coordinating

To enable real-time agent coordination:
  Option 1: Deploy Redis Stack (recommended)
    mycelium deploy start --yes

  Option 2: Create coordination directory
    mkdir -p .claude/coordination/
```

**Agent Not Found** (in detailed mode):

```
❌ Agent 'unknown-agent' not found

Available agents:
  - project-manager
  - platform-engineer
  - ai-engineer
  - data-engineer
  - python-pro
```

**Stale Heartbeats** (age > 60 minutes):

```
Heartbeat Status:
  ⚠️  Stale heartbeats detected:
    - ai-engineer: last seen 2h 15m ago
    - ml-engineer: last seen 3h 42m ago
    - python-pro: last seen 1h 5m ago
```

### MCP Tool Usage

Use these MCP tools to query Redis:

```javascript
// Get all agent statuses
const agentStatuses = await mcp__RedisMCPServer__hgetall({
  name: "agents:status"
});

// Get specific agent status
const status = await mcp__RedisMCPServer__hget({
  name: "agents:status",
  key: "ai-engineer"
});

// Get all heartbeats
const heartbeats = await mcp__RedisMCPServer__hgetall({
  name: "agents:heartbeat"
});

// Get specific heartbeat
const heartbeat = await mcp__RedisMCPServer__hget({
  name: "agents:heartbeat",
  key: "ai-engineer"
});
```

### Display Requirements

1. **Sort agents by workload** (highest to lowest) in overview mode
1. **Calculate total statistics** (total tasks, average load, variance)
1. **Format progress bars** with 10 blocks (█ and ░ characters)
1. **Check heartbeat freshness** and warn if stale (>60 min)
1. **Handle missing data gracefully** (show 0% workload, "available" status)
1. **Parse JSON correctly** (handle both JSON strings and plain values)
1. **Restore datetime fields** (fields ending in `_at` or containing `timestamp`)
1. **Format timestamps** as human-readable durations (e.g., "2h 15m")

### Integration Notes

This command integrates with:

- `RedisCoordinationHelper` library for JSON serialization patterns
- `mycelium deploy` command for Redis Stack deployment
- Agent heartbeat mechanisms for health monitoring
- Workload management for task distribution

### Expected Behavior

**Query Redis MCP Server**:

1. Check if MCP server is available
1. Query `agents:status` hash for all agent data
1. Query `agents:heartbeat` hash for heartbeat timestamps
1. Parse JSON data with datetime restoration
1. Display formatted output with statistics

**Handle Parsing Errors**:

- If JSON parsing fails, wrap value in `{"value": raw_value}`
- If datetime parsing fails, keep as string
- If Redis query fails, show helpful error with deployment instructions

**Calculate Statistics**:

- Sort agents by workload (descending)
- Sum total active tasks
- Calculate average workload percentage
- Calculate load variance (standard deviation)
- Determine balance status (\< 20% = balanced)

**Check Heartbeat Health**:

- Parse heartbeat timestamps
- Calculate age in minutes
- Warn if any heartbeat > 60 minutes old
- Format age as "Xh Ym" or "Ym"

### Example Outputs

**Scenario 1: Active Team**

```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

Agent Workload:
  ai-engineer          ██████████ 100% | 3 active tasks (at capacity)
  data-engineer        ████████░░ 80% | 2 active tasks
  python-pro           ████░░░░░░ 40% | 1 active task
  performance-eng      ░░░░░░░░░░ 0% | available

Task Distribution:
  Total Active: 6 tasks
  Average Load: 55%
  Load Variance: 38% (⚠️ unbalanced)

Heartbeat Status:
  ✅ All agents reporting healthy

Last Updated: 2025-11-07 20:45:30
```

**Scenario 2: Stale Heartbeats**

```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

Agent Workload:
  project-manager      ██████████ 100% | 1 active task

Task Distribution:
  Total Active: 1 task
  Average Load: 100%
  Load Variance: 0% (✅ balanced)

Heartbeat Status:
  ⚠️  Stale heartbeats detected:
    - project-manager: last seen 25 days ago

Last Updated: 2025-11-07 20:45:30
```

**Scenario 3: Detailed Agent View**

```
=== Agent Status: ai-engineer ===

Current Status: BUSY (85% capacity)

Active Tasks (2):
  1. train-voice-model
     - Progress: 35%
     - Duration: 4h 23m
     - Description: Training custom voice model

  2. evaluate-checkpoint
     - Progress: 70%
     - Duration: 45m
     - Description: Evaluating model checkpoint

Recent History (from status data):
  - Current workload: 85%
  - Task count: 2
  - Last updated: 2m ago

Circuit Breaker: ✅ CLOSED (healthy)
Last Heartbeat: 2m ago
```

**Scenario 4: No Agents**

```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

⚠️  No agents currently coordinating

To enable real-time agent coordination:
  Option 1: Deploy Redis Stack (recommended)
    mycelium deploy start --yes

  Option 2: Create coordination directory
    mkdir -p .claude/coordination/
```

## Implementation Steps

When user runs `/team-status`:

1. **Parse arguments**: Extract agent type from `$ARGS` if provided
1. **Query Redis MCP**:
   - Call `mcp__RedisMCPServer__hgetall` for `agents:status`
   - Call `mcp__RedisMCPServer__hgetall` for `agents:heartbeat`
1. **Parse JSON data**:
   - Use `parse_redis_value()` logic for each value
   - Restore datetime fields
1. **Determine display mode**:
   - If agent type specified: Show detailed view
   - Otherwise: Show overview with all agents
1. **Format output**:
   - Create progress bars (10 blocks)
   - Calculate statistics (total, average, variance)
   - Check heartbeat freshness (warn if >60 min)
   - Display timestamp
1. **Handle errors**:
   - Show helpful message if Redis unavailable
   - Show empty state if no agents
   - Show agent not found if invalid agent type

Now implement this formatted team status display with proper JSON parsing and error handling.
