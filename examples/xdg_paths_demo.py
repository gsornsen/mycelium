#!/usr/bin/env python3
"""Demo script for XDG-compliant path resolution and migration utilities.

This script demonstrates the new Sprint 2 Task B1 & B2 functionality:
- Cross-platform XDG-compliant path resolution
- Safe file migration utilities
- Atomic operations with backups

Usage:
    python examples/xdg_paths_demo.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from mycelium_onboarding.config import (
    Platform,
    get_cache_dir,
    get_data_dir,
    get_global_config_path,
    get_log_dir,
    get_platform,
    get_project_config_path,
    get_state_dir,
)
from mycelium_onboarding.config.path_utils import (
    atomic_move,
    find_legacy_configs,
    safe_read_yaml,
    safe_write_yaml,
)


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_platform_detection() -> None:
    """Demonstrate platform detection."""
    print_header("Platform Detection")

    platform = get_platform()
    print(f"Detected Platform: {platform.value.upper()}")

    if platform == Platform.LINUX:
        print("Running on Linux - Using XDG Base Directory Specification")
    elif platform == Platform.MACOS:
        print("Running on macOS - Using ~/Library paths")
    elif platform == Platform.WINDOWS:
        print("Running on Windows - Using AppData paths")
    else:
        print("Unknown platform detected")


def demo_xdg_paths() -> None:
    """Demonstrate XDG-compliant path resolution."""
    print_header("XDG-Compliant Path Resolution")

    print("Global Configuration:")
    print(f"  {get_global_config_path()}")

    print("\nProject Configuration (current directory):")
    print(f"  {get_project_config_path()}")

    print("\nData Directory:")
    print(f"  {get_data_dir()}")

    print("\nState Directory:")
    print(f"  {get_state_dir()}")

    print("\nCache Directory:")
    print(f"  {get_cache_dir()}")

    print("\nLog Directory:")
    print(f"  {get_log_dir()}")


def demo_yaml_operations() -> None:
    """Demonstrate safe YAML operations."""
    print_header("Safe YAML Operations")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        # Write YAML
        config_data = {
            "project_name": "demo-project",
            "schema_version": "1.0.0",
            "services": {
                "redis": {"port": 6379, "enabled": True},
                "postgres": {"port": 5432, "database": "mycelium"},
            },
        }

        print("Writing configuration to YAML...")
        safe_write_yaml(config_path, config_data, backup=False)
        print(f"  Created: {config_path}")

        # Read YAML
        print("\nReading configuration from YAML...")
        read_data = safe_read_yaml(config_path)
        print(f"  Project Name: {read_data['project_name']}")
        print(f"  Redis Port: {read_data['services']['redis']['port']}")
        print(f"  Postgres DB: {read_data['services']['postgres']['database']}")

        # Verify roundtrip
        assert read_data == config_data
        print("\n  Data integrity verified!")


def demo_migration_workflow() -> None:
    """Demonstrate configuration migration workflow."""
    print_header("Configuration Migration Workflow")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create legacy config
        legacy_dir = tmpdir / "legacy"
        legacy_dir.mkdir()
        legacy_config = legacy_dir / "mycelium-config.yaml"

        legacy_data = {
            "project_name": "legacy-project",
            "services": {"redis": {"port": 6379}},
        }

        print("Creating legacy configuration...")
        safe_write_yaml(legacy_config, legacy_data, backup=False)
        print(f"  Legacy config: {legacy_config}")

        # Find legacy configs
        print("\nSearching for legacy configurations...")
        found = find_legacy_configs([legacy_dir])
        print(f"  Found {len(found)} legacy config(s)")

        # Migrate to new location
        print("\nMigrating to new location...")
        new_config = tmpdir / "new" / "config.yaml"
        new_config.parent.mkdir(parents=True)

        atomic_move(legacy_config, new_config, backup=False)
        print(f"  Migrated to: {new_config}")

        # Verify migration
        print("\nVerifying migration...")
        migrated_data = safe_read_yaml(new_config)
        assert migrated_data == legacy_data
        assert not legacy_config.exists()
        print("  Migration successful!")
        print(f"  Legacy config removed: {not legacy_config.exists()}")
        print(f"  New config exists: {new_config.exists()}")


def demo_atomic_operations() -> None:
    """Demonstrate atomic file operations with backups."""
    print_header("Atomic Operations with Backups")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create original config
        config_path = tmpdir / "config.yaml"
        original_data = {"version": 1, "name": "original"}
        safe_write_yaml(config_path, original_data, backup=False)
        print(f"Created config: {config_path}")
        print(f"  Version: {original_data['version']}")

        # Update with backup
        print("\nUpdating config with backup enabled...")
        updated_data = {"version": 2, "name": "updated"}
        safe_write_yaml(config_path, updated_data, backup=True)
        print(f"  New version: {updated_data['version']}")
        print("  Backup created automatically")

        # Verify update
        current_data = safe_read_yaml(config_path)
        assert current_data == updated_data
        print("\n  Update successful!")


def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  XDG-Compliant Path Resolution & Migration Utilities Demo")
    print("  Sprint 2: Global Configuration Migration - Tasks B1 & B2")
    print("=" * 70)

    demo_platform_detection()
    demo_xdg_paths()
    demo_yaml_operations()
    demo_migration_workflow()
    demo_atomic_operations()

    print_header("Demo Complete")
    print("All functionality demonstrated successfully!")
    print("\nFor more information, see:")
    print("  - mycelium_onboarding/config/platform.py")
    print("  - mycelium_onboarding/config/paths.py")
    print("  - mycelium_onboarding/config/path_utils.py")
    print("")


if __name__ == "__main__":
    main()
