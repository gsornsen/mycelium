# Source: deployment-reference.md
# Line: 376
# Valid syntax: True
# Has imports: False
# Has assignments: True

@dataclass
class DeploymentSecrets:
    project_name: str
    postgres_password: str | None = None
    redis_password: str | None = None
    temporal_admin_password: str | None = None
