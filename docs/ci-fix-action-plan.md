# CI Fix Action Plan - PR #15

**Branch**: `feat/phase2-smart-onboarding-unified` **Status**: In Progress **Coordination**: Multi-Agent Systematic Fix
**Priority**: Critical - Blocking PR merge

## Executive Summary

Local validation passed (1404 tests, ruff clean, mypy with --no-verify) but CI fails on multiple fronts. Root cause:
configuration mismatch between local hooks and CI workflows. This plan coordinates specialized agents to systematically
align and fix all issues.

## Current CI Failures (PR #15)

### 1. Lint with Ruff - FAILING

- **Error**: Lint errors in files not being checked locally
- **Root Cause**: Local hooks only check changed files
- **Impact**: Unknown number of lint violations

### 2. Type Check with mypy - FAILING (28 errors)

- **Error**: 28 mypy type checking errors
- **Root Cause**: Local runs `plugins/mycelium-core` vs CI runs `plugins/`
- **Impact**: Type safety violations across codebase

### 3. Unit Tests - FAILING

- **Error**: Test failures across Python 3.10-3.13 matrix
- **Platforms**: Multiple failures on Windows/Mac/Linux
- **Root Cause**: Platform-specific issues, import path problems
- **Impact**: Core functionality broken on some platforms

### 4. Integration Tests - FAILING

- **Error**: Integration tests improperly skipped or failing
- **Root Cause**: Database setup, test markers, conditional skipping
- **Impact**: End-to-end workflows not validated

## Agent Team Assembly

### Phase 1: Analysis & Configuration Alignment (COMPLETED ✅)

**Lead**: Multi-Agent Coordinator (this agent)

**Deliverables**:

- ✅ Configuration discrepancy analysis
- ✅ Updated `.pre-commit-config.yaml` to match CI exactly
- ✅ Created `scripts/validate-ci-local.sh` for local CI simulation
- ✅ Documented alignment in `docs/ci-local-alignment.md`

### Phase 2: Type Safety Fixes (IN PROGRESS)

**Agent Required**: Type Safety Expert / Python Developer

**Task**: Fix all 28 mypy errors

**Approach**:

1. Run `uv run mypy plugins/ mycelium_onboarding/` to get full error list
1. Categorize errors by type:
   - Missing type hints
   - Untyped function definitions
   - `Any` type usage
   - Optional type handling
   - Import type issues
1. Fix systematically, starting with core modules
1. Validate after each fix batch

**Files to Fix** (predicted based on common patterns):

- `plugins/*/` - All plugin modules
- `mycelium_onboarding/` - Core onboarding modules

**Validation**:

```bash
uv run mypy plugins/ mycelium_onboarding/
# Must return 0 errors
```

### Phase 3: Ruff Lint Fixes (PARALLEL TO PHASE 2)

**Agent Required**: Code Quality Specialist

**Task**: Fix all ruff lint violations

**Approach**:

1. Run `uv run ruff check plugins/ mycelium_onboarding/ tests/` to get violations
1. Auto-fix where possible: `uv run ruff check --fix plugins/ mycelium_onboarding/ tests/`
1. Manually fix remaining issues
1. Ensure format compliance: `uv run ruff format plugins/ mycelium_onboarding/ tests/`

**Validation**:

```bash
uv run ruff check plugins/ mycelium_onboarding/ tests/
uv run ruff format --check plugins/ mycelium_onboarding/ tests/
# Both must pass with no errors
```

### Phase 4: Unit Test Fixes (DEPENDS ON PHASE 2 & 3)

**Agent Required**: Testing Coordinator / Python Developer

**Task**: Fix all unit test failures across Python versions

**Approach**:

1. Run locally: `uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow"`
1. Identify failure categories:
   - Import errors (PYTHONPATH)
   - Platform-specific path issues (Windows)
   - Async test fixture problems
   - Mock/patch issues
1. Fix systematically by category
1. Ensure coverage ≥80%

**Critical Issues to Address**:

- **PYTHONPATH**: Removed from `pyproject.toml` per recent commits
- **Platform paths**: Use `pathlib.Path` instead of `os.path`
- **Async tests**: Ensure `pytest-asyncio` markers correct
- **Fixtures**: Verify fixture scope and cleanup

**Validation**:

```bash
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --cov=plugins \
  --cov=mycelium_onboarding \
  --cov-report=term \
  --cov-fail-under=80
# Must pass all tests with coverage ≥80%
```

### Phase 5: Integration Test Fixes (DEPENDS ON PHASE 4)

**Agent Required**: Integration Test Specialist

**Task**: Fix integration test failures and skipping issues

**Approach**:

1. Verify PostgreSQL setup in CI (already configured)
1. Check test markers: Ensure all integration tests have `@pytest.mark.integration`
1. Fix conditional skipping logic
1. Validate database migrations run correctly
1. Test database connection and cleanup

**Critical Checks**:

- All integration tests have proper markers
- No improper `@pytest.mark.skip` decorators
- Database cleanup in teardown
- Environment variables properly set

**Validation** (requires PostgreSQL):

```bash
# Setup PostgreSQL locally
export DATABASE_URL=postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test
uv run alembic upgrade head

# Run integration tests
uv run pytest tests/integration/ -v -m "integration" --tb=short
# Must pass all integration tests
```

### Phase 6: Cross-Platform Validation (FINAL PHASE)

**Agent Required**: CI/CD Specialist

**Task**: Ensure fixes work across all platforms and Python versions

**Approach**:

1. Run local validation script: `./scripts/validate-ci-local.sh`
1. Check for platform-specific issues:
   - Path separator differences (Windows `\` vs Unix `/`)
   - Line ending differences (CRLF vs LF)
   - Case-sensitive filesystem issues
1. Validate on multiple Python versions (if possible locally)
1. Push and monitor CI for all matrix jobs

**Validation**:

```bash
./scripts/validate-ci-local.sh
# Must pass completely

# Then push and verify CI
git push origin feat/phase2-smart-onboarding-unified
# Monitor: https://github.com/USER/mycelium/actions
```

## Execution Timeline

### Immediate (Next 30 minutes)

- [x] Configuration alignment complete
- [ ] Start mypy error fixes
- [ ] Start ruff lint fixes

### Short-term (Next 2 hours)

- [ ] Complete all mypy fixes (28 errors)
- [ ] Complete all ruff fixes
- [ ] Begin unit test fixes

### Medium-term (Next 4 hours)

- [ ] Complete unit test fixes
- [ ] Begin integration test fixes
- [ ] Run full local validation

### Final (Before push)

- [ ] All local validation passes
- [ ] Documentation updated
- [ ] Commit and push to PR #15
- [ ] Monitor CI for green checks

## Command Sequence

Execute in this exact order:

```bash
# 1. Ensure clean state
cd /home/gerald/git/mycelium
git status  # Should be on feat/phase2-smart-onboarding-unified

# 2. Sync dependencies
uv sync --frozen --all-extras --group dev

# 3. Install updated pre-commit hooks
pre-commit clean
pre-commit install --hook-type pre-commit --hook-type pre-push

# 4. Fix mypy errors
uv run mypy plugins/ mycelium_onboarding/ | tee mypy-errors.log
# Fix all errors, then re-run until clean

# 5. Fix ruff issues
uv run ruff check --fix plugins/ mycelium_onboarding/ tests/
uv run ruff format plugins/ mycelium_onboarding/ tests/
uv run ruff check plugins/ mycelium_onboarding/ tests/  # Verify clean

# 6. Fix unit tests
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --maxfail=5  # Stop after 5 failures for faster iteration
# Fix failures, then run full suite

# 7. Run full unit test suite with coverage
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --cov=plugins \
  --cov=mycelium_onboarding \
  --cov-report=term \
  --cov-fail-under=80

# 8. Fix integration tests (if PostgreSQL available)
# Setup PostgreSQL first (see Phase 5 above)
uv run pytest tests/integration/ -v -m "integration" --tb=short

# 9. Run complete local CI validation
chmod +x scripts/validate-ci-local.sh
./scripts/validate-ci-local.sh

# 10. If all passes, commit and push
git add .
git commit -m "fix: align local validation with CI and resolve all blocking issues

- Update .pre-commit-config.yaml to match CI exactly
- Fix all 28 mypy type checking errors
- Resolve ruff lint violations
- Fix unit test failures across Python versions
- Fix integration test skipping and failures
- Add local CI validation script
- Document CI/local alignment strategy

Closes #15 CI failures"

git push origin feat/phase2-smart-onboarding-unified
```

## Risk Mitigation

### Risk: Breaking existing functionality

- **Mitigation**: Run full test suite after each fix batch
- **Rollback**: Git commits structured for easy revert

### Risk: Platform-specific fixes break other platforms

- **Mitigation**: Use cross-platform patterns (pathlib, not os.path)
- **Validation**: Monitor CI matrix for all platform results

### Risk: Mypy fixes introduce runtime errors

- **Mitigation**: Run tests after each mypy fix batch
- **Strategy**: Fix by module, test module, repeat

### Risk: Integration test failures hard to debug

- **Mitigation**: Local PostgreSQL setup for iteration
- **Fallback**: CI logs provide detailed failure info

## Success Criteria

All of the following must be true:

- [ ] `uv run mypy plugins/ mycelium_onboarding/` - 0 errors
- [ ] `uv run ruff check plugins/ mycelium_onboarding/ tests/` - 0 errors
- [ ] `uv run ruff format --check plugins/ mycelium_onboarding/ tests/` - Clean
- [ ] Unit tests pass on all Python versions (3.10-3.13)
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass with PostgreSQL
- [ ] `./scripts/validate-ci-local.sh` passes completely
- [ ] CI checks all green on PR #15
- [ ] No platform-specific failures (Windows/Mac/Linux)

## Communication Protocol

### Status Updates

After each phase completion, update with:

```json
{
  "agent": "agent-name",
  "phase": "phase-number",
  "status": "completed|in-progress|blocked",
  "metrics": {
    "mypy_errors": 0,
    "ruff_errors": 0,
    "test_failures": 0,
    "coverage_percent": 85
  },
  "blockers": []
}
```

### Escalation Path

If blocked:

1. Document blocker in this file
1. Attempt alternative approach
1. Request additional agent assistance
1. Escalate to multi-agent coordinator

## References

- **CI Configuration**: `.github/workflows/ci.yml`, `.github/workflows/test.yml`
- **Local Hooks**: `.pre-commit-config.yaml`
- **Validation Script**: `scripts/validate-ci-local.sh`
- **Alignment Doc**: `docs/ci-local-alignment.md`
- **PR Context**: https://github.com/USER/mycelium/pull/15

## Next Actions

**IMMEDIATE**: Start Phase 2 (Type Safety Fixes)

```bash
# Run this NOW to get the full mypy error list
cd /home/gerald/git/mycelium
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | tee mypy-errors-full.log
cat mypy-errors-full.log
```

Then proceed with systematic fixes following the phase plan above.
