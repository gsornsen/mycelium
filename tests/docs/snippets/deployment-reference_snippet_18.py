# Source: deployment-reference.md
# Line: 290
# Valid syntax: True
# Has imports: False
# Has assignments: True

secrets = manager.generate_secrets(postgres=True)

try:
    manager.save_secrets(secrets)
    print("Secrets saved securely")
except SecretsError as e:
    print(f"Failed to save: {e}")
