# Source: deployment-reference.md
# Line: 171
# Valid syntax: True
# Has imports: False
# Has assignments: True

class DeploymentMethod(str, Enum):
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"
