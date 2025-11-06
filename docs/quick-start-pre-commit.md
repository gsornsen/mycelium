# Pre-commit Quick Start

Quick reference for using pre-commit hooks that match CI exactly.

## Setup (One-time)

```bash
# Install dependencies
uv sync --all-extras --group dev

# Install hooks
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

## Daily Workflow

```bash
# 1. Make changes
vim myfile.py

# 2. Stage changes
git add myfile.py

# 3. Commit (hooks run automatically)
git commit -m "fix: update feature"
# -> Fast checks run: ruff, formatting, basic validation

# 4. Push (comprehensive hooks run automatically)
git push
# -> Slow checks run: mypy, full test suite with coverage
```

## Manual Commands (CI Equivalent)

### Check Everything (Same as CI)

```bash
# Run all hooks
uv run pre-commit run --all-files
```

### Individual Checks

```bash
# Lint check (same as CI lint job)
uv run ruff check plugins/ mycelium_onboarding/ tests/

# Format check (same as CI lint job)
uv run ruff format --check plugins/ mycelium_onboarding/ tests/

# Type check (same as CI type-check job)
uv run mypy plugins/ mycelium_onboarding/

# Unit tests (same as CI test-unit job)
uv run pytest tests/unit/ tests/test_*.py -v \
  -m "not integration and not benchmark and not slow" \
  --tb=short \
  --cov=plugins \
  --cov=mycelium_onboarding \
  --cov-report=term
```

### Fix Issues

```bash
# Auto-fix ruff issues
uv run ruff check --fix plugins/ mycelium_onboarding/ tests/

# Auto-format code
uv run ruff format plugins/ mycelium_onboarding/ tests/

# Fix markdown
uv run mdformat docs/ *.md --wrap 120
```

## Verify Environment

```bash
# Check if your tools match CI versions
python scripts/check_tool_versions.py
```

Expected output:

```
✅ Python: 3.10.14
✅ uv: 0.5.11
✅ ruff: 0.14.0
```

If you see warnings about Python version, consider using `pyenv`:

```bash
pyenv install 3.10.14
pyenv local 3.10.14
```

## Troubleshooting

### Skip hooks (NOT RECOMMENDED)

```bash
# Skip all hooks - will likely fail CI!
git commit --no-verify
git push --no-verify
```

### Update pre-commit

```bash
# Update hook repositories
uv run pre-commit autoupdate

# Reinstall hooks
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

### Clean pre-commit cache

```bash
# Remove cached environments
uv run pre-commit clean
uv run pre-commit gc
```

## What Runs When

### On `git commit` (fast, \< 30 seconds)

- ✓ Ruff linting check
- ✓ Ruff format check
- ✓ Markdown formatting
- ✓ Trailing whitespace check
- ✓ YAML validation
- ✓ Large file check

### On `git push` (thorough, 1-3 minutes)

- ✓ Tool version verification
- ✓ MyPy type checking
- ✓ Full unit test suite
- ✓ Test coverage reporting

## Key Differences from Before

| Aspect          | Before                  | Now                                |
| --------------- | ----------------------- | ---------------------------------- |
| Ruff version    | v0.8.4 (broken)         | 0.14.0 (from uv.lock)              |
| Ruff behavior   | Auto-fixed issues       | Only checks (like CI)              |
| Format behavior | Formatted in-place      | Only checks (like CI)              |
| MyPy paths      | `plugins/mycelium-core` | `plugins/` (like CI)               |
| Tests           | Basic unit tests        | Full suite with coverage (like CI) |
| Version check   | None                    | Warns on mismatches                |

**Result**: If pre-commit passes, CI will pass. No more surprises!

## Need Help?

- Full documentation: `docs/pre-commit-ci-parity.md`
- CI workflow: `.github/workflows/ci.yml`
- Pre-commit config: `.pre-commit-config.yaml`
