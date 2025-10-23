# Source: projects/onboarding/milestones/M04_INTERACTIVE_ONBOARDING.md
# Line: 142
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/wizard/screens.py
"""Individual wizard screens using InquirerPy."""

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def show_welcome_screen(detection_results: 'DetectionResults') -> None:
    """Display welcome screen with system detection summary."""
    console.clear()

    # Create detection summary table
    table = Table(title="🔍 System Detection Results")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # Add detection results
    table.add_row(
        "Docker",
        "✓ Available" if detection_results.docker.available else "✗ Not Found",
        detection_results.docker.version or "N/A"
    )
    table.add_row(
        "Redis",
        "✓ Running" if detection_results.redis.reachable else "○ Available",
        f"{detection_results.redis.host}:{detection_results.redis.port}"
    )
    # ... add other services ...

    console.print(table)
    console.print("\n")
    console.print(Panel(
        "[bold]Welcome to Mycelium Onboarding![/bold]\n\n"
        "This wizard will guide you through setting up your multi-agent "
        "coordination infrastructure. We've detected your system and will "
        "recommend the best configuration.",
        border_style="blue"
    ))

    inquirer.confirm(
        message="Ready to begin?",
        default=True,
    ).execute()

def prompt_service_selection(detection_results: 'DetectionResults') -> set[str]:
    """Prompt user to select services to enable."""
    console.print("\n[bold cyan]Service Selection[/bold cyan]")
    console.print("Select which coordination services to enable:\n")

    choices = [
        Choice(
            value="redis",
            name="Redis - Pub/Sub messaging and state management",
            enabled=detection_results.redis.available,
        ),
        Choice(
            value="postgres",
            name="PostgreSQL - Persistent data storage",
            enabled=detection_results.postgres.available,
        ),
        Choice(
            value="temporal",
            name="Temporal - Workflow orchestration",
            enabled=detection_results.temporal.available,
        ),
        Choice(
            value="taskqueue",
            name="TaskQueue - Task distribution (MCP)",
            enabled=True,  # Always available via MCP
        ),
    ]

    selected = inquirer.checkbox(
        message="Select services (Space to toggle, Enter to confirm):",
        choices=choices,
        validate=lambda result: len(result) > 0,
        invalid_message="You must select at least one service",
    ).execute()

    return set(selected)

def prompt_deployment_method(has_docker: bool) -> str:
    """Prompt user to choose deployment method."""
    console.print("\n[bold cyan]Deployment Method[/bold cyan]")

    if not has_docker:
        console.print(
            "[yellow]⚠ Docker not detected. Defaulting to Justfile deployment.[/yellow]\n"
        )
        return "justfile"

    choices = [
        Choice(
            value="docker-compose",
            name="Docker Compose (Recommended) - Containerized services with automatic dependency management",
        ),
        Choice(
            value="justfile",
            name="Justfile - Bare-metal deployment with manual service management",
        ),
    ]

    method = inquirer.select(
        message="Choose deployment method:",
        choices=choices,
        default="docker-compose",
    ).execute()

    return method

def prompt_project_metadata() -> dict[str, str]:
    """Prompt for project name and description."""
    console.print("\n[bold cyan]Project Metadata[/bold cyan]\n")

    name = inquirer.text(
        message="Project name:",
        default="mycelium",
        validate=lambda x: x.isidentifier(),
        invalid_message="Must be valid Python identifier (letters, numbers, underscores)",
    ).execute()

    description = inquirer.text(
        message="Project description (optional):",
        default="Multi-agent coordination system",
    ).execute()

    return {"name": name, "description": description}

def show_configuration_review(config: 'MyceliumConfig') -> bool:
    """Display configuration review and confirm."""
    console.print("\n[bold cyan]Configuration Review[/bold cyan]\n")

    # Create configuration summary
    table = Table(title="Final Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config.project_name)
    table.add_row("Deployment Method", config.deployment.method)
    table.add_row("Services Enabled", ", ".join([
        s for s in ["redis", "postgres", "temporal", "taskqueue"]
        if getattr(config.services, s).enabled
    ]))

    console.print(table)
    console.print("\n")

    confirmed = inquirer.confirm(
        message="Save this configuration?",
        default=True,
    ).execute()

    return confirmed
