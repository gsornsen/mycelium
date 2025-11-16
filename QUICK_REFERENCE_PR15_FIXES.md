# Quick Reference: PR #15 CI Fixes

**Branch**: feat/phase2-smart-onboarding-unified **Objective**: Fix 65+ ruff errors to pass GitHub CI **Status**: Ready
for execution

## Fast Track Commands

### Validate Current State

```bash
cd /home/gerald/git/mycelium
uv run ruff check plugins/ mycelium_onboarding/ tests/ --statistics
```

### Run Full CI Validation (after fixes)

```bash
./scripts/validate_ci.sh
```

### Check Specific Error Types

```bash
# B904 - Exception chaining
uv run ruff check --select B904 mycelium_onboarding/

# F821 - Undefined names
uv run ruff check --select F821 mycelium_onboarding/cli.py

# E402 - Import order
uv run ruff check --select E402 mycelium_onboarding/cli.py

# SIM102, F841, ARG001
uv run ruff check --select SIM102,F841,ARG001 mycelium_onboarding/cli_commands/
```

## Error Fix Patterns

### B904: Add exception chaining

```python
# Before
except Exception as e:
    raise SystemExit(1)

# After
except Exception as e:
    raise SystemExit(1) from e
```

### F821: Import missing names

```python
# Add to top of cli.py
from mycelium_onboarding.deployment.types import DeploymentMethod
```

### E402: Move imports to top

```python
# Move all imports from lines 1921-1935 to top of file
```

### SIM102: Collapse nested ifs

```python
# Before
if not yes and not dry_run:
    if not Confirm.ask("Proceed?"):
        return

# After
if not yes and not dry_run and not Confirm.ask("Proceed?"):
    return
```

### F841: Remove unused variable

```python
# Before
summary = detector.get_migration_summary()

# After
_ = detector.get_migration_summary()  # or remove entirely
```

### ARG001: Prefix unused parameter

```python
# Before
def callback(current, total, message):
    progress.update(task, completed=current)

# After
def callback(current, _total, message):
    progress.update(task, completed=current)
```

## Files to Modify

1. **mycelium_onboarding/cli.py** (Primary)

   - B904 errors: Lines 1352, 1394, 1432, 1599, 1643
   - F821 errors: Lines 1492, 1533, 1563
   - E402 errors: Lines 1921-1935

1. **mycelium_onboarding/cli_commands/commands/config.py**

   - B904 error: Line 493

1. **mycelium_onboarding/cli_commands/commands/config_migrate.py**

   - SIM102 errors: Lines 81, 289
   - F841 error: Line 275
   - ARG001 error: Line 304

1. **tests/integration/** (3 files)

   - test_orchestration.py: HandoffContext import
   - test_state_manager.py: coordination module
   - test_tracking.py: coordination module

## Phase Sequence

1. **Environment** (15m) - Create baseline
1. **B904** (30m) - Exception chaining
1. **F821** (20m) - Undefined names
1. **E402** (15m) - Import order
1. **SIM102/F841/ARG001** (20m) - Code cleanup
1. **Integration Tests** (45m) - Fix or skip
1. **Validation** (30m) - Comprehensive check
1. **Commit & Push** (15m) - Deploy fixes

**Total**: ~3 hours

## Success Checklist

- [ ] `uv run ruff check` = 0 errors
- [ ] `uv run ruff format --check` = passing
- [ ] `uv run mypy` = 0 errors
- [ ] Unit tests = 585+ passing
- [ ] Integration tests = pass or skip
- [ ] `./scripts/validate_ci.sh` = all green
- [ ] Ready to push

## Emergency Rollback

```bash
git reset --hard origin/feat/phase2-smart-onboarding-unified
```

## Documentation

- **Master Plan**: COORDINATION_PLAN_PR15.md
- **Dispatch Summary**: COORDINATION_DISPATCH_SUMMARY.md
- **Phase 1**: HANDOFF_PHASE1_ENVIRONMENT.md
- **Phase 2**: HANDOFF_PHASE2_B904.md
- **Phase 3**: HANDOFF_PHASE3_F821.md
- **Phases 4-8**: HANDOFF_PHASES_4_TO_8.md

## Contact

**Coordinator**: multi-agent-coordinator **Questions**: Reference master plan or ask coordinator
