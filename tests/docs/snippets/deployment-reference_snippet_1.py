# Source: deployment-reference.md
# Line: 19
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    DeploymentMethod,
)

config = MyceliumConfig(project_name="my-app")
generator = DeploymentGenerator(config)
result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)
