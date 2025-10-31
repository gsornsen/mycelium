# Pre-commit and CI Parity

This document explains how local pre-commit hooks are configured to match CI behavior exactly, ensuring that if
pre-commit passes locally, CI will also pass.

## Problem Statement

Previously, there were several critical discrepancies between local pre-commit hooks and CI:

1. **Ruff version mismatch**: Pre-commit used `v0.8.4` (non-existent), while CI used `0.14.0` from `uv.lock`
1. **Different commands**: Pre-commit used `ruff --fix` while CI used `ruff check` (no auto-fix)
1. **Path differences**: Pre-commit checked `plugins/mycelium-core` while CI checked `plugins/`
1. **Test differences**: Pre-commit ran basic unit tests while CI ran comprehensive tests with markers
1. **Python version**: CI uses Python 3.10, local might use different version

## Solution

All pre-commit hooks now use **local hooks with `uv run`** to ensure identical tool versions and commands.

### Key Changes

#### 1. Version Management

All tools now use versions from `uv.lock`:

```yaml
- repo: local
  hooks:
    - id: ruff-check
      entry: uv run ruff check plugins/ mycelium_onboarding/ tests/
```

This ensures ruff version matches exactly what's in `uv.lock` (0.14.0), which is what CI uses.

#### 2. Exact Command Parity

| Tool        | Pre-commit                                                                                                                                                              | CI                                                                                                                                                                                       | Status                           |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| Ruff lint   | `uv run ruff check plugins/ mycelium_onboarding/ tests/`                                                                                                                | `uv run ruff check plugins/ mycelium_onboarding/ tests/`                                                                                                                                 | ✅ Identical                     |
| Ruff format | `uv run ruff format --check plugins/ mycelium_onboarding/ tests/`                                                                                                       | `uv run ruff format --check plugins/ mycelium_onboarding/ tests/`                                                                                                                        | ✅ Identical                     |
| MyPy        | `uv run mypy plugins/ mycelium_onboarding/`                                                                                                                             | `uv run mypy plugins/ mycelium_onboarding/`                                                                                                                                              | ✅ Identical                     |
| Unit tests  | `uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short --cov=plugins --cov=mycelium_onboarding --cov-report=term` | `uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short --cov=plugins --cov=mycelium_onboarding --cov-report=xml --cov-report=term` | ✅ Identical (except XML report) |

#### 3. Version Verification Hook

A new pre-push hook checks that local tool versions match CI:

```python
# scripts/check_tool_versions.py
- Verifies Python 3.10.x (matches CI)
- Verifies uv 0.5.11 (matches CI)
- Verifies ruff uses version from uv.lock
```

This hook will warn if you're using Python 3.13 instead of 3.10, which could cause type-checking differences.

### Hook Stages

Pre-commit hooks run at two stages:

**Pre-commit stage** (fast checks):

- Ruff linting check
- Ruff format check
- Markdown formatting
- Trailing whitespace
- YAML validation

**Pre-push stage** (comprehensive checks):

- Tool version verification
- MyPy type checking
- Full unit test suite with coverage

This ensures fast feedback during development while preventing CI failures before push.

## Usage

### Initial Setup

```bash
# Install dependencies (includes pre-commit)
uv sync --all-extras --group dev

# Install pre-commit hooks
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

### Manual Verification

Run all hooks manually (same as CI):

```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files

# Run specific hooks
uv run pre-commit run ruff-check --all-files
uv run pre-commit run mypy --all-files
uv run pre-commit run pytest-unit --all-files
```

### Auto-fixing Issues

Pre-commit hooks now **only check**, matching CI behavior. To auto-fix issues:

```bash
# Auto-fix ruff issues
uv run ruff check --fix plugins/ mycelium_onboarding/ tests/

# Auto-format code
uv run ruff format plugins/ mycelium_onboarding/ tests/

# Auto-fix markdown
uv run mdformat docs/ *.md --wrap 120
```

### Version Verification

Check if your local environment matches CI:

```bash
python scripts/check_tool_versions.py
```

Expected output:

```
Checking tool versions against CI requirements...
============================================================
✅ Python: 3.10.14 (matches CI: 3.10.x)
✅ uv: 0.5.11 (matches CI)
✅ ruff: 0.14.0 (from uv.lock)
============================================================
✅ All tool versions match CI requirements
```

If you see warnings about Python version mismatch, consider using `pyenv`:

```bash
# Install Python 3.10 via pyenv
pyenv install 3.10.14
pyenv local 3.10.14
```

## CI Workflow Equivalents

### Lint Job

```bash
# CI: lint job
uv run ruff check plugins/ mycelium_onboarding/ tests/
uv run ruff format --check plugins/ mycelium_onboarding/ tests/

# Pre-commit equivalent
uv run pre-commit run ruff-check --all-files
uv run pre-commit run ruff-format-check --all-files
```

### Type Check Job

```bash
# CI: type-check job
uv run mypy plugins/ mycelium_onboarding/

# Pre-commit equivalent
uv run pre-commit run mypy --all-files
```

### Unit Test Job

```bash
# CI: test-unit job (simplified - CI runs on multiple Python versions)
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --cov=plugins \
  --cov=mycelium_onboarding \
  --cov-report=term

# Pre-commit equivalent
uv run pre-commit run pytest-unit --all-files
```

## Troubleshooting

### Pre-commit passes but CI fails

This should no longer happen! If it does:

1. Check tool versions: `python scripts/check_tool_versions.py`
1. Compare pre-commit commands with `.github/workflows/ci.yml`
1. Ensure `uv.lock` is up to date: `uv sync --frozen`
1. Report issue - this is a bug in the parity setup

### Pre-commit fails but you need to commit

```bash
# Skip hooks (NOT RECOMMENDED - will likely fail CI)
git commit --no-verify

# Better: Fix the issues
uv run ruff check --fix plugins/ mycelium_onboarding/ tests/
uv run ruff format plugins/ mycelium_onboarding/ tests/
git add -u
git commit
```

### Python version mismatch warnings

The version checker will warn if you're using Python 3.13 instead of 3.10:

```
⚠️  Python: 3.13.6 (CI uses 3.10.x)
```

This is a **warning**, not an error. Most code will work fine, but:

- Type checking behavior may differ slightly
- New Python 3.13 features will fail in CI
- Consider using `pyenv` to match CI version for complete parity

## Design Principles

1. **Single source of truth**: `uv.lock` controls all tool versions
1. **Exact command parity**: Pre-commit uses identical commands to CI
1. **Fail early**: Comprehensive checks run before push, not in CI
1. **Transparent verification**: Version checker makes mismatches visible
1. **Developer-friendly**: Fast feedback in pre-commit, thorough checks in pre-push

## Related Files

- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.github/workflows/ci.yml` - CI workflow (source of truth for commands)
- `scripts/check_tool_versions.py` - Version verification script
- `pyproject.toml` - Tool configuration (ruff, mypy, pytest settings)
- `uv.lock` - Locked tool versions

## Future Improvements

1. Add integration test pre-push hook (optional, requires PostgreSQL)
1. Add Python version auto-switcher using pyenv
1. Add pre-commit.ci integration for automated PR fixes
1. Add benchmark regression checks
