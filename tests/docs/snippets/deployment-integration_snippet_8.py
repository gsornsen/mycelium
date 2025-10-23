# Source: deployment-integration.md
# Line: 344
# Valid syntax: True
# Has imports: False
# Has assignments: True

# In your code
class CustomDeploymentMethod(str, Enum):
    DOCKER_SWARM = "docker-swarm"
    NOMAD = "nomad"
    LAMBDA = "lambda"
