# Sprint 4: Temporal Workflow Testing - Multi-Agent Coordination Plan

**Sprint Branch**: `feat/smart-onboarding-sprint4-temporal-testing`
**Base Branch**: `feat/smart-onboarding-sprint3-postgres-compat`
**Coordination Mode**: Task-based with dependency management
**Estimated Duration**: 12-16 hours
**Target Completion**: 2025-11-09

---

## Executive Summary

Deploy and validate Temporal with PostgreSQL backend using existing mycelium tooling, creating comprehensive test workflows to identify integration issues and validate the PostgreSQL compatibility system built in Sprint 3.

### Success Metrics

- Temporal deploys successfully with PostgreSQL backend
- Test workflow executes without errors
- Workflow state persists correctly across restarts
- Temporal UI accessible and functional
- Worker connects and processes activities
- All deployment issues documented and fixed
- PostgreSQL version compatibility warnings validated

---

## Agent Selection & Role Assignment

### Selected Agents (3 specialized experts)

#### 1. **devops-engineer** (Lead Deployment & Infrastructure)
**Primary Responsibilities:**
- Deploy Temporal + PostgreSQL using `mycelium deploy start`
- Validate deployment configurations
- Monitor service health and connectivity
- Handle deployment troubleshooting
- Document infrastructure setup

**Key Expertise:**
- Docker Compose orchestration
- Service health checks
- Network connectivity validation
- Environment configuration
- Log analysis

**Tools**: Bash, Read, Write

---

#### 2. **python-pro** (Test Workflow Development)
**Primary Responsibilities:**
- Design and implement Temporal test workflow
- Create worker implementation
- Develop workflow execution scripts
- Write activity handlers
- Implement signal/query handlers

**Key Expertise:**
- Python Temporal SDK
- Async workflow patterns
- Activity design
- Error handling
- State management

**Tools**: Read, Write, Bash(python:*)

**Deliverables:**
- `/home/gerald/git/mycelium/tests/integration/temporal/test_workflow.py`
- `/home/gerald/git/mycelium/tests/integration/temporal/worker.py`
- `/home/gerald/git/mycelium/tests/integration/temporal/execute_workflow.py`

---

#### 3. **qa-engineer** (Testing & Validation)
**Primary Responsibilities:**
- Execute test workflows
- Validate persistence across restarts
- Test PostgreSQL version compatibility warnings
- Document all issues found
- Verify fixes applied

**Key Expertise:**
- Integration testing
- Test case design
- Issue documentation
- Validation procedures
- Regression testing

**Tools**: Read, Write, Bash

**Deliverables:**
- Test execution reports
- Issue documentation with reproduction steps
- Validation checklists

---

## Detailed Task Breakdown & Dependencies

### Phase 1: Test Workflow Creation (3-4 hours)

**Task 1.1: Design Test Workflow Architecture**
- **Agent**: python-pro
- **Dependencies**: None (can start immediately)
- **Duration**: 1 hour
- **Output**: Workflow design document

**Workflow Requirements:**
```python
# Test workflow must validate:
1. Activity execution (worker connectivity)
2. State persistence (sleep and resume)
3. Child workflows (nested execution)
4. Signal handling (external communication)
5. Query handling (workflow state queries)
```

**Task 1.2: Implement Core Test Workflow**
- **Agent**: python-pro
- **Dependencies**: Task 1.1
- **Duration**: 2 hours
- **Files**:
  - `/home/gerald/git/mycelium/tests/integration/temporal/test_workflow.py`
  - `/home/gerald/git/mycelium/tests/integration/temporal/activities.py`

**Task 1.3: Implement Worker & Execution Scripts**
- **Agent**: python-pro
- **Dependencies**: Task 1.2
- **Duration**: 1 hour
- **Files**:
  - `/home/gerald/git/mycelium/tests/integration/temporal/worker.py`
  - `/home/gerald/git/mycelium/tests/integration/temporal/execute_workflow.py`

---

### Phase 2: Deployment Validation (2-3 hours)

**Task 2.1: Deploy Temporal + PostgreSQL**
- **Agent**: devops-engineer
- **Dependencies**: None (parallel with Phase 1)
- **Duration**: 1 hour
- **Commands**:
```bash
cd /home/gerald/git/mycelium
mycelium deploy start --auto-approve
```

**Expected Validation:**
- PostgreSQL compatibility check passes
- Temporal services start successfully
- PostgreSQL connection established
- Temporal UI accessible at http://localhost:8080

**Task 2.2: Verify Service Health**
- **Agent**: devops-engineer
- **Dependencies**: Task 2.1
- **Duration**: 30 minutes
- **Checks**:
```bash
# Service status
mycelium deploy status

# PostgreSQL connectivity
psql -h localhost -p 5432 -U temporal -d temporal -c "SELECT version();"

# Temporal server health
curl http://localhost:7233/api/v1/namespaces

# UI accessibility
curl http://localhost:8080
```

**Task 2.3: Validate PostgreSQL Schema**
- **Agent**: devops-engineer
- **Dependencies**: Task 2.2
- **Duration**: 30 minutes
- **Validation**:
```sql
-- Check Temporal schema created
\dt temporal.*;

-- Verify key tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'temporal';
```

**Task 2.4: Document Deployment Configuration**
- **Agent**: devops-engineer
- **Dependencies**: Task 2.3
- **Duration**: 1 hour
- **Output**: `/home/gerald/git/mycelium/docs/TEMPORAL_DEPLOYMENT.md`

---

### Phase 3: Workflow Execution Testing (2-3 hours)

**Task 3.1: Start Temporal Worker**
- **Agent**: python-pro
- **Dependencies**: Task 1.3, Task 2.2
- **Duration**: 30 minutes
- **Command**:
```bash
cd /home/gerald/git/mycelium
python tests/integration/temporal/worker.py
```

**Expected Output:**
- Worker connects to Temporal server
- Task queue registered
- Activities registered
- Worker polling for tasks

**Task 3.2: Execute Test Workflow**
- **Agent**: qa-engineer
- **Dependencies**: Task 3.1
- **Duration**: 1 hour
- **Command**:
```bash
python tests/integration/temporal/execute_workflow.py
```

**Validation Checkpoints:**
1. Workflow starts successfully
2. Activities execute in order
3. Workflow sleeps and resumes
4. Child workflow completes
5. Signal received and processed
6. Query returns correct state
7. Workflow completes successfully

**Task 3.3: Monitor Execution in Temporal UI**
- **Agent**: qa-engineer
- **Dependencies**: Task 3.2
- **Duration**: 30 minutes
- **UI Checks**:
  - Workflow appears in UI
  - Event history visible
  - Activity results recorded
  - Timeline accurate
  - No errors in events

**Task 3.4: Validate PostgreSQL Persistence**
- **Agent**: devops-engineer
- **Dependencies**: Task 3.2
- **Duration**: 1 hour
- **SQL Queries**:
```sql
-- Workflow executions
SELECT * FROM temporal.executions WHERE workflow_id = 'test-workflow-001';

-- Event history
SELECT * FROM temporal.events WHERE workflow_id = 'test-workflow-001';

-- Activity completions
SELECT * FROM temporal.activities WHERE workflow_id = 'test-workflow-001';
```

---

### Phase 4: Persistence Testing (1-2 hours)

**Task 4.1: Stop Temporal Services**
- **Agent**: devops-engineer
- **Dependencies**: Task 3.4
- **Duration**: 15 minutes
- **Command**:
```bash
mycelium deploy stop
```

**Task 4.2: Restart Services**
- **Agent**: devops-engineer
- **Dependencies**: Task 4.1
- **Duration**: 30 minutes
- **Command**:
```bash
mycelium deploy start --auto-approve
```

**Validation:**
- Services restart successfully
- PostgreSQL data intact
- Temporal schema unchanged

**Task 4.3: Re-execute Test Workflow**
- **Agent**: qa-engineer
- **Dependencies**: Task 4.2
- **Duration**: 45 minutes
- **Validation**:
```bash
# Restart worker
python tests/integration/temporal/worker.py &

# Execute new workflow
python tests/integration/temporal/execute_workflow.py

# Verify workflow history persisted
curl http://localhost:8080/api/v1/workflows/test-workflow-001
```

**Success Criteria:**
- Previous workflow history visible in UI
- New workflow executes successfully
- No data loss detected
- State recovery complete

---

### Phase 5: Issue Resolution & Documentation (2-4 hours)

**Task 5.1: Identify and Document Issues**
- **Agent**: qa-engineer
- **Dependencies**: All Phase 3 & 4 tasks
- **Duration**: 1 hour
- **Output**: `/home/gerald/git/mycelium/docs/SPRINT4_ISSUES.md`

**Issue Template:**
```markdown
### Issue #N: [Title]
**Severity**: Critical | High | Medium | Low
**Phase**: Deployment | Execution | Persistence
**Reproduction Steps**:
**Expected Behavior**:
**Actual Behavior**:
**Logs/Screenshots**:
**Proposed Fix**:
```

**Task 5.2: Fix Deployment Issues**
- **Agent**: devops-engineer
- **Dependencies**: Task 5.1
- **Duration**: 1-2 hours
- **Common Issues to Address**:
  1. Connection string formatting
  2. Environment variable configuration
  3. Port mapping conflicts
  4. Health check timeouts
  5. PostgreSQL schema initialization

**Task 5.3: Fix Workflow Issues**
- **Agent**: python-pro
- **Dependencies**: Task 5.1
- **Duration**: 1-2 hours
- **Common Issues to Address**:
  1. Worker connection failures
  2. Activity serialization errors
  3. Timeout configuration
  4. Error handling gaps
  5. Signal/query handler bugs

**Task 5.4: Validate Fixes**
- **Agent**: qa-engineer
- **Dependencies**: Task 5.2, Task 5.3
- **Duration**: 1 hour
- **Process**:
  1. Clean deployment
  2. Re-run all tests
  3. Verify all issues resolved
  4. Document regression tests

---

### Phase 6: PostgreSQL Compatibility Validation (1-2 hours)

**Task 6.1: Test Version Compatibility Warnings**
- **Agent**: qa-engineer
- **Dependencies**: Task 2.1
- **Duration**: 1 hour
- **Test Cases**:

```bash
# Test 1: Compatible version (should proceed)
mycelium deploy start --postgres-version 15.3 --temporal-version 1.24.0

# Test 2: Old PostgreSQL (should warn)
mycelium deploy start --postgres-version 12.0 --temporal-version 1.24.0

# Test 3: Force override
mycelium deploy start --postgres-version 12.0 --force-version

# Test 4: Auto-detection
mycelium deploy start  # Should detect running PostgreSQL version
```

**Task 6.2: Update Compatibility Matrix**
- **Agent**: devops-engineer
- **Dependencies**: Task 6.1
- **Duration**: 1 hour
- **Actions**:
  1. Document actual PostgreSQL version tested
  2. Verify Temporal version compatibility
  3. Update compatibility data if needed
  4. Document any discrepancies found

---

### Phase 7: Documentation & Cleanup (1-2 hours)

**Task 7.1: Create Deployment Guide**
- **Agent**: devops-engineer
- **Dependencies**: All previous tasks
- **Duration**: 1 hour
- **Output**: `/home/gerald/git/mycelium/docs/TEMPORAL_DEPLOYMENT.md`

**Content:**
- Prerequisites
- Deployment steps
- Configuration options
- Troubleshooting guide
- Health check procedures

**Task 7.2: Document Test Workflow**
- **Agent**: python-pro
- **Dependencies**: All workflow tasks
- **Duration**: 30 minutes
- **Output**: `/home/gerald/git/mycelium/tests/integration/temporal/README.md`

**Content:**
- Workflow architecture
- How to run tests
- Expected results
- Extending tests

**Task 7.3: Create Issue Summary Report**
- **Agent**: qa-engineer
- **Dependencies**: Task 5.4
- **Duration**: 30 minutes
- **Output**: `/home/gerald/git/mycelium/docs/SPRINT4_REPORT.md`

**Sections:**
- Issues found
- Fixes applied
- Test results
- Recommendations

---

## Dependency Graph

```
Phase 1 (Test Workflow)          Phase 2 (Deployment)
┌──────────────────┐            ┌──────────────────┐
│  Task 1.1        │            │  Task 2.1        │
│  Design          │            │  Deploy          │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│  Task 1.2        │            │  Task 2.2        │
│  Implement       │            │  Verify Health   │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│  Task 1.3        │            │  Task 2.3        │
│  Worker/Scripts  │            │  Validate Schema │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │                               ▼
         │                      ┌──────────────────┐
         │                      │  Task 2.4        │
         │                      │  Document        │
         │                      └────────┬─────────┘
         │                               │
         └───────────┬───────────────────┘
                     │
Phase 3              ▼
         ┌──────────────────┐
         │  Task 3.1        │
         │  Start Worker    │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Task 3.2        │
         │  Execute         │
         └────────┬─────────┘
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Task 3.3        │  │  Task 3.4        │
│  Monitor UI      │  │  Validate DB     │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └─────────┬───────────┘
                   │
Phase 4            ▼
         ┌──────────────────┐
         │  Task 4.1        │
         │  Stop Services   │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Task 4.2        │
         │  Restart         │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Task 4.3        │
         │  Re-execute      │
         └────────┬─────────┘
                  │
Phase 5            ▼
         ┌──────────────────┐
         │  Task 5.1        │
         │  Document Issues │
         └────────┬─────────┘
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Task 5.2        │  │  Task 5.3        │
│  Fix Deployment  │  │  Fix Workflow    │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └─────────┬───────────┘
                   │
                   ▼
         ┌──────────────────┐
         │  Task 5.4        │
         │  Validate Fixes  │
         └────────┬─────────┘
                  │
Phase 6            ▼
         ┌──────────────────┐
         │  Task 6.1        │
         │  Test Compat     │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Task 6.2        │
         │  Update Matrix   │
         └────────┬─────────┘
                  │
Phase 7            ▼
         ┌──────────────────┐
         │  Tasks 7.1-7.3   │
         │  Documentation   │
         └──────────────────┘
```

---

## Timeline Estimation

### Optimistic Path (12 hours)
- Phase 1: 3 hours
- Phase 2: 2 hours
- Phase 3: 2 hours
- Phase 4: 1 hour
- Phase 5: 2 hours
- Phase 6: 1 hour
- Phase 7: 1 hour

### Realistic Path (14-16 hours)
- Phase 1: 4 hours (complex workflow design)
- Phase 2: 3 hours (deployment debugging)
- Phase 3: 3 hours (execution issues)
- Phase 4: 2 hours (persistence validation)
- Phase 5: 3 hours (issue resolution)
- Phase 6: 2 hours (compatibility testing)
- Phase 7: 2 hours (comprehensive docs)

### Critical Path
**Task 2.1 → Task 2.2 → Task 3.1 → Task 3.2 → Task 5.1 → Task 5.2/5.3**

**Parallel Opportunities:**
- Phase 1 and Phase 2 can run simultaneously
- Task 3.3 and 3.4 can run in parallel
- Task 5.2 and 5.3 can run in parallel

---

## Integration Checkpoints

### Checkpoint 1: Post-Deployment (End of Phase 2)
**Criteria:**
- ✅ Temporal running
- ✅ PostgreSQL connected
- ✅ UI accessible
- ✅ Health checks passing

**Blocker Resolution:**
- If deployment fails, devops-engineer escalates
- If schema issues, consult PostgreSQL compatibility docs
- If connectivity issues, check network/firewall

### Checkpoint 2: First Workflow Execution (End of Phase 3)
**Criteria:**
- ✅ Worker connected
- ✅ Workflow completed
- ✅ UI shows history
- ✅ PostgreSQL has records

**Blocker Resolution:**
- If worker fails, python-pro debugs connection
- If workflow errors, check activity implementations
- If persistence fails, devops-engineer checks DB

### Checkpoint 3: Persistence Validation (End of Phase 4)
**Criteria:**
- ✅ Services restart cleanly
- ✅ Workflow history preserved
- ✅ New workflows execute
- ✅ No data corruption

**Blocker Resolution:**
- If data lost, check PostgreSQL persistence config
- If corruption, check Temporal schema migrations
- If restart fails, check Docker volume mounts

### Checkpoint 4: Issue Resolution (End of Phase 5)
**Criteria:**
- ✅ All issues documented
- ✅ Fixes implemented
- ✅ Regression tests pass
- ✅ No P0/P1 bugs remaining

**Blocker Resolution:**
- P0 bugs block merge
- P1 bugs require fix plan
- P2+ can be tracked in issues

---

## Communication Protocol

### Agent Status Updates

**Format:**
```json
{
  "agent": "agent-name",
  "task": "Task X.Y",
  "status": "in_progress | blocked | completed",
  "progress_percentage": 75,
  "blockers": [],
  "next_steps": [],
  "eta_hours": 1.5
}
```

**Update Frequency:**
- Status update every 30 minutes
- Immediate notification on blockers
- Completion notification with deliverables

### Blocker Escalation

**Severity Levels:**
1. **Critical**: Blocks all downstream tasks (escalate immediately)
2. **High**: Blocks agent's work (escalate within 15 min)
3. **Medium**: Workaround possible (escalate within 1 hour)
4. **Low**: Nice to fix (document and continue)

**Escalation Path:**
1. Agent identifies blocker
2. Agent attempts resolution (15 min)
3. If unresolved, notify coordinator
4. Coordinator assigns additional agent or re-plans

### Inter-Agent Communication

**Message Format:**
```json
{
  "from": "python-pro",
  "to": "devops-engineer",
  "type": "request | question | notification",
  "subject": "PostgreSQL connection string format",
  "body": "What connection string format does Temporal expect?",
  "priority": "high"
}
```

---

## Risk Management

### Identified Risks

#### Risk 1: PostgreSQL Connection Failures
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Pre-validate PostgreSQL accessibility
- Test connection strings before deployment
- Have fallback configuration templates

#### Risk 2: Temporal Schema Migration Issues
**Probability**: Low
**Impact**: Critical
**Mitigation**:
- Use official Temporal Docker images
- Verify schema version compatibility
- Backup PostgreSQL before migrations

#### Risk 3: Worker Connection Timeouts
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Configure generous timeouts
- Implement retry logic
- Monitor worker health continuously

#### Risk 4: Workflow State Corruption
**Probability**: Low
**Impact**: High
**Mitigation**:
- Use transaction-safe operations
- Validate state after each operation
- Implement state recovery procedures

#### Risk 5: Version Compatibility Surprises
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Test multiple PostgreSQL versions
- Validate compatibility matrix
- Document actual behavior vs expected

### Contingency Plans

**If Deployment Fails:**
1. Review deployment logs
2. Check Docker Compose configuration
3. Validate environment variables
4. Test PostgreSQL standalone
5. Fallback to manual Temporal setup

**If Workflow Execution Fails:**
1. Check worker logs
2. Verify activity registration
3. Test simple workflow first
4. Debug with Temporal CLI
5. Consult Temporal documentation

**If Persistence Fails:**
1. Verify PostgreSQL persistence enabled
2. Check volume mounts
3. Review Temporal configuration
4. Test PostgreSQL connection after restart
5. Validate schema integrity

---

## Quality Gates

### Phase Completion Criteria

**Phase 1 - Test Workflow Creation:**
- [ ] Workflow code passes linting (ruff)
- [ ] Workflow code passes type checking (mypy)
- [ ] All activities implemented
- [ ] Worker configuration complete
- [ ] Execution script functional

**Phase 2 - Deployment Validation:**
- [ ] All services running (docker ps)
- [ ] Health checks passing
- [ ] PostgreSQL schema created
- [ ] Temporal UI accessible
- [ ] Configuration documented

**Phase 3 - Workflow Execution:**
- [ ] Worker connects successfully
- [ ] All activities execute
- [ ] Workflow completes
- [ ] UI shows complete history
- [ ] PostgreSQL records verified

**Phase 4 - Persistence Testing:**
- [ ] Services restart cleanly
- [ ] Workflow history intact
- [ ] New workflows execute
- [ ] No data loss detected

**Phase 5 - Issue Resolution:**
- [ ] All P0 issues fixed
- [ ] All P1 issues fixed or planned
- [ ] Fixes validated
- [ ] Regression tests pass

**Phase 6 - Compatibility Validation:**
- [ ] All test cases executed
- [ ] Warnings validated
- [ ] Matrix updated if needed
- [ ] Documentation complete

**Phase 7 - Documentation:**
- [ ] Deployment guide complete
- [ ] Test workflow documented
- [ ] Issue report finalized
- [ ] All deliverables reviewed

---

## Deliverables Checklist

### Code Deliverables
- [ ] `/home/gerald/git/mycelium/tests/integration/temporal/test_workflow.py`
- [ ] `/home/gerald/git/mycelium/tests/integration/temporal/activities.py`
- [ ] `/home/gerald/git/mycelium/tests/integration/temporal/worker.py`
- [ ] `/home/gerald/git/mycelium/tests/integration/temporal/execute_workflow.py`
- [ ] `/home/gerald/git/mycelium/tests/integration/temporal/README.md`

### Documentation Deliverables
- [ ] `/home/gerald/git/mycelium/docs/TEMPORAL_DEPLOYMENT.md`
- [ ] `/home/gerald/git/mycelium/docs/SPRINT4_ISSUES.md`
- [ ] `/home/gerald/git/mycelium/docs/SPRINT4_REPORT.md`

### Configuration Deliverables
- [ ] Updated Docker Compose configuration (if needed)
- [ ] Updated health check configuration
- [ ] Updated compatibility matrix data

### Validation Deliverables
- [ ] Test execution logs
- [ ] PostgreSQL query results
- [ ] Temporal UI screenshots
- [ ] Performance metrics

---

## Success Criteria Validation

### Functional Requirements
✅ **Temporal deploys successfully with PostgreSQL backend**
- Verified by: Task 2.2, Task 2.3
- Evidence: Service status, PostgreSQL connection, schema tables

✅ **Test workflow executes without errors**
- Verified by: Task 3.2, Task 3.3
- Evidence: Workflow completion, UI history, logs

✅ **Workflow state persists correctly in PostgreSQL**
- Verified by: Task 3.4, Task 4.3
- Evidence: SQL query results, restart validation

✅ **Temporal UI accessible and shows workflow history**
- Verified by: Task 2.2, Task 3.3
- Evidence: UI screenshots, event history

✅ **Worker connects and processes activities**
- Verified by: Task 3.1, Task 3.2
- Evidence: Worker logs, activity completion

✅ **All deployment issues identified and fixed**
- Verified by: Task 5.1, Task 5.4
- Evidence: Issue report, fix validation

### Non-Functional Requirements
- **Documentation**: Comprehensive and actionable
- **Code Quality**: Passes linting and type checking
- **Reproducibility**: Another developer can follow guides
- **Performance**: Workflow execution < 5 seconds
- **Reliability**: 100% success rate on repeat runs

---

## Post-Sprint Activities

### Branch Merge Criteria
- [ ] All deliverables complete
- [ ] All tests passing
- [ ] All P0/P1 issues resolved
- [ ] Documentation reviewed
- [ ] Code review approved

### Knowledge Transfer
- [ ] Deployment runbook created
- [ ] Test workflow usage documented
- [ ] Common issues documented
- [ ] Next sprint planning input provided

### Metrics Collection
- [ ] Time spent per phase
- [ ] Issues found vs expected
- [ ] Test coverage achieved
- [ ] Performance benchmarks

---

## Appendix A: Test Workflow Specification

### Workflow Design

```python
@workflow.defn
class TemporalTestWorkflow:
    """Comprehensive test workflow validating Temporal + PostgreSQL integration."""

    @workflow.run
    async def run(self, test_data: dict) -> dict:
        """Execute multi-stage test workflow.

        Stages:
        1. Activity execution test
        2. State persistence test (sleep)
        3. Child workflow test
        4. Signal handling test
        5. Query handling test
        """

        # Stage 1: Activity execution
        result1 = await workflow.execute_activity(
            test_activity_execution,
            test_data,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Stage 2: State persistence (sleep and resume)
        await asyncio.sleep(5)  # Temporal timer

        # Stage 3: Child workflow
        child_result = await workflow.execute_child_workflow(
            ChildTestWorkflow.run,
            {"parent_data": result1}
        )

        # Stage 4: Wait for signal
        await workflow.wait_condition(lambda: self.signal_received)

        # Stage 5: Return queryable state
        return {
            "status": "completed",
            "activity_result": result1,
            "child_result": child_result,
            "signal_data": self.signal_data
        }
```

### Activity Implementations

```python
@activity.defn
async def test_activity_execution(data: dict) -> dict:
    """Test basic activity execution and PostgreSQL interaction."""
    # Simulate work
    await asyncio.sleep(1)

    # Return result
    return {
        "activity": "test_activity_execution",
        "status": "success",
        "input_data": data
    }

@activity.defn
async def test_database_operation(data: dict) -> dict:
    """Test activity with database interaction."""
    # Could interact with PostgreSQL if needed
    return {"db_operation": "success"}
```

---

## Appendix B: Expected Issues Checklist

Based on Sprint 3 integration, expected issues to validate:

### Connection Issues
- [ ] Temporal cannot connect to PostgreSQL
- [ ] Worker cannot connect to Temporal server
- [ ] UI cannot access Temporal frontend
- [ ] Connection string format issues

### Storage Issues
- [ ] Workflow state not persisting
- [ ] Activity results lost
- [ ] History truncated or corrupted
- [ ] Transaction isolation issues

### Version Compatibility
- [ ] PostgreSQL version warnings inaccurate
- [ ] Schema migration failures
- [ ] SQL compatibility issues
- [ ] Version detection failures

### Configuration Issues
- [ ] Wrong connection strings in templates
- [ ] Missing environment variables
- [ ] Incorrect port mappings
- [ ] Health check configuration

### Performance Issues
- [ ] Slow workflow execution
- [ ] Query timeouts
- [ ] Connection pool exhaustion
- [ ] Resource contention

---

## Appendix C: Agent Communication Examples

### Example 1: python-pro requests deployment info

```json
{
  "from": "python-pro",
  "to": "devops-engineer",
  "type": "question",
  "subject": "Temporal connection details",
  "body": "What host and port should the worker connect to? Also need namespace name.",
  "priority": "high"
}
```

### Example 2: devops-engineer reports blocker

```json
{
  "from": "devops-engineer",
  "to": "coordinator",
  "type": "blocker",
  "subject": "PostgreSQL schema migration failure",
  "body": "Temporal schema auto-init failing. Error: relation 'temporal.executions' already exists",
  "severity": "critical",
  "logs": "docker logs temporal-server 2>&1 | tail -50"
}
```

### Example 3: qa-engineer reports completion

```json
{
  "from": "qa-engineer",
  "to": "coordinator",
  "type": "completion",
  "subject": "Task 3.2 completed",
  "body": "Test workflow executed successfully. All 5 stages passed. UI shows complete history.",
  "deliverables": [
    "execution logs in /tmp/workflow-execution.log",
    "UI screenshot in /tmp/temporal-ui-test.png"
  ]
}
```

---

## Coordination Notes

**Multi-Agent Coordinator Notes:**
- This is a sequential-parallel hybrid workflow
- Phases 1 and 2 can run in parallel (separate agents)
- Checkpoint validation required before phase transitions
- Blocker escalation critical for timeline adherence
- Documentation quality impacts future sprint success

**Estimated Coordination Overhead**: < 5%
**Message Delivery Guarantee**: Required for blocker notifications
**Fault Tolerance**: Agent failure requires task reassignment
**Progress Tracking**: 30-minute update intervals

**Resource Requirements:**
- 3 agents (concurrent capacity)
- PostgreSQL 13+ (8GB RAM recommended)
- Temporal server (4GB RAM recommended)
- Development machine with Docker

---

**Plan Status**: Ready for Execution
**Approval Required**: Yes
**Risk Level**: Medium
**Confidence Level**: High (85%)

---

**Coordination completed. Awaiting execution approval.**
