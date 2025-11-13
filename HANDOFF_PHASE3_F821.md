# HANDOFF: Phase 3 - Fix F821 Errors (Undefined Names)

**TO**: python-pro **FROM**: multi-agent-coordinator **PRIORITY**: HIGH **ESTIMATED TIME**: 20 minutes **DEPENDENCIES**:
Phase 2 complete

## Mission

Fix all F821 ruff errors by ensuring all referenced names are properly defined or imported.

## What is F821?

F821 is the pyflakes rule that detects undefined names - variables or classes used but never defined or imported. This
catches typos and missing imports.

**Why it matters**: Undefined names cause `NameError` at runtime. Catching them at lint time prevents production
failures.

## Identified F821 Errors

### Error 1: DeploymentMethod undefined (Line 1492)

**Location**: mycelium_onboarding/cli.py:1492 **Code Context**:

```python
elif deploy_method == DeploymentMethod.KUBERNETES:  # type: ignore[name-defined]
```

**Problem**: `DeploymentMethod` is used but never imported **Current workaround**: `# type: ignore[name-defined]` -
suppressing the error instead of fixing it

### Error 2: DeploymentMethod undefined (Line 1533)

**Location**: mycelium_onboarding/cli.py:1533 **Code Context**:

```python
elif deploy_method == DeploymentMethod.SYSTEMD:  # type: ignore[name-defined]
```

**Problem**: Same as Error 1

### Error 3: watch undefined (Line 1563)

**Location**: mycelium_onboarding/cli.py:1563 **Code Context**:

```python
if watch:  # type: ignore[name-defined]
    console.print("\n[yellow]Watch mode not yet implemented[/yellow]")
```

**Problem**: `watch` variable is referenced but never defined as a parameter or variable

## Fix Procedure

### Step 1: Locate DeploymentMethod Definition

First, find where `DeploymentMethod` is defined:

```bash
# Search for DeploymentMethod class/enum definition
grep -r "class DeploymentMethod" /home/gerald/git/mycelium/mycelium_onboarding/
grep -r "DeploymentMethod = " /home/gerald/git/mycelium/mycelium_onboarding/
grep -r "from.*DeploymentMethod" /home/gerald/git/mycelium/mycelium_onboarding/

# Search in deployment module specifically
find /home/gerald/git/mycelium/mycelium_onboarding/deployment -name "*.py" -exec grep -l "DeploymentMethod" {} \;
```

**Expected locations**:

- `mycelium_onboarding/deployment/types.py`
- `mycelium_onboarding/deployment/models.py`
- `mycelium_onboarding/deployment/__init__.py`

### Step 2: Add DeploymentMethod Import

Once you've found where it's defined, add the import at the top of cli.py:

```python
# At the top of mycelium_onboarding/cli.py
# Add to existing imports section (around line 1-50)

from mycelium_onboarding.deployment.types import DeploymentMethod  # Or correct module
```

**Important**:

1. Add it in the correct import group (local imports come after stdlib and third-party)
1. Follow existing import style in the file
1. Maintain alphabetical order within the group

### Step 3: Remove type: ignore Comments

After adding the import, remove the workaround comments:

```python
# BEFORE
elif deploy_method == DeploymentMethod.KUBERNETES:  # type: ignore[name-defined]

# AFTER
elif deploy_method == DeploymentMethod.KUBERNETES:
```

Do this for BOTH occurrences (lines 1492 and 1533).

### Step 4: Fix watch Variable

Investigate the context around line 1563:

```bash
# Read the function definition containing the watch reference
sed -n '1400,1570p' /home/gerald/git/mycelium/mycelium_onboarding/cli.py | grep -B 50 "if watch"
```

**Possible scenarios**:

#### Scenario A: watch should be a function parameter (most likely)

```python
# Look for the function definition above line 1563
# It probably looks like:

@deploy.command()
@click.option("--method", ...)
# Missing: @click.option("--watch", is_flag=True, help="Watch mode")
def status(method: str | None) -> None:  # Missing: , watch: bool
    ...
    if watch:  # ← Error here
```

**Fix**:

```python
@deploy.command()
@click.option("--method", ...)
@click.option("--watch", "-w", is_flag=True, help="Enable watch mode")
def status(method: str | None, watch: bool = False) -> None:
    ...
    if watch:  # ← Now defined!
```

#### Scenario B: watch is unused legacy code

If watch functionality isn't implemented:

```python
# REMOVE the watch reference entirely
# if watch:  # type: ignore[name-defined]
#     console.print("\n[yellow]Watch mode not yet implemented[/yellow]")

# Or replace with:
# TODO: Implement watch mode in future sprint
```

#### Scenario C: watch should be imported

Unlikely, but check if there's a `watch` constant or function elsewhere:

```bash
grep -r "^watch = " /home/gerald/git/mycelium/mycelium_onboarding/
grep -r "^def watch" /home/gerald/git/mycelium/mycelium_onboarding/
```

### Step 5: Verify No Circular Imports

After adding the DeploymentMethod import:

```bash
# Try importing cli.py
cd /home/gerald/git/mycelium
python -c "from mycelium_onboarding.cli import cli; print('Import successful')"

# If this fails, you may have a circular import
# Check what deployment.types imports from cli
grep -r "from.*cli import" /home/gerald/git/mycelium/mycelium_onboarding/deployment/
```

If circular import detected:

1. Consider moving DeploymentMethod to a more isolated module
1. Or use TYPE_CHECKING import guard:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mycelium_onboarding.deployment.types import DeploymentMethod
else:
    DeploymentMethod = None  # Runtime fallback
```

## Detailed Fix Implementation

### Fix 1 & 2: DeploymentMethod Import

**Step-by-step**:

1. **Find the definition**:

```bash
find /home/gerald/git/mycelium/mycelium_onboarding/deployment -type f -name "*.py" -exec grep -l "class DeploymentMethod\|DeploymentMethod.*Enum" {} \;
```

2. **Read the file** to understand the structure:

```bash
# Assuming it's in deployment/types.py
cat /home/gerald/git/mycelium/mycelium_onboarding/deployment/types.py | grep -A 10 "DeploymentMethod"
```

3. **Check existing imports in cli.py**:

```bash
head -100 /home/gerald/git/mycelium/mycelium_onboarding/cli.py | grep "from mycelium_onboarding"
```

4. **Add the import** in the correct location (local imports section):

```python
# Example location - adjust based on actual file structure
from mycelium_onboarding.deployment.types import DeploymentMethod
```

5. **Remove type: ignore comments**:

```bash
# Edit lines 1492 and 1533
# Remove: # type: ignore[name-defined]
```

### Fix 3: watch Variable

**Investigation**:

```bash
# Find the function containing line 1563
awk '/^@deploy\.command\(\)|^def /{p=1} p{print NR": "$0; if(/^def / && NR>=1400 && NR<=1570) found=1} found && /^def [^s]/{exit}' /home/gerald/git/mycelium/mycelium_onboarding/cli.py
```

**Most likely fix** (based on similar patterns in the file):

```python
# Add click option decorator
@click.option("--watch", "-w", is_flag=True, help="Watch and refresh status")

# Add parameter to function signature
def status(method: str | None, watch: bool = False) -> None:
```

## Verification Commands

```bash
# 1. Check F821 errors are gone
echo "Checking F821 errors..."
uv run ruff check --select F821 mycelium_onboarding/cli.py
echo "Expected: All checks passed!"
echo ""

# 2. Verify imports work
echo "Testing imports..."
python -c "from mycelium_onboarding.cli import cli; print('✓ CLI import successful')"
python -c "from mycelium_onboarding.deployment.types import DeploymentMethod; print('✓ DeploymentMethod import successful')"
echo ""

# 3. Check for new errors
echo "Checking for new errors..."
uv run ruff check mycelium_onboarding/cli.py
echo ""

# 4. Run unit tests
echo "Running unit tests..."
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short -x
echo ""

# 5. Smoke test CLI
echo "CLI smoke test..."
uv run mycelium --help
uv run mycelium deploy --help
uv run mycelium deploy status --help
echo ""
```

## Success Criteria

- [ ] Located DeploymentMethod definition
- [ ] Added correct import for DeploymentMethod in cli.py
- [ ] Removed type: ignore comments from lines 1492 and 1533
- [ ] Fixed watch variable (added parameter or removed usage)
- [ ] `uv run ruff check --select F821` returns 0 errors
- [ ] No circular import errors
- [ ] CLI still imports successfully
- [ ] Unit tests still pass (585+)
- [ ] Deploy command still works (smoke test)

## Expected Changes

```python
# File: mycelium_onboarding/cli.py

# Change 1: Add import (around line 20-50)
+ from mycelium_onboarding.deployment.types import DeploymentMethod

# Change 2: Remove type: ignore (line 1492)
- elif deploy_method == DeploymentMethod.KUBERNETES:  # type: ignore[name-defined]
+ elif deploy_method == DeploymentMethod.KUBERNETES:

# Change 3: Remove type: ignore (line 1533)
- elif deploy_method == DeploymentMethod.SYSTEMD:  # type: ignore[name-defined]
+ elif deploy_method == DeploymentMethod.SYSTEMD:

# Change 4: Fix watch (around line 1563)
# Option A: Add parameter
+ @click.option("--watch", "-w", is_flag=True, help="Watch mode")
- def status(method: str | None) -> None:
+ def status(method: str | None, watch: bool = False) -> None:

# Option B: Remove unused code
- if watch:  # type: ignore[name-defined]
-     console.print("\n[yellow]Watch mode not yet implemented[/yellow]")
```

## Common Issues and Solutions

### Issue 1: DeploymentMethod not found

```bash
# If you can't find DeploymentMethod, check if it's defined inline
grep -n "KUBERNETES\|SYSTEMD\|DOCKER" /home/gerald/git/mycelium/mycelium_onboarding/cli.py | head -20

# It might be a string comparison instead of enum
# In that case, you might need to create the enum or change to string comparison
```

### Issue 2: Circular import

```python
# Use TYPE_CHECKING guard
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mycelium_onboarding.deployment.types import DeploymentMethod

# Then use string literals in type hints
def status(method: str | None, deploy_method: "DeploymentMethod | None" = None) -> None:
    ...
```

### Issue 3: watch parameter breaks existing usage

```bash
# Search for existing calls to status()
grep -r "status()" /home/gerald/git/mycelium/mycelium_onboarding/
grep -r "\.status\(" tests/

# Make watch parameter optional with default value
def status(method: str | None, watch: bool = False) -> None:
```

## Rollback Plan

```bash
# If something goes wrong
git diff mycelium_onboarding/cli.py  # Review changes
git checkout -- mycelium_onboarding/cli.py  # Discard if needed

# Report issue to coordinator
```

## Completion Checklist

- [ ] DeploymentMethod import added correctly
- [ ] type: ignore comments removed
- [ ] watch variable issue resolved
- [ ] F821 errors eliminated (verified)
- [ ] No circular imports
- [ ] No new errors introduced
- [ ] Tests passing
- [ ] CLI smoke test passing

## Handoff to Next Phase

Report to multi-agent-coordinator:

```
[PYTHON-PRO] Phase 3 Complete
- F821 errors fixed: 3
- DeploymentMethod imported from: [MODULE PATH]
- watch variable: [ADDED PARAMETER / REMOVED / OTHER]
- Circular imports: NONE
- Test status: [PASSED]
- Ruff F821 check: CLEAN
- Status: READY FOR PHASE 4
```

## Reference Files

- **Target File**: /home/gerald/git/mycelium/mycelium_onboarding/cli.py
- **Coordination Plan**: /home/gerald/git/mycelium/COORDINATION_PLAN_PR15.md
- **Previous Phase**: /home/gerald/git/mycelium/HANDOFF_PHASE2_B904.md

## Time Tracking

Start time: \_\_\_\_\_\_\_\_\_\_\_ End time: \_\_\_\_\_\_\_\_\_\_\_ Duration: \_\_\_\_\_\_\_\_\_\_\_ (target: 20
minutes)

## Questions?

Contact: multi-agent-coordinator
