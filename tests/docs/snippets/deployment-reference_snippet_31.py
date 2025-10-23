# Source: deployment-reference.md
# Line: 459
# Valid syntax: True
# Has imports: True
# Has assignments: False

from mycelium_onboarding.deployment.secrets import SecretsError

try:
    manager.save_secrets(secrets)
except SecretsError as e:
    print(f"Secrets operation failed: {e}")
    # Handle error...
