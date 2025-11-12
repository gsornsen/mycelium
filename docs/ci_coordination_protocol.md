# CI Status Check Coordination Protocol

## Mission Overview

Check GitHub CI run status for PR #15 and coordinate multi-agent response to any failures.

## Context

- **PR**: #15 - feat/phase2-smart-onboarding-unified
- **Branch**: feat/phase2-smart-onboarding-unified
- **Recent Commits**: 5668eeb, 8c61a0b (Phase 3 improvements)
- **Local Status**: 585 tests passing, 29 mypy errors (known)
- **PR URL**: https://github.com/gsornsen/mycelium/pull/15

## CI Pipeline Structure

### Critical Checks (Must Pass)

1. **Lint with Ruff**

   - Format check
   - Code style validation
   - Agent: `python-pro`

1. **Type Check with mypy**

   - Type annotation verification
   - Known: 29 errors acceptable
   - Agent: `python-pro`

1. **Unit Tests** (Python 3.10, 3.11, 3.12, 3.13)

   - Fast tests, no external services
   - Coverage reporting
   - Agent: `qa-expert`

1. **Integration Tests**

   - PostgreSQL + pgvector required
   - Database migrations
   - Agent: `qa-expert` + `devops-incident-responder`

1. **Migration Tests**

   - Forward/backward migration validation
   - Idempotency verification
   - Agent: `devops-incident-responder`

### Summary Check

- **CI Success**: Aggregates all above checks
- Must pass for merge approval

## Agent Coordination Matrix

| Failure Type      | Primary Agent             | Support Agent             | Priority |
| ----------------- | ------------------------- | ------------------------- | -------- |
| Linting           | python-pro                | -                         | HIGH     |
| Type Check        | python-pro                | -                         | MEDIUM   |
| Unit Tests        | qa-expert                 | python-pro                | HIGH     |
| Integration Tests | qa-expert                 | devops-incident-responder | HIGH     |
| Migration Tests   | devops-incident-responder | -                         | HIGH     |
| Infrastructure    | devops-incident-responder | -                         | CRITICAL |
| Dependencies      | python-pro                | devops-incident-responder | HIGH     |
| Timeouts          | devops-incident-responder | qa-expert                 | MEDIUM   |

## Coordination Workflow

### Phase 1: Status Assessment (2 min)

```bash
# Execute CI status analyzer
python scripts/ci_status_analyzer.py
```

**Output**: JSON report with categorized failures

### Phase 2: Agent Assignment (1 min)

Based on failure categories, coordinate with:

- **python-pro**: Code quality issues (lint, type, imports)
- **qa-expert**: Test failures (unit, integration)
- **devops-incident-responder**: Infrastructure, migrations, CI config

### Phase 3: Parallel Investigation (5 min)

Each agent investigates assigned failures:

- Review logs
- Identify root cause
- Propose fix
- Estimate effort

### Phase 4: Resolution (Remaining time)

- Apply fixes in priority order
- Re-run CI
- Verify resolution

## Communication Protocol

### Status Query Format

```json
{
  "requesting_agent": "multi-agent-coordinator",
  "request_type": "ci_status_check",
  "payload": {
    "pr_number": 15,
    "branch": "feat/phase2-smart-onboarding-unified",
    "check_type": "all"
  }
}
```

### Failure Assignment Format

```json
{
  "requesting_agent": "multi-agent-coordinator",
  "request_type": "investigate_failure",
  "target_agent": "qa-expert",
  "payload": {
    "check_name": "Unit Tests (3.10)",
    "failure_category": "unit_test",
    "log_excerpt": "...",
    "priority": "HIGH",
    "deadline": "10_minutes"
  }
}
```

### Resolution Report Format

```json
{
  "reporting_agent": "qa-expert",
  "report_type": "failure_resolution",
  "payload": {
    "check_name": "Unit Tests (3.10)",
    "root_cause": "Async test isolation issue",
    "fix_applied": "Updated test fixtures",
    "verification": "Local tests passing",
    "confidence": "HIGH"
  }
}
```

## Success Criteria

### ✅ Complete

- [x] CI status identified
- [x] Failures categorized
- [x] Agents coordinated
- [x] Fixes applied
- [x] CI re-run successful
- [x] All checks green

### ❌ Incomplete

- [ ] Some checks still failing
- [ ] Need additional investigation
- [ ] Infrastructure issues blocking

## Monitoring Commands

### Quick Status

```bash
gh pr checks 15
```

### Detailed Status

```bash
gh pr view 15 --json statusCheckRollup
```

### Watch Mode (Real-time)

```bash
gh pr checks 15 --watch
```

### Get Failed Logs

```bash
gh run view <run-id> --log-failed
```

## Escalation Paths

### If CI Stuck/Hanging

1. Check GitHub Status: https://www.githubstatus.com/
1. Cancel and re-run workflow
1. Coordinate with devops-incident-responder

### If Multiple Test Failures

1. Identify common patterns
1. Check for environment issues
1. Review recent changes for regressions

### If Infrastructure Issues

1. Verify PostgreSQL service startup
1. Check cache restoration
1. Review GitHub Actions logs
1. Consider re-running jobs

## Known Issues & Workarounds

### mypy Errors (29 expected)

- Phase 2 has 29 known mypy errors
- Acceptable for merge
- Will be addressed in separate PR

### Sentence-Transformers Cache

- May need time to download on first run
- Cache should hit on subsequent runs
- Not a failure if taking extra time

### PostgreSQL Connection

- Service needs ~30s to be ready
- Health checks should prevent premature tests
- If flaky, check health-check configuration

## Time Budget Allocation

| Phase              | Time   | Description                     |
| ------------------ | ------ | ------------------------------- |
| Status Check       | 2 min  | Run analyzer, get current state |
| Agent Coordination | 1 min  | Assign failures to agents       |
| Investigation      | 5 min  | Parallel root cause analysis    |
| Resolution         | 2 min  | Apply fixes, commit, push       |
| TOTAL              | 10 min | Maximum time budget             |

## Deliverables

1. **CI Status Report** (JSON + Human-readable)

   - Location: `/tmp/ci_status_report.json`
   - Format: Structured analysis with recommendations

1. **Agent Coordination Log**

   - Which agents were involved
   - What was assigned to each
   - Resolution status

1. **GO/NO-GO Decision**

   - Clear merge recommendation
   - Blocking issues identified
   - Risk assessment

1. **Next Steps**

   - If passing: Approve and merge
   - If failing: Prioritized fix list
   - If in-progress: Monitor and wait

## Example Scenarios

### Scenario 1: All Green

```
Status: PASSING
Checks: 7/7 passed
Merge Ready: YES
Action: Approve PR #15 for merge
```

### Scenario 2: Unit Test Failure

```
Status: FAILING
Failed: Unit Tests (3.11)
Cause: Import error in new module
Agent: python-pro
Fix: Add missing __init__.py
Time: 2 minutes
```

### Scenario 3: Integration Test Timeout

```
Status: FAILING
Failed: Integration Tests
Cause: PostgreSQL connection timeout
Agent: devops-incident-responder
Fix: Increase health-check retries
Time: 5 minutes
```

### Scenario 4: Still Running

```
Status: IN_PROGRESS
Running: 3/7 checks
ETA: 5 minutes
Action: Wait and monitor
```

## Post-Analysis Actions

### If All Passing

1. Generate success report
1. Notify user: "CI green, ready to merge"
1. Provide merge command or approval

### If Failures Detected

1. Categorize by severity
1. Assign to appropriate agents
1. Track resolution progress
1. Re-check after fixes

### If Infrastructure Issues

1. Document issue details
1. Check GitHub status
1. Consider re-run
1. Escalate if persistent

## Coordination Efficiency Metrics

- **Coordination Overhead**: \< 5% of total time
- **Agent Response Time**: \< 30 seconds
- **Parallel Execution**: 3+ agents simultaneously
- **Resolution Rate**: > 80% within time budget

______________________________________________________________________

**Coordinator**: multi-agent-coordinator **Protocol Version**: 1.0 **Last Updated**: 2025-11-11
