# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 619
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli.py
import click
from mycelium_onboarding.env_validator import validate_environment

@click.group()
def cli():
    """Mycelium onboarding CLI."""
    # Validate environment before running any commands
    try:
        validate_environment()
    except EnvironmentValidationError as e:
        click.echo(str(e), err=True)
        raise click.Abort()


@cli.command()
def status():
    """Show environment status."""
    from mycelium_onboarding.env_validator import get_environment_info

    info = get_environment_info()
    click.echo("Mycelium Environment Status:")
    for var, value in info.items():
        status = "✓" if value else "✗"
        click.echo(f"  {status} {var}: {value or '(not set)'}")