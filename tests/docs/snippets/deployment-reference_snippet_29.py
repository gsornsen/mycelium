# Source: deployment-reference.md
# Line: 442
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import generate_env_file

secrets = manager.load_secrets()
generate_env_file(secrets, Path(".env"))
