# Source: wizard-integration.md
# Line: 589
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.schema import DeploymentMethod
from enum import Enum

# Extend DeploymentMethod enum (in config/schema.py)
class ExtendedDeploymentMethod(str, Enum):
    """Extended deployment methods."""
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"
    NOMAD = "nomad"  # New method
    DOCKER_SWARM = "docker-swarm"  # New method

# Add to validator
def validate_deployment_method_extended(method: str) -> bool:
    """Validate extended deployment methods."""
    valid = [m.value for m in ExtendedDeploymentMethod]
    return method in valid

# Update screens to show new options
def show_extended_deployment(self) -> str:
    """Show deployment screen with extended options."""
    choices = [
        {"value": "docker-compose", "name": "Docker Compose"},
        {"value": "kubernetes", "name": "Kubernetes"},
        {"value": "systemd", "name": "systemd"},
        {"value": "nomad", "name": "HashiCorp Nomad"},
        {"value": "docker-swarm", "name": "Docker Swarm"},
    ]

    deployment = inquirer.select(
        message="Select deployment method:",
        choices=choices,
    ).execute()

    return deployment