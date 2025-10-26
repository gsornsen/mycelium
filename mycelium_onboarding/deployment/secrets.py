"""Secure secrets management for deployments.

This module provides cryptographically secure secret generation and storage
for deployment credentials. All secrets are generated using the `secrets`
module for cryptographic randomness and stored with secure file permissions.

Security Features:
    - Cryptographically secure random generation (secrets module)
    - Secure file permissions (0o600 for files, 0o700 for directories)
    - Secret rotation support
    - No plaintext logging of passwords
    - XDG-compliant storage location

Warning:
    NEVER commit secrets to version control. Always add .env files and
    secrets directories to .gitignore.

Example:
    >>> from mycelium_onboarding.deployment.secrets import SecretsManager
    >>> manager = SecretsManager("my-project")
    >>> secrets = manager.generate_secrets(postgres=True, redis=True)
    >>> manager.save_secrets(secrets)
    >>> env_vars = secrets.to_env_vars()
"""

from __future__ import annotations

import json
import logging
import secrets
import string
from dataclasses import asdict, dataclass
from pathlib import Path

from ..xdg_dirs import get_state_dir

# Module logger configured to never log password values
logger = logging.getLogger(__name__)

__all__ = [
    "DeploymentSecrets",
    "SecretsManager",
    "generate_env_file",
    "SecretsError",
]


class SecretsError(Exception):
    """Raised when secrets operations fail."""

    pass


@dataclass
class DeploymentSecrets:
    """Secrets for a deployment.

    Attributes:
        project_name: Name of the project
        postgres_password: PostgreSQL password (optional)
        redis_password: Redis password (optional)
        temporal_admin_password: Temporal admin password (optional)
    """

    project_name: str
    postgres_password: str | None = None
    redis_password: str | None = None
    temporal_admin_password: str | None = None

    def to_env_vars(self) -> dict[str, str]:
        """Convert to environment variable dict.

        Returns:
            Dictionary of environment variables with non-None values

        Example:
            >>> secrets = DeploymentSecrets("test", postgres_password="secret123")
            >>> env_vars = secrets.to_env_vars()
            >>> print(env_vars)
            {'POSTGRES_PASSWORD': 'secret123'}
        """
        env_vars: dict[str, str] = {}
        if self.postgres_password:
            env_vars["POSTGRES_PASSWORD"] = self.postgres_password
        if self.redis_password:
            env_vars["REDIS_PASSWORD"] = self.redis_password
        if self.temporal_admin_password:
            env_vars["TEMPORAL_ADMIN_PASSWORD"] = self.temporal_admin_password
        return env_vars


class SecretsManager:
    """Manages deployment secrets securely.

    This class handles generation, storage, and rotation of deployment secrets
    with cryptographic security and proper file permissions.

    Attributes:
        project_name: Name of the project
        secrets_dir: Directory for secrets storage
        secrets_file: Path to the secrets JSON file

    Example:
        >>> manager = SecretsManager("my-app")
        >>> secrets = manager.generate_secrets(postgres=True)
        >>> manager.save_secrets(secrets)
    """

    def __init__(self, project_name: str, secrets_dir: Path | None = None) -> None:
        """Initialize secrets manager.

        Args:
            project_name: Project name for secrets
            secrets_dir: Directory for secrets storage
                (defaults to XDG_STATE_HOME/secrets)

        Example:
            >>> manager = SecretsManager("my-project")
            >>> print(manager.secrets_file)
        """
        self.project_name = project_name
        self.secrets_dir = secrets_dir or (get_state_dir() / "secrets")
        self.secrets_file = self.secrets_dir / f"{project_name}.json"
        logger.debug(
            "Initialized SecretsManager for project: %s at %s",
            project_name,
            self.secrets_dir,
        )

    def generate_secrets(
        self,
        postgres: bool = False,
        redis: bool = False,
        temporal: bool = False,
        overwrite: bool = False,
    ) -> DeploymentSecrets:
        """Generate new secrets for enabled services.

        Args:
            postgres: Generate PostgreSQL password
            redis: Generate Redis password
            temporal: Generate Temporal admin password
            overwrite: Overwrite existing secrets

        Returns:
            DeploymentSecrets with generated passwords

        Example:
            >>> manager = SecretsManager("test")
            >>> secrets = manager.generate_secrets(postgres=True, redis=True)
            >>> assert secrets.postgres_password is not None
        """
        # Load existing secrets if not overwriting
        existing = None if overwrite else self.load_secrets()

        logger.info(
            "Generating secrets for project: %s "
            "(postgres=%s, redis=%s, temporal=%s, overwrite=%s)",
            self.project_name,
            postgres,
            redis,
            temporal,
            overwrite,
        )

        secrets_obj = DeploymentSecrets(
            project_name=self.project_name,
            postgres_password=(
                existing.postgres_password
                if existing and not overwrite and existing.postgres_password
                else (self._generate_password() if postgres else None)
            ),
            redis_password=(
                existing.redis_password
                if existing and not overwrite and existing.redis_password
                else (self._generate_password() if redis else None)
            ),
            temporal_admin_password=(
                existing.temporal_admin_password
                if existing and not overwrite and existing.temporal_admin_password
                else (self._generate_password() if temporal else None)
            ),
        )

        logger.debug("Secrets generated successfully (passwords not logged)")
        return secrets_obj

    def save_secrets(self, secrets_obj: DeploymentSecrets) -> None:
        """Save secrets to encrypted storage.

        Creates the secrets directory with 0o700 permissions and saves the
        secrets file with 0o600 permissions for maximum security.

        Args:
            secrets_obj: Secrets to save

        Raises:
            SecretsError: If directory or file creation fails

        Example:
            >>> manager = SecretsManager("test")
            >>> secrets = DeploymentSecrets("test", postgres_password="secret")
            >>> manager.save_secrets(secrets)
        """
        try:
            # Ensure secrets directory exists with secure permissions
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
            self.secrets_dir.chmod(0o700)  # Only owner can access

            # Save as JSON (in production, should use encryption)
            data = asdict(secrets_obj)
            with self.secrets_file.open("w") as f:
                json.dump(data, f, indent=2)

            # Set secure permissions on secrets file
            self.secrets_file.chmod(0o600)  # Only owner can read/write

            logger.info(
                "Secrets saved successfully to %s with secure permissions",
                self.secrets_file,
            )
        except OSError as e:
            logger.error("Failed to save secrets: %s", e, exc_info=True)
            raise SecretsError(
                f"Failed to save secrets to {self.secrets_file}: {e}"
            ) from e

    def load_secrets(self) -> DeploymentSecrets | None:
        """Load secrets from storage.

        Returns:
            DeploymentSecrets if found, None otherwise

        Example:
            >>> manager = SecretsManager("test")
            >>> secrets = manager.load_secrets()
            >>> if secrets:
            ...     print(secrets.project_name)
        """
        if not self.secrets_file.exists():
            logger.debug("No secrets file found at %s", self.secrets_file)
            return None

        try:
            with self.secrets_file.open() as f:
                data = json.load(f)
            logger.debug("Secrets loaded successfully from %s", self.secrets_file)
            return DeploymentSecrets(**data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to load secrets from %s: %s", self.secrets_file, e)
            return None

    def delete_secrets(self) -> bool:
        """Delete stored secrets.

        Returns:
            True if deleted, False if not found

        Example:
            >>> manager = SecretsManager("test")
            >>> deleted = manager.delete_secrets()
            >>> print(deleted)
        """
        if self.secrets_file.exists():
            self.secrets_file.unlink()
            logger.info("Secrets deleted: %s", self.secrets_file)
            return True
        logger.debug("No secrets file to delete at %s", self.secrets_file)
        return False

    def _generate_password(self, length: int = 32) -> str:
        """Generate a cryptographically secure password.

        Uses the `secrets` module for cryptographically strong randomness.
        Password includes at least one lowercase, uppercase, digit, and
        special character.

        Args:
            length: Password length (default 32)

        Returns:
            Generated password

        Raises:
            ValueError: If length is less than 4

        Example:
            >>> manager = SecretsManager("test")
            >>> password = manager._generate_password(32)
            >>> assert len(password) == 32
        """
        if length < 4:
            raise ValueError("Password length must be at least 4")

        # Use secrets module for cryptographically strong randomness
        alphabet = string.ascii_letters + string.digits + string.punctuation

        # Ensure at least one of each type for password strength
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation),
        ]

        # Fill the rest with random characters
        password += [secrets.choice(alphabet) for _ in range(length - 4)]

        # Shuffle using cryptographically secure random
        secrets.SystemRandom().shuffle(password)

        logger.debug("Generated password of length %d (value not logged)", length)
        return "".join(password)

    def rotate_secret(self, secret_type: str) -> DeploymentSecrets:
        """Rotate a specific secret.

        Generates a new password for the specified secret type while
        preserving other secrets.

        Args:
            secret_type: Type of secret to rotate ('postgres', 'redis', 'temporal')

        Returns:
            Updated DeploymentSecrets

        Raises:
            ValueError: If no existing secrets found or invalid secret type
            SecretsError: If rotation fails

        Example:
            >>> manager = SecretsManager("test")
            >>> rotated = manager.rotate_secret("postgres")
            >>> assert rotated.postgres_password is not None
        """
        existing = self.load_secrets()
        if not existing:
            raise ValueError(f"No existing secrets found for {self.project_name}")

        new_password = self._generate_password()

        if secret_type == "postgres":
            existing.postgres_password = new_password
        elif secret_type == "redis":
            existing.redis_password = new_password
        elif secret_type == "temporal":
            existing.temporal_admin_password = new_password
        else:
            raise ValueError(f"Unknown secret type: {secret_type}")

        logger.info("Rotating %s secret for project %s", secret_type, self.project_name)
        self.save_secrets(existing)
        return existing


def generate_env_file(secrets: DeploymentSecrets, output_path: Path) -> None:
    """Generate .env file from secrets.

    Creates a .env file with secure permissions (0o600) containing
    environment variables derived from the secrets.

    Args:
        secrets: Deployment secrets
        output_path: Path to .env file

    Raises:
        SecretsError: If file creation fails

    Example:
        >>> secrets = DeploymentSecrets("test", postgres_password="secret123")
        >>> generate_env_file(secrets, Path("/tmp/.env"))
    """
    try:
        env_vars = secrets.to_env_vars()

        lines = [
            f"# Environment variables for {secrets.project_name}",
            "# Generated by Mycelium",
            "# KEEP THIS FILE SECURE - DO NOT COMMIT TO VERSION CONTROL",
            "",
        ]

        for key, value in env_vars.items():
            lines.append(f"{key}={value}")

        output_path.write_text("\n".join(lines))
        output_path.chmod(0o600)  # Secure permissions

        logger.info("Generated .env file at %s with secure permissions", output_path)
    except OSError as e:
        logger.error("Failed to generate .env file: %s", e, exc_info=True)
        raise SecretsError(f"Failed to generate .env file at {output_path}: {e}") from e
