"""Command-line interface for Mycelium onboarding.

This module provides CLI commands for environment setup, direnv configuration,
system status checks, configuration management, and service detection. All commands
validate the environment before execution to ensure proper activation.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from functools import reduce
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from mycelium_onboarding.config.manager import (
    ConfigLoadError,
    ConfigManager,
    ConfigSaveError,
    ConfigValidationError,
)
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.config_loader import get_config_path
from mycelium_onboarding.env_validator import (
    EnvironmentValidationError,
    get_environment_info,
    is_environment_active,
    validate_environment,
)
from mycelium_onboarding.setup_direnv import setup_direnv
from mycelium_onboarding.xdg_dirs import get_all_dirs, get_config_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)

# Commands that don't require environment validation
SKIP_VALIDATION_COMMANDS = {"help", "setup-direnv", "config", "detect", "init", "deploy"}

# Rich console for pretty output
console = Console()


# ============================================================================
# Original Commands (preserved for compatibility)
# ============================================================================


def cmd_setup_direnv(_args: list[str]) -> int:
    """Set up direnv integration.

    This command does not require environment validation since it's used
    to set up the environment in the first place.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Setting up direnv integration for Mycelium...\n")

    try:
        success, message = setup_direnv()
        print(message)
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("Failed to setup direnv")
        return 1


def cmd_status(_args: list[str]) -> int:
    """Display environment status.

    Enhanced to show environment validation status and provide more
    detailed information using the environment validator.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, 1 if environment invalid)
    """
    print("Mycelium Environment Status:\n")

    # Use environment validator to get comprehensive info
    env_info = get_environment_info()
    active = is_environment_active()

    print("Environment Activation:")
    if active:
        print("  ✓ Environment is ACTIVE")
    else:
        print("  ✗ Environment is INACTIVE")
    print()

    # Show environment variables with validation
    print("Environment Variables:")
    for var, value in env_info.items():
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            print(f"  ✗ {var}: (not set)")
    print()

    # Try to validate environment and show results
    print("Environment Validation:")
    try:
        validate_environment()
        print("  ✓ All required variables set")
        print("  ✓ All directories exist and are writable")
        print("  ✓ MYCELIUM_ROOT is a valid git repository")
        print("  ✓ Environment is fully operational")
        validation_passed = True
    except EnvironmentValidationError as e:
        print("  ✗ Validation FAILED")
        print(f"\n{e}")
        validation_passed = False
    print()

    # Check XDG directories
    try:
        dirs = get_all_dirs()
        print("XDG Directories:")
        for name, path in dirs.items():
            exists = "✓" if path.exists() else "✗"
            print(f"  {exists} {name}: {path}")
        print()
    except Exception as e:
        print(f"Error reading XDG directories: {e}\n", file=sys.stderr)

    # Check direnv
    from mycelium_onboarding.setup_direnv import (
        check_direnv_hook_installed,
        check_direnv_installed,
        get_direnv_version,
    )

    print("direnv Status:")
    if check_direnv_installed():
        version = get_direnv_version()
        print(f"  ✓ Installed: {version or 'unknown version'}")

        hook_installed, hook_message = check_direnv_hook_installed()
        if hook_installed:
            print(f"  ✓ Shell hook: {hook_message}")
        else:
            print(f"  ✗ Shell hook: {hook_message}")

        # Check if .envrc exists
        envrc_path = Path.cwd() / ".envrc"
        if envrc_path.exists():
            print(f"  ✓ .envrc: exists at {envrc_path}")
        else:
            print("  ✗ .envrc: not found")
    else:
        print("  ✗ Not installed")

    # Return appropriate exit code
    return 0 if validation_passed else 1


def cmd_help(_args: list[str]) -> int:
    """Display help message.

    Args:
        args: Command-line arguments (unused)

    Returns:
        Exit code (always 0)
    """
    print(
        """Mycelium Onboarding CLI

Usage: python -m mycelium_onboarding <command> [options]

Commands:
  init            Interactive wizard to set up Mycelium
  setup-direnv    Set up direnv integration for automatic environment activation
  status          Display environment and configuration status (validates environment)
  config          Configuration management commands (see 'config --help')
  detect          Service detection commands (see 'detect --help')
  deploy          Deployment generation and management commands (see 'deploy --help')
  help            Show this help message

Configuration Commands:
  config show     Display current configuration
  config init     Initialize default configuration
  config get      Get configuration value
  config set      Set configuration value
  config validate Validate current configuration
  config migrate  Migrate configuration to newer schema version

Detection Commands:
  detect services Detect all available services
  detect docker   Detect Docker daemon availability
  detect redis    Detect Redis instances
  detect postgres Detect PostgreSQL instances
  detect temporal Detect Temporal server
  detect gpu      Detect available GPUs

Deployment Commands:
  deploy generate Generate deployment configuration files
  deploy start    Start deployed services
  deploy stop     Stop deployed services
  deploy status   Show status of deployed services
  deploy secrets  Manage deployment secrets

Environment Validation:
  Most commands require a properly activated Mycelium environment.
  Use 'status' to check your environment configuration.

  To activate:
    - With direnv: cd to project and run 'direnv allow'
    - Without direnv: run 'source bin/activate.sh'

Examples:
  python -m mycelium_onboarding init
  python -m mycelium_onboarding setup-direnv
  python -m mycelium_onboarding status
  python -m mycelium_onboarding config show
  python -m mycelium_onboarding config get services.redis.port
  python -m mycelium_onboarding config migrate --target 1.2
  python -m mycelium_onboarding detect services
  python -m mycelium_onboarding detect services --save-config
  python -m mycelium_onboarding deploy generate
  python -m mycelium_onboarding deploy generate --method kubernetes

For more information, visit: https://github.com/gsornsen/mycelium
"""
    )
    return 0


# ============================================================================
# Click-based Configuration Commands
# ============================================================================


@click.group()
def cli() -> None:
    """Mycelium Onboarding CLI."""
    pass


@cli.command()
@click.option(
    "--resume/--no-resume", default=None, help="Resume previous wizard session"
)
@click.option("--reset", is_flag=True, help="Clear any saved state and start fresh")
def init(resume: bool | None, reset: bool) -> None:
    """Interactive onboarding wizard to set up Mycelium.

    This wizard will guide you through:
    - Detecting available services
    - Selecting and configuring services
    - Choosing a deployment method
    - Generating configuration files

    Examples:
        mycelium init                 # Start fresh or auto-resume
        mycelium init --resume        # Force resume if state exists
        mycelium init --no-resume     # Force fresh start
        mycelium init --reset         # Clear saved state and start fresh
    """
    from mycelium_onboarding.wizard.flow import WizardFlow, WizardState, WizardStep
    from mycelium_onboarding.wizard.persistence import WizardStatePersistence
    from mycelium_onboarding.wizard.screens import WizardScreens
    from mycelium_onboarding.wizard.validation import WizardValidator

    persistence = WizardStatePersistence()

    # Handle reset flag
    if reset:
        if persistence.exists():
            persistence.clear()
            console.print("[yellow]✓[/yellow] Cleared saved wizard state")
        console.print("[cyan]Starting fresh wizard...[/cyan]\n")

    # Determine whether to resume
    should_resume = False
    if persistence.exists():
        if resume is None:
            # Auto-detect: ask user
            should_resume = click.confirm(
                "Found existing wizard session. Would you like to resume?", default=True
            )
        else:
            should_resume = resume

    # Load or create state
    if should_resume and persistence.exists():
        console.print("[cyan]Resuming wizard from previous session...[/cyan]\n")
        state = persistence.load()
        if state is None:
            console.print(
                "[yellow]⚠ Could not load saved state. Starting fresh.[/yellow]\n"
            )
            state = WizardState()
    else:
        state = WizardState()

    # Initialize flow and screens
    flow = WizardFlow(state)
    screens = WizardScreens(state)
    validator = WizardValidator(state)

    try:
        # Wizard flow
        while not state.is_complete():
            # Save state before each step (for resume)
            persistence.save(state)

            current_step = state.current_step

            if current_step == WizardStep.WELCOME:
                setup_mode = screens.show_welcome()
                state.setup_mode = setup_mode  # Store for Advanced screen skip
                flow.advance()

            elif current_step == WizardStep.DETECTION:
                summary = screens.show_detection()
                state.detection_results = summary  # type: ignore[assignment]
                flow.advance()

            elif current_step == WizardStep.SERVICES:
                # Get project name first
                if not state.project_name:
                    project_name = click.prompt(
                        "Project name", default="mycelium-project", type=str
                    )
                    state.project_name = project_name

                services = screens.show_services()
                state.services_enabled = services
                flow.advance()

            elif current_step == WizardStep.DEPLOYMENT:
                deployment = screens.show_deployment()
                state.deployment_method = deployment

                # Skip ADVANCED if quick mode
                if state.setup_mode == "quick":
                    state.current_step = WizardStep.REVIEW
                else:
                    flow.advance()

            elif current_step == WizardStep.ADVANCED:
                screens.show_advanced()
                flow.advance()

            elif current_step == WizardStep.REVIEW:
                action = screens.show_review()

                if action == "confirm":
                    # Validate state
                    if not validator.validate_state():
                        console.print("[red]✗ Validation errors:[/red]")
                        for error in validator.get_error_messages():
                            console.print(f"  • {error}")
                        click.pause("Press any key to continue...")
                        continue

                    # Convert to config and save
                    config = state.to_config()
                    manager = ConfigManager()
                    config_path = manager._determine_save_path()

                    # Ensure parent directory exists
                    config_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save configuration
                    manager.save(config)

                    # Mark complete and transition to COMPLETE step
                    # Transition to COMPLETE step (loop will continue one more time to show completion screen)
                    state.current_step = WizardStep.COMPLETE

                elif action.startswith("edit:"):
                    # Jump to edit step
                    edit_step = action.split(":")[1]
                    state.current_step = WizardStep(edit_step)

                elif action == "cancel":
                    if click.confirm("Are you sure you want to cancel?", default=False):
                        persistence.clear()
                        console.print("[yellow]Wizard cancelled.[/yellow]")
                        raise SystemExit(0)

            elif current_step == WizardStep.COMPLETE:
                config_path = get_config_dir() / "config.yaml"
                state.completed = True  # Mark wizard as fully complete
                screens.show_complete(str(config_path))
                break

        # Clear saved state on successful completion
        persistence.clear()

    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Wizard interrupted. Run 'mycelium init --resume' to continue.[/yellow]"
        )
        persistence.save(state)
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        persistence.save(state)
        raise


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command()
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Config file path to display",
)
@click.option(
    "--format",
    type=click.Choice(["yaml", "json", "table"], case_sensitive=False),
    default="yaml",
    help="Output format (default: yaml)",
)
def show(path: Path | None, format: str) -> None:
    """Display current configuration.

    Shows the configuration with colorized, formatted output. Supports
    YAML, JSON, and table formats.

    Examples:
        config show
        config show --format json
        config show --path /path/to/config.yaml
    """
    try:
        if path:
            manager = ConfigManager(config_path=path)
            location = path
        else:
            manager = ConfigManager()
            location = get_config_path(ConfigManager.CONFIG_FILENAME)

        cfg = manager.load()

        # Display location
        exists = location.exists()
        status = click.style("✓", fg="green") if exists else click.style("✗", fg="red")
        click.echo(f"{status} Configuration: {location}")

        if not exists:
            click.echo(click.style("  (using defaults - no file exists)", fg="yellow"))

        click.echo()

        # Display configuration
        if format == "yaml":
            yaml_content = cfg.to_yaml(exclude_none=True)
            # Simple colorization for YAML
            for line in yaml_content.splitlines():
                if line.strip().startswith("#"):
                    click.echo(click.style(line, fg="bright_black"))
                elif ":" in line:
                    key, _, value = line.partition(":")
                    click.echo(click.style(key, fg="cyan", bold=True) + ":" + value)
                else:
                    click.echo(line)
        elif format == "json":
            json_content = json.dumps(cfg.to_dict(exclude_none=True), indent=2)
            click.echo(json_content)
        else:  # table
            _display_config_table(cfg)

    except (ConfigLoadError, ConfigValidationError) as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(click.style(f"✗ {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to show configuration")
        sys.exit(1)


@config.command(name="init")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path (default: auto-detect)",
)
@click.option(
    "--project-local",
    is_flag=True,
    help="Create project-local configuration",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration",
)
def config_init(output: Path | None, project_local: bool, force: bool) -> None:
    """Initialize default configuration.

    Creates a new configuration file with default values. By default,
    creates user-global config unless --project-local is specified.

    Examples:
        config init
        config init --project-local
        config init --output /path/to/config.yaml --force
    """
    try:
        if output:
            location = output
        else:
            location = get_config_path(
                ConfigManager.CONFIG_FILENAME,
                prefer_project=project_local,
            )

        if location.exists() and not force:
            click.echo(
                click.style(f"✗ Configuration already exists: {location}", fg="red"),
                err=True,
            )
            click.echo("Use --force to overwrite", err=True)
            sys.exit(1)

        # Confirm if overwriting
        if (
            location.exists()
            and force
            and not click.confirm(
                click.style(
                    f"Overwrite existing configuration at {location}?",
                    fg="yellow",
                )
            )
        ):
            click.echo("Cancelled")
            sys.exit(0)

        # Create default configuration
        cfg = MyceliumConfig()
        manager = ConfigManager(config_path=location)

        # Create parent directories
        location.parent.mkdir(parents=True, exist_ok=True)

        # Save
        manager.save(cfg)

        click.echo(click.style(f"✓ Created configuration: {location}", fg="green"))

    except (ConfigSaveError, ConfigValidationError) as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to initialize configuration")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to initialize configuration")
        sys.exit(1)


@config.command()
@click.argument("key")
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Config file path to query",
)
def get(key: str, path: Path | None) -> None:
    """Get configuration value.

    Retrieves a configuration value using dot notation for nested keys.

    Examples:
        config get services.redis.port
        config get deployment.method
        config get project_name
    """
    try:
        manager = ConfigManager(config_path=path) if path else ConfigManager()

        cfg = manager.load()

        # Navigate nested keys using dot notation
        value = _get_nested_value(cfg.to_dict(), key)

        if value is None:
            click.echo(
                click.style(f"✗ Key not found: {key}", fg="red"),
                err=True,
            )
            sys.exit(1)

        # Format output
        click.echo(f"{click.style(key, fg='cyan', bold=True)}: {value}")

    except KeyError as e:
        click.echo(
            click.style(f"✗ Key not found: {key} ({e})", fg="red"),
            err=True,
        )
        sys.exit(1)
    except (ConfigLoadError, ConfigValidationError) as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to get configuration value")
        sys.exit(1)


@config.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "--project-local",
    is_flag=True,
    help="Save to project-local configuration",
)
def set(key: str, value: str, project_local: bool) -> None:
    """Set configuration value.

    Sets a configuration value using dot notation for nested keys.
    The value is automatically converted to the appropriate type.

    Examples:
        config set services.redis.port 6380
        config set deployment.method docker-compose
        config set services.redis.enabled true
    """
    try:
        # Determine location first (so we load from the right place)
        location = get_config_path(
            ConfigManager.CONFIG_FILENAME,
            prefer_project=project_local,
        )

        # Load existing config from that location
        manager = ConfigManager(config_path=location)
        cfg = manager.load()
        cfg_dict = cfg.to_dict()

        # Parse value (type-aware)
        parsed_value = _parse_value(value)

        # Set nested value
        _set_nested_value(cfg_dict, key, parsed_value)

        # Re-validate
        new_cfg = MyceliumConfig.from_dict(cfg_dict)

        # Save back to the same location
        manager.save(new_cfg)

        click.echo(click.style(f"✓ Set {key} = {parsed_value}", fg="green"))
        click.echo(f"  Saved to: {location}")

    except (KeyError, ValueError) as e:
        click.echo(
            click.style(f"✗ Invalid key or value: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
    except ConfigValidationError as e:
        click.echo(
            click.style(f"✗ Configuration validation failed: {e}", fg="red"),
            err=True,
        )
        sys.exit(2)
    except (ConfigLoadError, ConfigSaveError) as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to set configuration value")
        sys.exit(1)


@config.command()
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Config file path to validate",
)
def validate(path: Path | None) -> None:
    """Validate current configuration.

    Validates the configuration file and displays any errors or warnings.
    Shows a summary of enabled services on success.

    Examples:
        config validate
        config validate --path /path/to/config.yaml
    """
    try:
        if path:
            manager = ConfigManager(config_path=path)
            location = path
        else:
            manager = ConfigManager()
            location = get_config_path(ConfigManager.CONFIG_FILENAME)

        cfg = manager.load()

        # Validate
        errors = manager.validate(cfg)

        if errors:
            click.echo(click.style("✗ Configuration invalid:", fg="red"), err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(2)

        click.echo(click.style(f"✓ Configuration valid: {location}", fg="green"))
        click.echo()

        # Show summary
        click.echo(click.style("Configuration Summary:", bold=True))
        click.echo(f"  Project: {cfg.project_name}")
        click.echo(f"  Schema Version: {cfg.version}")
        click.echo(f"  Deployment: {cfg.deployment.method.value}")

        # Enabled services
        enabled_services = []
        if cfg.services.redis.enabled:
            enabled_services.append(f"redis (port {cfg.services.redis.port})")
        if cfg.services.postgres.enabled:
            enabled_services.append(f"postgres (port {cfg.services.postgres.port})")
        if cfg.services.temporal.enabled:
            enabled_services.append(
                f"temporal (UI: {cfg.services.temporal.ui_port}, "
                f"gRPC: {cfg.services.temporal.frontend_port})"
            )

        click.echo(f"  Enabled Services: {', '.join(enabled_services)}")

    except (ConfigLoadError, ConfigValidationError) as e:
        click.echo(click.style("✗ Configuration error:", fg="red"), err=True)
        click.echo(str(e), err=True)
        sys.exit(2)
    except FileNotFoundError as e:
        click.echo(click.style(f"✗ {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to validate configuration")
        sys.exit(1)


@config.command()
@click.option(
    "--target",
    help="Target version to migrate to (default: latest)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview migration changes without applying them",
)
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Config file path to migrate",
)
def migrate(target: str | None, dry_run: bool, path: Path | None) -> None:
    """Migrate configuration to newer schema version.

    Automatically discovers and applies the necessary migration chain
    to upgrade your configuration to the target version. Creates a backup
    before applying changes.

    Use --dry-run to preview changes without applying them.

    Examples:
        config migrate
        config migrate --target 1.2
        config migrate --dry-run
        config migrate --path /path/to/config.yaml --target 1.1
    """
    from mycelium_onboarding.config.migrations import (
        MigrationError,
        MigrationPathError,
        get_default_registry,
    )

    try:
        if path:
            manager = ConfigManager(config_path=path)
            location = path
        else:
            manager = ConfigManager()
            location = get_config_path(ConfigManager.CONFIG_FILENAME)

        # Check if config file exists
        if not location.exists():
            click.echo(
                click.style(f"✗ Configuration file not found: {location}", fg="red"),
                err=True,
            )
            click.echo("Run 'config init' to create a configuration file.", err=True)
            sys.exit(1)

        click.echo(f"Configuration: {location}")

        # Load current config to check version
        import yaml

        with location.open("r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        if config_dict is None:
            click.echo(click.style("✗ Configuration file is empty", fg="red"), err=True)
            sys.exit(1)

        current_version = config_dict.get("version", "unknown")
        click.echo(f"Current version: {click.style(current_version, fg='cyan')}")

        # Determine target version
        if target is None:
            target = MyceliumConfig().version
            click.echo(f"Target version: {click.style(target, fg='cyan')} (latest)")
        else:
            click.echo(f"Target version: {click.style(target, fg='cyan')}")

        # Check if migration is needed
        registry = get_default_registry()
        if not registry.needs_migration(config_dict, target):
            click.echo(click.style("✓ Configuration is already up to date", fg="green"))
            sys.exit(0)

        click.echo()

        # Get migration path
        try:
            migrations = registry.get_migration_path(current_version, target)
            click.echo(click.style("Migration Path:", bold=True))
            click.echo(
                "  "
                + " -> ".join([current_version] + [m.to_version for m in migrations])
            )
            click.echo()

            # Show migration details
            for i, migration in enumerate(migrations, 1):
                click.echo(
                    f"  {i}. {click.style(migration.from_version, fg='yellow')} "
                    f"-> {click.style(migration.to_version, fg='green')}"
                )
                click.echo(f"     {migration.description}")
            click.echo()

        except MigrationPathError as e:
            click.echo(click.style(f"✗ {e}", fg="red"), err=True)
            sys.exit(1)

        # Preview changes
        if dry_run:
            click.echo(click.style("Preview Mode (dry-run):", bold=True))
            click.echo()
            preview = registry.preview_migration(config_dict, target)
            click.echo(preview)
            click.echo()
            click.echo(
                click.style(
                    "No changes applied. Run without --dry-run to apply.", fg="yellow"
                )
            )
            sys.exit(0)

        # Confirm migration
        if not click.confirm(
            click.style(
                f"Apply migration from {current_version} to {target}?", fg="yellow"
            )
        ):
            click.echo("Migration cancelled")
            sys.exit(0)

        # Perform migration
        click.echo()
        click.echo(click.style("Applying migration...", bold=True))

        try:
            manager.load_and_migrate(target_version=target)

            click.echo()
            click.echo(
                click.style(f"✓ Successfully migrated to version {target}", fg="green")
            )
            click.echo(f"  Backup created: {location}.backup")
            click.echo(f"  Configuration updated: {location}")

            # Show migration history
            history = registry.get_history()
            if history:
                click.echo()
                click.echo(click.style("Migration History:", bold=True))
                for record in history:
                    status = (
                        click.style("✓", fg="green")
                        if record.success
                        else click.style("✗", fg="red")
                    )
                    click.echo(
                        f"  {status} {record.from_version} -> {record.to_version}"
                    )
                    if record.error:
                        click.echo(f"      Error: {record.error}")

        except MigrationError as e:
            click.echo()
            click.echo(click.style(f"✗ Migration failed: {e}", fg="red"), err=True)
            click.echo()
            click.echo(
                "The configuration was backed up and is still available at:",
                err=True,
            )
            click.echo(f"  {location}.backup", err=True)
            sys.exit(1)

    except (ConfigLoadError, ConfigValidationError) as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg="red"), err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(click.style(f"✗ {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        logger.exception("Failed to migrate configuration")
        sys.exit(1)


# ============================================================================
# Detection Commands
# ============================================================================


@cli.group()
def detect() -> None:
    """Service detection commands."""
    pass


@detect.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--save-config",
    is_flag=True,
    help="Save detected settings to configuration",
)
def services(format: str, save_config: bool) -> None:
    """Detect all available services (Docker, Redis, PostgreSQL, Temporal, GPU).

    Examples:
        detect services
        detect services --format json
        detect services --save-config
    """
    from mycelium_onboarding.detection.orchestrator import (
        detect_all,
        generate_detection_report,
        update_config_from_detection,
    )

    try:
        # Run detection with status indicator (only for text format)
        if format == "text":
            click.echo(click.style("Detecting services...", fg="blue", bold=True))
        summary = detect_all()

        # Display report
        report = generate_detection_report(summary, format=format)

        if format == "text":
            click.echo()
        click.echo(report)

        # Optionally save to config
        if save_config:
            try:
                manager = ConfigManager()
                # Load existing config or use defaults
                try:
                    existing_config = manager.load()
                except (ConfigLoadError, FileNotFoundError):
                    existing_config = None

                # Update config from detection
                config = update_config_from_detection(summary, existing_config)

                # Save config
                location = get_config_path(ConfigManager.CONFIG_FILENAME)
                location.parent.mkdir(parents=True, exist_ok=True)
                save_manager = ConfigManager(config_path=location)
                save_manager.save(config)

                click.echo()
                click.echo(
                    click.style(
                        "✓ Configuration updated with detected settings", fg="green"
                    )
                )
                click.echo(f"  Saved to: {location}")

            except Exception as e:
                click.echo()
                click.echo(
                    click.style(f"✗ Failed to save configuration: {e}", fg="red"),
                    err=True,
                )
                sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        logger.exception("Service detection failed")
        sys.exit(1)


@detect.command()
def docker() -> None:
    """Detect Docker daemon availability."""
    from mycelium_onboarding.detection.docker_detector import detect_docker

    try:
        click.echo(click.style("Detecting Docker...", fg="blue", bold=True))
        result = detect_docker()

        click.echo()
        if result.available:
            click.echo(click.style("✓ Docker Available", fg="green", bold=True))
            click.echo(f"  Version: {result.version or 'unknown'}")
            if result.socket_path:
                click.echo(f"  Socket: {result.socket_path}")
        else:
            click.echo(click.style("✗ Docker Not Available", fg="red", bold=True))
            if result.error_message:
                click.echo(f"  Error: {result.error_message}")

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        sys.exit(1)


@detect.command()
def redis() -> None:
    """Detect Redis instances."""
    from mycelium_onboarding.detection.redis_detector import scan_common_redis_ports

    try:
        click.echo(click.style("Detecting Redis instances...", fg="blue", bold=True))
        results = scan_common_redis_ports()

        click.echo()
        if results:
            click.echo(
                click.style(
                    f"✓ Found {len(results)} Redis instance(s)", fg="green", bold=True
                )
            )
            for i, redis in enumerate(results, 1):
                click.echo(f"\n  Instance {i}:")
                click.echo(f"    Host: {redis.host}")
                click.echo(f"    Port: {redis.port}")
                if redis.version:
                    click.echo(f"    Version: {redis.version}")
                if redis.password_required:
                    click.echo("    Auth: Required")
        else:
            click.echo(click.style("✗ No Redis instances found", fg="yellow"))
            click.echo("  Scanned ports: 6379, 6380, 6381")

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        sys.exit(1)


@detect.command()
def postgres() -> None:
    """Detect PostgreSQL instances."""
    from mycelium_onboarding.detection.postgres_detector import (
        scan_common_postgres_ports,
    )

    try:
        click.echo(
            click.style("Detecting PostgreSQL instances...", fg="blue", bold=True)
        )
        results = scan_common_postgres_ports()

        click.echo()
        if results:
            click.echo(
                click.style(
                    f"✓ Found {len(results)} PostgreSQL instance(s)",
                    fg="green",
                    bold=True,
                )
            )
            for i, pg in enumerate(results, 1):
                click.echo(f"\n  Instance {i}:")
                click.echo(f"    Host: {pg.host}")
                click.echo(f"    Port: {pg.port}")
                if pg.version:
                    click.echo(f"    Version: {pg.version}")
                if pg.authentication_method:
                    click.echo(f"    Auth Method: {pg.authentication_method}")
        else:
            click.echo(click.style("✗ No PostgreSQL instances found", fg="yellow"))
            click.echo("  Scanned ports: 5432, 5433")

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        sys.exit(1)


@detect.command()
def temporal() -> None:
    """Detect Temporal server."""
    from mycelium_onboarding.detection.temporal_detector import detect_temporal

    try:
        click.echo(click.style("Detecting Temporal server...", fg="blue", bold=True))
        result = detect_temporal()

        click.echo()
        if result.available:
            click.echo(click.style("✓ Temporal Available", fg="green", bold=True))
            click.echo(f"  Frontend Port: {result.frontend_port}")
            click.echo(f"  UI Port: {result.ui_port}")
            if result.version:
                click.echo(f"  Version: {result.version}")
        else:
            click.echo(click.style("✗ Temporal Not Available", fg="red", bold=True))
            if result.error_message:
                click.echo(f"  Error: {result.error_message}")

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        sys.exit(1)


@detect.command()
def gpu() -> None:
    """Detect available GPUs."""
    from mycelium_onboarding.detection.gpu_detector import detect_gpus

    try:
        click.echo(click.style("Detecting GPUs...", fg="blue", bold=True))
        result = detect_gpus()

        click.echo()
        if result.available:
            click.echo(
                click.style(f"✓ Found {len(result.gpus)} GPU(s)", fg="green", bold=True)
            )
            click.echo(f"  Total Memory: {result.total_memory_mb} MB")

            for i, gpu in enumerate(result.gpus, 1):
                click.echo(f"\n  GPU {i}:")
                click.echo(f"    Vendor: {gpu.vendor.value.upper()}")
                click.echo(f"    Model: {gpu.model}")
                if gpu.memory_mb:
                    click.echo(f"    Memory: {gpu.memory_mb} MB")
                if gpu.driver_version:
                    click.echo(f"    Driver: {gpu.driver_version}")
                if gpu.cuda_version:
                    click.echo(f"    CUDA: {gpu.cuda_version}")
                if gpu.rocm_version:
                    click.echo(f"    ROCm: {gpu.rocm_version}")
        else:
            click.echo(click.style("✗ No GPUs detected", fg="yellow"))
            if result.error_message:
                click.echo(f"  Info: {result.error_message}")

    except Exception as e:
        click.echo(click.style(f"✗ Detection failed: {e}", fg="red"), err=True)
        sys.exit(1)


# ============================================================================
# Deployment Commands
# ============================================================================


@cli.group()
def deploy() -> None:
    """Deployment generation and management commands."""
    pass


@deploy.command()
@click.option(
    "--method",
    type=click.Choice(["docker-compose", "kubernetes", "systemd"]),
    help="Deployment method (defaults to config value)",
)
@click.option("--output", type=click.Path(), help="Output directory")
@click.option(
    "--generate-secrets/--no-secrets",
    default=True,
    help="Generate secrets for services",
)
def generate(method: str | None, output: str | None, generate_secrets: bool) -> None:
    """Generate deployment configuration files.

    Generates deployment configs based on your MyceliumConfig from the wizard.

    Examples:
        mycelium deploy generate
        mycelium deploy generate --method kubernetes
        mycelium deploy generate --output ./my-deployment
        mycelium deploy generate --no-secrets
    """
    from mycelium_onboarding.deployment.generator import (
        DeploymentGenerator,
        DeploymentMethod,
    )
    from mycelium_onboarding.deployment.secrets import SecretsManager

    # Load config
    manager = ConfigManager()
    try:
        config = manager.load()
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        console.print("[yellow]Run 'mycelium init' to create a configuration.[/yellow]")
        raise SystemExit(1)

    # Determine deployment method
    deploy_method = (
        DeploymentMethod(method) if method else DeploymentMethod(config.deployment.method)
    )

    # Display generation info
    console.print(f"\n[bold cyan]Generating {deploy_method.value} deployment...[/bold cyan]")
    console.print(f"Project: [yellow]{config.project_name}[/yellow]")

    # Get enabled services
    enabled_services = []
    if config.services.redis.enabled:
        enabled_services.append("redis")
    if config.services.postgres.enabled:
        enabled_services.append("postgres")
    if config.services.temporal.enabled:
        enabled_services.append("temporal")

    console.print(f"Services: [yellow]{', '.join(enabled_services)}[/yellow]\n")

    # Generate secrets if requested
    secrets_obj = None
    if generate_secrets:
        with console.status("[bold green]Generating secrets..."):
            secrets_mgr = SecretsManager(config.project_name)
            secrets_obj = secrets_mgr.generate_secrets(
                postgres=config.services.postgres.enabled,
                redis=config.services.redis.enabled,
                temporal=config.services.temporal.enabled,
            )
            secrets_mgr.save_secrets(secrets_obj)
        console.print("[green]✓[/green] Secrets generated and saved securely")

    # Generate deployment files
    with console.status(f"[bold green]Generating {deploy_method.value} files..."):
        generator = DeploymentGenerator(
            config, output_dir=Path(output) if output else None
        )
        result = generator.generate(deploy_method)

    # Display results
    if result.success:
        console.print("\n[bold green]✓ Deployment generated successfully![/bold green]\n")
        console.print(f"Output directory: [cyan]{result.output_dir}[/cyan]")
        console.print("\nGenerated files:")
        for file in result.files_generated:
            console.print(f"  • {file.name}")

        # Show warnings if any
        if result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")

        # Show next steps
        console.print("\n[bold]Next Steps:[/bold]")
        if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
            console.print(f"  1. Review and update {result.output_dir}/.env with your credentials")
            console.print(f"  2. cd {result.output_dir}")
            console.print("  3. docker-compose up -d")
        elif deploy_method == DeploymentMethod.KUBERNETES:
            console.print(f"  1. cd {result.output_dir}")
            console.print("  2. kubectl apply -k .")
            console.print(f"  3. kubectl get all -n {config.project_name}")
        elif deploy_method == DeploymentMethod.SYSTEMD:
            console.print(f"  1. cd {result.output_dir}")
            console.print("  2. sudo ./install.sh")
            console.print(f"  3. sudo systemctl start {config.project_name}-*")
    else:
        console.print("\n[bold red]✗ Deployment generation failed![/bold red]\n")
        console.print("[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
        raise SystemExit(1)


@deploy.command()
@click.option(
    "--method",
    type=click.Choice(["docker-compose", "kubernetes", "systemd"]),
    help="Deployment method (defaults to config value)",
)
def start(method: str | None) -> None:
    """Start deployed services.

    Starts the services using the specified deployment method.

    Examples:
        mycelium deploy start
        mycelium deploy start --method docker-compose
    """
    from mycelium_onboarding.deployment.generator import DeploymentMethod

    # Load config
    manager = ConfigManager()
    config = manager.load()

    deploy_method = (
        DeploymentMethod(method) if method else DeploymentMethod(config.deployment.method)
    )

    console.print(f"[bold cyan]Starting {deploy_method.value} deployment...[/bold cyan]\n")

    # Execute start command based on method
    try:
        if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]✓[/green] Services started successfully")
            if result.stdout:
                console.print(result.stdout)

        elif deploy_method == DeploymentMethod.KUBERNETES:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", config.project_name],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(result.stdout)

        elif deploy_method == DeploymentMethod.SYSTEMD:
            services = []
            if config.services.redis.enabled:
                services.append(f"{config.project_name}-redis")
            if config.services.postgres.enabled:
                services.append(f"{config.project_name}-postgres")
            if config.services.temporal.enabled:
                services.append(f"{config.project_name}-temporal")

            for service in services:
                subprocess.run(["sudo", "systemctl", "start", service], check=True)
            console.print(f"[green]✓[/green] Started {len(services)} service(s)")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting services: {e}[/red]")
        if e.stderr:
            console.print(f"[red]{e.stderr}[/red]")
        raise SystemExit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Command not found: {e}[/red]")
        console.print(
            f"[yellow]Ensure {deploy_method.value} tools are installed[/yellow]"
        )
        raise SystemExit(1)


@deploy.command()
@click.option(
    "--method",
    type=click.Choice(["docker-compose", "kubernetes", "systemd"]),
    help="Deployment method (defaults to config value)",
)
def stop(method: str | None) -> None:
    """Stop deployed services.

    Stops the services using the specified deployment method.

    Examples:
        mycelium deploy stop
        mycelium deploy stop --method docker-compose
    """
    from mycelium_onboarding.deployment.generator import DeploymentMethod

    # Load config
    manager = ConfigManager()
    config = manager.load()

    deploy_method = (
        DeploymentMethod(method) if method else DeploymentMethod(config.deployment.method)
    )

    console.print(f"[bold cyan]Stopping {deploy_method.value} deployment...[/bold cyan]\n")

    # Execute stop command based on method
    try:
        if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
            result = subprocess.run(
                ["docker-compose", "down"],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]✓[/green] Services stopped successfully")
            if result.stdout:
                console.print(result.stdout)

        elif deploy_method == DeploymentMethod.KUBERNETES:
            result = subprocess.run(
                ["kubectl", "delete", "all", "--all", "-n", config.project_name],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print("[green]✓[/green] Kubernetes resources deleted")
            if result.stdout:
                console.print(result.stdout)

        elif deploy_method == DeploymentMethod.SYSTEMD:
            services = []
            if config.services.redis.enabled:
                services.append(f"{config.project_name}-redis")
            if config.services.postgres.enabled:
                services.append(f"{config.project_name}-postgres")
            if config.services.temporal.enabled:
                services.append(f"{config.project_name}-temporal")

            for service in services:
                subprocess.run(["sudo", "systemctl", "stop", service], check=True)
            console.print(f"[green]✓[/green] Stopped {len(services)} service(s)")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error stopping services: {e}[/red]")
        if e.stderr:
            console.print(f"[red]{e.stderr}[/red]")
        raise SystemExit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Command not found: {e}[/red]")
        console.print(
            f"[yellow]Ensure {deploy_method.value} tools are installed[/yellow]"
        )
        raise SystemExit(1)


@deploy.command()
@click.option(
    "--method",
    type=click.Choice(["docker-compose", "kubernetes", "systemd"]),
    help="Deployment method (defaults to config value)",
)
@click.option("--watch", is_flag=True, help="Watch for changes")
def status(method: str | None, watch: bool) -> None:
    """Show status of deployed services.

    Examples:
        mycelium deploy status
        mycelium deploy status --watch
    """
    from mycelium_onboarding.deployment.generator import DeploymentMethod

    manager = ConfigManager()
    config = manager.load()

    deploy_method = (
        DeploymentMethod(method) if method else DeploymentMethod(config.deployment.method)
    )

    # Create status table
    table = Table(title=f"{config.project_name} - Service Status", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    if deploy_method == DeploymentMethod.DOCKER_COMPOSE:
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Parse and display container status
            if result.stdout.strip():
                import json

                # Handle both single object and array of objects
                try:
                    containers = json.loads(result.stdout)
                    if not isinstance(containers, list):
                        containers = [containers]
                except json.JSONDecodeError:
                    # Try line-by-line JSON
                    containers = []
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            containers.append(json.loads(line))

                for container in containers:
                    status_str = (
                        "[green]Running[/green]"
                        if container.get("State") == "running"
                        else "[red]Stopped[/red]"
                    )
                    table.add_row(
                        container.get("Service", container.get("Name", "unknown")),
                        status_str,
                        container.get("Status", ""),
                    )
            else:
                console.print("[yellow]No running containers found[/yellow]")
                return
        except subprocess.CalledProcessError:
            console.print("[yellow]No running containers found[/yellow]")
            return
        except FileNotFoundError:
            console.print("[red]docker-compose command not found[/red]")
            raise SystemExit(1)

    elif deploy_method == DeploymentMethod.KUBERNETES:
        try:
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    config.project_name,
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            import json

            pods_data = json.loads(result.stdout)
            for pod in pods_data.get("items", []):
                name = pod["metadata"]["name"]
                status_str = pod["status"].get("phase", "Unknown")
                if status_str == "Running":
                    status_str = "[green]Running[/green]"
                elif status_str == "Pending":
                    status_str = "[yellow]Pending[/yellow]"
                else:
                    status_str = f"[red]{status_str}[/red]"

                container_statuses = pod["status"].get("containerStatuses", [])
                ready_count = sum(1 for c in container_statuses if c.get("ready"))
                total_count = len(container_statuses)
                ready = f"{ready_count}/{total_count}"
                table.add_row(name, status_str, f"Ready: {ready}")
        except subprocess.CalledProcessError:
            console.print(f"[yellow]No pods found in namespace {config.project_name}[/yellow]")
            return
        except FileNotFoundError:
            console.print("[red]kubectl command not found[/red]")
            raise SystemExit(1)

    elif deploy_method == DeploymentMethod.SYSTEMD:
        services = []
        if config.services.redis.enabled:
            services.append(f"{config.project_name}-redis")
        if config.services.postgres.enabled:
            services.append(f"{config.project_name}-postgres")
        if config.services.temporal.enabled:
            services.append(f"{config.project_name}-temporal")

        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                )
                status_str = result.stdout.strip()
                if status_str == "active":
                    status_str = "[green]Active[/green]"
                elif status_str == "inactive":
                    status_str = "[yellow]Inactive[/yellow]"
                else:
                    status_str = f"[red]{status_str}[/red]"

                table.add_row(service, status_str, "")
            except subprocess.CalledProcessError:
                table.add_row(service, "[red]Error[/red]", "")

    console.print(table)

    if watch:
        console.print("\n[yellow]Watch mode not yet implemented[/yellow]")


@deploy.command()
@click.argument("secret_type", required=False)
@click.option("--rotate", is_flag=True, help="Rotate the specified secret")
def secrets(secret_type: str | None, rotate: bool) -> None:
    """Manage deployment secrets.

    Examples:
        mycelium deploy secrets
        mycelium deploy secrets postgres --rotate
    """
    from mycelium_onboarding.deployment.secrets import DeploymentSecrets, SecretsManager

    manager = ConfigManager()
    config = manager.load()

    secrets_mgr = SecretsManager(config.project_name)

    # Rotate secret if requested
    if rotate:
        if not secret_type:
            console.print("[red]Error: Specify secret type to rotate (postgres, redis, temporal)[/red]")
            raise SystemExit(1)

        try:
            with console.status(f"[bold green]Rotating {secret_type} secret..."):
                rotated_secrets = secrets_mgr.rotate_secret(secret_type)
            console.print(f"[green]✓[/green] Successfully rotated {secret_type} secret")
            console.print(
                "[yellow]Note: Update deployment with new secret to apply changes[/yellow]"
            )
            return
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise SystemExit(1)

    # Display secrets (masked)
    secrets_obj: DeploymentSecrets | None = secrets_mgr.load_secrets()

    if not secrets_obj:
        console.print("[yellow]No secrets found for this project.[/yellow]")
        console.print("Generate secrets with: [cyan]mycelium deploy generate[/cyan]")
        return

    table = Table(title="Deployment Secrets", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status")

    if secrets_obj.postgres_password:
        table.add_row("PostgreSQL", "[green]✓ Set[/green]")
    if secrets_obj.redis_password:
        table.add_row("Redis", "[green]✓ Set[/green]")
    if secrets_obj.temporal_admin_password:
        table.add_row("Temporal", "[green]✓ Set[/green]")

    console.print(table)
    console.print(
        f"\n[dim]Secrets stored at: {secrets_mgr.secrets_file}[/dim]"
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _display_config_table(cfg: MyceliumConfig) -> None:
    """Display configuration as a formatted table."""
    click.echo(click.style("Configuration", bold=True, underline=True))
    click.echo()

    # General
    click.echo(click.style("General:", bold=True))
    click.echo(f"  Project Name:      {cfg.project_name}")
    click.echo(f"  Schema Version:    {cfg.version}")
    click.echo()

    # Deployment
    click.echo(click.style("Deployment:", bold=True))
    click.echo(f"  Method:            {cfg.deployment.method.value}")
    click.echo(f"  Auto Start:        {cfg.deployment.auto_start}")
    click.echo(f"  Health Timeout:    {cfg.deployment.healthcheck_timeout}s")
    click.echo()

    # Services
    click.echo(click.style("Services:", bold=True))

    # Redis
    status = (
        click.style("ENABLED", fg="green")
        if cfg.services.redis.enabled
        else click.style("DISABLED", fg="red")
    )
    click.echo(f"  Redis:             {status}")
    if cfg.services.redis.enabled:
        click.echo(f"    Port:            {cfg.services.redis.port}")
        click.echo(f"    Persistence:     {cfg.services.redis.persistence}")
        click.echo(f"    Max Memory:      {cfg.services.redis.max_memory}")

    # PostgreSQL
    status = (
        click.style("ENABLED", fg="green")
        if cfg.services.postgres.enabled
        else click.style("DISABLED", fg="red")
    )
    click.echo(f"  PostgreSQL:        {status}")
    if cfg.services.postgres.enabled:
        click.echo(f"    Port:            {cfg.services.postgres.port}")
        click.echo(f"    Database:        {cfg.services.postgres.database}")
        click.echo(f"    Max Connections: {cfg.services.postgres.max_connections}")

    # Temporal
    status = (
        click.style("ENABLED", fg="green")
        if cfg.services.temporal.enabled
        else click.style("DISABLED", fg="red")
    )
    click.echo(f"  Temporal:          {status}")
    if cfg.services.temporal.enabled:
        click.echo(f"    UI Port:         {cfg.services.temporal.ui_port}")
        click.echo(f"    Frontend Port:   {cfg.services.temporal.frontend_port}")
        click.echo(f"    Namespace:       {cfg.services.temporal.namespace}")


def _get_nested_value(data: dict[str, Any], key: str) -> Any:
    """Get nested value from dictionary using dot notation."""
    keys = key.split(".")
    try:
        return reduce(lambda d, k: d[k], keys, data)
    except (KeyError, TypeError):
        raise KeyError(f"Key not found: {key}") from None


def _set_nested_value(data: dict[str, Any], key: str, value: Any) -> None:
    """Set nested value in dictionary using dot notation."""
    keys = key.split(".")
    for k in keys[:-1]:
        if k not in data:
            data[k] = {}
        data = data[k]
    data[keys[-1]] = value


def _parse_value(value: str) -> Any:
    """Parse string value to appropriate type."""
    # Try boolean
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

    # Return as string
    return value


# ============================================================================
# Main Entry Point (legacy compatibility)
# ============================================================================


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point with environment validation.

    Validates the environment before running commands (except for commands
    that don't require it like 'help' and 'setup-direnv').

    Args:
        argv: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Parse command
    if not argv or argv[0] in ["help", "-h", "--help"]:
        return cmd_help(argv)

    command = argv[0]
    args = argv[1:]

    # Handle init command via Click
    if command == "init":
        try:
            cli(["init"] + args, standalone_mode=False)
            return 0
        except click.ClickException as e:
            e.show()
            return 1
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

    # Handle config command via Click
    if command == "config":
        try:
            # Don't validate environment for config commands
            cli(["config"] + args, standalone_mode=False)
            return 0
        except click.ClickException as e:
            e.show()
            return 1
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

    # Handle detect command via Click
    if command == "detect":
        try:
            # Don't validate environment for detect commands
            cli(["detect"] + args, standalone_mode=False)
            return 0
        except click.ClickException as e:
            e.show()
            return 1
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

    # Handle deploy command via Click
    if command == "deploy":
        try:
            # Don't validate environment for deploy commands
            cli(["deploy"] + args, standalone_mode=False)
            return 0
        except click.ClickException as e:
            e.show()
            return 1
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

    # Validate environment before running commands (unless skipped)
    if command not in SKIP_VALIDATION_COMMANDS:
        try:
            validate_environment()
            logger.debug("Environment validation passed")
        except EnvironmentValidationError as e:
            print(f"Environment Validation Error:\n{e}", file=sys.stderr)
            print(
                "\nRun 'python -m mycelium_onboarding status' "
                "for detailed diagnostics.",
                file=sys.stderr,
            )
            return 1

    # Dispatch to command handlers
    commands = {
        "setup-direnv": cmd_setup_direnv,
        "status": cmd_status,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Run 'python -m mycelium_onboarding help' for usage.", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("Command failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
