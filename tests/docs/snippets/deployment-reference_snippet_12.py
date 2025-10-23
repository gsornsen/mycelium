# Source: deployment-reference.md
# Line: 201
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import SecretsManager

manager = SecretsManager("my-project")
secrets = manager.generate_secrets(postgres=True, redis=True)
manager.save_secrets(secrets)