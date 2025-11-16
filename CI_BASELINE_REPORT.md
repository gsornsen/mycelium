# CI Baseline Report - Phase 1

**Generated**: $(date) **Branch**: feat/phase2-smart-onboarding-unified **Python Version**: $(uv run python --version)
**UV Version**: $(uv --version)

## Ruff Errors Detected

### Error Statistics

Total: 116 errors detected

Key error types to fix:

- **B904**: 7 (raise-without-from-inside-except) ← Phase 2
- **F821**: 3 (undefined-name) ← Phase 3
- **E402**: 5 (module-import-not-at-top-of-file) ← Phase 4
- **SIM102**: 6 (collapsible-if) ← Phase 5
- **F841**: 31 (unused-variable) ← Phase 5
- **ARG001**: 1 (unused-function-argument) ← Phase 5

Other errors (non-critical):

- ARG002: 22 (unused-method-argument)
- W293: 14 (blank-line-with-whitespace) - fixable
- D301: 7 (escape-sequence-in-docstring)
- SIM117: 5 (multiple-with-statements)
- PTH123: 4 (builtin-open)
- SIM108: 3 (if-else-block-instead-of-if-exp)
- F401: 2 (unused-import)
- SIM105: 2 (suppressible-exception)
- B007: 1 (unused-loop-control-variable)
- E501: 1 (line-too-long)
- I001: 1 (unsorted-imports) - fixable
- RET504: 1 (unnecessary-assign)

## Mypy Errors Detected

Total: 29 errors (non-blocking, consistent with Phase 3A baseline)

## Current Test Status

**Unit Tests**:

- Command: `uv run pytest tests/unit/ tests/test_*.py -v -m "not integration and not benchmark and not slow" --tb=short`
- Expected: 585+ passed, 42 skipped, 0 failed ✅

**Integration Tests** (May fail due to imports):

- Will be addressed in Phase 6

## Priority Fixes

### Phase 2: B904 Errors (7 locations)

Critical: Missing exception chaining

### Phase 3: F821 Errors (3 locations)

Critical: Undefined names (DeploymentMethod, watch)

### Phase 4: E402 Errors (5 locations)

Critical: Imports not at top of file

### Phase 5: SIM102/F841/ARG001 Errors

Medium priority: Code quality improvements

## Next Steps

1. ✅ Phase 1 complete: Environment configured
1. → Phase 2: Fix B904 errors (exception chaining)
1. → Phase 3: Fix F821 errors (undefined names)
1. → Phase 4: Fix E402 errors (import order)
1. → Phase 5: Fix SIM102/F841/ARG001 errors
1. → Phase 6: Fix integration test imports
1. → Phase 7: Comprehensive validation
1. → Phase 8: Commit and push

## Validation Script

Created: `/home/gerald/git/mycelium/scripts/validate_ci.sh`

Run before pushing:

```bash
./scripts/validate_ci.sh
```

## Phase 1 Complete ✅

- [x] Ran all GitHub CI commands locally
- [x] Captured 116 ruff errors
- [x] Captured 29 mypy errors
- [x] Created validation script
- [x] Generated baseline report

**Status**: READY FOR PHASE 2
