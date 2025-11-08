#!/usr/bin/env python3
"""Example script demonstrating the configuration migration system.

This script shows how to use the migration system to safely migrate
legacy configuration files to the new XDG-compliant structure.

Usage:
    python examples/migration_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mycelium_onboarding.config.migration import (
    MigrationDetector,
    MigrationExecutor,
    MigrationPlanner,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def demo_basic_migration() -> None:
    """Demonstrate basic migration workflow."""
    print_section("Basic Migration Workflow")

    # Step 1: Detect legacy configurations
    print("Step 1: Detecting legacy configurations...")
    detector = MigrationDetector()

    if not detector.needs_migration():
        print("  No legacy configurations found.")
        return

    legacy_configs = detector.scan_for_legacy_configs()
    print(f"  Found {len(legacy_configs)} legacy configuration(s):")
    for config in legacy_configs:
        print(f"    - {config}")

    # Step 2: Get migration summary
    print("\nStep 2: Getting migration summary...")
    summary = detector.get_migration_summary()
    print(f"  Total configs: {summary['total_configs']}")
    print(f"  Total size: {summary['total_size_bytes']} bytes")
    print(f"  Readable configs: {summary['readable_configs']}")
    print(f"  Conflicting configs: {summary['conflicting_configs']}")

    # Step 3: Validate migration feasibility
    print("\nStep 3: Validating migration feasibility...")
    errors = detector.validate_migration_feasibility()
    if errors:
        print("  ERRORS FOUND:")
        for error in errors:
            print(f"    - {error}")
        return
    print("  Validation passed - migration is feasible.")

    # Step 4: Create migration plan
    print("\nStep 4: Creating migration plan...")
    planner = MigrationPlanner()
    plan = planner.create_plan(
        legacy_configs,
        create_global=True,
        backup_all=True,
    )
    print(f"  Created plan with {len(plan)} steps:")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step.description}")

    # Step 5: Validate plan
    print("\nStep 5: Validating migration plan...")
    if not planner.validate_plan(plan):
        print("  Plan validation FAILED.")
        return
    print("  Plan validation passed.")

    # Step 6: Get plan summary
    print("\nStep 6: Plan summary...")
    plan_summary = planner.get_plan_summary(plan)
    print(f"  Total steps: {plan_summary['total']}")
    print(f"  Move operations: {plan_summary['move']}")
    print(f"  Backup operations: {plan_summary['backup']}")
    print(f"  Create operations: {plan_summary['create']}")

    # Step 7: Estimate migration time
    estimated_time = planner.estimate_time(plan)
    print(f"\nStep 7: Estimated migration time: {estimated_time:.2f} seconds")

    # Step 8: Execute dry run
    print("\nStep 8: Executing DRY RUN migration...")
    dry_executor = MigrationExecutor(dry_run=True)

    def progress_callback(current: int, total: int, message: str) -> None:
        """Print progress updates."""
        print(f"  [{current}/{total}] {message}")

    dry_result = dry_executor.execute(plan, progress_callback=progress_callback)

    print(f"\nDry run result: {dry_result}")
    if not dry_result.success:
        print("  DRY RUN FAILED. Errors:")
        for error in dry_result.errors:
            print(f"    - {error}")
        return

    # Step 9: Execute real migration
    print("\nStep 9: Executing REAL migration...")
    print("  (In a real scenario, you would prompt for confirmation here)")

    executor = MigrationExecutor(dry_run=False)
    result = executor.execute(plan, progress_callback=progress_callback)

    print(f"\nMigration result: {result}")

    if result.success:
        print("\nMIGRATION SUCCESSFUL!")
        print(f"  Completed {result.steps_completed}/{result.steps_total} steps")
        print(f"  Duration: {result.duration_seconds:.2f} seconds")
        if result.backup_dir:
            print(f"  Backup saved to: {result.backup_dir}")
    else:
        print("\nMIGRATION FAILED!")
        print("  Errors:")
        for error in result.errors:
            print(f"    - {error}")
        if result.backup_dir:
            print(f"\n  Backup available at: {result.backup_dir}")
            print("  You can rollback using:")
            print(f"    executor.rollback({result.backup_dir})")


def demo_advanced_features() -> None:
    """Demonstrate advanced migration features."""
    print_section("Advanced Migration Features")

    detector = MigrationDetector()

    if not detector.needs_migration():
        print("No legacy configurations to demonstrate with.")
        return

    # Get detailed summary
    summary = detector.get_migration_summary()
    print("Detailed Migration Summary:")
    print("  Configs by type:")
    for config_type, count in summary["configs_by_type"].items():
        print(f"    - {config_type}: {count}")
    print(f"  Has conflicts: {summary['has_conflicts']}")
    print(f"  All readable: {summary['all_readable']}")

    # Create custom plan
    planner = MigrationPlanner()
    legacy_configs = detector.scan_for_legacy_configs()

    # Create plan without global config creation
    print("\nCreating plan WITHOUT global config creation...")
    plan_no_global = planner.create_plan(
        legacy_configs,
        create_global=False,
        backup_all=True,
    )
    print(f"  Plan has {len(plan_no_global)} steps")

    # Create plan with global config creation
    print("\nCreating plan WITH global config creation...")
    plan_with_global = planner.create_plan(
        legacy_configs,
        create_global=True,
        backup_all=True,
    )
    print(f"  Plan has {len(plan_with_global)} steps")

    # Compare time estimates
    time_no_global = planner.estimate_time(plan_no_global)
    time_with_global = planner.estimate_time(plan_with_global)
    print(f"\n  Time estimate (no global): {time_no_global:.2f}s")
    print(f"  Time estimate (with global): {time_with_global:.2f}s")


def demo_error_handling() -> None:
    """Demonstrate error handling and validation."""
    print_section("Error Handling and Validation")

    detector = MigrationDetector()

    # Check for migration errors
    errors = detector.validate_migration_feasibility()

    if errors:
        print("Migration validation errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No migration validation errors found.")

    # Test plan validation
    if detector.needs_migration():
        planner = MigrationPlanner()
        legacy_configs = detector.scan_for_legacy_configs()
        plan = planner.create_plan(legacy_configs)

        if planner.validate_plan(plan):
            print("\nMigration plan is valid and safe to execute.")
        else:
            print("\nMigration plan validation FAILED.")


def main() -> None:
    """Run migration examples."""
    print("\nMycelium Configuration Migration System - Examples")
    print("=" * 60)

    try:
        # Run demonstrations
        demo_basic_migration()
        demo_advanced_features()
        demo_error_handling()

        print("\n" + "=" * 60)
        print("  Examples completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
