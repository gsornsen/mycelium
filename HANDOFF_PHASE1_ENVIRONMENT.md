# HANDOFF: Phase 1 - Environment Configuration Matching

**TO**: devops-engineer **FROM**: multi-agent-coordinator **PRIORITY**: HIGH **ESTIMATED TIME**: 15 minutes

## Mission

Make the local development environment match GitHub CI strictness exactly. This is critical - we need to see the same
errors locally that GitHub CI sees.

## Context

Currently:

- **Local tests**: 585 passed, 42 skipped, 0 failed ✅
- **GitHub CI**: FAILING with 65+ ruff errors ❌

The problem: Local ruff/mypy are not catching errors that GitHub CI catches. We need to run the EXACT same commands that
GitHub CI runs.

## Tasks

### Task 1: Run GitHub CI Lint Commands Locally

Execute the exact commands from GitHub CI workflow:

```bash
# Navigate to project root
cd /home/gerald/git/mycelium

# 1. Run ruff check (this should show 65+ errors)
uv run ruff check plugins/ mycelium_onboarding/ tests/ 2>&1 | tee ruff_errors.txt

# 2. Get structured error output
uv run ruff check plugins/ mycelium_onboarding/ tests/ --output-format=json > ruff_errors.json

# 3. Get error statistics
uv run ruff check plugins/ mycelium_onboarding/ tests/ --statistics | tee ruff_stats.txt

# 4. Run format check
uv run ruff format --check plugins/ mycelium_onboarding/ tests/ 2>&1 | tee ruff_format.txt

# 5. Run mypy check
uv run mypy plugins/ mycelium_onboarding/ 2>&1 | tee mypy_errors.txt
```

### Task 2: Analyze Error Distribution

Parse the output to categorize errors:

```bash
# Count errors by type
grep -E "B904|F821|E402|SIM102|F841|ARG001" ruff_errors.txt | sort | uniq -c

# List all files with errors
grep -oP '^[^:]+' ruff_errors.txt | sort | uniq -c
```

### Task 3: Create Validation Script

Create a script that mirrors GitHub CI checks:

```bash
cat > /home/gerald/git/mycelium/scripts/validate_ci.sh << 'EOF'
#!/bin/bash
# CI Validation Script - Mirrors GitHub CI checks exactly
# Run this before pushing to ensure CI will pass

set -e

echo "========================================="
echo "CI Validation Script"
echo "Mirrors GitHub CI workflow checks"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# 1. Ruff Lint Check
echo "Step 1: Ruff Lint Check"
echo "Command: uv run ruff check plugins/ mycelium_onboarding/ tests/"
if uv run ruff check plugins/ mycelium_onboarding/ tests/; then
    echo -e "${GREEN}✓ Ruff lint passed${NC}"
else
    echo -e "${RED}✗ Ruff lint failed${NC}"
    FAILED=1
fi
echo ""

# 2. Ruff Format Check
echo "Step 2: Ruff Format Check"
echo "Command: uv run ruff format --check plugins/ mycelium_onboarding/ tests/"
if uv run ruff format --check plugins/ mycelium_onboarding/ tests/; then
    echo -e "${GREEN}✓ Ruff format passed${NC}"
else
    echo -e "${RED}✗ Ruff format failed${NC}"
    FAILED=1
fi
echo ""

# 3. Mypy Type Check
echo "Step 3: Mypy Type Check"
echo "Command: uv run mypy plugins/ mycelium_onboarding/"
if uv run mypy plugins/ mycelium_onboarding/; then
    echo -e "${GREEN}✓ Mypy passed${NC}"
else
    echo -e "${RED}✗ Mypy failed${NC}"
    FAILED=1
fi
echo ""

# 4. Unit Tests
echo "Step 4: Unit Tests"
echo "Command: uv run pytest tests/unit/ tests/test_*.py -v -m 'not integration and not benchmark and not slow'"
if uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    FAILED=1
fi
echo ""

# Summary
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All CI checks passed! ✓${NC}"
    echo "Safe to push to GitHub"
    exit 0
else
    echo -e "${RED}Some CI checks failed ✗${NC}"
    echo "Fix errors before pushing"
    exit 1
fi
EOF

chmod +x /home/gerald/git/mycelium/scripts/validate_ci.sh
```

### Task 4: Create Baseline Report

Document the current state:

```bash
cat > /home/gerald/git/mycelium/CI_BASELINE_REPORT.md << 'EOF'
# CI Baseline Report - Phase 1

**Generated**: $(date)
**Branch**: feat/phase2-smart-onboarding-unified
**Python Version**: $(python --version)
**UV Version**: $(uv --version)

## Ruff Errors Detected

### Error Statistics
```

$(cat ruff_stats.txt)

```

### Error Distribution by Type
```

$(grep -E "B904|F821|E402|SIM102|F841|ARG001" ruff_errors.txt | cut -d: -f4 | sort | uniq -c | sort -rn)

```

### Files with Errors
```

$(grep -oP '^\[^:\]+' ruff_errors.txt | sort | uniq -c | sort -rn)

```

## Mypy Errors Detected

```

$(cat mypy_errors.txt)

````

## Current Test Status

**Unit Tests**:
- Command: `uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short`
- Expected: 585+ passed, 42 skipped, 0 failed

**Integration Tests** (May fail due to imports):
- Will be addressed in Phase 6

## Next Steps

1. Phase 2: Fix B904 errors (exception chaining)
2. Phase 3: Fix F821 errors (undefined names)
3. Phase 4: Fix E402 errors (import order)
4. Phase 5: Fix SIM102/F841/ARG001 errors
5. Phase 6: Fix integration test imports
6. Phase 7: Comprehensive validation
7. Phase 8: Commit and push

## Validation Script

Created: `/home/gerald/git/mycelium/scripts/validate_ci.sh`

Run before pushing:
```bash
./scripts/validate_ci.sh
````

EOF

```

## Expected Errors

You should see approximately:

### B904 Errors (Exception Chaining)
- mycelium_onboarding/cli.py:1352
- mycelium_onboarding/cli.py:1394
- mycelium_onboarding/cli.py:1432
- mycelium_onboarding/cli.py:1599
- mycelium_onboarding/cli.py:1643
- mycelium_onboarding/cli_commands/commands/config.py:493
- Additional locations

### F821 Errors (Undefined Names)
- mycelium_onboarding/cli.py:1492 - `DeploymentMethod`
- mycelium_onboarding/cli.py:1533 - `DeploymentMethod`
- mycelium_onboarding/cli.py:1563 - `watch`

### E402 Errors (Import Order)
- mycelium_onboarding/cli.py:1921-1935 - Imports not at top

### SIM102 Errors (Nested Ifs)
- mycelium_onboarding/cli_commands/commands/config_migrate.py:81
- mycelium_onboarding/cli_commands/commands/config_migrate.py:289

### F841 Error (Unused Variable)
- mycelium_onboarding/cli_commands/commands/config_migrate.py:275

### ARG001 Error (Unused Argument)
- mycelium_onboarding/cli_commands/commands/config_migrate.py:304

## Success Criteria

- [ ] Ran all GitHub CI commands locally
- [ ] Captured 65+ ruff errors in ruff_errors.txt
- [ ] Created error statistics in ruff_stats.txt
- [ ] Generated JSON error output in ruff_errors.json
- [ ] Created validation script at scripts/validate_ci.sh
- [ ] Generated CI_BASELINE_REPORT.md with complete error list
- [ ] Confirmed error count matches GitHub CI (~65+ errors)

## Deliverables

1. **ruff_errors.txt** - Full ruff error output
2. **ruff_errors.json** - Structured error data
3. **ruff_stats.txt** - Error statistics
4. **ruff_format.txt** - Format check results
5. **mypy_errors.txt** - Type check errors
6. **scripts/validate_ci.sh** - CI validation script
7. **CI_BASELINE_REPORT.md** - Comprehensive baseline report

## Handoff to Next Phase

Once complete, report back to multi-agent-coordinator with:

```

\[DEVOPS-ENGINEER\] Phase 1 Complete

- Total ruff errors detected: \[NUMBER\]
- Error types: B904: \[N\], F821: \[N\], E402: \[N\], SIM102: \[N\], F841: \[N\], ARG001: \[N\]
- Validation script created: YES
- Baseline report created: YES
- Status: READY FOR PHASE 2

```

Then the coordinator will dispatch python-pro for Phase 2 (B904 fixes).

## Questions?

Contact: multi-agent-coordinator
Reference: /home/gerald/git/mycelium/COORDINATION_PLAN_PR15.md

## Time Checkpoint

Start time: ___________
End time: ___________
Duration: ___________ (target: 15 minutes)
```
