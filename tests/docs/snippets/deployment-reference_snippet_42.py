# Source: deployment-reference.md
# Line: 609
# Valid syntax: True
# Has imports: True
# Has assignments: True

from mycelium_onboarding.deployment.secrets import SecretsManager

# Initialize manager
manager = SecretsManager("my-app")

# Generate secrets
secrets = manager.generate_secrets(
    postgres=True,
    redis=True,
    temporal=True
)

# Save securely
manager.save_secrets(secrets)

# Load later
loaded = manager.load_secrets()
if loaded:
    env_vars = loaded.to_env_vars()
    print("Environment variables:", env_vars.keys())
