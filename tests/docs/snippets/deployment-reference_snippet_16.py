# Source: deployment-reference.md
# Line: 255
# Valid syntax: True
# Has imports: False
# Has assignments: True

# Generate secrets for PostgreSQL and Redis
secrets = manager.generate_secrets(postgres=True, redis=True)

# Preserve existing secrets (default)
secrets = manager.generate_secrets(postgres=True, overwrite=False)

# Force regenerate all secrets
secrets = manager.generate_secrets(
    postgres=True,
    redis=True,
    temporal=True,
    overwrite=True
)
