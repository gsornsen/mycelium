# Pre-commit CI Parity Verification Checklist

Use this checklist to verify that pre-commit and CI have identical behavior.

## Setup Verification

- [ ] Pre-commit installed: `uv run pre-commit --version`
- [ ] Hooks installed: `ls -la .git/hooks/pre-commit .git/hooks/pre-push`
- [ ] Version checker exists: `ls scripts/check_tool_versions.py`
- [ ] Version checker executable: `python scripts/check_tool_versions.py`

## Command Parity Verification

### Ruff Lint

- [ ] **Pre-commit command**:

  ```bash
  grep -A 2 "id: ruff-check" .pre-commit-config.yaml
  ```

  Expected: `entry: uv run ruff check plugins/ mycelium_onboarding/ tests/`

- [ ] **CI command**:

  ```bash
  grep -A 2 "Run Ruff linting" .github/workflows/ci.yml
  ```

  Expected: `uv run ruff check plugins/ mycelium_onboarding/ tests/`

- [ ] Commands are identical: ✅

### Ruff Format

- [ ] **Pre-commit command**:

  ```bash
  grep -A 2 "id: ruff-format-check" .pre-commit-config.yaml
  ```

  Expected: `entry: uv run ruff format --check plugins/ mycelium_onboarding/ tests/`

- [ ] **CI command**:

  ```bash
  grep -A 2 "Run Ruff format check" .github/workflows/ci.yml
  ```

  Expected: `uv run ruff format --check plugins/ mycelium_onboarding/ tests/`

- [ ] Commands are identical: ✅

### MyPy

- [ ] **Pre-commit command**:

  ```bash
  grep -A 2 "id: mypy" .pre-commit-config.yaml
  ```

  Expected: `entry: uv run mypy plugins/ mycelium_onboarding/`

- [ ] **CI command**:

  ```bash
  grep -A 2 "Run mypy" .github/workflows/ci.yml
  ```

  Expected: `uv run mypy plugins/ mycelium_onboarding/`

- [ ] Commands are identical: ✅

### Unit Tests

- [ ] **Pre-commit command**:

  ```bash
  grep -A 7 "id: pytest-unit" .pre-commit-config.yaml
  ```

  Expected includes: `-m "not integration and not benchmark and not slow"`, `--cov=plugins`, `--cov=mycelium_onboarding`

- [ ] **CI command**:

  ```bash
  grep -A 7 "Run full unit test suite" .github/workflows/ci.yml
  ```

  Expected includes: `-m "not integration and not benchmark and not slow"`, `--cov=plugins`, `--cov=mycelium_onboarding`

- [ ] Commands are identical (except XML report): ✅

## Version Verification

- [ ] **Ruff version**:

  ```bash
  uv run ruff --version
  ```

  Expected: `ruff 0.14.0` (or version from uv.lock)

- [ ] **MyPy version**:

  ```bash
  uv run mypy --version
  ```

  Expected: From uv.lock (1.18.x or similar)

- [ ] **Python version**:

  ```bash
  python --version
  ```

  Expected: 3.10.x (or 3.13.x with warning from version checker)

- [ ] **Version checker runs**:

  ```bash
  python scripts/check_tool_versions.py
  ```

  Expected: Shows version comparison, warns on mismatches

## Functional Testing

### Test 1: Ruff Hook Catches Issues

- [ ] **Run ruff hook**:
  ```bash
  uv run pre-commit run ruff-check --all-files
  ```
  Expected: Should find same issues CI would find (if any exist)

### Test 2: Format Hook Catches Issues

- [ ] **Run format hook**:
  ```bash
  uv run pre-commit run ruff-format-check --all-files
  ```
  Expected: Should find same formatting issues CI would find

### Test 3: MyPy Hook Works

- [ ] **Run mypy hook**:
  ```bash
  uv run pre-commit run mypy --all-files
  ```
  Expected: Should find same type errors CI would find

### Test 4: Test Hook Works

- [ ] **Run test hook**:
  ```bash
  uv run pre-commit run pytest-unit --all-files
  ```
  Expected: Should run same test suite as CI

### Test 5: Version Check Works

- [ ] **Run version check**:
  ```bash
  uv run pre-commit run check-tool-versions --all-files
  ```
  Expected: Should verify versions match CI requirements

## Integration Testing

### Test 6: Pre-commit Stage

- [ ] **Make a small change**:

  ```bash
  echo "# test" >> README.md
  git add README.md
  ```

- [ ] **Commit triggers hooks**:

  ```bash
  git commit -m "test: verify pre-commit hooks"
  ```

  Expected: Ruff and format checks run (fast)

### Test 7: Pre-push Stage

- [ ] **Push triggers comprehensive hooks**:
  ```bash
  git push --dry-run
  ```
  Expected: Version check, mypy, and tests run (slower)

## Output Comparison

### Test 8: Same Errors as CI

- [ ] **Introduce a linting error**:

  ```python
  # In a test file, add:
  import os
  unused_variable = 1
  ```

- [ ] **Run pre-commit ruff-check**:

  ```bash
  uv run pre-commit run ruff-check --all-files
  ```

  Expected: Should report `F841 Local variable 'unused_variable' is assigned to but never used`

- [ ] **Compare with CI command**:

  ```bash
  uv run ruff check plugins/ mycelium_onboarding/ tests/
  ```

  Expected: Same error message

- [ ] **Clean up**:

  ```bash
  git restore .
  ```

## Configuration Validation

- [ ] **No remote ruff hooks**:

  ```bash
  grep -q "astral-sh/ruff-pre-commit" .pre-commit-config.yaml && echo "FOUND REMOTE HOOK" || echo "OK"
  ```

  Expected: `OK`

- [ ] **Uses local hooks**:

  ```bash
  grep -c "repo: local" .pre-commit-config.yaml
  ```

  Expected: At least 2 (for version check + tools)

- [ ] **Uses uv run**:

  ```bash
  grep -c "uv run" .pre-commit-config.yaml
  ```

  Expected: At least 4 (ruff-check, ruff-format, mypy, pytest)

- [ ] **Stages configured**:

  ```bash
  grep -c "stages:" .pre-commit-config.yaml
  ```

  Expected: At least 5 (one per major hook)

## Documentation Verification

- [ ] **Full documentation exists**: `ls docs/pre-commit-ci-parity.md`
- [ ] **Quick start exists**: `ls docs/quick-start-pre-commit.md`
- [ ] **Report exists**: `ls PRECOMMIT_CI_PARITY_REPORT.md`
- [ ] **Comparison table exists**: `ls comparison_table.md`
- [ ] **Executive summary exists**: `ls EXECUTIVE_SUMMARY.md`

## Final Acceptance Test

### Test 9: Clean Run Matches CI

- [ ] **Ensure clean state**:

  ```bash
  git status
  ```

  Expected: No uncommitted changes

- [ ] **Run all pre-commit hooks**:

  ```bash
  uv run pre-commit run --all-files
  ```

  Expected: All pass (or same failures as CI)

- [ ] **Push to trigger CI**:

  ```bash
  git push
  ```

  Expected: CI passes if pre-commit passed

### Test 10: Failure Parity

- [ ] **Introduce a type error**:

  ```python
  # In a Python file:
  x: int = "string"  # Type error
  ```

- [ ] **Run mypy pre-commit**:

  ```bash
  uv run pre-commit run mypy --all-files
  ```

  Expected: Type error detected

- [ ] **Verify CI would catch it**:

  ```bash
  uv run mypy plugins/ mycelium_onboarding/
  ```

  Expected: Same type error

- [ ] **Clean up**:

  ```bash
  git restore .
  ```

## Success Criteria

All checkboxes must be checked (✅) for verification to be complete.

**Overall Status**:

- [ ] All commands match CI exactly
- [ ] All tool versions match CI (or from uv.lock)
- [ ] Version checker warns on mismatches
- [ ] Pre-commit hooks catch same issues as CI
- [ ] Documentation is complete and accessible

**Verification Date**: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Verified By**: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Notes**:

______________________________________________________________________

______________________________________________________________________

______________________________________________________________________

## Troubleshooting

If any checklist item fails:

1. **Commands don't match**: Compare `.pre-commit-config.yaml` with `.github/workflows/ci.yml`
1. **Versions don't match**: Run `uv sync --frozen` to ensure uv.lock is used
1. **Hooks don't run**: Reinstall with `uv run pre-commit install --hook-type pre-commit --hook-type pre-push`
1. **Different errors**: Check Python version with `python scripts/check_tool_versions.py`

## Continuous Verification

Run this checklist:

- [ ] After updating `.pre-commit-config.yaml`
- [ ] After updating `.github/workflows/ci.yml`
- [ ] After updating tool versions in `pyproject.toml`
- [ ] Monthly as part of maintenance
- [ ] Before major releases
