# Source: deployment-reference.md
# Line: 221
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Use default directory
manager = SecretsManager("my-app")

# Use custom directory
manager = SecretsManager("my-app", secrets_dir=Path("/secure/location"))