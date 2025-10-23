# Source: projects/onboarding/milestones/M02_CONFIGURATION_SYSTEM.md
# Line: 589
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/config_commands.py
"""CLI commands for configuration management."""

import click
import yaml
from pathlib import Path

from mycelium_onboarding.config.manager import ConfigManager, ConfigValidationError
from mycelium_onboarding.config.schema import MyceliumConfig


@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass


@config_group.command(name="show")
@click.option(
    "--project-local",
    is_flag=True,
    help="Show project-local configuration only"
)
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format"
)
def show_config(project_local: bool, format: str):
    """Show current configuration."""
    try:
        config = ConfigManager.load(prefer_project=project_local)

        if format == "yaml":
            output = yaml.dump(
                config.model_dump(mode="json"),
                default_flow_style=False,
                sort_keys=False
            )
        else:  # json
            output = config.model_dump_json(indent=2)

        click.echo(output)

    except ConfigValidationError as e:
        click.echo(f"❌ Configuration invalid: {e}", err=True)
        raise click.Abort()


@config_group.command(name="validate")
@click.argument("config_file", type=click.Path(exists=True), required=False)
def validate_config(config_file: Optional[str]):
    """Validate configuration file.

    If CONFIG_FILE not provided, validates current configuration.
    """
    try:
        if config_file:
            config = ConfigManager.load_from_path(Path(config_file))
            click.echo(f"✓ Configuration valid: {config_file}")
        else:
            config = ConfigManager.load()
            click.echo("✓ Configuration valid")

        # Show summary
        enabled_services = [
            name for name, svc in config.services.model_dump().items()
            if svc.get("enabled", False)
        ]
        click.echo(f"\nDeployment: {config.deployment.method.value}")
        click.echo(f"Services: {', '.join(enabled_services)}")

    except ConfigValidationError as e:
        click.echo(f"❌ Configuration invalid:\n{e}", err=True)
        raise click.Abort()
    except FileNotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()


@config_group.command(name="location")
@click.option(
    "--project-local",
    is_flag=True,
    help="Show project-local location"
)
def show_location(project_local: bool):
    """Show configuration file location."""
    location = ConfigManager.get_config_location(prefer_project=project_local)
    exists = location.exists()

    status = "✓" if exists else "✗"
    click.echo(f"{status} {location}")

    if not exists:
        click.echo("  (file does not exist)")


@config_group.command(name="init")
@click.option(
    "--project-local",
    is_flag=True,
    help="Create project-local configuration"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration"
)
def init_config(project_local: bool, force: bool):
    """Initialize configuration with defaults."""
    location = ConfigManager.get_config_location(prefer_project=project_local)

    if location.exists() and not force:
        click.echo(f"❌ Configuration already exists: {location}", err=True)
        click.echo("Use --force to overwrite")
        raise click.Abort()

    # Create default configuration
    config = MyceliumConfig()
    saved_path = ConfigManager.save(config, project_local=project_local)

    click.echo(f"✓ Created configuration: {saved_path}")