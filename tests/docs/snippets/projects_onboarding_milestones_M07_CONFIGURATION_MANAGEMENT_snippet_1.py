# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 64
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/config.py
"""Configuration management CLI commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
import yaml
import json

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig

console = Console()

@click.group()
def config():
    """Manage Mycelium configuration."""
    pass

@config.command()
@click.option(
    '--format',
    type=click.Choice(['yaml', 'json', 'table'], case_sensitive=False),
    default='table',
    help='Output format'
)
@click.option(
    '--path',
    is_flag=True,
    help='Show configuration file path'
)
@click.option(
    '--project',
    is_flag=True,
    help='Use project-local configuration'
)
def show(format: str, path: bool, project: bool):
    """Display current configuration."""

    try:
        # Load configuration
        config = ConfigManager.load(prefer_project=project)
        config_path = ConfigManager.get_config_path(prefer_project=project)

        if path:
            # Just show path
            console.print(f"[cyan]{config_path}[/cyan]")
            return

        # Display based on format
        if format == 'table':
            _show_table_format(config)
        elif format == 'yaml':
            _show_yaml_format(config)
        elif format == 'json':
            _show_json_format(config)

        # Show file location
        console.print(f"\n[dim]Configuration: {config_path}[/dim]")

    except FileNotFoundError:
        console.print("[yellow]⚠ No configuration found. Run /mycelium-onboarding to create one.[/yellow]")
        raise click.Abort()

def _show_table_format(config: MyceliumConfig):
    """Display configuration as formatted table."""

    # Project Info
    table = Table(title="Project Configuration", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)

    console.print(table)
    console.print()

    # Services
    table = Table(title="Enabled Services")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Configuration", style="white")

    if config.services.redis.enabled:
        table.add_row(
            "Redis",
            "✓ Enabled",
            f"Port: {config.services.redis.port}, Persistence: {config.services.redis.persistence}"
        )

    if config.services.postgres.enabled:
        table.add_row(
            "PostgreSQL",
            "✓ Enabled",
            f"Port: {config.services.postgres.port}"
        )

    if config.services.temporal.enabled:
        table.add_row(
            "Temporal",
            "✓ Enabled",
            f"Port: {config.services.temporal.frontend_port}"
        )

    if config.services.taskqueue.enabled:
        table.add_row(
            "TaskQueue",
            "✓ Enabled",
            "MCP Server"
        )

    console.print(table)

def _show_yaml_format(config: MyceliumConfig):
    """Display configuration as YAML with syntax highlighting."""
    config_dict = config.model_dump()

    # Mask sensitive data
    config_dict = _mask_sensitive_data(config_dict)

    yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)

def _show_json_format(config: MyceliumConfig):
    """Display configuration as JSON."""
    config_dict = config.model_dump()

    # Mask sensitive data
    config_dict = _mask_sensitive_data(config_dict)

    json_str = json.dumps(config_dict, indent=2)

    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)

def _mask_sensitive_data(config_dict: dict) -> dict:
    """Mask sensitive values like passwords."""
    sensitive_keys = {'password', 'secret', 'api_key', 'token'}

    def mask_recursive(obj):
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if any(s in k.lower() for s in sensitive_keys) else mask_recursive(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        else:
            return obj

    return mask_recursive(config_dict)