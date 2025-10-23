# Source: deployment-reference.md
# Line: 405
# Valid syntax: True
# Has imports: True
# Has assignments: True

secrets = DeploymentSecrets(
    project_name="my-app",
    postgres_password="secret123",
    redis_password="secret456"
)

env_vars = secrets.to_env_vars()
# {
#     "POSTGRES_PASSWORD": "secret123",
#     "REDIS_PASSWORD": "secret456"
# }

# Use in deployment
import os

for key, value in env_vars.items():
    os.environ[key] = value
