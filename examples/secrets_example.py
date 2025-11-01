#!/usr/bin/env python3
"""Example usage of the secrets management system.

This example demonstrates how to:
1. Generate secure secrets for deployment services
2. Save and load secrets securely
3. Generate .env files
4. Rotate secrets for security
"""

from pathlib import Path

from mycelium_onboarding.deployment.secrets import (
    SecretsManager,
    generate_env_file,
)


def main() -> None:
    """Demonstrate secrets management functionality."""
    # Example 1: Generate secrets for a new project
    print("Example 1: Generating secrets for a new project")
    print("-" * 50)

    manager = SecretsManager("my-temporal-app")

    # Generate secrets for PostgreSQL, Redis, and Temporal
    secrets = manager.generate_secrets(postgres=True, redis=True, temporal=True)

    print(f"Project: {secrets.project_name}")
    print(f"PostgreSQL password: {secrets.postgres_password[:8]}... (hidden)")
    print(f"Redis password: {secrets.redis_password[:8]}... (hidden)")
    print(f"Temporal password: {secrets.temporal_admin_password[:8]}... (hidden)")
    print()

    # Example 2: Save secrets securely
    print("Example 2: Saving secrets to secure storage")
    print("-" * 50)

    manager.save_secrets(secrets)
    print(f"Secrets saved to: {manager.secrets_file}")
    print("File permissions: 0o600 (owner read/write only)")
    print("Directory permissions: 0o700 (owner rwx only)")
    print()

    # Example 3: Load existing secrets
    print("Example 3: Loading existing secrets")
    print("-" * 50)

    loaded = manager.load_secrets()
    if loaded:
        print("Secrets loaded successfully!")
        print(f"Project: {loaded.project_name}")
        print(f"Has PostgreSQL password: {loaded.postgres_password is not None}")
        print(f"Has Redis password: {loaded.redis_password is not None}")
    print()

    # Example 4: Generate .env file
    print("Example 4: Generating .env file")
    print("-" * 50)

    env_file = Path("/tmp/my-temporal-app.env")
    generate_env_file(secrets, env_file)
    print(f".env file created at: {env_file}")
    print("File permissions: 0o600 (secure)")
    print("\nFile contents:")
    print(env_file.read_text())
    print()

    # Example 5: Rotate a specific secret
    print("Example 5: Rotating PostgreSQL secret")
    print("-" * 50)

    old_password = secrets.postgres_password
    rotated = manager.rotate_secret("postgres")
    print(f"Old password: {old_password[:8]}... (hidden)")
    print(f"New password: {rotated.postgres_password[:8]}... (hidden)")
    print(f"Password changed: {old_password != rotated.postgres_password}")
    print()

    # Example 6: Generate secrets with overwrite
    print("Example 6: Overwriting existing secrets")
    print("-" * 50)

    new_secrets = manager.generate_secrets(postgres=True, redis=True, temporal=True, overwrite=True)
    print("All secrets regenerated with new values")
    print(f"New PostgreSQL password: {new_secrets.postgres_password[:8]}... (hidden)")
    print()

    # Example 7: Environment variables
    print("Example 7: Converting to environment variables")
    print("-" * 50)

    env_vars = new_secrets.to_env_vars()
    print("Environment variables:")
    for key, value in env_vars.items():
        # Show only first 8 characters for security
        print(f"  {key}={value[:8]}... (hidden)")
    print()

    # Cleanup
    print("Cleanup: Deleting secrets")
    print("-" * 50)
    deleted = manager.delete_secrets()
    print(f"Secrets deleted: {deleted}")
    if env_file.exists():
        env_file.unlink()
        print(f"Example .env file deleted: {env_file}")


if __name__ == "__main__":
    main()
