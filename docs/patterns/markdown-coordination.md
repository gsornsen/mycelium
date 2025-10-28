# Markdown Coordination Pattern

This document defines best practices for using markdown files as a coordination mechanism between Claude Code agents
when Redis/TaskQueue MCP servers are unavailable.

## Overview

Markdown coordination uses filesystem-based `.md` files in `.claude/coordination/` directory to share state between
agents. While less robust than Redis, it provides a zero-dependency fallback for development environments.

## Directory Structure

```
.claude/coordination/
├── README.md                      # Documentation
├── agent-ai-engineer.md          # Agent status
├── agent-data-engineer.md        # Agent status
├── agent-ml-engineer.md          # Agent status
├── task-train-model.md           # Task status
├── task-process-dataset.md       # Task status
├── events-training.md            # Event log
├── events-errors.md              # Error log
├── metrics-performance.md        # Performance metrics
└── archive/                      # Stale files (>24h)
    ├── agent-old-agent.md
    └── task-completed-123.md
```

## File Naming Convention

| Entity Type    | Pattern                            | Example                    |
| -------------- | ---------------------------------- | -------------------------- |
| Agent Status   | `agent-{name}.md`                  | `agent-ai-engineer.md`     |
| Task Status    | `task-{id}.md` or `task-{name}.md` | `task-train-model.md`      |
| Events         | `events-{channel}.md`              | `events-training.md`       |
| Metrics        | `metrics-{type}.md`                | `metrics-performance.md`   |
| Shared Context | `context-{project}-{domain}.md`    | `context-proj1-dataset.md` |

## Agent Status File Format

**File**: `.claude/coordination/agent-ai-engineer.md`

```markdown
# Agent: ai-engineer

**Status**: BUSY
**Last Updated**: 2025-10-12T14:30:00Z
**Workload**: 85%

## Active Tasks

### Task: train-model (proj-1)
- **Task ID**: task-123
- **Started**: 2025-10-12T10:00:00Z
- **Duration**: 4h 30m
- **Status**: in_progress
- **Progress**: 35% (3500/10000 steps)
- **Metrics**:
  - Loss: 0.42
  - Learning Rate: 0.0004
  - Samples/sec: 45.2

### Task: evaluate-checkpoint (proj-3)
- **Task ID**: task-125
- **Started**: 2025-10-12T13:45:00Z
- **Duration**: 45m
- **Status**: in_progress
- **Progress**: 70%

## Recent Completions (Last 24h)

- **tune-hyperparameters** (task-120)
  - Completed: 2025-10-12T09:45:00Z
  - Duration: 2h 15m
  - Success: ✅

- **load-checkpoint** (task-118)
  - Completed: 2025-10-12T07:30:00Z
  - Duration: 5m
  - Success: ✅

## Metrics

- **Success Rate**: 100% (24/24)
- **Average Duration**: 3h 30m
- **Total Tasks (24h)**: 24
- **Failed Tasks**: 0

## Circuit Breaker

- **State**: CLOSED
- **Failure Count**: 0/3
- **Last Failure**: N/A

## Notes

Agent is at high capacity (85%). Consider routing new tasks to other agents if available.
```

## Task Status File Format

**File**: `.claude/coordination/task-train-model.md`

````markdown
# Task: Train model on Alice dataset

**Task ID**: task-123
**Project ID**: proj-1
**Status**: in_progress
**Assigned Agent**: ai-engineer

## Timeline

- **Created**: 2025-10-12T09:55:00Z
- **Assigned**: 2025-10-12T09:56:00Z
- **Started**: 2025-10-12T10:00:00Z
- **Last Updated**: 2025-10-12T14:30:00Z
- **ETA**: 2025-10-12T18:30:00Z (estimated)

## Progress

- **Current**: 35% (3500/10000 steps)
- **Duration**: 4h 30m
- **Remaining**: ~8h 30m

## Metrics

```json
{
  "step": 3500,
  "total_steps": 10000,
  "loss": 0.42,
  "learning_rate": 0.0004,
  "gpu_memory_gb": 23.1,
  "gpu_utilization_pct": 97,
  "samples_per_second": 45.2
}
````

## Context References

- Dataset: `.claude/coordination/context-proj1-dataset.md`
- Hyperparameters: `.claude/coordination/context-proj1-training-config.md`
- Checkpoints: `checkpoints/voice-clone-training-proj-1/`

## Dependencies

- ✅ Dataset processing (task-122) - COMPLETE
- 🟡 GPU availability check (task-121) - COMPLETE

## Next Steps

On completion:

1. Save final model to `checkpoints/voice-clone-training-proj-1/final.pt`
1. Store metrics in `.claude/coordination/context-proj1-training-results.md`
1. Create evaluation task (task-124)

## Logs

Recent activity:

```
[2025-10-12 14:30:00] Checkpoint saved at step 3500
[2025-10-12 14:20:00] Loss: 0.42
[2025-10-12 14:10:00] Loss: 0.45
[2025-10-12 14:00:00] Checkpoint saved at step 3000
```

````

## Event Log File Format

**File**: `.claude/coordination/events-training.md`

```markdown
# Training Events Log

Last updated: 2025-10-12T14:30:00Z

---

## Event: checkpoint_saved
**Time**: 2025-10-12T14:30:00Z
**Workflow**: voice-clone-training-proj-1
**Step**: 3500
**Loss**: 0.42
**Checkpoint Path**: `checkpoints/voice-clone-training-proj-1/step_3500.pt`

---

## Event: training_step
**Time**: 2025-10-12T14:20:00Z
**Workflow**: voice-clone-training-proj-1
**Step**: 3400
**Loss**: 0.43
**GPU Memory**: 23.1 GB

---

## Event: checkpoint_saved
**Time**: 2025-10-12T14:00:00Z
**Workflow**: voice-clone-training-proj-1
**Step**: 3000
**Loss**: 0.48

---

## Event: training_started
**Time**: 2025-10-12T10:00:00Z
**Workflow**: voice-clone-training-proj-1
**Total Steps**: 10000
**Batch Size**: 8
**Learning Rate**: 0.0005

---

_Note: This log contains the last 100 events. Older events are in `archive/events-training-2025-10-11.md`_
````

## Context Sharing File Format

**File**: `.claude/coordination/context-proj1-dataset.md`

````markdown
# Dataset Context: Project 1 (Alice Voice Clone)

**Project**: proj-1
**Last Updated**: 2025-10-12T09:50:00Z
**Created By**: data-engineer (task-122)

## Dataset Information

```json
{
  "path": "data/processed/alice/",
  "manifest_path": "data/processed/alice/manifest.csv",
  "segments_count": 1847,
  "segments_kept": 1812,
  "segments_rejected": 35,
  "total_duration_sec": 2712,
  "average_quality": 0.964,
  "average_snr_db": 24.3
}
````

## Splits

| Split | Count | Duration |
| ----- | ----- | -------- |
| Train | 1450  | 36m 10s  |
| Val   | 181   | 4m 31s   |
| Test  | 181   | 4m 31s   |

## Quality Report

- **High Quality**: 1750 segments (96.4%)
- **Medium Quality**: 62 segments (3.4%)
- **Low Quality**: 35 segments (rejected)

Full quality report: `data/processed/alice/quality_report.md`

## Usage

This dataset is ready for training. Use the manifest file for dataloader creation:

```python
import pandas as pd
manifest = pd.read_csv("data/processed/alice/manifest.csv")
train_segments = manifest[manifest["split"] == "train"]
```

## Dependencies

- Source recordings: `recordings/alice/`
- Processing script: `voice_dataset_kit.cli.process`
- Configuration: `podcast_config.yaml`

````

## File Lifecycle Management

### Creation

Agents create files when work begins:

```bash
#!/bin/bash

# Agent starts work on task
TASK_ID="task-123"
AGENT="ai-engineer"
TIMESTAMP=$(date -Iseconds)

cat > ".claude/coordination/task-${TASK_ID}.md" <<EOF
# Task: Train model

**Task ID**: $TASK_ID
**Status**: in_progress
**Assigned Agent**: $AGENT
**Started**: $TIMESTAMP

## Progress

Starting work...
EOF
````

### Updates

Agents update files periodically (every 5-10 minutes):

```bash
#!/bin/bash

# Update task progress
TASK_FILE=".claude/coordination/task-123.md"

# Use temporary file to avoid race conditions
cat > "${TASK_FILE}.tmp" <<EOF
# Task: Train model

**Task ID**: task-123
**Status**: in_progress
**Last Updated**: $(date -Iseconds)
**Progress**: 35% (3500/10000 steps)

## Metrics

Current loss: 0.42
EOF

# Atomic move
mv "${TASK_FILE}.tmp" "$TASK_FILE"
```

### Archival

Cleanup script removes stale files:

```bash
#!/bin/bash
# cleanup-coordination.sh

COORDINATION_DIR=".claude/coordination"
ARCHIVE_DIR="$COORDINATION_DIR/archive"
STALE_HOURS=24

mkdir -p "$ARCHIVE_DIR"

echo "Cleaning up coordination files older than ${STALE_HOURS}h..."

# Archive completed tasks
find "$COORDINATION_DIR" -name "task-*.md" -type f -mmin +$((STALE_HOURS * 60)) \
  -exec sh -c 'grep -q "Status.*complete" "$1" && mv "$1" "'"$ARCHIVE_DIR"'"' _ {} \;

# Archive stale agent status (agents may have crashed)
find "$COORDINATION_DIR" -name "agent-*.md" -type f -mmin +$((STALE_HOURS * 60)) \
  -exec mv {} "$ARCHIVE_DIR/" \;

# Rotate event logs (keep last 100 events)
for event_log in "$COORDINATION_DIR"/events-*.md; do
  if [ -f "$event_log" ]; then
    # Keep last 100 events (assumes events separated by ---)
    tail -n 300 "$event_log" > "${event_log}.tmp"
    mv "${event_log}.tmp" "$event_log"
  fi
done

echo "Cleanup complete."
```

Run cleanup periodically (cron or systemd timer):

```bash
# Add to crontab: Run every hour
0 * * * * cd /path/to/project && ./.claude/coordination/cleanup.sh
```

## Concurrency Control

### File Locking

Use `flock` to prevent race conditions:

```bash
#!/bin/bash

LOCK_FILE=".claude/coordination/.lock-task-123"
TASK_FILE=".claude/coordination/task-123.md"

# Acquire exclusive lock
{
  flock -x 200

  # Critical section: Update file
  cat > "$TASK_FILE" <<EOF
# Updated content
EOF

} 200>"$LOCK_FILE"

# Lock released automatically when fd 200 closes
```

### Atomic Updates

Use temporary files + atomic move:

```bash
# Write to temp file
cat > "$TASK_FILE.tmp" <<EOF
Updated content
EOF

# Atomic move (replaces original)
mv "$TASK_FILE.tmp" "$TASK_FILE"
```

## Staleness Detection

Check file modification time to detect stale data:

```bash
#!/bin/bash

TASK_FILE=".claude/coordination/task-123.md"

if [ -f "$TASK_FILE" ]; then
  FILE_AGE_SEC=$(($(date +%s) - $(stat -c %Y "$TASK_FILE")))
  FILE_AGE_MIN=$((FILE_AGE_SEC / 60))

  if [ $FILE_AGE_SEC -gt 3600 ]; then
    echo "⚠️  Task file is stale (${FILE_AGE_MIN} minutes old)"
    echo "   Agent may have crashed or stopped updating"
  fi
fi
```

## Search and Query Patterns

### Find all active tasks

```bash
# List all task files
ls -1 .claude/coordination/task-*.md

# Filter by status
for task in .claude/coordination/task-*.md; do
  if grep -q "Status.*in_progress" "$task"; then
    echo "Active: $(basename $task)"
  fi
done
```

### Find agents by workload

```bash
# High workload agents (>70%)
for agent in .claude/coordination/agent-*.md; do
  workload=$(grep -oP 'Workload.*:\s*\K\d+' "$agent")
  if [ "$workload" -gt 70 ]; then
    echo "High load: $(basename $agent .md | sed 's/agent-//'): ${workload}%"
  fi
done
```

### Extract metrics from event log

```bash
# Get last 10 training losses
grep -oP 'Loss.*:\s*\K[\d.]+' .claude/coordination/events-training.md | head -10
```

## Integration with Git

### Gitignore Configuration

Add to `.gitignore`:

```
# Coordination files (ephemeral state)
.claude/coordination/
!.claude/coordination/README.md
!.claude/coordination/.gitkeep
```

**Rationale**: Coordination files are runtime state, not source code. Don't commit them.

**Exception**: You may want to commit templates or documentation:

```
# .claude/coordination/.gitkeep ensures directory exists
touch .claude/coordination/.gitkeep

# README explains coordination system
cat > .claude/coordination/README.md <<EOF
# Coordination Directory

This directory contains ephemeral coordination files used by Claude Code agents.

Files are created/updated during agent execution and cleaned up periodically.

Do not manually edit these files while agents are running.
EOF
```

## Best Practices

1. **Update frequently** - Every 5-10 minutes during long-running tasks
1. **Use atomic updates** - Temporary file + move to avoid partial reads
1. **Implement locking** - Use `flock` for critical sections
1. **Check staleness** - Warn if files older than 1 hour
1. **Clean up regularly** - Archive completed/stale files
1. **Include timestamps** - Always timestamp updates
1. **Structured content** - Use consistent markdown format
1. **Limit log size** - Rotate event logs to prevent unbounded growth
1. **Don't commit** - Add to `.gitignore` (ephemeral state)
1. **Provide fallback** - Gracefully handle missing files

## Limitations and Workarounds

### Limitation: No Real-Time Updates

**Problem**: Agents must poll files to detect changes

**Workaround**: Use filesystem watchers

```bash
# Watch coordination directory for changes
inotifywait -m -r -e modify .claude/coordination/ |
while read path action file; do
  echo "File changed: $file"
  # React to change
done
```

### Limitation: Race Conditions

**Problem**: Multiple agents may write simultaneously

**Workaround**: Use file locking (flock) + atomic updates

### Limitation: No Pub/Sub

**Problem**: Can't subscribe to events

**Workaround**: Poll event logs periodically + track last read position

```bash
# Track last read event
LAST_EVENT_COUNT=$(wc -l < .claude/coordination/.last-event-count 2>/dev/null || echo 0)
CURRENT_EVENT_COUNT=$(grep -c "^## Event:" .claude/coordination/events-training.md)

if [ "$CURRENT_EVENT_COUNT" -gt "$LAST_EVENT_COUNT" ]; then
  echo "New events detected!"
  # Process new events
  tail -n +$((LAST_EVENT_COUNT + 1)) .claude/coordination/events-training.md
fi

# Update tracker
echo "$CURRENT_EVENT_COUNT" > .claude/coordination/.last-event-count
```

### Limitation: Limited Query Capabilities

**Problem**: Can't query structured data efficiently

**Workaround**: Use JSON blocks in markdown + `jq` for parsing

````bash
# Extract JSON from markdown
sed -n '/```json/,/```/p' .claude/coordination/context-proj1-dataset.md |
  sed '1d;$d' |
  jq '.segments_count'
````

## Migration to Redis

When project outgrows markdown coordination:

```bash
#!/bin/bash
# migrate-to-redis.sh

echo "Migrating coordination state to Redis..."

# Migrate agent statuses
for agent_file in .claude/coordination/agent-*.md; do
  agent=$(basename "$agent_file" .md | sed 's/^agent-//')

  # Extract key fields (simplified)
  status=$(grep -oP '^\*\*Status\*\*:\s*\K\w+' "$agent_file")
  workload=$(grep -oP '^\*\*Workload\*\*:\s*\K\d+' "$agent_file")

  # Store in Redis
  redis-cli HSET "agents:status:$agent" \
    status "$status" \
    workload "$workload" \
    last_updated "$(date -Iseconds)"

  echo "  Migrated: $agent"
done

# Archive markdown files
mkdir -p .claude/coordination/archive/pre-redis/
mv .claude/coordination/*.md .claude/coordination/archive/pre-redis/

echo "Migration complete! Update agents to use Redis coordination."
```

## Related Documentation

- [Dual-Mode Coordination](./dual-mode-coordination.md) - Redis vs Markdown patterns
- [Redis MCP Integration](./redis-mcp-integration.md) - Redis migration guide
- [Agent Coordination Overview](./agent-coordination-overview.md) - High-level patterns

______________________________________________________________________

**Maintained by**: Claude Code Extensibility Team **Last Updated**: 2025-10-12
