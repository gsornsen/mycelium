# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 462
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/wizard/persistence.py
"""Configuration persistence after wizard completion."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from mycelium_onboarding.config.manager import ConfigManager
from mycelium_onboarding.config.schema import MyceliumConfig

console = Console()

def save_configuration(
    config: MyceliumConfig,
    project_local: bool = False
) -> tuple[bool, Optional[Path]]:
    """
    Save configuration using ConfigManager.

    Args:
        config: Configuration to save
        project_local: If True, save to project dir; else user config

    Returns:
        (success, config_path) tuple
    """
    try:
        config_path = ConfigManager.save(config, project_local=project_local)

        console.print(Panel(
            f"[bold green]✓ Configuration saved successfully![/bold green]\n\n"
            f"Location: [cyan]{config_path}[/cyan]\n\n"
            f"Next steps:\n"
            f"1. Review configuration: [bold]cat {config_path}[/bold]\n"
            f"2. Generate deployment: [bold]/mycelium-generate[/bold]\n"
            f"3. Start services: [bold]just up[/bold] or [bold]docker-compose up[/bold]",
            border_style="green",
            title="Success"
        ))

        return True, config_path

    except Exception as e:
        console.print(Panel(
            f"[bold red]✗ Failed to save configuration[/bold red]\n\n"
            f"Error: {e}\n\n"
            f"Please check permissions and try again.",
            border_style="red",
            title="Error"
        ))

        return False, None

def resume_from_previous() -> Optional[MyceliumConfig]:
    """
    Attempt to load previous configuration for resume.

    Returns:
        Previous config if found, else None
    """
    try:
        config = ConfigManager.load()

        console.print(Panel(
            f"[bold yellow]Previous configuration found![/bold yellow]\n\n"
            f"Project: {config.project_name}\n"
            f"Deployment: {config.deployment.method}\n\n"
            f"Would you like to resume or start fresh?",
            border_style="yellow",
            title="Resume Onboarding"
        ))

        from InquirerPy import inquirer
        choice = inquirer.select(
            message="Choose action:",
            choices=["Resume", "Start Fresh", "Cancel"],
        ).execute()

        if choice == "Resume":
            return config
        if choice == "Cancel":
            return None

        # Start fresh - return None
        return None

    except FileNotFoundError:
        # No previous config - this is expected
        return None
