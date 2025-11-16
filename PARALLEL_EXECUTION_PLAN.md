# Parallel Execution Plan - CI/Local Alignment Fixes

**Coordination Date**: 2025-11-11 **Branch**: `feat/phase2-smart-onboarding-unified` **Strategy**: Two parallel teams,
independent execution, coordinated merge **Estimated Total Time**: 2-3 hours (parallel execution)

## Executive Summary

Two specialized teams will work simultaneously on separate file territories to fix CI/local alignment issues:

- **Team 1 (Type Safety)**: Fixes 28 mypy errors + 16 auto-fixable ruff errors in `mycelium_onboarding/` and `plugins/`
- **Team 2 (Test Quality)**: Fixes 36 manual ruff errors + 5 test failures + deprecation warnings in `tests/`

**No file conflicts**: Teams have completely separate territories with clear boundaries.

## Team Territories (No Overlap)

### Team 1: Type Safety & Auto-Fix

**Branch**: `fix/type-safety-errors` **Files**:

- `mycelium_onboarding/**/*.py` (ALL source files)
- `plugins/**/*.py` (ALL plugin files)
- `tests/**/*.py` (ONLY auto-fixable W293, I001, F401)

**Deliverables**:

- 28 mypy errors fixed (0 remaining)
- 16 auto-fixable ruff errors fixed
- Type safety validation passing

### Team 2: Test & Quality

**Branch**: `fix/test-quality-errors` **Files**:

- `tests/**/*.py` (ALL manual fixes - PTH123, SIM105, SIM117, RET504, F841)
- `tests/test_cli_config.py` (test failure fixes)
- Source files (ONLY Pydantic and pytest warning fixes)

**Deliverables**:

- 36 manual ruff errors fixed
- 5 unit test failures fixed
- 4 Pydantic warnings fixed
- 2 pytest collection warnings fixed

## Timeline & Milestones

### Phase 0: Initialization (T+0 to T+15 minutes)

**Both Teams - Parallel Setup**

```bash
# Team 1
cd /home/gerald/git/mycelium
git checkout feat/phase2-smart-onboarding-unified
git pull origin feat/phase2-smart-onboarding-unified
git checkout -b fix/type-safety-errors
uv sync --frozen --all-extras --group dev

# Team 2 (simultaneously)
cd /home/gerald/git/mycelium
git checkout feat/phase2-smart-onboarding-unified
git pull origin feat/phase2-smart-onboarding-unified
git checkout -b fix/test-quality-errors
uv sync --frozen --all-extras --group dev
```

**Checkpoint 0** (T+15 min):

- [ ] Both branches created
- [ ] Both environments synced
- [ ] Baseline reports generated
- [ ] No blockers

______________________________________________________________________

### Phase 1: Quick Wins (T+15 to T+45 minutes)

#### Team 1: Auto-Fix Ruff + Group A Mypy (30 min)

- [ ] Auto-fix 16 ruff errors with `--fix` flag
- [ ] Fix 7 Group A mypy errors (imports/unreachable)
- [ ] Commit: "fix(tests): auto-fix ruff W293, I001, F401 errors"
- [ ] Commit: "fix(types): resolve Group A mypy errors (import/unreachable)"

#### Team 2: Manual Ruff Fixes (30 min)

- [ ] Fix PTH123 (1 error) - Path.open()
- [ ] Fix SIM105 (2 errors) - contextlib.suppress()
- [ ] Fix SIM117 (5 errors) - combine with statements
- [ ] Fix RET504 (1 error) - remove unnecessary assignment
- [ ] Commit: "fix(tests): resolve PTH123, SIM105, SIM117, RET504 errors"

**Checkpoint 1** (T+45 min):

- [ ] Team 1: 7/28 mypy errors fixed, 16 ruff auto-fixes done
- [ ] Team 2: 9/36 manual ruff errors fixed
- [ ] Both teams have clean commits
- [ ] No merge conflicts expected

______________________________________________________________________

### Phase 2: Core Fixes (T+45 to T+120 minutes)

#### Team 1: Group B + Group C Mypy (75 min)

- [ ] Fix 14 Group B errors (type annotations) \[45 min\]
- [ ] Fix 7 Group C errors (type mismatches) \[30 min\]
- [ ] Commit: "fix(types): resolve Group B mypy errors (type annotations)"
- [ ] Commit: "fix(types): resolve Group C mypy errors (type mismatches)"

#### Team 2: F841 + Test Failures (75 min)

- [ ] Fix 27 F841 errors (unused variables) \[30 min\]
- [ ] Fix 5 test failures in test_cli_config.py \[30 min\]
- [ ] Fix 4 Pydantic deprecation warnings \[15 min\]
- [ ] Commit: "fix(tests): remove unused variables (F841)"
- [ ] Commit: "fix(tests): resolve test_cli_config.py failures"
- [ ] Commit: "fix(pydantic): migrate to ConfigDict"

**Checkpoint 2** (T+120 min):

- [ ] Team 1: 28/28 mypy errors fixed (ALL DONE!)
- [ ] Team 2: 36/36 ruff errors fixed, 5/5 tests fixed, 4/4 warnings fixed
- [ ] Both teams ready for final validation
- [ ] No blockers

______________________________________________________________________

### Phase 3: Final Validation (T+120 to T+150 minutes)

#### Team 1: Type Safety Validation (15 min)

```bash
uv run mypy plugins/ mycelium_onboarding/
# Expected: Success: no issues found in 87 source files

uv run ruff check plugins/ mycelium_onboarding/
# Expected: Found 0 errors
```

#### Team 2: Test Quality Validation (15 min)

```bash
uv run ruff check tests/
# Expected: Found 0 errors

uv run pytest tests/test_cli_config.py -v
# Expected: 5/5 tests passed

uv run pytest tests/unit/ -q --tb=no 2>&1 | grep -c "Deprecated"
# Expected: 0 warnings
```

**Checkpoint 3** (T+150 min):

- [ ] Team 1: All validations passing
- [ ] Team 2: All validations passing
- [ ] Final reports generated
- [ ] Ready for merge

______________________________________________________________________

### Phase 4: Coordinated Merge (T+150 to T+180 minutes)

**Merge Strategy**: Sequential merge to avoid conflicts

#### Step 1: Merge Team 1 First (15 min)

```bash
# Coordinator executes
cd /home/gerald/git/mycelium
git checkout feat/phase2-smart-onboarding-unified
git merge fix/type-safety-errors --no-ff -m "Merge Team 1: Type safety fixes

- Fixed all 28 mypy errors
- Auto-fixed 16 ruff errors
- Type safety validation passing"

# Validate after merge
uv run mypy plugins/ mycelium_onboarding/
```

#### Step 2: Merge Team 2 Second (15 min)

```bash
# Coordinator executes
git merge fix/test-quality-errors --no-ff -m "Merge Team 2: Test quality fixes

- Fixed 36 manual ruff errors
- Fixed 5 unit test failures
- Fixed Pydantic and pytest warnings"

# Validate after merge
uv run ruff check tests/
uv run pytest tests/test_cli_config.py -v
```

#### Step 3: Full Integration Validation

```bash
# Run complete validation script
chmod +x scripts/validate-ci-local.sh
./scripts/validate-ci-local.sh

# Expected results:
# ✅ Mypy: 0 errors
# ✅ Ruff: 0 errors
# ✅ Unit tests: All passing
```

**Checkpoint 4** (T+180 min):

- [ ] Both branches merged successfully
- [ ] No merge conflicts
- [ ] Full validation passing
- [ ] Ready to push to GitHub

______________________________________________________________________

## Dependency Graph

```
Phase 0 (Setup)
    ├─ Team 1 Setup ─────┐
    └─ Team 2 Setup ─────┼─────> Phase 1
                         │
Phase 1 (Quick Wins)     │
    ├─ Team 1: Auto-fix + Group A ─┐
    └─ Team 2: Manual Ruff ─────────┼─> Phase 2
                                     │
Phase 2 (Core Fixes)                │
    ├─ Team 1: Groups B + C ────────┐
    └─ Team 2: F841 + Tests ────────┼─> Phase 3
                                     │
Phase 3 (Validation)                │
    ├─ Team 1: Validate ────────────┐
    └─ Team 2: Validate ────────────┼─> Phase 4
                                     │
Phase 4 (Merge)                     │
    ├─ Merge Team 1 ────────────────┤
    ├─ Merge Team 2 ────────────────┤
    └─ Full Validation ─────────────┴─> DONE
```

**Critical Path**: Phase 2 (Team 1 Group B) - 45 minutes is longest task

**Parallel Efficiency**: ~67% (2 hours sequential work done in ~3 hours parallel)

## Communication Protocol

### Status Updates

Every 30 minutes, both teams report:

```json
{
  "team": "team-1 or team-2",
  "phase": "current-phase",
  "progress": {
    "tasks_complete": "X/Y",
    "commits_made": N,
    "validations_passing": true/false
  },
  "blockers": ["blocker description if any"],
  "eta_to_next_checkpoint": "X minutes"
}
```

### Blocker Escalation

If any team is blocked:

1. **Immediate**: Document blocker in `teamN-blockers.txt`
1. **5 minutes**: Attempt alternative approach
1. **10 minutes**: Request coordinator assistance
1. **15 minutes**: Other team may help if in Phase 3+

### Coordination Points

**Checkpoints 1-3**: Teams work independently, coordinator monitors

**Checkpoint 4**: Coordinator takes control for merge

## Risk Management

### Risk: Merge Conflicts

**Probability**: LOW (teams have separate territories)

**Mitigation**:

- Strict file ownership rules
- Checkpoint validations
- Sequential merge strategy

**Contingency**:

- If conflict occurs, coordinator manually resolves
- Worst case: Cherry-pick commits from each branch

### Risk: Team Velocity Mismatch

**Probability**: MEDIUM (tasks may take longer than estimated)

**Mitigation**:

- Buffer time built into estimates
- Faster team can help slower team in Phase 3

**Contingency**:

- Extend Phase 2 by up to 30 minutes
- Coordinator can reassign tasks between teams

### Risk: Validation Failures

**Probability**: MEDIUM (complex type fixes may introduce bugs)

**Mitigation**:

- Incremental commits (easy to revert)
- Validation after each commit group
- Full test suite runs at checkpoints

**Contingency**:

- Revert problematic commits
- Fix-forward with focused debugging
- Worst case: Roll back entire branch and retry

### Risk: Blocker Dependency

**Probability**: LOW (tasks are independent)

**Mitigation**:

- Multiple parallel tasks per team
- Can skip and return to blocked tasks

**Contingency**:

- Skip blocked task, document for follow-up
- Merge what's complete, create follow-up issue

## Success Criteria (All Must Pass)

### Team 1 Success

- [ ] `uv run mypy plugins/ mycelium_onboarding/` → 0 errors
- [ ] `uv run ruff check plugins/ mycelium_onboarding/` → 0 errors
- [ ] All commits follow conventional commits format
- [ ] Branch `fix/type-safety-errors` ready to merge

### Team 2 Success

- [ ] `uv run ruff check tests/` → 0 errors
- [ ] `uv run pytest tests/test_cli_config.py -v` → 5/5 passed
- [ ] 0 Pydantic deprecation warnings
- [ ] 0 pytest collection warnings
- [ ] All commits follow conventional commits format
- [ ] Branch `fix/test-quality-errors` ready to merge

### Integration Success

- [ ] Both branches merged to `feat/phase2-smart-onboarding-unified`
- [ ] No merge conflicts
- [ ] `./scripts/validate-ci-local.sh` passes completely
- [ ] All unit tests passing
- [ ] Ready to push to GitHub with confidence

## Final Deliverables

### From Team 1

- [x] Task breakdown document: `TEAM1_TYPE_SAFETY.md`
- [ ] Progress log: `team1-progress.log`
- [ ] Final report: `team1-final-report.txt`
- [ ] Completion marker: `TEAM1_COMPLETE.marker`
- [ ] Branch: `fix/type-safety-errors` (merged)

### From Team 2

- [x] Task breakdown document: `TEAM2_TEST_QUALITY.md`
- [ ] Progress log: `team2-progress.log`
- [ ] Final report: `team2-final-report.txt`
- [ ] Completion marker: `TEAM2_COMPLETE.marker`
- [ ] Branch: `fix/test-quality-errors` (merged)

### From Coordinator

- [x] Execution plan: `PARALLEL_EXECUTION_PLAN.md`
- [ ] Merge coordination log
- [ ] Final validation report
- [ ] Integration complete signal

## Post-Execution Actions

After successful merge and validation:

```bash
# 1. Push to GitHub
git push origin feat/phase2-smart-onboarding-unified

# 2. Monitor CI
gh run watch

# 3. If CI passes, update PR
gh pr view 15
gh pr comment 15 -b "✅ CI/local alignment complete. All checks passing."

# 4. Clean up branches (after merge confirmed)
git branch -d fix/type-safety-errors
git branch -d fix/test-quality-errors
```

## Rollback Strategy

If critical failure occurs at any checkpoint:

### Checkpoint 1-3 Failure

```bash
# Reset individual team branch
git checkout fix/type-safety-errors  # or fix/test-quality-errors
git reset --hard feat/phase2-smart-onboarding-unified
# Restart from Phase 0
```

### Checkpoint 4 (Merge) Failure

```bash
# Abort merge if in progress
git merge --abort

# Or reset if merge completed but validation failed
git reset --hard HEAD~1  # Undo last merge
```

### Nuclear Option

```bash
# If everything fails, reset to starting point
git checkout feat/phase2-smart-onboarding-unified
git reset --hard origin/feat/phase2-smart-onboarding-unified
git branch -D fix/type-safety-errors fix/test-quality-errors
# Analyze what went wrong, adjust plan, retry
```

## Coordination Command Center

**Location**: `/home/gerald/git/mycelium/`

**Key Files**:

- `TEAM1_TYPE_SAFETY.md` - Team 1 instructions
- `TEAM2_TEST_QUALITY.md` - Team 2 instructions
- `PARALLEL_EXECUTION_PLAN.md` - This file
- `validation-report.txt` - Baseline errors
- `scripts/validate-ci-local.sh` - Validation script

**Live Monitoring**:

```bash
# Watch Team 1 progress
watch -n 30 'tail -20 team1-progress.log'

# Watch Team 2 progress
watch -n 30 'tail -20 team2-progress.log'

# Check both team statuses
ls -1 TEAM*_COMPLETE.marker 2>/dev/null | wc -l
# Expected: 2 when both teams complete
```

## Start Execution

**Ready to begin**: Both team documents created and validated.

**Next Actions**:

1. Review team documents: `TEAM1_TYPE_SAFETY.md` and `TEAM2_TEST_QUALITY.md`
1. Assign agents to teams
1. Execute Phase 0 setup commands
1. Begin parallel execution
1. Monitor progress at checkpoints

**Go Signal**: Coordinator initiates Phase 0 when both teams acknowledge readiness.

______________________________________________________________________

**Coordination Status**: Plan complete. Awaiting team assignments and execution start.

**Expected Completion**: 2025-11-11 (same day, ~3 hours from start)
