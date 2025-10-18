# Mycelium Coordination Deep Dive

Comprehensive guide to dual-mode coordination, event-driven patterns, and workflow orchestration in the Mycelial network.

## Table of Contents

1. [Coordination Architecture](#coordination-architecture)
2. [Dual-Mode Coordination](#dual-mode-coordination)
3. [Redis MCP Mode](#redis-mcp-mode)
4. [TaskQueue MCP Mode](#taskqueue-mcp-mode)
5. [Markdown Mode](#markdown-mode)
6. [Coordination Library API](#coordination-library-api)
7. [Event-Driven Patterns](#event-driven-patterns)
8. [Workflow Orchestration](#workflow-orchestration)
9. [Performance Benchmarks](#performance-benchmarks)
10. [Best Practices](#best-practices)

## Coordination Architecture

### The Substrate Metaphor

Just as mycelium in nature communicates through chemical signals and distributes resources through interconnected threads, Mycelium's coordination substrate enables agent communication and task distribution.

```
┌─────────────────────────────────────────────────┐
│         Application Layer (Agents)              │
│  ai-engineer | data-engineer | devops-engineer  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      Coordination Library (lib/)                │
│  - Auto-detection of available substrate       │
│  - Unified API across all modes                │
│  - Graceful degradation                         │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌──────────┐  ┌──────────┐
   │ Redis  │  │TaskQueue │  │Markdown  │
   │  MCP   │  │   MCP    │  │  Files   │
   └────────┘  └──────────┘  └──────────┘
   Real-time   Task-centric   Zero-deps
```

### Auto-Detection Flow

```javascript
// Coordination library automatically detects available substrate
const client = new CoordinationClient();
await client.initialize();

// Detection priority:
// 1. Redis MCP (if REDIS_URL available and reachable)
// 2. TaskQueue MCP (if npx taskqueue-mcp available)
// 3. Markdown Files (fallback, always available)

console.log(`Coordination mode: ${client.mode}`);
// → "redis" | "taskqueue" | "markdown"
```

## Dual-Mode Coordination

### Mode Comparison

| Feature | Redis | TaskQueue | Markdown |
|---------|-------|-----------|----------|
| **Latency** | 0.8ms | 100ms | 500ms |
| **Throughput** | 234K msg/min | 3K tasks/min | 6K ops/min |
| **Real-time Events** | ✅ Yes | ❌ No | ❌ No |
| **Persistence** | ⚠️ Optional | ✅ Yes | ✅ Yes |
| **Offline Support** | ❌ No | ❌ No | ✅ Yes |
| **Setup Complexity** | Medium | Low | None |
| **Agent Scalability** | 100+ | 50+ | 20 |
| **Network Required** | Yes | Yes (npx) | No |
| **Git Trackable** | ❌ No | ❌ No | ✅ Yes |

### Mode Selection Strategy

**Use Redis when**:
- Real-time agent collaboration required
- High message throughput needed (>10K/min)
- Multiple agents working in parallel
- Production deployment
- Network latency is low (<10ms)

**Use TaskQueue when**:
- Task-oriented workflows
- Integration with MCP ecosystem
- Structured task management needed
- Don't want to run Redis server
- Occasional agent collaboration

**Use Markdown when**:
- Offline development
- Git-tracked coordination state desired
- Minimal infrastructure dependencies
- Single-user workflows
- Learning/experimentation

### Graceful Degradation

```javascript
// Library handles mode failures automatically

// Redis fails → TaskQueue fallback
client.initialize(); // tries Redis first
// Redis connection refused
// → Falls back to TaskQueue
// → If TaskQueue unavailable, falls back to Markdown

// You write mode-agnostic code:
await client.storeAgentStatus('ai-engineer', { status: 'busy' });
// Works in all modes!
```

## Redis MCP Mode

### Architecture

Redis mode leverages Redis as a high-performance pub/sub and key-value store for real-time agent coordination.

```
┌─────────────────┐
│   Agent 1       │─┐
└─────────────────┘ │
                    ├──> Redis Pub/Sub ──> ┌─────────────────┐
┌─────────────────┐ │                      │   Agent 2       │
│   Agent 3       │─┘                      └─────────────────┘
└─────────────────┘
        │
        └──> Redis KV Store (agent status, task queues)
```

### Setup

```bash
# Using Docker (recommended)
docker run -d \
  -p 6379:6379 \
  --name redis \
  redis:latest

# Or Valkey (Redis fork)
docker run -d \
  -p 6379:6379 \
  --name valkey \
  valkey/valkey:latest

# Verify
redis-cli ping  # Should return PONG
```

### Configuration

```bash
# Environment variables
export REDIS_URL="redis://localhost:6379"
export REDIS_PASSWORD=""
export REDIS_DB="0"

# Or .mycelium/config.json
{
  "coordination": {
    "mode": "redis",
    "redis": {
      "url": "redis://localhost:6379",
      "password": null,
      "db": 0,
      "connection_timeout_seconds": 5,
      "operation_timeout_seconds": 2,
      "retry_attempts": 3,
      "retry_delay_ms": 100
    }
  }
}
```

### Key Patterns

**Agent Status**:
```
Key: agents:status:<agent-name>
Type: Hash
TTL: 300 seconds (5 minutes)
Fields:
  - status: idle|busy|error
  - last_updated: ISO timestamp
  - active_tasks: JSON array
  - metadata: JSON object
```

**Task Queues**:
```
Key: tasks:queue:<priority>
Type: List
Operations:
  - LPUSH (add task)
  - RPOP (get task)
  - LLEN (queue size)
```

**Pub/Sub Channels**:
```
Channel: agents:events
Channel: tasks:events
Channel: workflows:events
Channel: training:events (custom)
```

**Workflow State**:
```
Key: workflows:<workflow-id>
Type: Hash
TTL: 3600 seconds (1 hour)
Fields:
  - status: running|completed|failed
  - progress: 0.0-1.0
  - result: JSON object
  - error: string (if failed)
```

### Performance Characteristics

- **Latency**: 0.5-1.5ms avg (local), 5-10ms (LAN)
- **Throughput**: 234K messages/min (measured)
- **Agent coordination overhead**: <5%
- **Memory usage**: ~256MB for 100 active agents
- **Network bandwidth**: ~1 Mbps for 50K msg/min

## TaskQueue MCP Mode

### Architecture

TaskQueue mode uses the MCP TaskQueue server for structured task management and coordination.

```
┌─────────────────┐
│   Agent 1       │──> Create Task ──> TaskQueue Server
└─────────────────┘                          │
                                             │
┌─────────────────┐                          ▼
│   Agent 2       │<── Poll Tasks <── Task Store (SQLite)
└─────────────────┘
```

### Setup

```bash
# Install via npm
npm install -g taskqueue-mcp

# Or use npx (no install)
npx taskqueue-mcp --help

# Verify
npx taskqueue-mcp --version
```

### Configuration

```bash
# Environment variables
export TASKQUEUE_MODE="enabled"
export TASKQUEUE_POLL_INTERVAL="1000"  # 1 second

# Or .mycelium/config.json
{
  "coordination": {
    "mode": "taskqueue",
    "taskqueue": {
      "poll_interval_ms": 1000,
      "max_tasks": 100,
      "task_timeout_seconds": 300
    }
  }
}
```

### Task Schema

```json
{
  "id": "task-123",
  "type": "train-model",
  "status": "pending",
  "assigned_to": "ai-engineer",
  "depends_on": ["task-122"],
  "payload": {
    "dataset": "alice-voice",
    "config": "configs/lora.yaml"
  },
  "created_at": "2025-10-17T00:00:00Z",
  "updated_at": "2025-10-17T00:01:00Z",
  "result": null,
  "error": null
}
```

### Performance Characteristics

- **Latency**: 100-500ms avg (polling delay)
- **Throughput**: 50 tasks/sec creation, 3K tasks/min processing
- **Agent coordination overhead**: ~10%
- **Memory usage**: ~128MB for 50 agents
- **Disk usage**: ~10MB per 1000 tasks

## Markdown Mode

### Architecture

Markdown mode uses simple markdown files in `.claude/coordination/` for human-readable, git-trackable coordination.

```
.claude/coordination/
├── agent-ai-engineer.md       # Agent status
├── agent-data-engineer.md
├── task-prepare-dataset.md    # Task definitions
├── task-train-model.md
├── workflow-training.md       # Workflow state
└── events.md                  # Event log
```

### Setup

```bash
# Just create directory
mkdir -p .claude/coordination/

# That's it! No dependencies.
```

### File Formats

**Agent Status** (`.claude/coordination/agent-<name>.md`):
```markdown
---
agent: ai-engineer
status: busy
last_updated: 2025-10-17T00:00:00Z
---

# Agent: ai-engineer

**Status**: busy
**Last Updated**: 2025-10-17T00:00:00Z

## Active Tasks

- train-model (started: 2025-10-17T00:00:00Z)

## Metadata

{
  "current_workflow": "workflow-123",
  "resources_allocated": {
    "gpu": "NVIDIA RTX 4090",
    "memory_gb": 24
  }
}
```

**Task Definition** (`.claude/coordination/task-<id>.md`):
```markdown
---
id: task-123
type: train-model
status: running
assigned_to: ai-engineer
created: 2025-10-17T00:00:00Z
---

# Task: train-model

**Type**: train-model
**Status**: running
**Assigned To**: ai-engineer

## Dependencies

- task-122 (prepare-dataset) - COMPLETED ✅

## Payload

{
  "dataset": "alice-voice",
  "config": "configs/lora.yaml",
  "epochs": 3
}

## Progress

- [x] Load dataset
- [x] Initialize model
- [ ] Training (epoch 1/3)
- [ ] Validation
- [ ] Save checkpoint

## Result

_In progress..._
```

### Performance Characteristics

- **Latency**: 100-1000ms avg (file I/O)
- **Throughput**: 100 writes/sec, 500 reads/sec
- **Agent coordination overhead**: ~20%
- **Memory usage**: <100MB
- **Disk usage**: ~1KB per agent, ~5KB per task

## Coordination Library API

### Initialization

```javascript
import { CoordinationClient } from 'mycelium/lib/coordination.js';

// Auto-detect mode
const client = new CoordinationClient();
await client.initialize();

// Force specific mode
const redisClient = new CoordinationClient({ mode: 'redis' });
await redisClient.initialize();

// Check active mode
console.log(`Mode: ${client.mode}`);
// → "redis" | "taskqueue" | "markdown"
```

### Agent Status Management

```javascript
// Store agent status (works in all modes)
await client.storeAgentStatus('ai-engineer', {
  status: 'busy',
  active_tasks: ['train-model'],
  metadata: {
    gpu: 'RTX 4090',
    memory_gb: 24
  },
  last_updated: new Date().toISOString()
});

// Retrieve agent status
const status = await client.getAgentStatus('ai-engineer');
console.log(status);
// → { status: 'busy', active_tasks: [...], ... }

// List all agents
const agents = await client.listAgents();
// → ['ai-engineer', 'data-engineer', ...]

// Remove agent status
await client.removeAgentStatus('ai-engineer');
```

### Task Management

```javascript
// Create task
const taskId = await client.createTask({
  type: 'train-model',
  assigned_to: 'ai-engineer',
  depends_on: ['task-122'],
  payload: {
    dataset: 'alice-voice',
    config: 'configs/lora.yaml'
  }
});

// Get task status
const task = await client.getTask(taskId);
console.log(task.status);
// → 'pending' | 'running' | 'completed' | 'failed'

// Update task status
await client.updateTaskStatus(taskId, 'running', {
  progress: 0.5,
  current_epoch: 2
});

// Complete task with result
await client.completeTask(taskId, {
  checkpoint_path: 'checkpoints/model.pth',
  final_loss: 0.042,
  validation_accuracy: 0.96
});

// Fail task with error
await client.failTask(taskId, {
  error: 'Out of memory',
  stack_trace: '...'
});
```

### Event Publishing & Subscription

```javascript
// Publish event (Redis only, no-op in other modes)
await client.publishEvent('training:events', {
  event: 'checkpoint_saved',
  task_id: taskId,
  step: 1000,
  loss: 0.42
});

// Subscribe to events (Redis only)
await client.subscribeEvents('training:events', (event) => {
  console.log('Received:', event);

  if (event.event === 'checkpoint_saved') {
    console.log(`Checkpoint at step ${event.step}, loss ${event.loss}`);
  }
});

// Unsubscribe
await client.unsubscribeEvents('training:events');
```

### Workflow Management

```javascript
// Create workflow
const workflowId = await client.createWorkflow({
  type: 'model-training',
  tasks: ['prepare-dataset', 'train-model', 'evaluate-model'],
  metadata: {
    dataset: 'alice-voice',
    target_accuracy: 0.95
  }
});

// Get workflow status
const workflow = await client.getWorkflow(workflowId);
console.log(workflow);
// → { status: 'running', progress: 0.67, tasks: [...] }

// Update workflow progress
await client.updateWorkflow(workflowId, {
  progress: 0.75,
  current_task: 'evaluate-model'
});

// Complete workflow
await client.completeWorkflow(workflowId, {
  result: {
    final_accuracy: 0.96,
    model_path: 'models/alice-v1.pth'
  }
});
```

## Event-Driven Patterns

### Pub/Sub Pattern (Redis only)

```javascript
// Publisher agent
await client.publishEvent('training:progress', {
  agent: 'ai-engineer',
  event: 'training_started',
  workflow_id: 'wf-123'
});

// Subscriber agent
await client.subscribeEvents('training:progress', async (event) => {
  if (event.event === 'training_started') {
    // Trigger dependent workflow
    await startMonitoring(event.workflow_id);
  }
});
```

### Task Handoff Pattern

```javascript
// Agent 1: Create and hand off task
const taskId = await client.createTask({
  type: 'prepare-dataset',
  assigned_to: 'data-engineer',
  payload: { dataset: 'alice-voice' }
});

// Agent 2: Poll for assigned tasks
const tasks = await client.getTasksForAgent('data-engineer');
for (const task of tasks) {
  if (task.status === 'pending') {
    await client.updateTaskStatus(task.id, 'running');

    // Do work...
    const result = await prepareDataset(task.payload);

    await client.completeTask(task.id, result);
  }
}
```

### Dependency Chain Pattern

```javascript
// Create task chain with dependencies
const task1 = await client.createTask({
  type: 'prepare-dataset',
  assigned_to: 'data-engineer'
});

const task2 = await client.createTask({
  type: 'train-model',
  assigned_to: 'ai-engineer',
  depends_on: [task1]  // Wait for task1 completion
});

const task3 = await client.createTask({
  type: 'evaluate-model',
  assigned_to: 'performance-engineer',
  depends_on: [task2]  // Wait for task2 completion
});

// Monitor entire chain
await client.monitorWorkflow([task1, task2, task3]);
```

## Workflow Orchestration

### Temporal Integration (Advanced)

For complex, long-running workflows, Mycelium integrates with Temporal:

```javascript
import { WorkflowClient } from 'mycelium/lib/workflow.js';

const wf = new WorkflowClient();

// Create durable workflow
const workflowId = await wf.createWorkflow('train-model', {
  dataset: 'alice-voice',
  epochs: 3,
  checkpoint_interval: 500
});

// Workflow runs durably - survives process restarts
// Automatic retries on failure
// Built-in monitoring and observability

// Check status
const status = await wf.getWorkflowStatus(workflowId);
console.log(status);
// → { status: 'running', progress: 0.35, step: 3500 }

// Wait for completion
const result = await wf.waitForCompletion(workflowId);
console.log(result);
// → { checkpoint_path: '...', final_loss: 0.042 }
```

### Workflow Patterns

**Sequential Workflow**:
```javascript
// Task A → Task B → Task C
const a = await client.createTask({ type: 'A' });
const b = await client.createTask({ type: 'B', depends_on: [a] });
const c = await client.createTask({ type: 'C', depends_on: [b] });
```

**Parallel Workflow**:
```javascript
// Task A → [Task B1, Task B2, Task B3] → Task C
const a = await client.createTask({ type: 'A' });

const b1 = await client.createTask({ type: 'B1', depends_on: [a] });
const b2 = await client.createTask({ type: 'B2', depends_on: [a] });
const b3 = await client.createTask({ type: 'B3', depends_on: [a] });

const c = await client.createTask({ type: 'C', depends_on: [b1, b2, b3] });
```

**Conditional Workflow**:
```javascript
// Task A → (if success) Task B → (if failure) Task C
const a = await client.createTask({ type: 'A' });

// Agent monitors task A completion
client.subscribeEvents('tasks:completed', async (event) => {
  if (event.task_id === a && event.result.success) {
    await client.createTask({ type: 'B' });
  } else {
    await client.createTask({ type: 'C' });  // Fallback/recovery
  }
});
```

## Performance Benchmarks

### Redis Mode Benchmarks

**Test Setup**:
- Local Redis instance
- 100 concurrent agents
- Mixed read/write operations

**Results**:
```
Operation               p50     p95     p99     Throughput
─────────────────────────────────────────────────────────
Store Agent Status      0.8ms   1.2ms   2.0ms   234K/min
Get Agent Status        0.5ms   0.9ms   1.5ms   400K/min
Create Task             1.0ms   1.5ms   2.5ms   180K/min
Publish Event           0.6ms   1.0ms   1.8ms   300K/min
Subscribe (latency)     <0.1ms  <0.1ms  0.2ms   -
```

**Memory Usage**:
- 1 agent: ~2.5KB
- 100 agents: ~256MB (including Redis)
- 1000 tasks: ~5MB

### TaskQueue Mode Benchmarks

**Test Setup**:
- TaskQueue MCP via npx
- 50 concurrent agents
- Poll interval: 1 second

**Results**:
```
Operation               p50     p95     p99     Throughput
─────────────────────────────────────────────────────────
Create Task             100ms   200ms   500ms   50/sec
Poll Tasks              50ms    100ms   200ms   20/sec
Update Task Status      80ms    150ms   300ms   30/sec
```

**Latency Breakdown**:
- npx overhead: ~50ms
- SQLite write: ~20ms
- SQLite read: ~10ms
- Network (if remote): +10-50ms

### Markdown Mode Benchmarks

**Test Setup**:
- Local SSD filesystem
- 20 concurrent agents
- File-based coordination

**Results**:
```
Operation               p50     p95     p99     Throughput
─────────────────────────────────────────────────────────
Store Agent Status      100ms   200ms   500ms   100/sec
Get Agent Status        50ms    100ms   200ms   200/sec
Create Task             150ms   300ms   600ms   60/sec
```

**Filesystem Operations**:
- Write markdown file: ~50ms
- Read markdown file: ~20ms
- Parse YAML frontmatter: ~10ms
- Git commit (if tracked): +100-500ms

## Best Practices

### Mode Selection

1. **Development**: Start with Markdown (zero setup)
2. **Testing**: Use TaskQueue (structured, MCP-native)
3. **Production**: Use Redis (real-time, high-performance)

### Error Handling

```javascript
// Always handle coordination failures
try {
  await client.storeAgentStatus('ai-engineer', { status: 'busy' });
} catch (error) {
  console.error('Coordination failed:', error);
  // Fallback to local state or retry
}

// Use timeout for coordination operations
const timeout = (ms) => new Promise((_, reject) =>
  setTimeout(() => reject(new Error('Timeout')), ms)
);

try {
  await Promise.race([
    client.getTask(taskId),
    timeout(5000)  // 5 second timeout
  ]);
} catch (error) {
  // Handle timeout or coordination error
}
```

### Resource Cleanup

```javascript
// Always clean up agent status on exit
process.on('SIGINT', async () => {
  await client.removeAgentStatus('ai-engineer');
  await client.close();
  process.exit(0);
});

// Use TTL for automatic cleanup (Redis)
await client.storeAgentStatus('ai-engineer', {
  status: 'busy',
  ttl: 300  // 5 minutes
});
```

### Performance Optimization

```javascript
// Batch operations when possible (Redis)
const pipeline = client.pipeline();
for (const agent of agents) {
  pipeline.storeAgentStatus(agent.name, agent.status);
}
await pipeline.execute();  // Single round-trip

// Use pub/sub for real-time events, not polling
// ❌ Bad: Poll for task completion
while (true) {
  const task = await client.getTask(taskId);
  if (task.status === 'completed') break;
  await sleep(1000);
}

// ✅ Good: Subscribe to completion events
await client.subscribeEvents('tasks:completed', (event) => {
  if (event.task_id === taskId) {
    handleCompletion(event);
  }
});
```

### Monitoring

```javascript
// Track coordination metrics
setInterval(async () => {
  const stats = await client.getStats();
  console.log({
    mode: stats.mode,
    active_agents: stats.agent_count,
    pending_tasks: stats.task_queue_size,
    latency_ms: stats.avg_latency
  });
}, 60000);  // Every minute
```

## Next Steps

- **Read [deployment.md](./deployment.md)** - Deploy coordination infrastructure to production
- **Read [agents.md](./agents.md)** - Create agents that use coordination
- **See [examples/](../../docs/examples/)** - Complete workflow examples
- **Read [patterns/](../../docs/patterns/)** - Advanced coordination patterns

## Support

- **Documentation**: [.mycelium/modules/](./)
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Main README**: [README.md](../../README.md)
