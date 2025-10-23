# Source: deployment-reference.md
# Line: 180
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.generator import DeploymentMethod

# Use enum values
method = DeploymentMethod.KUBERNETES
print(method.value)  # "kubernetes"

# Create from string
method = DeploymentMethod("docker-compose")

# Compare
if method == DeploymentMethod.DOCKER_COMPOSE:
    print("Using Docker Compose")
