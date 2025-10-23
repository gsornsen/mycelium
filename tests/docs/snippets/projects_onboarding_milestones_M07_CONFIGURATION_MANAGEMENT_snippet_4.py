# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 385
# Valid syntax: True
# Has imports: False
# Has assignments: True

# mycelium_onboarding/cli/config.py (continued)

@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Validate project-local configuration'
)
@click.option(
    '--strict',
    is_flag=True,
    help='Enable strict validation (warnings as errors)'
)
def validate(project: bool, strict: bool):
    """Validate configuration file."""

    try:
        config_path = ConfigManager.get_config_path(prefer_project=project)

        if not config_path.exists():
            console.print(f"[yellow]⚠ Configuration file not found: {config_path}[/yellow]")
            raise click.Abort()

        # Load and validate
        console.print(f"[cyan]Validating: {config_path}[/cyan]\n")

        config = ConfigManager.load_from_path(config_path)

        # Run additional checks
        warnings = _check_configuration_warnings(config)

        if warnings:
            console.print("[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  ⚠ {warning}")

            if strict:
                console.print("\n[red]✗ Validation failed (strict mode)[/red]")
                raise click.ClickException("Configuration has warnings")

        # Success
        console.print("\n[green]✓ Configuration is valid[/green]")

        # Show summary
        _show_validation_summary(config)

    except Exception as e:
        console.print("\n[red]✗ Validation failed:[/red]")
        console.print(f"  {e}")
        raise click.ClickException("Invalid configuration")

def _check_configuration_warnings(config: MyceliumConfig) -> list[str]:
    """Check for configuration warnings (non-fatal issues)."""
    warnings = []

    # Check for deprecated settings
    # (Add checks as configuration evolves)

    # Check for unusual port numbers
    if config.services.redis.enabled:
        if config.services.redis.port < 1024:
            warnings.append("Redis port < 1024 requires root privileges")

    # Check for missing recommended settings
    if config.services.redis.enabled and not config.services.redis.persistence:
        warnings.append("Redis persistence disabled (data loss on restart)")

    return warnings

def _show_validation_summary(config: MyceliumConfig):
    """Show validation summary."""
    table = Table(title="Configuration Summary", show_header=False)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Version", config.version)
    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)

    enabled_services = []
    if config.services.redis.enabled:
        enabled_services.append("Redis")
    if config.services.postgres.enabled:
        enabled_services.append("PostgreSQL")
    if config.services.temporal.enabled:
        enabled_services.append("Temporal")
    if config.services.taskqueue.enabled:
        enabled_services.append("TaskQueue")

    table.add_row("Enabled Services", ", ".join(enabled_services))

    console.print(table)
