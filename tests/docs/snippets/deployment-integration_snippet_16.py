# Source: deployment-integration.md
# Line: 766
# Valid syntax: True
# Has imports: False
# Has assignments: True

class DeploymentFactory:
    """Factory for creating deployments."""

    @staticmethod
    def create_development(project_name: str) -> GenerationResult:
        """Create development deployment."""
        config = MyceliumConfig(
            project_name=project_name,
            services={
                "redis": {"enabled": True, "max_memory": "128mb"},
                "postgres": {"enabled": True, "max_connections": 50}
            },
            deployment={"method": "docker-compose"}
        )

        generator = DeploymentGenerator(config)
        return generator.generate(DeploymentMethod.DOCKER_COMPOSE)

    @staticmethod
    def create_production(project_name: str) -> GenerationResult:
        """Create production deployment."""
        config = MyceliumConfig(
            project_name=project_name,
            services={
                "redis": {"enabled": True, "max_memory": "2gb"},
                "postgres": {"enabled": True, "max_connections": 500}
            },
            deployment={
                "method": "kubernetes",
                "healthcheck_timeout": 120
            }
        )

        generator = DeploymentGenerator(config)
        return generator.generate(DeploymentMethod.KUBERNETES)

# Usage
dev_result = DeploymentFactory.create_development("my-app")
prod_result = DeploymentFactory.create_production("my-app")