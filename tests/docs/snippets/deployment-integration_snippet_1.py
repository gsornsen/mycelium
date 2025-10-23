# Source: deployment-integration.md
# Line: 20
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    DeploymentMethod,
)


def setup_deployment(project_name: str, services: dict) -> bool:
    """Set up deployment for a project."""
    try:
        # Create configuration
        config = MyceliumConfig(
            project_name=project_name,
            services=services,
            deployment={"method": "docker-compose"}
        )

        # Generate deployment
        generator = DeploymentGenerator(config)
        result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

        if result.success:
            print(f"Deployment generated at: {result.output_dir}")
            return True
        print(f"Errors: {result.errors}")
        return False

    except Exception as e:
        print(f"Failed to generate deployment: {e}")
        return False

# Usage
success = setup_deployment(
    project_name="my-microservice",
    services={
        "redis": {"enabled": True, "port": 6379},
        "postgres": {"enabled": True}
    }
)
