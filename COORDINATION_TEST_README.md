# Multi-Agent Coordination Test - Execution Guide

## Sprint 1 Redis MCP Validation

This guide walks you through executing the comprehensive multi-agent coordination test to validate Sprint 1 Redis MCP
fixes.

______________________________________________________________________

## Quick Start

### 1. Pre-Flight Check

Verify your environment is ready:

```bash
# Check Redis MCP availability
/infra-check

# Verify clean coordination state
/team-status
```

Expected: Redis healthy or coordination directory ready.

### 2. Run the Test

Execute the multi-agent coordination workflow:

```bash
cd /home/gerald/git/mycelium
python3 test_coordination_workflow.py
```

This launches 4 agents performing real coordination tasks.

### 3. Monitor Coordination

While agents are working (in another terminal or after pausing):

```bash
# View all agents
/team-status

# View specific agent details
/team-status code-reviewer
/team-status qa-expert
/team-status security-auditor
/team-status performance-engineer
```

### 4. Validate Results

Check the test output for validation results:

- Agent registration: 4/4 agents
- JSON serialization: No errors
- Workload tracking: Correct percentages
- Task coordination: All tasks tracked
- Heartbeat monitoring: All healthy

______________________________________________________________________

## Test Artifacts

### Files Created

1. **Test Plan**: `/home/gerald/git/mycelium/test_multi_agent_coordination.md`

   - Comprehensive test scenario description
   - Success criteria definitions
   - Risk assessment

1. **Test Orchestrator**: `/home/gerald/git/mycelium/test_coordination_workflow.py`

   - Main test execution script
   - Agent simulation with real coordination
   - Validation logic

1. **Test Report Template**: `/home/gerald/git/mycelium/COORDINATION_TEST_REPORT.md`

   - Structured report for capturing results
   - Pre-defined validation criteria
   - Appendices for evidence

1. **Agent Coordinator Utility**: `/home/gerald/git/mycelium/scripts/agent_coordinator.py`

   - CLI tool for agents to report status
   - Can be used by any agent for coordination
   - Supports status, heartbeat, task updates

1. **This Guide**: `/home/gerald/git/mycelium/COORDINATION_TEST_README.md`

   - Execution instructions
   - Troubleshooting tips

______________________________________________________________________

## Test Scenario Details

### Agents Involved

**1. code-reviewer** (40% workload)

- Task: Review Redis coordination helper code quality
- Focus: Architecture, best practices, maintainability
- Duration: ~10 seconds

**2. qa-expert** (75% workload)

- Task: Analyze test coverage for mycelium project
- Focus: Test quality, coverage gaps, test patterns
- Duration: ~15 seconds

**3. security-auditor** (100% workload - at capacity)

- Task: Security audit of Redis coordination helper
- Focus: Vulnerabilities, injection risks, security best practices
- Duration: ~20 seconds

**4. performance-engineer** (60% workload)

- Task: Performance analysis of agent discovery system
- Focus: Memory usage, latency characteristics, optimization
- Duration: ~12 seconds

### Coordination Flow

Each agent follows this workflow:

```
1. Initialize → Report idle status (0% workload)
                    ↓
2. Accept Task → Update status to busy with workload %
                    ↓
3. Work → Send periodic heartbeats
         → Update progress every ~2 seconds
                    ↓
4. Complete → Report completion (0% workload)
```

### Expected Statistics

- **Total Active Tasks**: 4
- **Average Workload**: 68.75%
- **Load Variance**: ~24% (should show "⚠️ unbalanced")
- **Coordination Overhead**: \< 5%

______________________________________________________________________

## What to Look For

### ✓ Success Indicators

**In Test Output**:

```
✓ Agent registration: 4 agents registered
✓ JSON serialization: No errors
✓ Workload tracking: All agents at 0% (completed)
✓ Task coordination: All agents tracked tasks
✓ Heartbeat monitoring: All agents reporting healthy
```

**In `/team-status` (mid-test)**:

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
```

### ✗ Failure Indicators

**Error Messages**:

- JSON parsing errors
- Datetime conversion failures
- Redis connection errors
- Missing agent data

**Incorrect Display**:

- Progress bars not rendering (missing █ ░ blocks)
- Statistics calculations wrong
- Workload percentages incorrect
- Heartbeat status not updating

______________________________________________________________________

## Detailed Test Execution

### Step-by-Step Process

#### Step 1: Pre-Test Baseline

Capture initial state:

```bash
# Check infrastructure
/infra-check > pre_test_infra.log

# Check team status
/team-status > pre_test_status.log
```

Expected: Clean state, no active agents.

______________________________________________________________________

#### Step 2: Launch Test

Run the orchestrator:

```bash
python3 test_coordination_workflow.py 2>&1 | tee test_execution.log
```

Watch for:

- 4 agents launching
- Status updates every ~2 seconds
- Progress increasing: 0% → 20% → 40% → 60% → 80% → 100%
- Heartbeats being sent
- Validation results at end

______________________________________________________________________

#### Step 3: Monitor Mid-Test (Optional)

If you want to see live coordination, pause the test or run in separate terminal:

```bash
# General status
/team-status

# Detailed views
/team-status code-reviewer
/team-status qa-expert
/team-status security-auditor
/team-status performance-engineer
```

Verify:

- Progress bars display correctly
- Workload percentages match expected (40%, 75%, 100%, 60%)
- Task descriptions are visible
- Heartbeat timestamps are recent

______________________________________________________________________

#### Step 4: Post-Test Verification

After test completes:

```bash
# Check final status
/team-status > post_test_status.log

# Verify agents are idle or completed
# All workloads should be 0%
```

______________________________________________________________________

#### Step 5: Analyze Results

Review test output:

```bash
# Check validation results
cat test_execution.log | grep "✓"

# Look for any errors
cat test_execution.log | grep -i error

# Review final statistics
cat test_execution.log | grep -A 10 "Test Results Summary"
```

______________________________________________________________________

## Using the Agent Coordinator Utility

The `/home/gerald/git/mycelium/scripts/agent_coordinator.py` utility can be used by any agent to report coordination
status.

### Examples

**Report idle status**:

```bash
python scripts/agent_coordinator.py report code-reviewer --status idle
```

**Report active task**:

```bash
python scripts/agent_coordinator.py report code-reviewer \
    --status busy \
    --workload 75 \
    --task-id code-review-main \
    --task-desc "Reviewing main application code" \
    --progress 45
```

**Update heartbeat**:

```bash
python scripts/agent_coordinator.py heartbeat code-reviewer
```

**Get agent status**:

```bash
python scripts/agent_coordinator.py get code-reviewer
```

**List all agents**:

```bash
python scripts/agent_coordinator.py list
```

### Integration with Agents

Specialized agents can invoke this utility to report their status:

```bash
# In an agent's workflow
python scripts/agent_coordinator.py report my-agent-type \
    --status busy \
    --workload 50 \
    --task-id my-task \
    --task-desc "Doing important work" \
    --progress 25
```

______________________________________________________________________

## Troubleshooting

### Redis Not Available

**Symptom**: Test fails with "Redis initialization failed" or MCP errors

**Solution**:

1. Check if Redis MCP is running: `/infra-check`
1. The test uses a mock Redis client by default for demonstration
1. To use real Redis, modify the orchestrator's `use_mock` parameter

### JSON Serialization Errors

**Symptom**: Errors about objects not being JSON serializable

**Solution**:

- This should not happen due to RedisCoordinationHelper's datetime handling
- If it does, check the test logs for the specific object causing issues
- File an issue with the error details

### /team-status Not Showing Agents

**Symptom**: `/team-status` shows "No agents currently coordinating"

**Solution**:

1. Verify test completed: `cat test_execution.log | tail -20`
1. Check if agents wrote to Redis: `python scripts/agent_coordinator.py list`
1. Ensure Redis MCP is connected

### Progress Bars Not Rendering

**Symptom**: Progress bars show as plain text instead of █ ░ blocks

**Solution**:

- This may be a terminal encoding issue
- Try a different terminal that supports UTF-8
- The data is still correct even if display is wrong

### Statistics Calculations Wrong

**Symptom**: Average load or variance doesn't match expected values

**Solution**:

1. Verify workload percentages in Redis: `python scripts/agent_coordinator.py list`
1. Calculate manually:
   - Average: (40 + 75 + 100 + 60) / 4 = 68.75%
   - Variance: ~24%
1. If calculations still wrong, file an issue

______________________________________________________________________

## Validation Checklist

Use this checklist while executing the test:

### Pre-Test

- [ ] Redis MCP is available or mock mode is acceptable
- [ ] Coordination state is clean (`/team-status` shows empty)
- [ ] Test files are in place
- [ ] Python environment is ready

### During Test

- [ ] 4 agents launch successfully
- [ ] Progress updates appear in logs
- [ ] Heartbeats are being sent
- [ ] No error messages in output

### Post-Test

- [ ] All validation checks pass (✓)
- [ ] `/team-status` displays formatted output correctly
- [ ] Progress bars render properly
- [ ] Statistics calculate correctly
- [ ] Agents show 0% workload (completed)

### Documentation

- [ ] Capture test output logs
- [ ] Screenshot `/team-status` outputs
- [ ] Fill in test report template
- [ ] Document any issues found

______________________________________________________________________

## Test Report Completion

After executing the test:

1. **Fill in test report**: `/home/gerald/git/mycelium/COORDINATION_TEST_REPORT.md`

   - Replace all `[To be captured during test]` sections
   - Add actual outputs, screenshots, logs
   - Check all validation criteria boxes

1. **Capture evidence**:

   - Save test execution logs
   - Screenshot `/team-status` at different stages
   - Export Redis data samples if possible

1. **Assess Sprint 1 readiness**:

   - If all checks pass → Sprint 1 COMPLETE
   - If issues found → Document and prioritize fixes

1. **Generate summary**:

   - Overall pass/fail status
   - Key findings
   - Recommendations for next steps

______________________________________________________________________

## Success Criteria Summary

For Sprint 1 to be considered COMPLETE, all these must pass:

✅ **Agent Registration**

- 4/4 agents register successfully
- JSON serialization works
- No errors

✅ **Workload Tracking**

- Percentages update correctly (40%, 75%, 100%, 60%)
- Progress bars display
- Statistics accurate

✅ **Task Coordination**

- All tasks tracked
- IDs and descriptions visible
- Progress updates work

✅ **Heartbeat Monitoring**

- Timestamps serialize/deserialize correctly
- Age calculations work
- Healthy status displays

✅ **Team Status Display**

- Formatted output renders
- No parsing errors
- Datetime fields correct

✅ **Error Handling**

- No Redis errors
- No JSON errors
- Graceful degradation

______________________________________________________________________

## Next Steps After Testing

### If All Tests Pass ✓

1. **Mark Sprint 1 COMPLETE**
1. **Commit test results** to repository
1. **Update documentation** with test findings
1. **Plan Sprint 2** enhancements
1. **Share test patterns** with other teams

### If Tests Fail ✗

1. **Document failures** in test report
1. **File issues** for bugs discovered
1. **Prioritize fixes** (critical vs nice-to-have)
1. **Re-run tests** after fixes
1. **Update Sprint 1 timeline** if needed

______________________________________________________________________

## Support

If you encounter issues during testing:

1. **Check logs**: `test_execution.log` for detailed output
1. **Review test plan**: `test_multi_agent_coordination.md`
1. **Consult report template**: `COORDINATION_TEST_REPORT.md`
1. **Use coordinator utility**: `scripts/agent_coordinator.py` for debugging

______________________________________________________________________

## Appendix: File Locations

All test files are in `/home/gerald/git/mycelium/`:

```
mycelium/
├── test_multi_agent_coordination.md        # Test plan
├── test_coordination_workflow.py           # Test orchestrator
├── COORDINATION_TEST_REPORT.md             # Report template
├── COORDINATION_TEST_README.md             # This guide
├── scripts/
│   └── agent_coordinator.py                # Coordination utility
└── mycelium_onboarding/
    └── coordination/
        └── redis_helper.py                 # Coordination library
```

Redis coordination command:

```
plugins/mycelium-core/commands/team-status.md
```

______________________________________________________________________

**Ready to Test?**

Run: `python3 test_coordination_workflow.py`

Then: `/team-status` to see the results!

______________________________________________________________________

*This test validates Sprint 1 Redis MCP coordination fixes and demonstrates real multi-agent collaboration patterns.*
