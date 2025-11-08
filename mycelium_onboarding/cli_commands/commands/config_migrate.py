"""Configuration migration CLI command.

This module provides the migration command for migrating legacy configuration
files to the new XDG-compliant structure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

# For now, we'll create placeholder implementations for the migration classes
# These should be implemented in Phase 1/C1/C2 tasks
from mycelium_onboarding.config.paths import (
    ensure_migration_backup_dir_exists,
    get_global_config_path,
)

console = Console()


@click.command(name="migrate")
@click.option("--dry-run", is_flag=True, help="Simulate migration without changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--backup-dir", type=click.Path(path_type=Path), help="Custom backup directory")
def migrate_command(dry_run: bool, yes: bool, backup_dir: Path | None):
    """Migrate configuration to XDG-compliant locations.

    Migrates legacy mycelium-config.yaml files to new structure:
    - Global: ~/.config/mycelium/config.yaml
    - Project: .mycelium/config.yaml

    Creates backup before migration and supports rollback.

    Examples:
        mycelium config migrate                # Interactive migration
        mycelium config migrate --dry-run      # Simulate without changes
        mycelium config migrate --yes          # Skip confirmation
    """
    try:
        # Import migration utilities (these should be created in Phase 1)
        # For now, we'll provide a basic implementation
        from mycelium_onboarding.config.migration_util import (
            detect_migration_candidates,
        )

        console.print("[bold]Scanning for legacy configuration...[/bold]")

        # Detect legacy configs
        try:
            legacy_configs = detect_migration_candidates()
        except Exception:
            # Fallback to manual detection if migration_util not available
            legacy_configs = _detect_legacy_configs_fallback()

        if not legacy_configs:
            console.print("[green]✓ No migration needed - already using new config structure[/green]")
            return

        # Show migration summary
        console.print(f"\nFound {len(legacy_configs)} legacy config file(s):")
        for config in legacy_configs:
            if hasattr(config, "path"):
                console.print(f"  • {config.path}")
            else:
                console.print(f"  • {config}")

        # Create migration plan
        migration_steps = _create_migration_plan(legacy_configs)

        console.print(f"\nMigration plan ({len(migration_steps)} steps):")
        for i, step in enumerate(migration_steps, 1):
            console.print(f"  {i}. {step['description']}")

        # Confirm (unless --yes or --dry-run)
        if not yes and not dry_run:
            if not Confirm.ask("\nProceed with migration?"):
                console.print("[yellow]Migration cancelled[/yellow]")
                return

        # Determine backup directory
        if backup_dir is None:
            backup_dir = ensure_migration_backup_dir_exists()
        else:
            backup_dir.mkdir(parents=True, exist_ok=True)

        # Execute migration
        if dry_run:
            console.print("\n[bold yellow]DRY RUN MODE[/bold yellow] - No changes will be made\n")
            _simulate_migration(migration_steps)
            console.print("\n[green]✓ Dry-run successful - no changes made[/green]")
        else:
            success, errors = _execute_migration(migration_steps, backup_dir)

            if success:
                console.print("\n[green]✓ Migration completed successfully[/green]")
                console.print(f"  Backup saved to: {backup_dir}")
            else:
                console.print("\n[red]✗ Migration failed[/red]")
                for error in errors:
                    console.print(f"  • {error}")
                console.print(f"\n[yellow]To rollback, run: mycelium config rollback {backup_dir}[/yellow]")
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Migration cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


def _detect_legacy_configs_fallback() -> list[Path]:
    """Fallback implementation to detect legacy config files.

    Looks for common legacy config locations:
    - ./mycelium-config.yaml (project root)
    - ~/.mycelium-config.yaml (home directory)
    - $MYCELIUM_ROOT/mycelium-config.yaml
    """
    import os

    legacy_configs = []

    # Check project root
    project_legacy = Path.cwd() / "mycelium-config.yaml"
    if project_legacy.exists():
        legacy_configs.append(project_legacy)

    # Check home directory
    home_legacy = Path.home() / ".mycelium-config.yaml"
    if home_legacy.exists():
        legacy_configs.append(home_legacy)

    # Check MYCELIUM_ROOT
    mycelium_root = os.environ.get("MYCELIUM_ROOT")
    if mycelium_root:
        root_legacy = Path(mycelium_root) / "mycelium-config.yaml"
        if root_legacy.exists() and root_legacy not in legacy_configs:
            legacy_configs.append(root_legacy)

    return legacy_configs


def _create_migration_plan(legacy_configs: list) -> list[dict]:
    """Create a migration plan from legacy configs."""
    steps = []

    for config in legacy_configs:
        if hasattr(config, "path"):
            config_path = config.path
        else:
            config_path = config

        # Determine destination based on location
        if _is_in_home_directory(config_path):
            dest_path = get_global_config_path()
            scope = "global"
        else:
            # Project-level config
            from mycelium_onboarding.config.paths import get_project_config_path

            dest_path = get_project_config_path()
            scope = "project"

        steps.append(
            {
                "description": f"Migrate {config_path} to {scope} config ({dest_path})",
                "source": config_path,
                "destination": dest_path,
                "scope": scope,
            }
        )

    return steps


def _is_in_home_directory(path: Path) -> bool:
    """Check if a path is in the user's home directory."""
    try:
        path.relative_to(Path.home())
        return True
    except ValueError:
        return False


def _simulate_migration(steps: list[dict]) -> None:
    """Simulate migration without making changes."""
    console.print("[bold]Migration Steps:[/bold]\n")

    for i, step in enumerate(steps, 1):
        console.print(f"[cyan]Step {i}:[/cyan] {step['description']}")
        console.print(f"  Source: {step['source']}")
        console.print(f"  Destination: {step['destination']}")
        console.print(f"  Scope: {step['scope']}")
        console.print()


def _execute_migration(steps: list[dict], backup_dir: Path) -> tuple[bool, list[str]]:
    """Execute migration steps with progress tracking."""
    import shutil
    from datetime import datetime

    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Migrating configuration...", total=len(steps))

        for i, step in enumerate(steps, 1):
            try:
                source_path = step["source"]
                dest_path = step["destination"]

                # Update progress
                progress.update(task, completed=i, description=f"Migrating {source_path.name}...")

                # Create backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"{source_path.name}.backup.{timestamp}"
                shutil.copy2(source_path, backup_file)

                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy to new location
                shutil.copy2(source_path, dest_path)

                # Optionally remove source (commented out for safety)
                # source_path.unlink()

            except Exception as e:
                errors.append(f"Failed to migrate {source_path}: {e}")

        progress.update(task, completed=len(steps), description="Migration complete")

    return len(errors) == 0, errors


# Alternative implementation using Phase 1 migration classes (if available)
def migrate_command_with_phase1_classes(dry_run: bool, yes: bool, backup_dir: Path | None):
    """Migration command using Phase 1 MigrationDetector/Planner/Executor classes.

    This is the ideal implementation that should be used once Phase 1 classes are available.
    """
    try:
        # Import Phase 1 migration classes
        from mycelium_onboarding.config.migration import (
            MigrationDetector,
            MigrationExecutor,
            MigrationPlanner,
        )

        # Step 1: Detect legacy configs
        console.print("[bold]Scanning for legacy configuration...[/bold]")
        detector = MigrationDetector()
        legacy_configs = detector.scan_for_legacy_configs()

        if not detector.needs_migration():
            console.print("[green]✓ No migration needed - already using new config structure[/green]")
            return

        # Step 2: Show migration summary
        summary = detector.get_migration_summary()
        console.print(f"\nFound {len(legacy_configs)} legacy config file(s):")
        for config in legacy_configs:
            console.print(f"  • {config.path}")

        # Step 3: Create migration plan
        planner = MigrationPlanner()
        steps = planner.create_plan(legacy_configs)

        console.print(f"\nMigration plan ({len(steps)} steps):")
        for i, step in enumerate(steps, 1):
            console.print(f"  {i}. {step.description}")

        # Step 4: Confirm (unless --yes)
        if not yes and not dry_run:
            if not Confirm.ask("\nProceed with migration?"):
                console.print("[yellow]Migration cancelled[/yellow]")
                return

        # Step 5: Execute migration
        executor = MigrationExecutor(dry_run=dry_run, backup_dir=backup_dir)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Migrating configuration...", total=len(steps))

            def progress_callback(current, total, message):
                progress.update(task, completed=current, description=message)

            result = executor.execute(steps, progress_callback=progress_callback)

        # Step 6: Report results
        if result.success:
            if dry_run:
                console.print("\n[green]✓ Dry-run successful - no changes made[/green]")
            else:
                console.print("\n[green]✓ Migration completed successfully[/green]")
                console.print(f"  Backup saved to: {result.backup_dir}")
        else:
            console.print("\n[red]✗ Migration failed[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
            if result.backup_dir:
                console.print(f"\n[yellow]To rollback, run: mycelium config rollback {result.backup_dir}[/yellow]")
            sys.exit(1)

    except ImportError:
        console.print("[yellow]Migration classes not yet implemented, using fallback implementation[/yellow]")
        migrate_command(dry_run, yes, backup_dir)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)
