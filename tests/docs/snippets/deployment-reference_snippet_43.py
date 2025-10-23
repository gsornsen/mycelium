# Source: deployment-reference.md
# Line: 634
# Valid syntax: True
# Has imports: True
# Has assignments: True

from pathlib import Path

config = MyceliumConfig(project_name="multi-deploy")

# Generate Docker Compose
generator = DeploymentGenerator(config, output_dir=Path("./compose"))
compose_result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

# Generate Kubernetes
generator = DeploymentGenerator(config, output_dir=Path("./k8s"))
k8s_result = generator.generate(DeploymentMethod.KUBERNETES)

# Generate systemd
generator = DeploymentGenerator(config, output_dir=Path("./systemd"))
systemd_result = generator.generate(DeploymentMethod.SYSTEMD)
