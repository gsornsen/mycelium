# Source: wizard-integration.md
# Line: 299
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.wizard.screens import WizardScreens
from mycelium_onboarding.wizard.flow import WizardStep
from InquirerPy import inquirer
from rich.console import Console

console = Console()

class ExtendedWizardScreens(WizardScreens):
    """Extended wizard screens with custom functionality."""

    def show_monitoring(self) -> dict[str, any]:
        """Show custom monitoring configuration screen."""
        console.print("\n[bold]Monitoring Configuration[/bold]\n")

        # Monitoring provider selection
        provider = inquirer.select(
            message="Select monitoring provider:",
            choices=[
                {"value": "prometheus", "name": "Prometheus + Grafana"},
                {"value": "datadog", "name": "Datadog"},
                {"value": "none", "name": "No monitoring"},
            ],
            default="prometheus",
        ).execute()

        config = {"provider": provider}

        if provider == "prometheus":
            # Prometheus-specific config
            port = inquirer.number(
                message="Prometheus port:",
                default=9090,
                min_allowed=1024,
                max_allowed=65535,
            ).execute()
            config["prometheus_port"] = port

        elif provider == "datadog":
            # Datadog-specific config
            api_key = inquirer.secret(
                message="Datadog API key:",
            ).execute()
            config["datadog_api_key"] = api_key

        return config

# Usage
state = WizardState()
screens = ExtendedWizardScreens(state)
monitoring_config = screens.show_monitoring()