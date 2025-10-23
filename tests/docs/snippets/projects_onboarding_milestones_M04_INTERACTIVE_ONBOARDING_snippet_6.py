# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 636
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/cli.py
"""CLI entry point for onboarding command."""

import asyncio
import click
from rich.console import Console

from mycelium_onboarding.wizard.integration import run_wizard_with_detection
from mycelium_onboarding.wizard.persistence import save_configuration, resume_from_previous

console = Console()

@click.command()
@click.option(
    '--project-local',
    is_flag=True,
    help='Save configuration to project directory'
)
@click.option(
    '--force',
    is_flag=True,
    help='Skip resume prompt and start fresh'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Re-run service detection'
)
@click.option(
    '--non-interactive',
    is_flag=True,
    help='Run in non-interactive mode using defaults'
)
def onboard(project_local: bool, force: bool, no_cache: bool, non_interactive: bool):
    """Launch Mycelium onboarding wizard."""

    # Check for resume unless --force
    if not force and not non_interactive:
        previous_config = resume_from_previous()
        if previous_config is not None:
            # User chose to cancel
            return

    # Run wizard
    config = asyncio.run(run_wizard_with_detection(use_cache=not no_cache))

    if config is None:
        # User cancelled during wizard
        console.print("[yellow]Onboarding cancelled.[/yellow]")
        return

    # Save configuration
    success, config_path = save_configuration(config, project_local=project_local)

    if not success:
        raise click.ClickException("Failed to save configuration")

if __name__ == '__main__':
    onboard()