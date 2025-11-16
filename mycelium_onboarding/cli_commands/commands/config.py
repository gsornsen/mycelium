"""Configuration management CLI commands.

This module provides comprehensive CLI commands for managing Mycelium configuration,
including viewing, editing, and modifying configuration values across global and
project scopes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.table import Table

from mycelium_onboarding.config.loader import ConfigLoader, ConfigLoadError, ConfigValidationError
from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.paths import get_global_config_path, get_project_config_path
from mycelium_onboarding.config.schema import MyceliumConfig

console = Console()


@click.group(name="config")
def config_group() -> None:
    """Manage Mycelium configuration."""
    pass


@config_group.command(name="where")
@click.option("--global", "show_global", is_flag=True, help="Show global config path only")
@click.option("--project", "show_project", is_flag=True, help="Show project config path only")
def where_command(show_global: bool, show_project: bool) -> None:
    """Show configuration file locations.

    Displays the paths to global and project-local configuration files,
    along with their existence status and access permissions.

    Examples:
        mycelium config where                  # Show all paths
        mycelium config where --global         # Show global config only
        mycelium config where --project        # Show project config only
    """
    try:
        # Get configuration paths
        global_path = get_global_config_path()
        project_path = get_project_config_path()

        # If specific scope requested, show only that
        if show_global:
            _display_config_location("Global", global_path)
        elif show_project:
            _display_config_location("Project", project_path)
        else:
            # Show both
            console.print("[bold]Configuration File Locations:[/bold]\n")

            # Create table
            table = Table(show_header=True)
            table.add_column("Scope", style="cyan", no_wrap=True)
            table.add_column("Path", style="white")
            table.add_column("Status", justify="center")
            table.add_column("Access", justify="center")

            # Global config
            global_exists = global_path.exists()
            global_status = "[green]✓ Exists[/green]" if global_exists else "[yellow]✗ Not found[/yellow]"
            global_access = ""
            if global_exists:
                global_writable = os.access(global_path, os.W_OK)
                global_access = "[green]✓ Writable[/green]" if global_writable else "[yellow]⚠ Read-only[/yellow]"

            table.add_row("GLOBAL", str(global_path), global_status, global_access)

            # Project config
            project_exists = project_path.exists()
            project_status = "[green]✓ Exists[/green]" if project_exists else "[yellow]✗ Not found[/yellow]"
            project_access = ""
            if project_exists:
                project_writable = os.access(project_path, os.W_OK)
                project_access = "[green]✓ Writable[/green]" if project_writable else "[yellow]⚠ Read-only[/yellow]"

            table.add_row("PROJECT", str(project_path), project_status, project_access)

            console.print(table)

            # Show which config is active
            console.print("\n[bold]Active Configuration:[/bold]")
            if project_exists:
                console.print("[cyan]PROJECT[/cyan] (project config takes precedence)")
            elif global_exists:
                console.print("[cyan]GLOBAL[/cyan] (no project config found)")
            else:
                console.print("[yellow]DEFAULTS[/yellow] (no config files found)")

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@config_group.command(name="show")
@click.option(
    "--source",
    type=click.Choice(["merged", "global", "project", "defaults"]),
    default="merged",
    help="Which config to show (default: merged)",
)
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format (default: yaml)")
def show_command(source: str, format: str) -> None:
    """Display configuration.

    Shows the configuration from different sources with precedence applied.

    Examples:
        mycelium config show                   # Show merged config
        mycelium config show --source=global   # Show global config only
        mycelium config show --format=json     # Show as JSON
    """
    try:
        if source == "merged":
            # Load merged configuration
            loader = ConfigLoader()
            config = loader.load()
            config_dict = config.to_dict(exclude_none=True)
            console.print("[bold]Merged Configuration[/bold] (defaults → global → project)\n")

        elif source == "global":
            # Load only global config
            global_path = get_global_config_path()
            if not global_path.exists():
                console.print("[yellow]No global configuration file found[/yellow]")
                console.print(f"Expected location: {global_path}")
                return

            manager = ConfigManager(config_path=global_path)
            config = manager.load()
            config_dict = config.to_dict(exclude_none=True)
            console.print(f"[bold]Global Configuration[/bold] ({global_path})\n")

        elif source == "project":
            # Load only project config
            project_path = get_project_config_path()
            if not project_path.exists():
                console.print("[yellow]No project configuration file found[/yellow]")
                console.print(f"Expected location: {project_path}")
                return

            manager = ConfigManager(config_path=project_path)
            config = manager.load()
            config_dict = config.to_dict(exclude_none=True)
            console.print(f"[bold]Project Configuration[/bold] ({project_path})\n")

        elif source == "defaults":
            # Show defaults
            from mycelium_onboarding.config.defaults import get_default_config_dict

            config_dict = get_default_config_dict()
            console.print("[bold]Default Configuration[/bold]\n")

        # Display in requested format
        if format == "yaml":
            yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
            console.print(yaml_str)
        elif format == "json":
            json_str = json.dumps(config_dict, indent=2)
            console.print(json_str)

    except (ConfigLoadError, ConfigValidationError) as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@config_group.command(name="get")
@click.argument("key")
@click.option("--default", help="Default value if key not found")
@click.option("--path", type=click.Path(exists=True), help="Path to specific config file")
def get_command(key: str, default: str | None, path: str | None) -> None:
    """Get configuration value by key.

    Supports dot notation for nested values (e.g., 'services.postgres.port').

    Examples:
        mycelium config get postgres.port
        mycelium config get redis.host --default=localhost
        mycelium config get services.postgres.enabled
        mycelium config get project_name --path=./custom-config.yaml
    """
    try:
        # Load merged configuration
        if path:
            # Load from specific file
            from pathlib import Path

            config_path = Path(path)
            loader = ConfigLoader()
            config_dict = loader._load_yaml_file(config_path) or {}
        else:
            # Load merged configuration from default paths
            loader = ConfigLoader()
            config = loader.load()
            config_dict = config.to_dict()

        # Navigate to nested value using dot notation
        value = _get_nested_value(config_dict, key)

        if value is None:
            if default is not None:
                console.print(f"{key}: {default}")
            else:
                console.print(f"[red]✗ Key not found: {key}[/red]")
                sys.exit(1)
        else:
            # Format output based on type
            if isinstance(value, (dict, list)):
                console.print(f"{key}:")
                console.print(yaml.dump(value, default_flow_style=False))
            else:
                console.print(f"{key}: {value}")

    except KeyError:
        if default is not None:
            console.print(f"{key}: {default}")
        else:
            console.print(f"[red]✗ Key not found: {key}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "set_global", is_flag=True, help="Set in global config")
@click.option("--path", type=click.Path(), help="Path to specific config file")
@click.option(
    "--type",
    type=click.Choice(["string", "int", "float", "bool"]),
    help="Value type (default: auto-detect)",
)
def set_command(key: str, value: str, set_global: bool, path: str | None, type: str | None) -> None:
    """Set configuration value.

    Sets a configuration value in either global or project config.
    By default, sets in project config (or global if no project exists).

    Type is auto-detected unless explicitly specified with --type.

    Examples:
        mycelium config set services.postgres.port 5433
        mycelium config set services.redis.host localhost --global
        mycelium config set deployment.auto_start true --type=bool
        mycelium config set project_name my-project --path=./config.yaml
    """
    try:
        # Determine target config file
        if path:
            # Use specific path provided
            target_path = Path(path)
            scope_name = "specified file"
        elif set_global:
            target_path = get_global_config_path()
            scope_name = "global"
        else:
            # Try project first, fallback to global
            project_path = get_project_config_path()
            if project_path.exists():
                target_path = project_path
                scope_name = "project"
            else:
                target_path = get_global_config_path()
                scope_name = "global"
                console.print("[yellow]No project config found, setting in global config[/yellow]")

        # Load existing config or create new one
        if target_path.exists():
            manager = ConfigManager(config_path=target_path)
            config = manager.load()
            config_dict = config.to_dict()
        else:
            # Create new config with defaults
            config = MyceliumConfig()
            config_dict = config.to_dict()

        # Parse value based on type (auto-detect if not specified)
        parsed_value = _parse_value_with_type(value, type) if type else _auto_parse_value(value)

        # Set nested value
        _set_nested_value(config_dict, key, parsed_value)

        # Validate and save
        new_config = MyceliumConfig.from_dict(config_dict)

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        manager = ConfigManager(config_path=target_path)
        manager.save(new_config)

        # Format output value - use Python repr for booleans
        display_value = repr(parsed_value) if isinstance(parsed_value, bool) else parsed_value

        console.print(f"[green]✓ Set {key} = {display_value}[/green]")
        console.print(f"  Scope: {scope_name}")
        console.print(f"  File: {target_path}")

    except ConfigValidationError as e:
        console.print(f"[red]✗ Validation error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@config_group.command(name="edit")
@click.option("--global", "edit_global", is_flag=True, help="Edit global config")
@click.option("--editor", help="Editor to use (default: $EDITOR)")
def edit_command(edit_global: bool, editor: str | None) -> None:
    """Open configuration file in editor.

    Opens the configuration file in your preferred text editor.
    Defaults to $EDITOR environment variable, with fallback to nano/vi.

    Examples:
        mycelium config edit                   # Edit project config
        mycelium config edit --global          # Edit global config
        mycelium config edit --editor=vim      # Use specific editor
    """
    try:
        # Determine which config to edit
        if edit_global:
            config_path = get_global_config_path()
            scope_name = "global"
        else:
            # Prefer project config
            project_path = get_project_config_path()
            if project_path.exists():
                config_path = project_path
                scope_name = "project"
            else:
                config_path = get_global_config_path()
                scope_name = "global"
                console.print("[yellow]No project config found, editing global config[/yellow]")

        # Ensure config file exists
        if not config_path.exists():
            console.print(f"[yellow]Config file does not exist: {config_path}[/yellow]")
            if click.confirm("Create new config file?", default=True):
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config = MyceliumConfig()
                manager = ConfigManager(config_path=config_path)
                manager.save(config)
                console.print(f"[green]✓ Created {scope_name} config: {config_path}[/green]")
            else:
                return

        # Determine editor
        if editor is None:
            editor = os.environ.get("EDITOR")
            if editor is None:
                # Try common editors
                for fallback_editor in ["nano", "vi", "vim"]:
                    if subprocess.run(["which", fallback_editor], capture_output=True).returncode == 0:
                        editor = fallback_editor
                        break

        if editor is None:
            console.print("[red]✗ No editor found. Set $EDITOR or use --editor option[/red]")
            sys.exit(1)

        console.print(f"[cyan]Opening {scope_name} config in {editor}...[/cyan]")

        # Open editor
        result = subprocess.run([editor, str(config_path)])

        if result.returncode != 0:
            console.print(f"[red]✗ Editor exited with code {result.returncode}[/red]")
            sys.exit(1)

        # Validate the edited config
        try:
            manager = ConfigManager(config_path=config_path)
            manager.load()
            console.print("[green]✓ Configuration is valid[/green]")
        except (ConfigLoadError, ConfigValidationError) as e:
            console.print(f"[red]✗ Configuration validation failed: {e}[/red]")
            if click.confirm("Would you like to edit again to fix errors?", default=True):
                edit_command(edit_global, editor)

    except KeyboardInterrupt:
        console.print("\n[yellow]Editing cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


@config_group.command(name="rollback")
@click.argument("backup-dir", type=click.Path(exists=True, path_type=Path))
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def rollback_command(backup_dir: Path, yes: bool) -> None:
    """Rollback configuration from backup.

    Restores configuration files from a backup directory created during migration.

    Examples:
        mycelium config rollback ~/.local/share/mycelium/backups/20231107-123456
        mycelium config rollback /path/to/backup --yes
    """
    try:
        # Check if backup directory has the expected structure
        if not backup_dir.is_dir():
            console.print(f"[red]✗ Not a directory: {backup_dir}[/red]")
            sys.exit(1)

        # Find backup files
        backup_files = list(backup_dir.glob("*.yaml"))

        if not backup_files:
            console.print(f"[red]✗ No backup files found in: {backup_dir}[/red]")
            sys.exit(1)

        # Show what will be restored
        console.print("[bold yellow]The following files will be restored:[/bold yellow]\n")
        for backup_file in backup_files:
            console.print(f"  {backup_file.name}")

        console.print(f"\n[yellow]From backup: {backup_dir}[/yellow]")

        # Confirm rollback
        if not yes and not click.confirm("\nProceed with rollback?", default=False):
            console.print("[yellow]Rollback cancelled[/yellow]")
            return

        # Perform rollback
        restored_count = 0
        for backup_file in backup_files:
            try:
                # Determine restore location based on backup file name
                if "global" in backup_file.name.lower():
                    restore_path = get_global_config_path()
                else:
                    restore_path = get_project_config_path()

                # Restore file
                import shutil

                restore_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, restore_path)

                console.print(f"[green]✓[/green] Restored: {restore_path}")
                restored_count += 1

            except Exception as e:
                console.print(f"[red]✗ Failed to restore {backup_file.name}: {e}[/red]")

        if restored_count > 0:
            console.print(f"\n[green]✓ Rollback complete - restored {restored_count} file(s)[/green]")
        else:
            console.print("\n[red]✗ Rollback failed - no files were restored[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


# Helper functions


def _display_config_location(scope: str, path: Path) -> None:
    """Display a single configuration location."""
    console.print(f"[bold]{scope} Configuration:[/bold]")
    console.print(f"  Path: {path}")

    if path.exists():
        console.print("  Status: [green]✓ Exists[/green]")
        writable = os.access(path, os.W_OK)
        access = "[green]✓ Writable[/green]" if writable else "[yellow]⚠ Read-only[/yellow]"
        console.print(f"  Access: {access}")

        # Show file stats
        stats = path.stat()
        console.print(f"  Size: {stats.st_size} bytes")

        from datetime import datetime

        modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"  Modified: {modified}")
    else:
        console.print("  Status: [yellow]✗ Not found[/yellow]")


def _get_nested_value(data: dict[str, Any], key: str) -> Any:
    """Get nested value from dictionary using dot notation."""
    keys = key.split(".")
    value = data

    try:
        for k in keys:
            if isinstance(value, dict):
                value = value[k]
            else:
                raise KeyError(f"Cannot access key '{k}' in non-dict value")
        return value
    except (KeyError, TypeError):
        raise KeyError(f"Key not found: {key}") from None


def _set_nested_value(data: dict[str, Any], key: str, value: Any) -> None:
    """Set nested value in dictionary using dot notation."""
    keys = key.split(".")
    current = data

    # Navigate to parent of target key
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            raise ValueError(f"Cannot set nested value: '{k}' is not a dictionary")
        current = current[k]

    # Set the final value
    current[keys[-1]] = value


def _parse_value_with_type(value: str, type_name: str) -> Any:
    """Parse string value to specified type."""
    if type_name == "bool":
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        raise ValueError(f"Invalid boolean value: {value}")

    if type_name == "int":
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"Invalid integer value: {value}") from e

    elif type_name == "float":
        try:
            return float(value)
        except ValueError as e:
            raise ValueError(f"Invalid float value: {value}") from e

    else:  # string
        return value


def _auto_parse_value(value: str) -> Any:
    """Auto-detect and parse value type.

    Attempts to parse in order: bool, int, float, string.
    """
    # Try boolean first
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Default to string
    return value
