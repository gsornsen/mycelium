# Team 1: Type Safety & Auto-Fix Team

**Priority**: 🔴 CRITICAL (Blocking CI) **Branch**: `fix/type-safety-errors` (create from current branch) **Lead Agent**:
`python-pro` **Support Agent**: `code-reviewer` **Status**: READY TO START **Estimated Time**: 2-3 hours

## Mission

Fix ALL mypy type errors (28 total) and auto-fixable ruff errors (16 total) to unblock CI pipeline. Your team owns type
safety and automated code quality improvements.

## File Ownership (No Conflicts with Team 2)

**Your Territory**:

- `mycelium_onboarding/*.py` - ALL files in this directory
- `plugins/*.py` - ALL plugin files
- Auto-fixable issues in `tests/*.py` (W293, I001, F401 only)

**Team 2 Territory (DO NOT TOUCH)**:

- Manual ruff fixes in `tests/*.py` (except auto-fixes)
- Test failure fixes in `tests/test_cli_config.py`

## Setup Commands

```bash
# 1. Create your branch
cd /home/gerald/git/mycelium
git checkout feat/phase2-smart-onboarding-unified
git pull origin feat/phase2-smart-onboarding-unified
git checkout -b fix/type-safety-errors

# 2. Verify environment
uv sync --frozen --all-extras --group dev

# 3. Baseline assessment
echo "=== BASELINE: MYPY ERRORS ===" > team1-progress.log
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | tee -a team1-progress.log

echo "\n=== BASELINE: RUFF AUTO-FIXABLE ===" >> team1-progress.log
uv run ruff check plugins/ mycelium_onboarding/ tests/ 2>&1 | grep -E "\[\*\]" | tee -a team1-progress.log
```

## Task 1: Auto-Fix Ruff Errors (16 fixable) - 15 minutes

### Quick Wins - Run These Commands

```bash
# Auto-fix all fixable ruff errors
uv run ruff check --fix tests/

# Expected fixes:
# - W293: Blank line whitespace (15 instances in test_workflow_integration.py)
# - I001: Import sorting (1 instance in test_deployment_validation.py)
# - F401: Unused imports (1 instance - pathlib.Path)

# Verify fixes applied
uv run ruff check tests/ | grep "Found 0 errors" || echo "Manual fixes still needed"

# Commit auto-fixes immediately
git add tests/
git commit -m "fix(tests): auto-fix ruff W293, I001, F401 errors

- Remove whitespace from blank lines (W293)
- Sort imports correctly (I001)
- Remove unused imports (F401)

Auto-fixed by Team 1 - Type Safety"
```

### Validation

```bash
# Should see significant reduction in ruff error count
uv run ruff check plugins/ mycelium_onboarding/ tests/ 2>&1 | tee team1-ruff-after.log
```

## Task 2: Fix Mypy Errors - Group A (Import/Unreachable) - 30 minutes

### 7 Errors - Import and Control Flow Issues

#### Error 1-3: import-untyped in tui/__init__.py

**Location**: `mycelium_onboarding/tui/__init__.py:9-11`

**Error**:

```
error: Skipping analyzing "mycelium_onboarding.tui.health_monitor": module is installed, but missing library stubs or py.typed marker  [import-untyped]
error: Skipping analyzing "mycelium_onboarding.tui.realtime_updates": module is installed, but missing library stubs or py.typed marker  [import-untyped]
error: Skipping analyzing "mycelium_onboarding.tui.status_display": module is installed, but missing library stubs or py.typed marker  [import-untyped]
```

**Fix Strategy**:

```python
# Option 1: Add py.typed marker to tui package
# Create: mycelium_onboarding/tui/py.typed (empty file)
touch mycelium_onboarding/tui/py.typed

# Option 2: Add type: ignore comments if modules truly untyped
# In mycelium_onboarding/tui/__init__.py:
from mycelium_onboarding.tui.health_monitor import HealthMonitor  # type: ignore[import-untyped]
from mycelium_onboarding.tui.realtime_updates import RealtimeUpdates  # type: ignore[import-untyped]
from mycelium_onboarding.tui.status_display import StatusDisplay  # type: ignore[import-untyped]
```

**Recommendation**: Use Option 1 (py.typed) if modules have types, Option 2 if they don't.

#### Error 4: unreachable in platform.py:49

**Location**: `mycelium_onboarding/config/platform.py:49`

**Error**: `error: Statement is unreachable  [unreachable]`

**Fix Strategy**:

```bash
# View the code around line 49
sed -n '45,55p' mycelium_onboarding/config/platform.py

# Likely pattern:
# if condition:
#     return something
# return default  # This line is unreachable if all paths return

# Fix: Remove the unreachable statement or restructure control flow
```

#### Error 5: unreachable in deployment_validator.py:492

**Location**: `mycelium_onboarding/deployment/validation/deployment_validator.py:492`

**Error**: `error: Statement is unreachable  [unreachable]`

**Fix Strategy**: Same as Error 4 - identify and remove unreachable code.

#### Error 6: import-not-found for tomli

**Location**: `mycelium_onboarding/deployment/postgres/temporal_detector.py:25`

**Error**: `error: Cannot find implementation or library stub for module named "tomli"  [import-not-found]`

**Fix Strategy**:

```python
# tomli is a backport for Python <3.11
# Fix: Conditional import based on Python version

import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        import tomllib  # type: ignore[no-redef]
```

#### Error 7: unused-ignore in temporal_detector.py:27

**Location**: `mycelium_onboarding/deployment/postgres/temporal_detector.py:27`

**Error**: `error: Unused "type: ignore" comment  [unused-ignore]`

**Fix Strategy**: Simply remove the `# type: ignore` comment on line 27.

### Commit After Group A

```bash
git add mycelium_onboarding/tui/ mycelium_onboarding/config/platform.py \
        mycelium_onboarding/deployment/validation/deployment_validator.py \
        mycelium_onboarding/deployment/postgres/temporal_detector.py

git commit -m "fix(types): resolve Group A mypy errors (import/unreachable)

- Add py.typed marker to tui package
- Remove unreachable statements in platform.py and deployment_validator.py
- Fix conditional tomli import for Python 3.11+
- Remove unused type:ignore comment

7/28 mypy errors fixed by Team 1"

# Verify progress
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | grep "Found.*errors" | tee -a team1-progress.log
```

## Task 3: Fix Mypy Errors - Group B (Type Annotations) - 45 minutes

### 14 Errors - Missing or Wrong Type Annotations

#### Errors 8-10: no-any-return (3 instances)

**Locations**:

- `mycelium_onboarding/coordination/redis_helper.py:330`
- `mycelium_onboarding/deployment/postgres/compatibility.py:459`
- `mycelium_onboarding/deployment/postgres/compatibility.py:467`

**Error**: `error: Returning Any from function declared to return "dict[str, Any] | None"  [no-any-return]`

**Fix Strategy**:

```python
# Problem: Function returns result of operation that mypy thinks is Any
# Solution: Add explicit type cast

# Before:
def some_function() -> dict[str, Any] | None:
    result = some_operation()  # mypy thinks this is Any
    return result

# After:
def some_function() -> dict[str, Any] | None:
    result = some_operation()
    if result is None:
        return None
    return dict(result)  # Explicit cast ensures correct type
```

#### Errors 11-13: union-attr Path|str issues

**Locations**:

- `mycelium_onboarding/config/path_utils.py:104` (exists, is_dir)
- `mycelium_onboarding/config/path_utils.py:108` (/ operator)

**Error**:

```
error: Item "str" of "Path | str" has no attribute "exists"  [union-attr]
error: Item "str" of "Path | str" has no attribute "is_dir"  [union-attr]
error: Unsupported left operand type for / ("str")  [operator]
```

**Fix Strategy**:

```python
# Problem: Function accepts Path | str but doesn't normalize
from pathlib import Path

def function_with_path(path: Path | str) -> bool:
    # Before (causes error):
    if path.exists() and path.is_dir():  # str doesn't have .exists()
        return True

    # After (normalize first):
    path = Path(path) if isinstance(path, str) else path
    if path.exists() and path.is_dir():
        return True
```

#### Errors 14-20: config_migrate.py type issues (7 errors)

**Locations**:

- Line 59: Incompatible assignment (list\[Path\] vs list\[ConfigLocation\])
- Line 152: Missing type parameters for list
- Line 152: Missing type parameters for dict
- Line 191: Missing type parameters for dict
- Line 203: Missing type parameters for dict
- Line 248: Missing return type annotation
- Line 289: Unexpected keyword argument "backup_dir"
- Line 298: Missing type annotation

**Fix Strategy**:

```python
# Error at line 59: Type mismatch
# Before:
paths: list[ConfigLocation] = [Path("/some/path")]

# After:
from mycelium_onboarding.config.migration.detector import ConfigLocation
paths: list[ConfigLocation] = [
    ConfigLocation(path=Path("/some/path"), is_legacy=True, ...)
]

# Errors at lines 152, 191, 203: Missing generics
# Before:
def function() -> list:
    return []

# After:
def function() -> list[str]:
    return []

# Error at line 248, 298: Missing annotations
# Before:
def function(arg):
    pass

# After:
def function(arg: str) -> None:
    pass

# Error at line 289: Wrong kwarg
# Check MigrationExecutor.__init__ signature and remove or fix backup_dir argument
```

#### Error 21: no-untyped-def in deployment_validator.py:806

**Location**: `mycelium_onboarding/deployment/validation/deployment_validator.py:806`

**Error**: `error: Function is missing a type annotation for one or more arguments  [no-untyped-def]`

**Fix Strategy**:

```python
# Before:
def some_function(arg1, arg2):
    pass

# After:
def some_function(arg1: str, arg2: int) -> None:
    pass
```

### Commit After Group B

```bash
git add mycelium_onboarding/coordination/redis_helper.py \
        mycelium_onboarding/deployment/postgres/compatibility.py \
        mycelium_onboarding/config/path_utils.py \
        mycelium_onboarding/cli_commands/commands/config_migrate.py \
        mycelium_onboarding/deployment/validation/deployment_validator.py

git commit -m "fix(types): resolve Group B mypy errors (type annotations)

- Fix no-any-return errors with explicit type casts
- Normalize Path|str unions before attribute access
- Add missing type parameters for generic types
- Add missing return type annotations
- Fix function argument type annotations
- Correct MigrationExecutor constructor call

14/28 mypy errors fixed by Team 1 (21/28 total)"

# Verify progress
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | grep "Found.*errors" | tee -a team1-progress.log
```

## Task 4: Fix Mypy Errors - Group C (Type Mismatches) - 30 minutes

### 7 Errors - Type Compatibility Issues

#### Error 22: assignment incompatibility in rollback.py:145

**Location**: `mycelium_onboarding/config/migration/rollback.py:145`

**Error**:
`error: Incompatible types in assignment (expression has type "TextIOWrapper[_WrappedBuffer]", variable has type "BufferedReader[_BufferedReaderStream]")  [assignment]`

**Fix Strategy**:

```python
# Problem: Opening file in wrong mode
# Before:
file: BufferedReader = open(path, 'w')  # Wrong mode

# After:
file: BufferedReader = open(path, 'rb')  # Binary read mode
# OR change variable type:
file: TextIOWrapper = open(path, 'r')  # Text mode
```

#### Error 23: arg-type list variance in detector.py:138

**Location**: `mycelium_onboarding/config/migration/detector.py:138`

**Error**:
`error: Argument "search_paths" to "find_legacy_configs" has incompatible type "list[Path]"; expected "list[Path | str] | None"  [arg-type]`

**Fix Strategy**:

```python
# Problem: List invariance - list[Path] is not compatible with list[Path | str]
# Before:
paths: list[Path] = [Path("/some/path")]
result = find_legacy_configs(search_paths=paths)  # Type error

# After Option 1: Use Sequence (covariant)
from collections.abc import Sequence
def find_legacy_configs(search_paths: Sequence[Path | str] | None = None):
    ...

# After Option 2: Cast at call site
result = find_legacy_configs(search_paths=list(paths))  # Works with list constructor
```

#### Error 24: call-arg wrong kwarg in config_migrate.py:289

**Location**: `mycelium_onboarding/cli_commands/commands/config_migrate.py:289`

**Error**: `error: Unexpected keyword argument "backup_dir" for "MigrationExecutor"  [call-arg]`

**Fix Strategy**:

```python
# Check MigrationExecutor constructor signature
# View: mycelium_onboarding/config/migration/executor.py:101

# Option 1: Remove backup_dir kwarg
executor = MigrationExecutor()

# Option 2: If backup_dir should be supported, add it to MigrationExecutor.__init__
```

#### Error 25: attr-defined __test__ in test_workflow.py:273

**Location**: `mycelium_onboarding/deployment/workflows/test_workflow.py:273`

**Error**:
`error: "Callable[[bool, int], Coroutine[Any, Any, dict[str, Any]]]" has no attribute "__test__"  [attr-defined]`

**Fix Strategy**:

```python
# Problem: Setting __test__ on wrong object type
# Before:
some_callable.__test__ = False

# After:
# Don't set __test__ on callables, set on classes
class TestWorkflow:
    __test__ = False  # Tell pytest not to collect this class
```

#### Errors 26-28: arg-type ValidationResult mismatch (3 instances)

**Location**: `mycelium_onboarding/deployment/commands/deploy.py:409`

**Error**:
`error: Argument 1 to "format_validation_result" of "WarningFormatter" has incompatible type "ValidationResult"; expected "CompatibilityRequirement"  [arg-type]`

**Fix Strategy**:

```python
# Problem: Passing wrong type to formatter
# Before:
validation_result: ValidationResult = validate()
formatter.format_validation_result(validation_result)  # Wrong type

# After Option 1: Use correct method for ValidationResult
formatter.format_validation_result_v2(validation_result)

# After Option 2: Extract CompatibilityRequirement from ValidationResult
if hasattr(validation_result, 'requirement'):
    formatter.format_validation_result(validation_result.requirement)

# After Option 3: Fix method signature to accept ValidationResult
def format_validation_result(self, result: ValidationResult | CompatibilityRequirement):
    if isinstance(result, ValidationResult):
        # Handle ValidationResult
        pass
    else:
        # Handle CompatibilityRequirement
        pass
```

### Commit After Group C

```bash
git add mycelium_onboarding/config/migration/rollback.py \
        mycelium_onboarding/config/migration/detector.py \
        mycelium_onboarding/cli_commands/commands/config_migrate.py \
        mycelium_onboarding/deployment/workflows/test_workflow.py \
        mycelium_onboarding/deployment/commands/deploy.py

git commit -m "fix(types): resolve Group C mypy errors (type mismatches)

- Fix file handle type mismatch in rollback.py
- Use Sequence for covariant list types in detector.py
- Remove invalid backup_dir kwarg in config_migrate.py
- Fix __test__ attribute assignment in test_workflow.py
- Fix ValidationResult type mismatch in deploy.py

7/28 mypy errors fixed by Team 1 (28/28 total - ALL DONE!)"

# Verify ZERO errors
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | tee team1-final.log
grep "Success: no issues found" team1-final.log || echo "ERROR: Still have mypy errors!"
```

## Final Validation

```bash
# 1. Mypy should be clean
uv run mypy plugins/ mycelium_onboarding/
# Expected: Success: no issues found in 87 source files

# 2. Ruff should show only manual fixes remaining (for Team 2)
uv run ruff check plugins/ mycelium_onboarding/ tests/
# Expected: Only non-auto-fixable errors in tests/

# 3. Run full validation on your files
uv run ruff check plugins/ mycelium_onboarding/
# Expected: Found 0 errors

# 4. Generate final report
echo "=== TEAM 1 FINAL REPORT ===" > team1-final-report.txt
echo "\nMypy Status:" >> team1-final-report.txt
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | tail -1 >> team1-final-report.txt

echo "\nRuff Status (Your Territory):" >> team1-final-report.txt
uv run ruff check plugins/ mycelium_onboarding/ 2>&1 | tail -1 >> team1-final-report.txt

echo "\nRuff Auto-Fixes Applied:" >> team1-final-report.txt
git log --oneline --grep "auto-fix" >> team1-final-report.txt

cat team1-final-report.txt
```

## Deliverables Checklist

- [ ] All 16 auto-fixable ruff errors resolved
- [ ] All 28 mypy errors resolved (Group A: 7, Group B: 14, Group C: 7)
- [ ] `uv run mypy plugins/ mycelium_onboarding/` returns 0 errors
- [ ] `uv run ruff check plugins/ mycelium_onboarding/` returns 0 errors
- [ ] All changes committed to `fix/type-safety-errors` branch
- [ ] Commit messages follow conventional commits format
- [ ] Final report generated (team1-final-report.txt)
- [ ] Ready for merge coordination with Team 2

## Communication Protocol

### Progress Updates (Every 30 minutes)

```bash
# Update progress log
echo "\n=== CHECKPOINT $(date) ===" >> team1-progress.log
echo "Mypy errors remaining: $(uv run mypy plugins/ mycelium_onboarding/ 2>&1 | grep -o '[0-9]* error' | cut -d' ' -f1 || echo 0)" >> team1-progress.log
echo "Commits so far: $(git log --oneline feat/phase2-smart-onboarding-unified..HEAD | wc -l)" >> team1-progress.log
```

### Blocker Reporting

If blocked on any issue:

1. Document blocker in `team1-blockers.txt`
1. Note which error numbers (1-28) are blocked
1. Continue with other errors
1. Report to coordinator at next checkpoint

### Completion Signal

When all tasks complete:

```bash
# Create completion marker
echo "TEAM 1 COMPLETE - $(date)" > TEAM1_COMPLETE.marker
echo "Mypy errors fixed: 28/28" >> TEAM1_COMPLETE.marker
echo "Ruff auto-fixes: 16/16" >> TEAM1_COMPLETE.marker
echo "Branch: fix/type-safety-errors" >> TEAM1_COMPLETE.marker
echo "Ready for merge: YES" >> TEAM1_COMPLETE.marker

# Notify coordinator
cat TEAM1_COMPLETE.marker
```

## Success Criteria

ALL must be true:

- [ ] `uv run mypy plugins/ mycelium_onboarding/` → Success: no issues found
- [ ] `uv run ruff check plugins/ mycelium_onboarding/` → Found 0 errors
- [ ] Git history is clean with meaningful commit messages
- [ ] No changes made to Team 2's territory (manual test fixes)
- [ ] Branch `fix/type-safety-errors` exists and is up to date
- [ ] All work committed (no uncommitted changes)
- [ ] Final report generated and validated

## Emergency Rollback

If something goes wrong:

```bash
# Reset to start of branch
git reset --hard feat/phase2-smart-onboarding-unified

# Or revert specific commit
git revert <commit-hash>

# Or delete branch and restart
git checkout feat/phase2-smart-onboarding-unified
git branch -D fix/type-safety-errors
git checkout -b fix/type-safety-errors
```

## Reference Files

- Baseline errors: `/home/gerald/git/mycelium/validation-report.txt`
- Coordination doc: `/home/gerald/git/mycelium/docs/ci-fix-action-plan.md`
- Progress tracking: `team1-progress.log` (you create this)
- Final report: `team1-final-report.txt` (you create this)

## Time Estimates by Task

- Task 1 (Auto-fix Ruff): 15 minutes
- Task 2 (Group A Mypy): 30 minutes
- Task 3 (Group B Mypy): 45 minutes
- Task 4 (Group C Mypy): 30 minutes
- Final Validation: 15 minutes
- Buffer for blockers: 30 minutes

**Total**: 2 hours 45 minutes

______________________________________________________________________

**START NOW**: Execute the Setup Commands section and begin with Task 1!
