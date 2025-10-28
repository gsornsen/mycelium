"""Wizard screen implementations using InquirerPy.

This module implements all 7 wizard screens using InquirerPy for interactive
prompts and rich for formatted console output. Each screen is implemented as
a method in the WizardScreens class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import NumberValidator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mycelium_onboarding.detection.orchestrator import DetectionSummary, detect_all

if TYPE_CHECKING:
    from mycelium_onboarding.wizard.flow import WizardState

__all__ = ["WizardScreens"]

console = Console()


def _validate_services_selection(result: Any) -> bool:
    """Validate that at least one service is selected.

    Args:
        result: User selection from checkbox

    Returns:
        True if valid, False otherwise (InquirerPy handles error message)
    """
    return len(result) > 0


class WizardScreens:
    """All wizard screen implementations.

    This class encapsulates all 7 wizard screens, providing methods for each
    screen that handle user interaction, validation, and state updates.

    Attributes:
        state: Current wizard state
    """

    def __init__(self, state: WizardState) -> None:
        """Initialize wizard screens with state.

        Args:
            state: Current wizard state
        """
        self.state = state

    def show_welcome(self) -> str:
        """Show welcome screen and return setup mode.

        Displays the welcome banner, explains what the wizard does, and
        prompts the user to choose between quick and custom setup.

        Returns:
            Setup mode: "quick" or "custom"

        Raises:
            SystemExit: If user confirms exit
        """
        # Display welcome banner
        console.print(
            Panel.fit(
                "[bold cyan]Welcome to Mycelium![/bold cyan]\n\n"
                "Mycelium is a distributed multi-agent coordination system\n"
                "for AI-powered workflows. This wizard will help you:\n\n"
                "• Detect available services (Docker, Redis, PostgreSQL)\n"
                "• Configure your environment\n"
                "• Generate deployment configurations\n"
                "• Set up your first project\n\n"
                "Estimated time: 2-5 minutes",
                title="Mycelium Setup Wizard",
            )
        )

        # Get setup mode choice
        setup_mode = inquirer.select(  # type: ignore[attr-defined]
            message="How would you like to proceed?",
            choices=[
                Choice(
                    value="quick",
                    name="Quick Setup (recommended for first-time users)",
                ),
                Choice(
                    value="custom",
                    name="Custom Setup (advanced configuration options)",
                ),
                Choice(value="exit", name="Exit wizard"),
            ],
            default="quick",
        ).execute()

        if setup_mode == "exit":
            confirm = inquirer.confirm(  # type: ignore[attr-defined]
                message="Are you sure you want to exit?", default=False
            ).execute()
            if confirm:
                raise SystemExit("Wizard cancelled by user")
            # Re-show welcome if user cancels exit
            return self.show_welcome()

        return str(setup_mode)

    def show_detection(self) -> DetectionSummary:
        """Show detection screen with progress and results.

        Runs service detection using M03 orchestrator, displays results in
        a formatted table, and stores results in wizard state.

        Returns:
            DetectionSummary with all detection results
        """
        console.print("\n[bold]Detecting Services...[/bold]\n")

        # Run detection with progress indicator
        with console.status("[bold green]Scanning your system..."):
            summary = detect_all()

        # Display detection results in table
        table = Table(title="Detection Results", show_header=True, header_style="bold cyan")
        table.add_column("Service", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Details")

        # Docker
        if summary.has_docker:
            table.add_row(
                "Docker",
                "[green]✓ Found[/green]",
                f"Version {summary.docker.version}",
            )
        else:
            table.add_row(
                "Docker",
                "[yellow]✗ Not Found[/yellow]",
                summary.docker.error_message or "Not installed",
            )

        # Redis
        if summary.has_redis:
            redis_ports = ", ".join(str(r.port) for r in summary.redis if r.available)
            table.add_row(
                "Redis",
                "[green]✓ Found[/green]",
                f"{len(summary.redis)} instance(s) on port(s) {redis_ports}",
            )
        else:
            table.add_row("Redis", "[yellow]✗ Not Found[/yellow]", "Not running")

        # PostgreSQL
        if summary.has_postgres:
            table.add_row(
                "PostgreSQL",
                "[green]✓ Found[/green]",
                f"{len(summary.postgres)} instance(s)",
            )
        else:
            table.add_row("PostgreSQL", "[yellow]✗ Not Found[/yellow]", "Not running")

        # Temporal
        if summary.has_temporal:
            table.add_row(
                "Temporal",
                "[green]✓ Found[/green]",
                f"Frontend: {summary.temporal.frontend_port}, UI: {summary.temporal.ui_port}",
            )
        else:
            table.add_row("Temporal", "[yellow]✗ Not Found[/yellow]", "Not running")

        # GPU
        if summary.has_gpu:
            gpu_details = f"{len(summary.gpu.gpus)} GPU(s)"
            if summary.gpu.gpus:
                gpu_details += f" - {summary.gpu.gpus[0].model}"
            table.add_row("GPU", "[green]✓ Found[/green]", gpu_details)
        else:
            table.add_row("GPU", "[yellow]✗ Not Found[/yellow]", "No GPU detected")

        console.print(table)
        console.print(f"\n[dim]Detection completed in {summary.detection_time:.2f}s[/dim]\n")

        # Store in state (cast to Any to avoid type errors with dict[str, Any])
        self.state.detection_results = summary  # type: ignore[assignment]

        # Ask if user wants to re-detect
        redetect = inquirer.confirm(  # type: ignore[attr-defined]
            message="Would you like to re-run detection?", default=False
        ).execute()

        if redetect:
            return self.show_detection()

        return summary

    def show_services(self) -> dict[str, bool]:
        """Show services selection screen.

        Displays checkboxes for service selection, pre-filled based on
        detection results. Prompts for service-specific configuration
        (database name, namespace) when applicable.

        Returns:
            Dictionary mapping service names to enabled status
        """
        console.print("\n[bold]Select Services to Enable[/bold]\n")

        # Pre-fill based on detection
        defaults = []
        if self.state.detection_results:
            detection = self.state.detection_results
            # Handle both DetectionSummary and dict types
            if isinstance(detection, DetectionSummary):
                if detection.has_redis:
                    defaults.append("redis")
                if detection.has_postgres:
                    defaults.append("postgres")
                if detection.has_temporal:
                    defaults.append("temporal")
            elif isinstance(detection, dict):
                # Fallback for dict type (should not happen in practice)
                if detection.get("has_redis"):
                    defaults.append("redis")
                if detection.get("has_postgres"):
                    defaults.append("postgres")
                if detection.get("has_temporal"):
                    defaults.append("temporal")

        # Multi-select with checkboxes
        services = inquirer.checkbox(  # type: ignore[attr-defined]
            message=("Select services to enable (use space to select, enter to confirm):"),
            choices=[
                Choice(value="redis", name="Redis - Message broker and caching"),
                Choice(value="postgres", name="PostgreSQL - Primary database"),
                Choice(value="temporal", name="Temporal - Workflow orchestration"),
            ],
            default=defaults,
            validate=_validate_services_selection,
            invalid_message="Please select at least one service",
        ).execute()

        # Convert to dict
        services_enabled = {
            "redis": "redis" in services,
            "postgres": "postgres" in services,
            "temporal": "temporal" in services,
        }

        # Configure service-specific settings
        if services_enabled["postgres"]:
            db_name = inquirer.text(  # type: ignore[attr-defined]
                message="PostgreSQL database name:",
                default=self.state.project_name.lower().replace("-", "_") if self.state.project_name else "mycelium",
                validate=lambda text: len(text) > 0 and text.replace("_", "").replace("-", "").isalnum(),
                invalid_message=("Database name must be alphanumeric with underscores/hyphens"),
            ).execute()
            self.state.postgres_database = str(db_name)

        if services_enabled["temporal"]:
            namespace = inquirer.text(  # type: ignore[attr-defined]
                message="Temporal namespace:",
                default="default",
                validate=lambda text: len(text) > 0,
                invalid_message="Namespace cannot be empty",
            ).execute()
            self.state.temporal_namespace = str(namespace)

        self.state.services_enabled = services_enabled
        return services_enabled

    def show_deployment(self) -> str:
        """Show deployment method selection screen.

        Prompts user to select deployment method (Docker Compose, Kubernetes,
        or systemd) and whether to auto-start services on boot.

        Returns:
            Selected deployment method
        """
        console.print("\n[bold]Deployment Configuration[/bold]\n")

        # Determine available deployment methods based on detection
        choices = []

        # Check if Docker is available
        has_docker = False
        if self.state.detection_results:
            detection = self.state.detection_results
            if isinstance(detection, DetectionSummary):
                has_docker = detection.has_docker
            elif isinstance(detection, dict):
                has_docker = bool(detection.get("has_docker"))

        if has_docker:
            choices.append(
                Choice(
                    value="docker-compose",
                    name="Docker Compose - Best for development and small deployments",
                )
            )
            choices.append(
                Choice(
                    value="kubernetes",
                    name="Kubernetes - Best for production and scalability",
                )
            )
        else:
            console.print("[yellow]⚠ Docker not detected. Some deployment options may be limited.[/yellow]\n")

        choices.append(Choice(value="systemd", name="systemd - Native Linux services"))

        deployment_method = inquirer.select(  # type: ignore[attr-defined]
            message="Select deployment method:",
            choices=choices,
            default="docker-compose" if has_docker else "systemd",
        ).execute()

        self.state.deployment_method = str(deployment_method)

        # Auto-start option
        auto_start = inquirer.confirm(  # type: ignore[attr-defined]
            message="Auto-start services on system boot?", default=True
        ).execute()
        self.state.auto_start = bool(auto_start)

        return str(deployment_method)

    def show_advanced(self) -> None:
        """Show advanced configuration screen (Custom mode only).

        Prompts for advanced settings including data persistence and
        service-specific ports. Only shown in custom setup mode.
        """
        console.print("\n[bold]Advanced Configuration[/bold]\n")

        # Persistence option
        enable_persistence = inquirer.confirm(  # type: ignore[attr-defined]
            message="Enable data persistence for databases?", default=True
        ).execute()
        self.state.enable_persistence = bool(enable_persistence)

        # Service-specific ports (if services enabled)
        if self.state.services_enabled.get("redis"):
            redis_port = inquirer.number(  # type: ignore[attr-defined]
                message="Redis port:",
                default=6379,
                min_allowed=1024,
                max_allowed=65535,
                validate=NumberValidator(),
            ).execute()
            self.state.redis_port = int(redis_port)

        if self.state.services_enabled.get("postgres"):
            postgres_port = inquirer.number(  # type: ignore[attr-defined]
                message="PostgreSQL port:",
                default=5432,
                min_allowed=1024,
                max_allowed=65535,
                validate=NumberValidator(),
            ).execute()
            self.state.postgres_port = int(postgres_port)

    def show_review(self) -> str:
        """Show review screen with summary and confirmation.

        Displays a summary table of all configuration choices and prompts
        user to confirm, edit, or cancel.

        Returns:
            Action: "confirm", "edit:<step>", or "cancel"
        """
        console.print("\n[bold]Review Your Configuration[/bold]\n")

        # Create summary table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("Project Name", self.state.project_name or "[dim]Not set[/dim]")
        table.add_row("Deployment Method", self.state.deployment_method)
        table.add_row("Auto-start", "Yes" if self.state.auto_start else "No")

        # Services
        enabled_services = [k for k, v in self.state.services_enabled.items() if v]
        table.add_row(
            "Enabled Services",
            ", ".join(enabled_services) if enabled_services else "[dim]None[/dim]",
        )

        if self.state.services_enabled.get("redis"):
            table.add_row("  Redis Port", str(self.state.redis_port))

        if self.state.services_enabled.get("postgres"):
            table.add_row("  PostgreSQL Port", str(self.state.postgres_port))
            table.add_row("  PostgreSQL Database", self.state.postgres_database)

        if self.state.services_enabled.get("temporal"):
            table.add_row("  Temporal Namespace", self.state.temporal_namespace)

        table.add_row(
            "Data Persistence",
            "Enabled" if self.state.enable_persistence else "Disabled",
        )

        console.print(table)

        # Confirmation
        action = inquirer.select(  # type: ignore[attr-defined]
            message="What would you like to do?",
            choices=[
                Choice(value="confirm", name="Confirm and create configuration"),
                Choice(value="edit", name="Edit a setting"),
                Choice(value="cancel", name="Cancel wizard"),
            ],
            default="confirm",
        ).execute()

        if action == "edit":
            # Import here to avoid circular import
            from mycelium_onboarding.wizard.flow import WizardStep

            # Show which step to edit
            edit_choices = [
                Choice(value=WizardStep.SERVICES, name="Services"),
                Choice(value=WizardStep.DEPLOYMENT, name="Deployment"),
            ]

            # Only show advanced if in custom mode or resumed
            if self.state.setup_mode == "custom" or self.state.resumed:
                edit_choices.append(Choice(value=WizardStep.ADVANCED, name="Advanced Settings"))

            edit_step = inquirer.select(  # type: ignore[attr-defined]
                message="Which section would you like to edit?",
                choices=edit_choices,
            ).execute()
            return f"edit:{edit_step.value}"

        return str(action)

    def show_complete(self, config_path: str) -> None:
        """Show completion screen with success message.

        Displays success message with next steps and the path to the
        generated configuration file.

        Args:
            config_path: Path to the saved configuration file
        """
        console.print(
            Panel.fit(
                "[bold green]✓ Configuration Complete![/bold green]\n\n"
                f"Your configuration has been saved to:\n"
                f"[cyan]{config_path}[/cyan]\n\n"
                "[bold]Next Steps:[/bold]\n"
                "1. Review your configuration: [cyan]mycelium config show[/cyan]\n"
                "2. Start services: [cyan]mycelium deploy start[/cyan]\n"
                "3. Check status: [cyan]mycelium status[/cyan]\n\n"
                "For help: [cyan]mycelium --help[/cyan]",
                title="Setup Complete",
                border_style="green",
            )
        )
