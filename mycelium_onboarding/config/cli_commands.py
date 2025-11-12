"""Additional CLI commands for configuration scope management.

This module provides CLI commands for managing configuration scope,
migration between global and project-local configurations, and
configuration discovery.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.migration_util import (
    detect_migration_candidates,
    migrate_to_global,
    migrate_to_project,
    preview_migration,
)
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config.scope import (
    ConfigScope,
    get_active_scope,
    get_config_location,
    list_all_configs,
)
from mycelium_onboarding.xdg_dirs import get_config_dir

logger = logging.getLogger(__name__)
console = Console()

__all__ = [
    "where",
    "list_configs",
    "migrate_config",
    "reset_config",
]


@click.command()
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed information about configuration location",
)
def where(verbose: bool) -> None:
    """Show which configuration file is being used.

    Displays the active configuration file location and scope.

    Examples:
        mycelium config where
        mycelium config where --verbose
    """
    try:
        location = get_config_location()
        active_scope = get_active_scope()

        # Create table for display
        table = Table(title="Configuration Location", show_header=True)
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        # Add basic information
        table.add_row("Active Scope", active_scope.value.upper())

        if location.path:
            table.add_row("Config File", str(location.path))
            exists_status = "[green]Yes[/green]" if location.exists else "[red]No[/red]"
            table.add_row("Exists", exists_status)

            if location.exists:
                writable_status = "[green]Yes[/green]" if location.writable else "[red]No[/red]"
                table.add_row("Writable", writable_status)

                # File stats
                stats = location.path.stat()
                from datetime import datetime

                modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                table.add_row("Modified", modified)
                table.add_row("Size", f"{stats.st_size} bytes")
        else:
            table.add_row("Config File", "[yellow]Using defaults (no file)[/yellow]")

        console.print(table)

        # Show verbose information
        if verbose:
            console.print("\n[bold]All Configuration Locations:[/bold]")
            all_configs = list_all_configs()

            for config in all_configs:
                scope_color = "green" if config.scope == active_scope else "dim"
                status = "EXISTS" if config.exists else "not found"
                writable = ", writable" if config.writable else ", read-only"

                console.print(
                    f"  [{scope_color}]{config.scope.value.upper()}[/{scope_color}]: "
                    f"{config.path} ([yellow]{status}[/yellow]{writable if config.exists else ''})"
                )

            # Show environment variables
            console.print("\n[bold]Environment Variables:[/bold]")
            env_vars = {
                "MYCELIUM_PROJECT_DIR": os.environ.get("MYCELIUM_PROJECT_DIR", "[dim]not set[/dim]"),
                "MYCELIUM_USE_PROJECT_CONFIG": os.environ.get("MYCELIUM_USE_PROJECT_CONFIG", "[dim]not set[/dim]"),
            }

            for var, value in env_vars.items():
                console.print(f"  {var}: {value}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", style="bold")
        logger.exception("Failed to determine configuration location")
        sys.exit(1)


@click.command(name="list")
@click.option(
    "--format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
def list_configs(format: str) -> None:
    """List all configuration files found.

    Shows all potential configuration file locations and their status.

    Examples:
        mycelium config list
        mycelium config list --format json
    """
    try:
        configs = list_all_configs()

        if format == "json":
            import json

            output = [
                {
                    "scope": config.scope.value,
                    "path": str(config.path) if config.path else None,
                    "exists": config.exists,
                    "writable": config.writable,
                }
                for config in configs
            ]
            console.print(json.dumps(output, indent=2))
        else:
            # Table format
            table = Table(title="Configuration Files", show_header=True)
            table.add_column("Scope", style="cyan")
            table.add_column("Path", style="white")
            table.add_column("Status", justify="center")
            table.add_column("Access", justify="center")

            for config in configs:
                status = "[green]✓ Exists[/green]" if config.exists else "[dim]✗ Not found[/dim]"
                access = ""
                if config.exists:
                    access = "[green]✓ Writable[/green]" if config.writable else "[yellow]⚠ Read-only[/yellow]"

                table.add_row(
                    config.scope.value.upper(),
                    str(config.path) if config.path else "[dim]N/A[/dim]",
                    status,
                    access,
                )

            console.print(table)

            # Show active configuration
            active_scope = get_active_scope()
            console.print(f"\n[bold]Active:[/bold] [cyan]{active_scope.value.upper()}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", style="bold")
        logger.exception("Failed to list configurations")
        sys.exit(1)


@click.command(name="migrate")
@click.option(
    "--to",
    "destination",
    type=click.Choice(["global", "project"], case_sensitive=False),
    default="global",
    help="Destination scope (default: global)",
)
@click.option(
    "--merge",
    is_flag=True,
    help="Merge with existing configuration instead of replacing",
)
@click.option(
    "--remove-source",
    is_flag=True,
    help="Remove source configuration after migration",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview migration without applying changes",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project directory (required for --to project)",
)
def migrate_config(
    destination: str,
    merge: bool,
    remove_source: bool,
    dry_run: bool,
    project_dir: Path | None,
) -> None:
    """Migrate configuration between scopes.

    Migrates configuration files between global and project-local scopes.
    Optionally merges with existing configurations and removes the source.

    Examples:
        mycelium config migrate --to global
        mycelium config migrate --to global --merge --remove-source
        mycelium config migrate --to project --project-dir /path/to/project
        mycelium config migrate --dry-run
    """
    try:
        if destination == "project" and not project_dir:
            console.print("[red]Error: --project-dir required when migrating to project scope[/red]")
            sys.exit(1)

        # Detect migration candidates
        candidates = detect_migration_candidates()

        if destination == "global":
            if not candidates:
                console.print("[yellow]No project-local configurations found to migrate[/yellow]")
                sys.exit(0)

            # Show what will be migrated
            console.print("[bold cyan]Migrating to global scope...[/bold cyan]")
            console.print(f"Source: {candidates[0].path}")
            console.print(f"Destination: {get_config_dir() / 'config.yaml'}")

            if merge:
                console.print("Mode: [yellow]Merge[/yellow] (combine with existing)")
            else:
                console.print("Mode: [yellow]Replace[/yellow] (overwrite existing)")

            console.print()

            if dry_run:
                console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
                if candidates[0].path:
                    action = preview_migration(candidates[0].path, ConfigScope.GLOBAL, merge=merge)
                    console.print(f"Would migrate: {action.source} -> {action.destination}")
                    if action.will_merge:
                        console.print("  Configurations would be merged")
                    if action.backup_path:
                        console.print(f"  Backup would be created: {action.backup_path}")
                return

            # Confirm migration
            if not click.confirm("Proceed with migration?", default=True):
                console.print("Migration cancelled")
                return

            # Perform migration
            with console.status("[bold green]Migrating configuration..."):
                result = migrate_to_global(
                    merge=merge,
                    create_backup=True,
                    remove_source=remove_source,
                )

            if result.success:
                console.print("\n[green]✓ Successfully migrated to global scope[/green]")
                console.print(f"  Source: {result.source}")
                console.print(f"  Destination: {result.destination}")

                if result.backup_created:
                    console.print(f"  Backup: {result.backup_created}")

                if result.merged:
                    console.print("  [yellow]Configurations were merged[/yellow]")

                if remove_source:
                    console.print("  [yellow]Source configuration removed[/yellow]")
            else:
                console.print(f"\n[red]✗ Migration failed: {result.error}[/red]")
                sys.exit(1)

        else:  # destination == "project"
            if not project_dir:
                console.print("[red]Error: Project directory required[/red]")
                sys.exit(1)

            console.print("[bold cyan]Migrating to project scope...[/bold cyan]")
            console.print(f"Source: {get_config_dir() / 'config.yaml'}")
            console.print(f"Destination: {project_dir / 'config.yaml'}")

            if merge:
                console.print("Mode: [yellow]Merge[/yellow] (combine with existing)")
            else:
                console.print("Mode: [yellow]Replace[/yellow] (overwrite existing)")

            console.print()

            if dry_run:
                console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
                console.print(f"Would create: {project_dir / 'config.yaml'}")
                return

            # Confirm migration
            if not click.confirm("Proceed with migration?", default=True):
                console.print("Migration cancelled")
                return

            # Perform migration
            with console.status("[bold green]Migrating configuration..."):
                result = migrate_to_project(
                    project_dir=project_dir,
                    merge=merge,
                    create_backup=True,
                )

            if result.success:
                console.print("\n[green]✓ Successfully migrated to project scope[/green]")
                console.print(f"  Destination: {result.destination}")

                if result.backup_created:
                    console.print(f"  Backup: {result.backup_created}")

                if result.merged:
                    console.print("  [yellow]Configurations were merged[/yellow]")
            else:
                console.print(f"\n[red]✗ Migration failed: {result.error}[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]", style="bold")
        logger.exception("Migration failed")
        sys.exit(1)


@click.command(name="reset")
@click.option(
    "--scope",
    type=click.Choice(["global", "project", "all"], case_sensitive=False),
    default="global",
    help="Configuration scope to reset (default: global)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reset_config(scope: str, force: bool) -> None:
    """Reset configuration to defaults.

    Removes existing configuration file(s) and creates fresh default
    configuration. Use with caution as this cannot be undone.

    Examples:
        mycelium config reset
        mycelium config reset --scope all --force
        mycelium config reset --scope project
    """
    try:
        configs_to_reset = []

        if scope in ("global", "all"):
            global_config = get_config_dir() / "config.yaml"
            if global_config.exists():
                configs_to_reset.append(("Global", global_config))

        if scope in ("project", "all"):
            project_configs = detect_migration_candidates()
            for config in project_configs:
                if config.path:
                    configs_to_reset.append(("Project", config.path))

        if not configs_to_reset:
            console.print("[yellow]No configuration files found to reset[/yellow]")
            return

        # Show what will be reset
        console.print("[bold yellow]The following configurations will be reset:[/bold yellow]\n")
        for scope_name, path in configs_to_reset:
            console.print(f"  [{scope_name}] {path}")

        console.print("\n[bold red]WARNING: This action cannot be undone![/bold red]")
        console.print("All settings will be lost and replaced with defaults.\n")

        # Confirm reset
        if not force and not click.confirm("Are you sure you want to reset these configurations?", default=False):
            console.print("Reset cancelled")
            return

        # Perform reset
        for scope_name, path in configs_to_reset:
            try:
                # Create backup before reset
                backup_path = path.with_suffix(".yaml.bak")
                import shutil

                shutil.copy2(path, backup_path)

                # Remove existing config
                path.unlink()

                # Create default config
                default_config = MyceliumConfig()
                manager = ConfigManager(config_path=path)
                path.parent.mkdir(parents=True, exist_ok=True)
                manager.save(default_config)

                console.print(f"[green]✓[/green] Reset [{scope_name}] {path}")
                console.print(f"    Backup created: {backup_path}")

            except Exception as e:
                console.print(f"[red]✗[/red] Failed to reset [{scope_name}] {path}: {e}")

        console.print("\n[green]Configuration reset complete[/green]")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]", style="bold")
        logger.exception("Reset failed")
        sys.exit(1)
