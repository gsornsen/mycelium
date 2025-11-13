# Manual CI Status Check Guide for PR #15

## Quick Status Check

### Option 1: GitHub Web UI

1. Visit: https://github.com/gsornsen/mycelium/pull/15
1. Scroll to "Checks" section at bottom
1. Review status of each check

### Option 2: GitHub CLI

```bash
cd /home/gerald/git/mycelium

# Quick check
gh pr checks 15

# Detailed view
gh pr view 15 --json statusCheckRollup | python3 -m json.tool

# Watch mode (real-time updates)
gh pr checks 15 --watch --interval 10
```

### Option 3: GitHub API (curl)

```bash
# Get PR checks
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/gsornsen/mycelium/pulls/15/checks

# Get workflow runs
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/gsornsen/mycelium/actions/runs?branch=feat/phase2-smart-onboarding-unified
```

## Expected CI Checks

### 1. Lint with Ruff ✓

**Purpose**: Code style and formatting validation **Duration**: ~2-3 minutes **What it checks**:

- Ruff linting rules
- Format compliance
- Code style consistency

**Common failures**:

- Unused imports
- Line too long
- Missing docstrings
- Format violations

**Fix locally**:

```bash
uv run ruff check --fix plugins/ mycelium_onboarding/ tests/
uv run ruff format plugins/ mycelium_onboarding/ tests/
```

### 2. Type Check with mypy ⚠️

**Purpose**: Type annotation validation **Duration**: ~2-3 minutes **Known Status**: 29 errors expected (acceptable)
**What it checks**:

- Type hints correctness
- Type inference
- Return type matching

**Common failures**:

- Missing type hints
- Incompatible types
- Optional handling

**Fix locally**:

```bash
uv run mypy plugins/ mycelium_onboarding/
```

**Note**: Phase 2 has 29 known mypy errors that are acceptable for merge.

### 3. Unit Tests (Python 3.10, 3.11, 3.12, 3.13) ✓

**Purpose**: Fast unit tests without external dependencies **Duration**: ~5-8 minutes per version **What it checks**:

- Core functionality
- Edge cases
- Error handling
- Code coverage

**Common failures**:

- Assertion errors
- Import errors
- Mock setup issues
- Async test problems

**Fix locally**:

```bash
# Run all unit tests
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow"

# Run specific test file
uv run pytest tests/unit/test_specific.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=plugins --cov=mycelium_onboarding
```

### 4. Integration Tests ✓

**Purpose**: Tests with PostgreSQL and external services **Duration**: ~8-12 minutes **What it checks**:

- Database operations
- Service integration
- Migration application
- Data persistence

**Services required**:

- PostgreSQL 16+ with pgvector
- Test database setup

**Common failures**:

- Database connection timeout
- Migration errors
- Service not ready
- Test isolation issues

**Fix locally**:

```bash
# Start PostgreSQL with Docker
docker run -d --name postgres-test \
  -e POSTGRES_USER=mycelium \
  -e POSTGRES_PASSWORD=mycelium_test \
  -e POSTGRES_DB=mycelium_test \
  -p 5432:5432 \
  ankane/pgvector:latest

# Wait for PostgreSQL
until pg_isready -h localhost -p 5432 -U mycelium; do sleep 2; done

# Run migrations
export DATABASE_URL=postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test
uv run alembic upgrade head

# Run integration tests
uv run pytest tests/integration/ -v -m "integration"

# Cleanup
docker stop postgres-test && docker rm postgres-test
```

### 5. Migration Tests ✓

**Purpose**: Verify database migrations work correctly **Duration**: ~5-8 minutes **What it checks**:

- Forward migration (upgrade)
- Backward migration (downgrade)
- Re-migration (idempotency)
- Migration history

**Common failures**:

- SQL syntax errors
- Missing dependencies between migrations
- Non-reversible operations
- Data migration issues

**Fix locally**:

```bash
# Test forward migration
uv run alembic upgrade head

# Test backward migration
uv run alembic downgrade base

# Test forward again
uv run alembic upgrade head

# Check current version
uv run alembic current

# Check history
uv run alembic history
```

### 6. CI Success (Summary) ✓

**Purpose**: Aggregate all checks **Duration**: N/A (depends on other checks) **Status**: Passes only if all above
checks pass

## CI Status Interpretation

### All Green (✓✓✓✓✓✓)

```
✓ Lint with Ruff
✓ Type Check with mypy
✓ Unit Tests (3.10)
✓ Unit Tests (3.11)
✓ Unit Tests (3.12)
✓ Unit Tests (3.13)
✓ Integration Tests
✓ Migration Tests
✓ CI Success
```

**Action**: READY TO MERGE

### Some Failures (✓✗✓✗✓✓)

```
✓ Lint with Ruff
✗ Type Check with mypy (NEW errors beyond 29)
✓ Unit Tests (3.10)
✗ Unit Tests (3.11) (FAILURE)
✓ Integration Tests
✓ Migration Tests
✗ CI Success (BLOCKED)
```

**Action**: FIX FAILURES

### In Progress (✓⟳⟳⟳⟳⟳)

```
✓ Lint with Ruff
⟳ Type Check with mypy (Running...)
⟳ Unit Tests (3.10) (Running...)
⟳ Unit Tests (3.11) (Pending...)
⟳ Integration Tests (Pending...)
⟳ Migration Tests (Pending...)
○ CI Success (Waiting...)
```

**Action**: WAIT AND MONITOR

## Recent Commits Status

### Commit: 5668eeb (Phase 3 improvements)

**Expected**: Should pass all checks **Local Validation**: ✓ 585 tests passing

### Commit: 8c61a0b (Phase 3 improvements)

**Expected**: Should pass all checks **Local Validation**: ✓ 585 tests passing

## Troubleshooting Guide

### Check 1: Is CI Running?

```bash
gh run list --branch feat/phase2-smart-onboarding-unified --limit 1
```

- If "in_progress": Wait and monitor
- If "completed": Check results
- If "queued": Wait for runner availability

### Check 2: Get Failure Logs

```bash
# Get latest run ID
RUN_ID=$(gh run list --branch feat/phase2-smart-onboarding-unified --limit 1 --json databaseId --jq '.[0].databaseId')

# View run details
gh run view $RUN_ID

# Get failure logs
gh run view $RUN_ID --log-failed > /tmp/ci_failures.log

# Analyze logs
less /tmp/ci_failures.log
```

### Check 3: Compare with Local

```bash
# Run same checks locally
uv run ruff check plugins/ mycelium_onboarding/ tests/
uv run ruff format --check plugins/ mycelium_onboarding/ tests/
uv run mypy plugins/ mycelium_onboarding/
uv run pytest tests/unit/ -v -m "not integration and not benchmark and not slow"
```

### Check 4: Check GitHub Status

- Visit: https://www.githubstatus.com/
- Look for GitHub Actions incidents
- Check for degraded performance

### Check 5: Re-run Failed Jobs

```bash
# Re-run all failed jobs
gh run rerun $RUN_ID --failed

# Re-run entire workflow
gh run rerun $RUN_ID
```

## Time Estimates

| Check               | Duration     | Parallel | Total          |
| ------------------- | ------------ | -------- | -------------- |
| Lint                | 2-3 min      | Yes      | 3 min          |
| Type Check          | 2-3 min      | Yes      | 3 min          |
| Unit (all versions) | 5-8 min each | Yes      | 8 min          |
| Integration         | 8-12 min     | Yes      | 12 min         |
| Migration           | 5-8 min      | Yes      | 8 min          |
| **Total**           |              |          | **~12-15 min** |

## Decision Tree

```
Start: Check PR #15 CI Status
   |
   v
Is CI running?
   |
   +-- No --> Trigger workflow --> Wait
   |
   +-- Yes --> Check progress
               |
               v
          All checks complete?
               |
               +-- No --> Monitor (wait 2-3 min) --> Loop
               |
               +-- Yes --> All passing?
                          |
                          +-- Yes --> ✓ READY TO MERGE
                          |
                          +-- No --> Identify failures
                                     |
                                     v
                                  Categorize by type:
                                     |
                                     +-- Lint --> Fix format --> Push
                                     +-- Type --> Add hints --> Push
                                     +-- Tests --> Fix bugs --> Push
                                     +-- Integration --> Fix DB --> Push
                                     +-- Migration --> Fix SQL --> Push
                                     +-- Infrastructure --> Re-run
```

## Agent Coordination for Failures

### Lint Failures

**Coordinate with**: python-pro **Action**: Fix code style issues **Command**: `uv run ruff check --fix`

### Type Check Failures (NEW errors)

**Coordinate with**: python-pro **Action**: Add missing type hints **Command**: `uv run mypy --show-error-codes`

### Unit Test Failures

**Coordinate with**: qa-expert **Action**: Debug test failures **Command**: `uv run pytest -v --tb=long <test_file>`

### Integration Test Failures

**Coordinate with**: qa-expert + devops-incident-responder **Action**: Check database setup **Command**: Check
PostgreSQL logs and service status

### Migration Failures

**Coordinate with**: devops-incident-responder **Action**: Fix migration SQL **Command**:
`uv run alembic upgrade head --sql`

### Infrastructure Failures

**Coordinate with**: devops-incident-responder **Action**: Re-run or escalate **Command**: `gh run rerun --failed`

## Success Criteria Checklist

- [ ] All CI checks visible in PR
- [ ] All checks completed (not pending)
- [ ] All checks passing (green ✓)
- [ ] No new mypy errors beyond 29
- [ ] All 4 Python versions passing unit tests
- [ ] Integration tests passing
- [ ] Migration tests passing
- [ ] CI Success check green
- [ ] PR marked as "Ready to merge"

## Quick Commands Reference

```bash
# Status check
gh pr checks 15

# Detailed JSON
gh pr view 15 --json statusCheckRollup

# Watch mode
gh pr checks 15 --watch

# List runs
gh run list --branch feat/phase2-smart-onboarding-unified

# View run
gh run view <run-id>

# Get logs
gh run view <run-id> --log-failed

# Re-run
gh run rerun <run-id> --failed

# Local validation
uv run pytest tests/ -v
uv run ruff check .
uv run mypy plugins/ mycelium_onboarding/
```

## Expected Timeline

| Time | Status                          |
| ---- | ------------------------------- |
| T+0  | Push commits, CI triggered      |
| T+2  | Lint and type check complete    |
| T+5  | Unit tests starting to complete |
| T+8  | Most unit tests done            |
| T+10 | Integration tests running       |
| T+12 | Migration tests complete        |
| T+15 | All checks complete, CI success |

## Contact Points

- **Repository**: https://github.com/gsornsen/mycelium
- **PR**: https://github.com/gsornsen/mycelium/pull/15
- **Branch**: feat/phase2-smart-onboarding-unified
- **Actions**: https://github.com/gsornsen/mycelium/actions

______________________________________________________________________

**Last Updated**: 2025-11-11 **Coordinator**: multi-agent-coordinator **Status**: Active monitoring for PR #15
