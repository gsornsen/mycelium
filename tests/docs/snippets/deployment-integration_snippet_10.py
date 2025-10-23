# Source: deployment-integration.md
# Line: 405
# Valid syntax: True
# Has imports: False
# Has assignments: True

config = MyceliumConfig(project_name="swarm-app")
generator = ExtendedDeploymentGenerator(config)
result = generator.generate("docker-swarm")