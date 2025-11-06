# Redis Coordination Patterns

## Overview

Redis provides high-performance, in-memory data structures for distributed coordination, real-time event broadcasting,
and shared state management across multi-agent systems. This pattern guide covers production-ready implementations of
context storage, error tracking, pub/sub messaging, and circuit breaker coordination.

**Use Cases:**

- Distributed error tracking and correlation
- Real-time event broadcasting (task completion, training metrics, alerts)
- Shared context and state synchronization
- Circuit breaker coordination
- Retry queue management
- Agent workload distribution

## Prerequisites

### Required Tools

- **RedisMCPServer MCP server** - Redis client with hash, pub/sub, list, set, and vector operations
- **Redis server** - Redis 7.0+ for production workloads

### Dependencies

```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis              # macOS

# Start Redis server
redis-server
```

### Environment Setup

```bash
# Redis connection (default localhost:6379)
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=  # If authentication enabled
```

## Available Redis MCP Tools

**Key-Value Operations:**

- `mcp__RedisMCPServer__set` - Store string values with optional expiration
- `mcp__RedisMCPServer__get` - Retrieve string values
- `mcp__RedisMCPServer__delete` - Remove keys

**Hash Operations (Recommended for structured data):**

- `mcp__RedisMCPServer__hset` - Set hash field with optional expiration
- `mcp__RedisMCPServer__hget` - Get hash field value
- `mcp__RedisMCPServer__hgetall` - Get all hash fields
- `mcp__RedisMCPServer__hdel` - Delete hash field
- `mcp__RedisMCPServer__hexists` - Check if hash field exists

**Pub/Sub Operations:**

- `mcp__RedisMCPServer__publish` - Broadcast message to channel
- `mcp__RedisMCPServer__subscribe` - Listen to channel

**List Operations:**

- `mcp__RedisMCPServer__lpush` / `rpush` - Add to list (left/right)
- `mcp__RedisMCPServer__lpop` / `rpop` - Remove from list
- `mcp__RedisMCPServer__lrange` - Get list range
- `mcp__RedisMCPServer__llen` - Get list length

**Set Operations:**

- `mcp__RedisMCPServer__sadd` - Add to set
- `mcp__RedisMCPServer__srem` - Remove from set
- `mcp__RedisMCPServer__smembers` - Get all set members

**Sorted Set Operations:**

- `mcp__RedisMCPServer__zadd` - Add member with score
- `mcp__RedisMCPServer__zrange` - Get members by rank
- `mcp__RedisMCPServer__zrem` - Remove member

**Utility Operations:**

- `mcp__RedisMCPServer__scan_keys` / `scan_all_keys` - Find keys by pattern
- `mcp__RedisMCPServer__type` - Get key type
- `mcp__RedisMCPServer__expire` - Set key expiration
- `mcp__RedisMCPServer__rename` - Rename key

## Pattern 1: Context Storage with Hashes

**Use Case:** Store structured context (project metadata, agent state, configuration) with atomic updates

**Why Hashes?** More efficient than JSON strings; supports partial field updates; atomic operations.

**Implementation:**

```javascript
// File: context-manager/project-context.js

// Store project context in hash
async function storeProjectContext(projectId, metadata) {
  await mcp__RedisMCPServer__hset({
    name: `context:project:${projectId}`,
    key: "name",
    value: metadata.name
  });

  await mcp__RedisMCPServer__hset({
    name: `context:project:${projectId}`,
    key: "status",
    value: metadata.status
  });

  await mcp__RedisMCPServer__hset({
    name: `context:project:${projectId}`,
    key: "dataset_size",
    value: metadata.datasetSize.toString()
  });

  await mcp__RedisMCPServer__hset({
    name: `context:project:${projectId}`,
    key: "quality_score",
    value: metadata.qualityScore.toString()
  });

  // Publish context update event
  await mcp__RedisMCPServer__publish({
    channel: "events:context:updated",
    message: JSON.stringify({
      type: "project_context_updated",
      projectId,
      timestamp: new Date().toISOString()
    })
  });
}

// Retrieve entire project context atomically
async function getProjectContext(projectId) {
  const context = await mcp__RedisMCPServer__hgetall({
    name: `context:project:${projectId}`
  });

  return {
    name: context.name,
    status: context.status,
    datasetSize: parseInt(context.dataset_size),
    qualityScore: parseFloat(context.quality_score)
  };
}

// Update single field without reading entire context
async function updateProjectStatus(projectId, newStatus) {
  await mcp__RedisMCPServer__hset({
    name: `context:project:${projectId}`,
    key: "status",
    value: newStatus
  });
}
```

**Agent State Tracking:**

```javascript
// Track agent workload in real-time
async function updateAgentStatus(agentType, status, currentTask = null) {
  await mcp__RedisMCPServer__hset({
    name: `agent:status:${agentType}`,
    key: "status",
    value: status  // "idle", "busy", "failed"
  });

  if (currentTask) {
    await mcp__RedisMCPServer__hset({
      name: `agent:status:${agentType}`,
      key: "current_task",
      value: currentTask
    });
  }

  await mcp__RedisMCPServer__hset({
    name: `agent:status:${agentType}`,
    key: "updated_at",
    value: new Date().toISOString()
  });
}

// Query agent availability for task assignment
async function getAvailableAgents() {
  const agentKeys = await mcp__RedisMCPServer__scan_all_keys({
    pattern: "agent:status:*"
  });

  const availableAgents = [];
  for (const key of agentKeys) {
    const status = await mcp__RedisMCPServer__hget({
      name: key,
      key: "status"
    });

    if (status.value === "idle") {
      const agentType = key.split(":")[2];
      availableAgents.push(agentType);
    }
  }

  return availableAgents;
}
```

**Considerations:**

- Use `hgetall` for reading entire context (fewer round trips than multiple `hget`)
- Set expiration on temporary context using `expire_seconds` parameter
- Namespace keys consistently: `type:entity:id` (e.g., `context:project:proj-1`)
- Hash fields are strings; convert numbers when retrieving

## Pattern 2: Pub/Sub Event Broadcasting

**Use Case:** Real-time coordination via async messaging (task completion, training progress, errors, alerts)

**Why Pub/Sub?** Fire-and-forget; subscribers don't block publishers; multiple subscribers per channel.

**Implementation:**

### Task Completion Events

```javascript
// Publisher: Task executor broadcasts completion
async function publishTaskCompletion(taskId, projectId, agent, result) {
  await mcp__RedisMCPServer__publish({
    channel: "events:tasks:completed",
    message: JSON.stringify({
      projectId,
      taskId,
      agent,
      completedAt: new Date().toISOString(),
      result
    })
  });
}

// Subscriber: Multi-agent-coordinator listens for progress
await mcp__RedisMCPServer__subscribe({
  channel: "events:tasks:completed"
});
```

### Training Progress Broadcasting

```javascript
// Broadcast training metrics every N steps
async function publishTrainingMetrics(projectId, step, metrics) {
  await mcp__RedisMCPServer__publish({
    channel: "events:training:progress",
    message: JSON.stringify({
      projectId,
      step,
      loss: metrics.loss,
      wer: metrics.wer,
      timestamp: new Date().toISOString()
    })
  });
}

// Multiple subscribers:
// - performance-monitor: Track metrics
// - error-coordinator: Detect anomalies
// - context-manager: Store time-series data
await mcp__RedisMCPServer__subscribe({
  channel: "events:training:progress"
});
```

### Error Event Broadcasting

```javascript
// Broadcast critical errors to all agents
async function publishError(agent, taskId, error, severity) {
  await mcp__RedisMCPServer__publish({
    channel: `events:errors:${severity}`,
    message: JSON.stringify({
      type: "task_failure",
      agent,
      taskId,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      timestamp: new Date().toISOString()
    })
  });
}

// Error-coordinator subscribes with wildcard
await mcp__RedisMCPServer__subscribe({
  channel: "events:errors:*"  // All error levels
});
```

**Considerations:**

- Pub/sub is fire-and-forget; no delivery guarantees
- Use lists for durable message queues (pattern 4)
- Wildcard subscriptions: `events:errors:*` matches all error channels
- Serialize complex objects to JSON before publishing

## Pattern 3: Error Tracking with Lists & Hashes

**Use Case:** Track errors chronologically, correlate across components, implement retry logic

**Why Lists?** FIFO/LIFO ordering; efficient append/pop; range queries for time windows.

**Implementation:**

### Error Logging

```javascript
// File: error-coordinator/error-tracking.js

async function logTaskError(taskId, projectId, agent, error) {
  const errorEvent = {
    type: "task_failure",
    taskId,
    projectId,
    agent,
    error: {
      name: error.name,
      message: error.message,
      code: error.code
    },
    timestamp: new Date().toISOString(),
    severity: classifyErrorSeverity(error),
    recoverable: isRecoverable(error)
  };

  // Append to chronological error log
  await mcp__RedisMCPServer__lpush({
    name: "errors:tasks:log",
    value: JSON.stringify(errorEvent),
    expire: 604800  // 7 days retention
  });

  // Store detailed error context in hash
  await mcp__RedisMCPServer__hset({
    name: `errors:task:${taskId}:details`,
    key: "error_message",
    value: error.message
  });

  await mcp__RedisMCPServer__hset({
    name: `errors:task:${taskId}:details`,
    key: "agent",
    value: agent
  });

  await mcp__RedisMCPServer__hset({
    name: `errors:task:${taskId}:details`,
    key: "severity",
    value: errorEvent.severity,
    expire_seconds: 604800  // 7 days
  });

  // Track unique error signatures for deduplication
  const errorSignature = generateErrorSignature(error);
  await mcp__RedisMCPServer__sadd({
    name: "errors:unique_signatures",
    value: errorSignature
  });

  // Increment error counter by type
  const currentCount = await mcp__RedisMCPServer__hget({
    name: "errors:counters",
    key: error.name
  });

  await mcp__RedisMCPServer__hset({
    name: "errors:counters",
    key: error.name,
    value: (parseInt(currentCount || "0") + 1).toString()
  });
}

function generateErrorSignature(error) {
  // Deduplicate by normalizing error patterns
  const messagePattern = error.message
    .replace(/\d+/g, "N")              // Replace numbers
    .replace(/[a-f0-9-]{36}/g, "UUID") // Replace UUIDs
    .substring(0, 100);

  return `${error.name}:${messagePattern}`;
}
```

### Error Correlation

```javascript
// Correlate errors across components within time window
async function correlateErrors(newError) {
  const CORRELATION_WINDOW = 300000;  // 5 minutes

  // Get recent errors from all log sources
  const taskErrors = await mcp__RedisMCPServer__lrange({
    name: "errors:tasks:log",
    start: 0,
    stop: 99  // Last 100 errors
  });

  const trainingErrors = await mcp__RedisMCPServer__lrange({
    name: "errors:training:proj-1:log",
    start: 0,
    stop: 99
  });

  const recentErrors = [...taskErrors, ...trainingErrors]
    .map(e => JSON.parse(e))
    .filter(e => {
      const errorTime = new Date(e.timestamp).getTime();
      return Date.now() - errorTime < CORRELATION_WINDOW;
    });

  // Detect error cascades (multiple error types in short period)
  const errorsByType = recentErrors.reduce((acc, err) => {
    acc[err.type] = (acc[err.type] || 0) + 1;
    return acc;
  }, {});

  if (Object.keys(errorsByType).length >= 3) {
    await mcp__RedisMCPServer__publish({
      channel: "events:errors:correlations",
      message: JSON.stringify({
        type: "error_cascade_detected",
        severity: "critical",
        error_types: Object.keys(errorsByType),
        error_counts: errorsByType,
        recommendation: "Investigate root cause - multiple subsystems failing",
        timestamp: new Date().toISOString()
      })
    });
  }
}
```

**Considerations:**

- Set TTL on error logs to prevent memory bloat (7 days for tasks, 30 days for training)
- Use `lrange` with reasonable limits (last 100 errors, not all)
- Store error details in hashes for structured querying
- Track error signatures in sets for deduplication

## Pattern 4: Circuit Breaker Coordination

**Use Case:** Prevent cascade failures by stopping requests to failing components

**Why Redis?** Distributed state sharing; atomic state transitions; auto-reset with expiration.

**Implementation:**

```javascript
// File: error-coordinator/circuit-breaker.js

// Circuit breaker states: closed, open, half-open
async function checkCircuitBreaker(component) {
  const state = await mcp__RedisMCPServer__hget({
    name: `circuit_breakers:${component}`,
    key: "state"
  });

  if (!state || state === "closed") {
    return { open: false, state: "closed" };
  }

  if (state === "open") {
    // Check if timeout expired (transition to half-open)
    const openedAt = await mcp__RedisMCPServer__hget({
      name: `circuit_breakers:${component}`,
      key: "opened_at"
    });

    const timeout = 300000;  // 5 minutes
    const elapsed = Date.now() - parseInt(openedAt);

    if (elapsed > timeout) {
      // Transition to half-open (allow test request)
      await mcp__RedisMCPServer__hset({
        name: `circuit_breakers:${component}`,
        key: "state",
        value: "half-open"
      });

      await mcp__RedisMCPServer__publish({
        channel: "events:errors:circuit_breakers",
        message: JSON.stringify({
          type: "circuit_breaker_half_open",
          component,
          timestamp: new Date().toISOString()
        })
      });

      return { open: false, state: "half-open" };
    }

    return { open: true, state: "open" };
  }

  return { open: false, state };
}

// Open circuit breaker after repeated failures
async function openCircuitBreaker(component, reason) {
  await mcp__RedisMCPServer__hset({
    name: `circuit_breakers:${component}`,
    key: "state",
    value: "open"
  });

  await mcp__RedisMCPServer__hset({
    name: `circuit_breakers:${component}`,
    key: "opened_at",
    value: Date.now().toString()
  });

  // Auto-close after timeout using expiration
  await mcp__RedisMCPServer__expire({
    name: `circuit_breakers:${component}`,
    expire_seconds: 300  // 5 minutes
  });

  await mcp__RedisMCPServer__publish({
    channel: "events:errors:circuit_breakers",
    message: JSON.stringify({
      type: "circuit_breaker_opened",
      component,
      reason,
      timestamp: new Date().toISOString()
    })
  });
}

// Close circuit breaker after successful test in half-open state
async function recordCircuitBreakerSuccess(component) {
  const state = await mcp__RedisMCPServer__hget({
    name: `circuit_breakers:${component}`,
    key: "state"
  });

  if (state === "half-open") {
    await mcp__RedisMCPServer__hset({
      name: `circuit_breakers:${component}`,
      key: "state",
      value: "closed"
    });

    await mcp__RedisMCPServer__publish({
      channel: "events:errors:circuit_breakers",
      message: JSON.stringify({
        type: "circuit_breaker_closed",
        component,
        reason: "recovery_successful",
        timestamp: new Date().toISOString()
      })
    });
  }
}

// Usage: Execute task with circuit breaker protection
async function executeWithCircuitBreaker(component, taskFn) {
  const breaker = await checkCircuitBreaker(component);

  if (breaker.open) {
    throw new Error(`Circuit breaker open for ${component}`);
  }

  try {
    const result = await taskFn();
    await recordCircuitBreakerSuccess(component);
    return result;
  } catch (error) {
    await openCircuitBreaker(component, error.message);
    throw error;
  }
}
```

**Considerations:**

- Use hash for circuit breaker state (allows atomic multi-field updates)
- Auto-reset with `expire` to transition from open ' closed
- Broadcast state changes via pub/sub for observability
- Implement half-open state for gradual recovery

## Pattern 5: Retry Queue with Exponential Backoff

**Use Case:** Retry failed tasks with exponential backoff and dead letter queue

**Why Lists?** Natural FIFO queue; atomic push/pop; supports delay with metadata.

**Implementation:**

```javascript
// File: error-coordinator/retry-queue.js

async function enqueueForRetry(taskId, projectId, agent, error, attempt = 0) {
  const MAX_RETRIES = 3;

  if (attempt >= MAX_RETRIES) {
    // Move to dead letter queue
    await mcp__RedisMCPServer__rpush({
      name: "retry:dead_letter_queue",
      value: JSON.stringify({
        taskId,
        projectId,
        agent,
        error: error.message,
        attempts: attempt,
        timestamp: new Date().toISOString()
      })
    });

    await mcp__RedisMCPServer__publish({
      channel: "events:errors:retry_exhausted",
      message: JSON.stringify({
        type: "retry_exhausted",
        taskId,
        projectId,
        attempts: attempt,
        timestamp: new Date().toISOString()
      })
    });

    return;
  }

  // Calculate exponential backoff with jitter
  const baseDelay = 1000;  // 1 second
  const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;

  // Enqueue with delay metadata
  await mcp__RedisMCPServer__rpush({
    name: "retry:queue",
    value: JSON.stringify({
      taskId,
      projectId,
      agent,
      error: error.message,
      attempt: attempt + 1,
      retryAfter: Date.now() + delay,
      timestamp: new Date().toISOString()
    })
  });

  await mcp__RedisMCPServer__publish({
    channel: "events:errors:retry_scheduled",
    message: JSON.stringify({
      type: "retry_scheduled",
      taskId,
      attempt: attempt + 1,
      delayMs: delay,
      timestamp: new Date().toISOString()
    })
  });
}

// Retry queue processor (background worker)
async function processRetryQueue() {
  while (true) {
    const item = await mcp__RedisMCPServer__lpop({
      name: "retry:queue"
    });

    if (!item) {
      await sleep(1000);  // Wait 1 second before checking again
      continue;
    }

    const retryTask = JSON.parse(item);

    // Check if delay elapsed
    if (Date.now() < retryTask.retryAfter) {
      // Re-enqueue (not ready yet)
      await mcp__RedisMCPServer__rpush({
        name: "retry:queue",
        value: item
      });
      await sleep(100);
      continue;
    }

    // Check circuit breaker before retrying
    const breaker = await checkCircuitBreaker(`agent:${retryTask.agent}`);
    if (breaker.open) {
      retryTask.retryAfter = Date.now() + 60000;  // 1 minute
      await mcp__RedisMCPServer__rpush({
        name: "retry:queue",
        value: JSON.stringify(retryTask)
      });
      continue;
    }

    // Execute retry
    try {
      await executeTask(retryTask.taskId, retryTask.agent);

      await mcp__RedisMCPServer__publish({
        channel: "events:errors:retry_success",
        message: JSON.stringify({
          type: "retry_success",
          taskId: retryTask.taskId,
          attempt: retryTask.attempt,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      // Retry failed, enqueue again with incremented attempt
      await enqueueForRetry(
        retryTask.taskId,
        retryTask.projectId,
        retryTask.agent,
        error,
        retryTask.attempt
      );
    }
  }
}
```

**Considerations:**

- Use `rpush` + `lpop` for FIFO queue processing
- Store delay in metadata, not Redis TTL (allows re-queuing)
- Implement jitter to prevent thundering herd
- Use dead letter queue for manual intervention after max retries
- Check circuit breakers before retry attempts

## Pattern 6: Time-Series Metrics Storage

**Use Case:** Store training metrics, performance data, and system health over time

**Why Lists?** Chronological ordering; efficient append; range queries for time windows.

**Implementation:**

```javascript
// File: performance-monitor/metrics-storage.js

// Store training loss metrics
async function recordTrainingMetric(projectId, step, metrics) {
  await mcp__RedisMCPServer__lpush({
    name: `metrics:training:${projectId}:loss`,
    value: JSON.stringify({
      timestamp: Date.now(),
      step,
      loss: metrics.loss,
      learning_rate: metrics.learningRate
    })
  });

  // Limit to last 1000 metrics (trim old data)
  const length = await mcp__RedisMCPServer__llen({
    name: `metrics:training:${projectId}:loss`
  });

  if (length > 1000) {
    // Remove oldest metrics (beyond 1000)
    await mcp__RedisMCPServer__ltrim({
      name: `metrics:training:${projectId}:loss`,
      start: 0,
      stop: 999
    });
  }
}

// Retrieve recent metrics for visualization
async function getRecentMetrics(projectId, limit = 100) {
  const metricsJson = await mcp__RedisMCPServer__lrange({
    name: `metrics:training:${projectId}:loss`,
    start: 0,
    stop: limit - 1
  });

  return metricsJson.map(m => JSON.parse(m));
}

// Calculate moving average
async function calculateMovingAverage(projectId, windowSize = 10) {
  const recentMetrics = await getRecentMetrics(projectId, windowSize);
  const avgLoss = recentMetrics.reduce((sum, m) => sum + m.loss, 0) / recentMetrics.length;
  return avgLoss;
}
```

**Considerations:**

- Use `lpush` for newest-first ordering
- Trim lists periodically to prevent unbounded growth
- Set TTL on entire list for automatic cleanup
- For large-scale metrics, consider sorted sets with timestamps as scores

## Best Practices

1. **Namespace keys consistently** - Use `type:entity:id` pattern (e.g., `context:project:proj-1`)
1. **Use hashes for structured data** - More efficient than JSON strings in key-value pairs
1. **Set expiration on temporary data** - Prevent memory leaks with `expire_seconds`
1. **Batch reads when possible** - `hgetall` instead of multiple `hget` calls
1. **Use pub/sub for real-time events** - Async, non-blocking, multiple subscribers
1. **Scan with patterns, not KEYS** - `scan_all_keys` is production-safe, `KEYS *` blocks server
1. **Implement TTL on error logs** - 7 days for tasks, 30 days for training, 90 days for correlations
1. **Monitor memory usage** - Redis is in-memory; plan capacity and eviction policies
1. **Serialize complex objects as JSON** - Before storing in strings or publishing
1. **Use lists for queues, not pub/sub** - Pub/sub has no delivery guarantees; lists are durable

## Related Agents

- **error-coordinator** (`plugins/mycelium-core/agents/09-meta-error-coordinator.md`) - Error tracking, correlation,
  circuit breakers
- **context-manager** (`plugins/mycelium-core/agents/09-meta-context-manager.md`) - Shared state, context storage,
  synchronization
- **performance-monitor** - Metrics storage and time-series analysis
- **multi-agent-coordinator** - Agent workload distribution and task routing

## References

- [Redis Documentation](https://redis.io/docs/)
- [Redis MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/redis)
- [Pub/Sub Best Practices](https://redis.io/docs/manual/pubsub/)
- [Redis Data Types](https://redis.io/docs/data-types/)
