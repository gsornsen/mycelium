# Source: deployment-integration.md
# Line: 812
# Valid syntax: True
# Has imports: False
# Has assignments: True

class DeploymentBuilder:
    """Builder for deployment configurations."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.services = {}
        self.deployment_config = {}

    def with_redis(self, port: int = 6379, **kwargs) -> 'DeploymentBuilder':
        """Add Redis service."""
        self.services["redis"] = {"enabled": True, "port": port, **kwargs}
        return self

    def with_postgres(self, database: str = "mydb", **kwargs) -> 'DeploymentBuilder':
        """Add PostgreSQL service."""
        self.services["postgres"] = {
            "enabled": True,
            "database": database,
            **kwargs
        }
        return self

    def with_method(self, method: str) -> 'DeploymentBuilder':
        """Set deployment method."""
        self.deployment_config["method"] = method
        return self

    def build(self) -> MyceliumConfig:
        """Build configuration."""
        return MyceliumConfig(
            project_name=self.project_name,
            services=self.services,
            deployment=self.deployment_config
        )

    def generate(self) -> GenerationResult:
        """Build and generate deployment."""
        config = self.build()
        generator = DeploymentGenerator(config)
        return generator.generate(
            DeploymentMethod(self.deployment_config.get("method", "docker-compose"))
        )

# Usage
result = (DeploymentBuilder("my-app")
    .with_redis(port=6380, max_memory="512mb")
    .with_postgres(database="production")
    .with_method("kubernetes")
    .generate())