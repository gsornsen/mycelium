# HANDOFF: Phase 2 - Fix B904 Errors (Exception Chaining)

**TO**: python-pro **FROM**: multi-agent-coordinator **PRIORITY**: HIGH **ESTIMATED TIME**: 30 minutes **DEPENDENCIES**:
Phase 1 complete

## Mission

Fix all B904 ruff errors by adding proper exception chaining. This improves error debugging by preserving the original
exception context.

## What is B904?

B904 is the flake8-bugbear rule that enforces exception chaining. When re-raising or raising a new exception inside an
except block, you should use `from` to preserve the original exception context.

**Why it matters**: Exception chaining helps developers trace the root cause of errors through the full exception stack.

## Error Pattern

```python
# BAD - B904 violation
try:
    risky_operation()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise SystemExit(1)  # ← Original exception context lost!

# GOOD - B904 compliant
try:
    risky_operation()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise SystemExit(1) from e  # ← Exception context preserved!
```

## Locations to Fix

Based on GitHub CI output and code review:

### File 1: mycelium_onboarding/cli.py

**Location 1: Line 1352**

```python
# Context: deploy start command
except KeyboardInterrupt:
    console.print("\n[yellow]Deployment cancelled by user.[/yellow]")
    raise SystemExit(130)  # ← ADD: from e (or from None if no exception)
```

**Location 2: Line 1394**

```python
# Context: deploy stop command
except KeyboardInterrupt:
    console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    raise SystemExit(130)  # ← ADD: from e (or from None if KeyboardInterrupt)
```

**Location 3: Line 1432**

```python
# Context: Another deploy operation
except Exception as e:
    console.print(f"[bold red]✗ Failed: {e}[/bold red]")
    if verbose:
        logger.exception("Operation failed")
    raise SystemExit(1)  # ← ADD: from e
```

**Location 4: Line 1599**

```python
# Context: TBD - check actual code
# ADD: from e or from None as appropriate
```

**Location 5: Line 1643**

```python
# Context: TBD - check actual code
# ADD: from e or from None as appropriate
```

### File 2: mycelium_onboarding/cli_commands/commands/config.py

**Location 6: Line 493**

```python
# Context: Config command
# ADD: from e or from None as appropriate
```

## Fix Procedure

### Step 1: Read and Understand Context

For EACH location:

```bash
# Read the specific section
cat /home/gerald/git/mycelium/mycelium_onboarding/cli.py | sed -n '1350,1360p'
```

Understand:

- What exception is being caught?
- Is there a named exception variable (e.g., `as e`)?
- Is it KeyboardInterrupt (should be `from None`) or Exception (should be `from e`)?

### Step 2: Apply the Correct Fix

**Rule 1: If catching `Exception as e` or similar**

```python
except Exception as e:
    # ... error handling ...
    raise SystemExit(1) from e  # ← Chain the exception
```

**Rule 2: If catching `KeyboardInterrupt` (no variable)**

```python
except KeyboardInterrupt:
    # ... cleanup ...
    raise SystemExit(130) from None  # ← Suppress the chain (user action, not error)
```

**Rule 3: If catching specific exception with variable**

```python
except ValueError as e:
    # ... handling ...
    raise CustomError("Invalid value") from e  # ← Chain the original
```

### Step 3: Read Each File and Apply Fixes

```bash
# 1. Read cli.py around line 1352
# 2. Make the fix
# 3. Repeat for each location
```

**IMPORTANT**: Read the ACTUAL code before making changes. Line numbers may have shifted slightly.

### Step 4: Verify Fixes

```bash
# Check only B904 errors
uv run ruff check --select B904 mycelium_onboarding/

# Expected: 0 errors
```

### Step 5: Run Full Test Suite

```bash
# Ensure we didn't break anything
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short

# Expected: 585+ passed, 42 skipped, 0 failed
```

## Detailed Fix Examples

### Example 1: Simple Exception Chaining

**BEFORE**:

```python
try:
    success = asyncio.run(deploy_cmd.start(method=method))
    if not success:
        raise SystemExit(1)
except KeyboardInterrupt:
    console.print("\n[yellow]Deployment cancelled by user.[/yellow]")
    raise SystemExit(130)  # ← B904 error
except Exception as e:
    console.print(f"[bold red]✗ Deployment failed: {e}[/bold red]")
    if verbose:
        logger.exception("Deployment failed")
    raise SystemExit(1)  # ← B904 error
```

**AFTER**:

```python
try:
    success = asyncio.run(deploy_cmd.start(method=method))
    if not success:
        raise SystemExit(1)
except KeyboardInterrupt:
    console.print("\n[yellow]Deployment cancelled by user.[/yellow]")
    raise SystemExit(130) from None  # ← Fixed: KeyboardInterrupt = from None
except Exception as e:
    console.print(f"[bold red]✗ Deployment failed: {e}[/bold red]")
    if verbose:
        logger.exception("Deployment failed")
    raise SystemExit(1) from e  # ← Fixed: Exception as e = from e
```

### Example 2: Config.py Fix (Line 493)

**Need to read the actual code first**:

```bash
# Read the context
sed -n '490,500p' /home/gerald/git/mycelium/mycelium_onboarding/cli_commands/commands/config.py
```

Then apply the appropriate fix based on the exception type.

## Verification Commands

```bash
# 1. Check B904 errors are gone
echo "Checking B904 errors..."
uv run ruff check --select B904 mycelium_onboarding/
echo "Expected: All checks passed!"
echo ""

# 2. Verify no new errors introduced
echo "Checking for new errors..."
uv run ruff check mycelium_onboarding/cli.py mycelium_onboarding/cli_commands/commands/config.py
echo ""

# 3. Run unit tests
echo "Running unit tests..."
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short -x
echo ""

# 4. Quick smoke test (if available)
echo "Smoke test - ensure CLI still works..."
uv run mycelium --help
uv run mycelium config --help
echo ""
```

## Success Criteria

- [ ] Read and understood all 6+ B904 error locations
- [ ] Applied correct fix (`from e` or `from None`) to each location
- [ ] `uv run ruff check --select B904` returns 0 errors
- [ ] Unit tests still pass (585+)
- [ ] No new ruff errors introduced
- [ ] CLI smoke test passes (basic commands work)
- [ ] Code changes reviewed for correctness

## Expected Changes

You should modify approximately:

- **mycelium_onboarding/cli.py**: 5-7 lines changed
- **mycelium_onboarding/cli_commands/commands/config.py**: 1 line changed

Total: ~6-8 lines of code changed (adding ` from e` or ` from None`)

## Common Pitfalls

### Pitfall 1: Using `from e` when there's no `e`

```python
# WRONG
except KeyboardInterrupt:
    raise SystemExit(130) from e  # ← e doesn't exist!

# RIGHT
except KeyboardInterrupt:
    raise SystemExit(130) from None
```

### Pitfall 2: Using `from None` when you should chain

```python
# WRONG - loses debugging information
except Exception as e:
    raise SystemExit(1) from None  # ← Should be 'from e'

# RIGHT
except Exception as e:
    raise SystemExit(1) from e
```

### Pitfall 3: Missing exception in outer scope

```python
# WRONG
try:
    ...
except ValueError as e:
    logger.error(f"Error: {e}")

try:
    raise SystemExit(1) from e  # ← e is out of scope!
except:
    pass

# RIGHT - only use 'from e' inside the same except block
try:
    ...
except ValueError as e:
    logger.error(f"Error: {e}")
    raise SystemExit(1) from e  # ← Same except block
```

## Rollback Plan

If something goes wrong:

```bash
# Discard changes
git checkout -- mycelium_onboarding/cli.py
git checkout -- mycelium_onboarding/cli_commands/commands/config.py

# Report to coordinator
echo "Phase 2 rollback executed - awaiting guidance"
```

## Completion Checklist

Before marking complete:

1. [ ] All B904 errors fixed (verified with ruff)
1. [ ] Tests passing (verified with pytest)
1. [ ] No new errors introduced
1. [ ] Changes make semantic sense
1. [ ] Smoke test passes

## Handoff to Next Phase

Once complete, report to multi-agent-coordinator:

```
[PYTHON-PRO] Phase 2 Complete
- B904 errors fixed: [NUMBER]
- Files modified: cli.py, config.py
- Test status: [PASSED/FAILED]
- Ruff B904 check: CLEAN
- New errors introduced: 0
- Status: READY FOR PHASE 3
```

The coordinator will then dispatch python-pro (or you continue) to Phase 3 for F821 fixes.

## Reference Files

- **Coordination Plan**: /home/gerald/git/mycelium/COORDINATION_PLAN_PR15.md
- **Baseline Report**: /home/gerald/git/mycelium/CI_BASELINE_REPORT.md
- **Target Files**:
  - /home/gerald/git/mycelium/mycelium_onboarding/cli.py
  - /home/gerald/git/mycelium/mycelium_onboarding/cli_commands/commands/config.py

## Time Tracking

Start time: \_\_\_\_\_\_\_\_\_\_\_ End time: \_\_\_\_\_\_\_\_\_\_\_ Duration: \_\_\_\_\_\_\_\_\_\_\_ (target: 30
minutes)

## Questions?

Contact: multi-agent-coordinator
