# Multi-Agent Coordination Test Plan

## Sprint 1 Redis MCP Validation

**Test Date**: 2025-11-07 **Test Coordinator**: multi-agent-coordinator **Objective**: Validate Redis MCP coordination
fixes with real multi-agent workflow

______________________________________________________________________

## Test Scenario: Code Quality Assessment Workflow

This test simulates a realistic multi-agent collaboration for code quality assessment:

### Participating Agents (4 specialists)

1. **code-reviewer** - Review Python code quality and architecture
1. **qa-expert** - Analyze test coverage and quality
1. **security-auditor** - Perform security analysis
1. **performance-engineer** - Assess performance characteristics

### Test Workflow

Each agent will:

- Report initial status to Redis (0% workload)
- Accept assigned task and update workload
- Send periodic heartbeats during work
- Update progress as they work
- Report completion

### Tasks Assigned

**Task 1 - Code Reviewer** (40% workload):

- Review `/home/gerald/git/mycelium/mycelium_onboarding/coordination/redis_helper.py`
- Assess code quality, architecture, best practices
- Duration: ~5 minutes

**Task 2 - QA Expert** (75% workload):

- Analyze test coverage for the mycelium project
- Review test quality and identify gaps
- Duration: ~8 minutes

**Task 3 - Security Auditor** (100% workload):

- Security audit of Redis coordination helper
- Check for vulnerabilities, injection risks
- Duration: ~10 minutes

**Task 4 - Performance Engineer** (60% workload):

- Performance analysis of agent discovery system
- Review memory usage, latency characteristics
- Duration: ~6 minutes

______________________________________________________________________

## Coordination Protocol

Each agent will use RedisCoordinationHelper to:

```python
from mycelium_onboarding.coordination.redis_helper import RedisCoordinationHelper

# Initialize
helper = RedisCoordinationHelper(redis_client)

# Report initial status
await helper.set_agent_status("code-reviewer", {
    "status": "idle",
    "workload": 0,
    "current_task": None,
    "started_at": datetime.now()
})

# Update heartbeat
await helper.update_heartbeat("code-reviewer")

# Accept task
await helper.set_agent_status("code-reviewer", {
    "status": "busy",
    "workload": 40,
    "current_task": {
        "id": "code-review-redis-helper",
        "progress": 0,
        "description": "Review Redis coordination helper code quality"
    },
    "started_at": datetime.now()
})

# Update progress
await helper.set_agent_status("code-reviewer", {
    "status": "busy",
    "workload": 40,
    "current_task": {
        "id": "code-review-redis-helper",
        "progress": 50,
        "description": "Review Redis coordination helper code quality"
    },
    "started_at": task_start_time
})

# Complete task
await helper.set_agent_status("code-reviewer", {
    "status": "completed",
    "workload": 0,
    "current_task": None,
    "completed_at": datetime.now()
})
```

______________________________________________________________________

## Success Criteria

### 1. Agent Registration

- [ ] All 4 agents successfully register in Redis
- [ ] JSON serialization works without errors
- [ ] Initial status shows 0% workload

### 2. Workload Tracking

- [ ] Workload percentages update correctly (40%, 75%, 100%, 60%)
- [ ] Progress bars display properly in `/team-status`
- [ ] Statistics calculate correctly (total, average, variance)

### 3. Task Coordination

- [ ] Active tasks tracked per agent
- [ ] Task IDs and descriptions visible
- [ ] Progress updates reflect in Redis

### 4. Heartbeat Monitoring

- [ ] Heartbeat timestamps serialize to ISO format
- [ ] Timestamps deserialize back to datetime objects
- [ ] Age calculations work correctly
- [ ] Fresh heartbeats show "healthy" status

### 5. Team Status Display

- [ ] `/team-status` shows formatted output
- [ ] Progress bars render (10 blocks with █ and ░)
- [ ] No JSON parsing errors
- [ ] Datetime fields display correctly
- [ ] Load variance calculation works
- [ ] Balance status displays correctly

### 6. Error Handling

- [ ] No Redis connection errors
- [ ] No JSON serialization errors
- [ ] No datetime conversion errors
- [ ] Graceful handling of missing fields

______________________________________________________________________

## Validation Steps

### Step 1: Pre-Test Baseline

```bash
# Verify Redis is clean
/team-status
# Expected: Empty or minimal coordination data
```

### Step 2: Launch Agent Coordination

Execute the multi-agent workflow (see test_coordination.py)

### Step 3: Monitor Live Coordination

```bash
# While agents are working
/team-status
# Expected: 4 agents with varying workloads
```

### Step 4: Check Detailed Agent Status

```bash
/team-status code-reviewer
/team-status qa-expert
/team-status security-auditor
/team-status performance-engineer
```

### Step 5: Verify Statistics

- Total tasks: 4
- Average load: (40 + 75 + 100 + 60) / 4 = 68.75%
- Load variance: Calculate standard deviation
- Balance status: Should show variance

### Step 6: Post-Test Cleanup

```bash
# Verify all agents completed
/team-status
# Expected: All agents show 0% workload or completed status
```

______________________________________________________________________

## Expected Results

### Initial State (Pre-Test)

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

### Active Coordination (Mid-Test)

```
=== Multi-Agent Team Status ===
Coordination Method: Redis MCP

Agent Workload:
  security-auditor     ██████████ 100% | 1 active task (at capacity)
  qa-expert            ████████░░ 75% | 1 active task
  performance-eng      ██████░░░░ 60% | 1 active task
  code-reviewer        ████░░░░░░ 40% | 1 active task

Task Distribution:
  Total Active: 4 tasks
  Average Load: 69%
  Load Variance: 24% (⚠️ unbalanced)

Heartbeat Status:
  ✅ All agents reporting healthy

Last Updated: 2025-11-07 20:45:30
```

### Detailed Agent View (Mid-Test)

```
=== Agent Status: security-auditor ===

Current Status: BUSY (100% capacity)

Active Tasks (1):
  1. security-audit-redis-helper
     - Progress: 45%
     - Duration: 4m 23s
     - Description: Security audit of Redis coordination helper

Recent History (from status data):
  - Current workload: 100%
  - Task count: 1
  - Last updated: 23s ago

Circuit Breaker: ✅ CLOSED (healthy)
Last Heartbeat: 23s ago
```

______________________________________________________________________

## Test Execution Plan

1. **Create test orchestration script** (Python)

   - Initialize Redis connection
   - Create RedisCoordinationHelper instances for each agent
   - Launch agents in parallel threads/asyncio tasks
   - Each agent performs real work on assigned tasks
   - Monitor coordination state

1. **Execute test workflow**

   - Run orchestration script
   - Monitor `/team-status` output at different stages
   - Capture screenshots/logs of coordination

1. **Validate all success criteria**

   - Check JSON serialization
   - Verify datetime handling
   - Confirm statistics calculations
   - Test error handling

1. **Generate test report**

   - Document results
   - Note any issues found
   - Provide recommendations

______________________________________________________________________

## Risk Assessment

### Potential Issues

1. **Redis Connection**: Redis MCP server may not be available

   - Mitigation: Pre-check with `/infra-check`

1. **JSON Serialization**: Complex objects may fail to serialize

   - Mitigation: RedisCoordinationHelper handles this

1. **Datetime Conversion**: Timezone issues or format inconsistencies

   - Mitigation: ISO format with explicit conversion

1. **Concurrent Access**: Race conditions in Redis updates

   - Mitigation: Redis atomic operations

1. **Memory Leaks**: Long-running agents may accumulate state

   - Mitigation: Time-bound test execution

### Contingency Plans

- If Redis unavailable: Document fallback to markdown mode
- If serialization fails: Capture error details for debugging
- If agents fail to coordinate: Check MCP tool availability

______________________________________________________________________

## Test Deliverables

1. **Test Execution Report**

   - Before/after `/team-status` outputs
   - Detailed agent status captures
   - Success criteria validation results

1. **Issue Log**

   - Any errors encountered
   - Unexpected behaviors
   - Performance observations

1. **Recommendations**

   - Improvements for coordination system
   - Additional test scenarios
   - Documentation updates

______________________________________________________________________

## Next Steps After Testing

1. **Document results** in Sprint 1 completion report
1. **File issues** for any bugs discovered
1. **Update coordination documentation** based on learnings
1. **Plan Sprint 2** enhancements if needed
1. **Share test patterns** with other agents for future coordination testing
