# Configuration Migration - Quick Reference

## Basic Usage

```python
from mycelium_onboarding.config.migration import (
    MigrationDetector,
    MigrationPlanner,
    MigrationExecutor,
)

# 1. Detect
detector = MigrationDetector()
configs = detector.scan_for_legacy_configs()

# 2. Plan
planner = MigrationPlanner()
plan = planner.create_plan(configs)

# 3. Execute
executor = MigrationExecutor(dry_run=False)
result = executor.execute(plan)
```

## Key Classes

### MigrationDetector

- `scan_for_legacy_configs()` - Find legacy configs
- `needs_migration()` - Check if migration needed
- `get_migration_summary()` - Get statistics
- `validate_migration_feasibility()` - Check for issues

### MigrationPlanner

- `create_plan(configs)` - Generate migration plan
- `validate_plan(plan)` - Verify plan safety
- `estimate_time(plan)` - Estimate duration
- `get_plan_summary(plan)` - Get plan stats

### MigrationExecutor

- `execute(plan, callback)` - Run migration
- `rollback(backup_dir)` - Restore from backup

## Migration Actions

- **MOVE** - Move file to new location
- **COPY** - Copy file (preserve original)
- **MERGE** - Merge with existing config
- **CREATE** - Create new config
- **SKIP** - Skip (already migrated)
- **BACKUP** - Create backup

## Safety Features

- Full backup before changes
- Atomic operations
- Rollback capability
- Dry-run mode
- Progress reporting
- Comprehensive validation

## File Locations

**Module:** `/home/gerald/git/mycelium/mycelium_onboarding/config/migration/` **Tests:**
`/home/gerald/git/mycelium/tests/unit/config/migration/` **Examples:**
`/home/gerald/git/mycelium/examples/migration_example.py`

## Test Results

```
66 tests, 100% passing
- Detector: 20 tests
- Planner: 20 tests
- Executor: 19 tests
- Integration: 7 tests
```

## Branch

`feat/smart-onboarding-sprint2-global-config`
