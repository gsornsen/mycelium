# Source: deployment-reference.md
# Line: 578
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment.generator import (
    DeploymentGenerator,
    DeploymentMethod,
)

# Create configuration
config = MyceliumConfig(
    project_name="my-app",
    services={
        "redis": {"enabled": True, "port": 6379},
        "postgres": {"enabled": True, "database": "mydb"}
    },
    deployment={"method": "docker-compose"}
)

# Generate deployment
generator = DeploymentGenerator(config)
result = generator.generate(DeploymentMethod.DOCKER_COMPOSE)

if result.success:
    print(f"Generated files in: {result.output_dir}")
    for file in result.files_generated:
        print(f"  - {file}")
else:
    print(f"Failed: {result.errors}")
