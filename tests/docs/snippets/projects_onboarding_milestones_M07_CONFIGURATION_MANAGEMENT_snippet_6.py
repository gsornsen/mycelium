# Source: projects/onboarding/milestones/M07_CONFIGURATION_MANAGEMENT.md
# Line: 534
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli/config.py (continued)

@config.command()
@click.option(
    '--project',
    is_flag=True,
    help='Create project-local configuration'
)
@click.option(
    '--template',
    type=click.Choice(['minimal', 'docker', 'justfile', 'full']),
    default='minimal',
    help='Configuration template to use'
)
@click.option(
    '--force',
    is_flag=True,
    help='Overwrite existing configuration'
)
def init(project: bool, template: str, force: bool):
    """Initialize new configuration."""

    config_path = ConfigManager.get_config_path(prefer_project=project)

    if config_path.exists() and not force:
        console.print(f"[yellow]⚠ Configuration already exists: {config_path}[/yellow]")
        console.print(f"[dim]Use --force to overwrite[/dim]")
        raise click.Abort()

    # Create configuration from template
    config = _create_from_template(template)

    # Save configuration
    ConfigManager.save(config, project_local=project)

    console.print(Panel(
        f"[bold green]✓ Configuration initialized![/bold green]\n\n"
        f"Location: [cyan]{config_path}[/cyan]\n"
        f"Template: [cyan]{template}[/cyan]\n\n"
        f"Next steps:\n"
        f"1. Review configuration: [bold]/mycelium-configuration show[/bold]\n"
        f"2. Edit if needed: [bold]/mycelium-configuration edit[/bold]\n"
        f"3. Generate deployment: [bold]/mycelium-generate[/bold]",
        border_style="green"
    ))

def _create_from_template(template: str) -> MyceliumConfig:
    """Create configuration from template."""
    from mycelium_onboarding.config.schema import (
        MyceliumConfig,
        DeploymentConfig,
        ServicesConfig,
        RedisConfig,
        PostgresConfig,
        TemporalConfig,
        TaskQueueConfig,
    )

    if template == 'minimal':
        # Minimal: Redis + TaskQueue
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=False),
                temporal=TemporalConfig(enabled=False),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'docker':
        # Docker Compose with all services
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True, persistence=True),
                postgres=PostgresConfig(enabled=True),
                temporal=TemporalConfig(enabled=True),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'justfile':
        # Justfile with core services
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="justfile"),
            services=ServicesConfig(
                redis=RedisConfig(enabled=True),
                postgres=PostgresConfig(enabled=True),
                temporal=TemporalConfig(enabled=False),  # Complex for bare-metal
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    elif template == 'full':
        # All services with recommended settings
        return MyceliumConfig(
            project_name="mycelium",
            deployment=DeploymentConfig(method="docker-compose", healthcheck_timeout=90),
            services=ServicesConfig(
                redis=RedisConfig(
                    enabled=True,
                    persistence=True,
                    max_memory="512mb",
                ),
                postgres=PostgresConfig(
                    enabled=True,
                    max_connections=100,
                ),
                temporal=TemporalConfig(
                    enabled=True,
                ),
                taskqueue=TaskQueueConfig(enabled=True),
            ),
        )

    else:
        raise ValueError(f"Unknown template: {template}")