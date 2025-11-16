# CI and Local Validation Alignment

## Problem Statement

There was a critical discrepancy between local pre-commit/pre-push hooks and GitHub CI checks, causing CI failures even
though code passed locally. This document outlines the issues, solutions, and ongoing validation strategy.

## Root Causes Identified

### 1. Ruff Configuration Mismatch

**Before:**

- Local: Only checked files being committed
- CI: Checked ALL files in `plugins/`, `mycelium_onboarding/`, `tests/`
- **Impact**: Lint errors in unchanged files were missed locally

**After:**

- Local hooks now explicitly check the same directories as CI
- Added `files: ^(plugins/|mycelium_onboarding/|tests/)` to ruff hooks

### 2. Mypy Type Checking Mismatch

**Before:**

- Local: `uv run mypy plugins/mycelium-core mycelium_onboarding` (specific subdirectory)
- CI: `uv run mypy plugins/ mycelium_onboarding/` (entire directories)
- **Impact**: 28 mypy errors existed that weren't caught locally

**After:**

- Local now runs: `uv run mypy plugins/ mycelium_onboarding/`
- Exactly matches CI command
- Type errors must be fixed before push

### 3. Unit Test Execution Mismatch

**Before:**

- Local: Quick tests with `-x --tb=short` (exit on first failure)
- CI: Full test suite with coverage across Python 3.10-3.13, all platforms
- **Impact**: Tests passed locally (1404) but failed in CI cross-platform

**After:**

- Local runs full unit test suite with coverage
- Added coverage threshold (`--cov-fail-under=80`)
- Matches CI test markers and exclusions

### 4. Integration Test Gap

**Before:**

- Local: No integration test validation
- CI: Full integration tests with PostgreSQL service
- **Impact**: Integration test failures only discovered in CI

**After:**

- Local validates integration tests when PostgreSQL available
- Falls back to collection-only mode without PostgreSQL
- Warns user that integration tests will run in CI

## Updated Configuration Files

### `.pre-commit-config.yaml`

Updated to match CI exactly:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        files: ^(plugins/|mycelium_onboarding/|tests/)  # Match CI
      - id: ruff-format
        files: ^(plugins/|mycelium_onboarding/|tests/)  # Match CI

  - repo: local
    hooks:
      - id: mypy
        name: Type check with mypy (STRICT - matches CI)
        args: [plugins/, mycelium_onboarding/]  # Match CI exactly
        stages: [pre-push]

      - id: pytest-unit
        name: Unit tests (matches CI unit test suite)
        stages: [pre-push]
        args:
          - |
            uv run pytest tests/unit/ tests/test_*.py -v \
              -m "not integration and not benchmark and not slow" \
              --tb=short \
              --cov=plugins \
              --cov=mycelium_onboarding \
              --cov-report=term \
              --cov-fail-under=80

      - id: ruff-all-check
        name: Ruff check all files (matches CI lint job)
        stages: [pre-push]
        # Runs ruff check + format check on all directories

      - id: integration-test-check
        name: Integration test validation
        stages: [pre-push]
        # Conditionally runs integration tests if PostgreSQL available
```

### New Tool: `scripts/validate-ci-local.sh`

Created a comprehensive local validation script that:

1. Runs exact CI commands locally
1. Provides colored output for easy debugging
1. Supports `--fix` mode for auto-fixing issues
1. Supports `--skip-integration` when PostgreSQL unavailable
1. Validates path compatibility for cross-platform support

Usage:

```bash
# Full validation (recommended before push)
./scripts/validate-ci-local.sh

# Auto-fix ruff issues
./scripts/validate-ci-local.sh --fix

# Skip integration tests (no PostgreSQL required)
./scripts/validate-ci-local.sh --skip-integration
```

## CI Workflow Structure

### `.github/workflows/ci.yml` (Main CI Pipeline)

Jobs executed on every PR:

1. **lint**: Ruff linting and format checking
1. **type-check**: Mypy type checking
1. **test-unit**: Unit tests (Python 3.10-3.13 matrix)
1. **test-integration**: Integration tests with PostgreSQL
1. **migration-tests**: Database migration verification
1. **ci-success**: Aggregates all job results

### `.github/workflows/test.yml` (Comprehensive Testing)

Extended test matrix:

1. **test-matrix**: Cross-platform tests (Ubuntu/macOS/Windows)
1. **integration-postgres**: PostgreSQL integration tests
1. **benchmarks**: Performance benchmarks (scheduled/manual)

## Validation Checklist

Before pushing code, ensure ALL of these pass:

- [ ] `uv run ruff check plugins/ mycelium_onboarding/ tests/` - No lint errors
- [ ] `uv run ruff format --check plugins/ mycelium_onboarding/ tests/` - Formatting correct
- [ ] `uv run mypy plugins/ mycelium_onboarding/` - No type errors
- [ ] Unit tests pass with coverage ≥80%
- [ ] Integration tests pass (or validated for collection)
- [ ] `./scripts/validate-ci-local.sh` passes completely

## Fixing Current Issues

### Step 1: Fix Mypy Errors (28 errors currently)

Run locally to see errors:

```bash
uv run mypy plugins/ mycelium_onboarding/
```

Common mypy fixes needed:

- Add type hints to function signatures
- Fix `Any` type usage
- Add return type annotations
- Handle Optional types correctly
- Fix untyped imports

### Step 2: Fix Unit Test Failures

Run locally to identify failures:

```bash
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short
```

Common test fixes:

- Fix import paths (PYTHONPATH issues)
- Mock external dependencies correctly
- Handle async test fixtures
- Fix platform-specific path handling

### Step 3: Fix Integration Test Failures

Ensure PostgreSQL is running locally:

```bash
# Start PostgreSQL (if using Docker)
docker run -d \
  --name mycelium-postgres \
  -e POSTGRES_USER=mycelium \
  -e POSTGRES_PASSWORD=mycelium_test \
  -e POSTGRES_DB=mycelium_test \
  -p 5432:5432 \
  ankane/pgvector:latest

# Run migrations
export DATABASE_URL=postgresql://mycelium:mycelium_test@localhost:5432/mycelium_test
uv run alembic upgrade head

# Run integration tests
uv run pytest tests/integration/ -v -m "integration" --tb=short
```

### Step 4: Validate Everything Locally

```bash
# Full validation
./scripts/validate-ci-local.sh

# If issues found, fix and re-run
./scripts/validate-ci-local.sh --fix
```

## Prevention Strategy

### For Developers

1. **Always run pre-push hooks**: Don't use `--no-verify`
1. **Run local validation before pushing**: `./scripts/validate-ci-local.sh`
1. **Keep dependencies in sync**: `uv sync --frozen --all-extras --group dev`
1. **Test across Python versions locally** (if possible): Use `tox` or multiple venvs

### For CI/CD

1. **Fail fast**: CI jobs ordered by speed (lint → type → tests)
1. **Caching optimized**: UV packages, pytest cache, model cache
1. **Matrix testing**: Python 3.10-3.13, Linux/macOS/Windows
1. **Coverage tracking**: Maintain ≥80% coverage threshold

### For Repository Maintenance

1. **Keep pre-commit hooks synchronized** with CI configuration
1. **Document any CI-only checks** that can't run locally
1. **Regular validation script updates** when CI changes
1. **Monitor CI performance** and optimize slow jobs

## Success Metrics

After alignment, expect:

- **100% local-CI parity**: If it passes locally, it passes in CI
- **Zero surprise failures**: All failures caught before push
- **Faster feedback**: Issues found in \<2 minutes locally vs 5-10 minutes in CI
- **Higher confidence**: Push knowing CI will succeed

## Next Steps

1. **Fix all 28 mypy errors** - Type safety critical
1. **Resolve unit test failures** - Core functionality validation
1. **Fix integration test issues** - End-to-end validation
1. **Update pre-commit hooks** - Already done ✓
1. **Test local validation script** - Already created ✓
1. **Document for team** - This document ✓

## Commands Reference

### Local Development

```bash
# Install/update dependencies
uv sync --frozen --all-extras --group dev

# Install pre-commit hooks
pre-commit install --hook-type pre-commit --hook-type pre-push

# Run specific checks
uv run ruff check plugins/ mycelium_onboarding/ tests/
uv run mypy plugins/ mycelium_onboarding/
uv run pytest tests/unit/ -v

# Full local CI validation
./scripts/validate-ci-local.sh

# Auto-fix issues
./scripts/validate-ci-local.sh --fix
```

### CI Debugging

```bash
# Check CI logs on GitHub
gh run list --limit 5
gh run view <run-id>
gh run view <run-id> --log-failed

# Download CI artifacts
gh run download <run-id>

# Reproduce CI environment locally (using act)
act -j lint
act -j type-check
act -j test-unit
```

## Configuration Matrix

| Check             | Local (.pre-commit-config.yaml)        | CI (ci.yml)                            | Status               |
| ----------------- | -------------------------------------- | -------------------------------------- | -------------------- |
| Ruff lint         | `plugins/ mycelium_onboarding/ tests/` | `plugins/ mycelium_onboarding/ tests/` | ✅ Aligned           |
| Ruff format       | `plugins/ mycelium_onboarding/ tests/` | `plugins/ mycelium_onboarding/ tests/` | ✅ Aligned           |
| Mypy              | `plugins/ mycelium_onboarding/`        | `plugins/ mycelium_onboarding/`        | ✅ Aligned           |
| Unit tests        | Full suite with coverage               | Full suite with coverage               | ✅ Aligned           |
| Integration tests | Conditional (if PostgreSQL available)  | Full (PostgreSQL service)              | ⚠️ Partial           |
| Python versions   | Local version only                     | 3.10, 3.11, 3.12, 3.13                 | ⚠️ Matrix only in CI |
| Platforms         | Local OS only                          | Linux, macOS, Windows                  | ⚠️ Matrix only in CI |

## Maintenance

### When to Update This Alignment

- Adding new lint rules
- Changing mypy strictness
- Adding new test categories
- Modifying CI workflows
- Updating Python version support
- Adding new validation steps

### Version History

- **2025-11-11**: Initial CI/local alignment
  - Updated `.pre-commit-config.yaml`
  - Created `validate-ci-local.sh`
  - Documented discrepancies and fixes

## Troubleshooting

### "Mypy errors but pre-commit passed"

- Old pre-commit configuration cached
- Solution: `pre-commit clean && pre-commit install --hook-type pre-push`

### "Tests pass locally but fail in CI"

- Python version differences
- Platform-specific issues (Windows path separators)
- Solution: Run `./scripts/validate-ci-local.sh` and check for path issues

### "Integration tests fail in CI"

- Database not initialized properly
- Migration errors
- Solution: Check CI logs for PostgreSQL connection errors, verify migrations

### "Ruff passes locally but fails in CI"

- Not checking all files
- Different ruff version
- Solution: Ensure `files: ^(plugins/|mycelium_onboarding/|tests/)` in pre-commit config

## Contact

For questions or issues with CI/local alignment:

- Review this document
- Check CI logs: `gh run list --limit 5`
- Run local validation: `./scripts/validate-ci-local.sh`
- Review PR #15 for context
