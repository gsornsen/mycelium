"""Tests for secure secrets management module.

This test suite ensures cryptographic security, proper file permissions,
and correct secret management functionality.
"""

import stat
import sys
from pathlib import Path

import pytest

from mycelium_onboarding.deployment.secrets import (
    DeploymentSecrets,
    SecretsError,
    SecretsManager,
    generate_env_file,
)


class TestPasswordGeneration:
    """Tests for password generation security and quality."""

    def test_generate_password_length(self, tmp_path: Path) -> None:
        """Test password generation creates correct length."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password(length=32)
        assert len(password) == 32

    def test_generate_password_custom_length(self, tmp_path: Path) -> None:
        """Test password generation with custom length."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password(length=64)
        assert len(password) == 64

    def test_generate_password_minimum_length(self, tmp_path: Path) -> None:
        """Test password generation with minimum length."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password(length=4)
        assert len(password) == 4

    def test_generate_password_invalid_length(self, tmp_path: Path) -> None:
        """Test password generation fails with invalid length."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        with pytest.raises(ValueError, match="Password length must be at least 4"):
            manager._generate_password(length=3)

    def test_generate_password_uniqueness(self, tmp_path: Path) -> None:
        """Test passwords are unique."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        pwd1 = manager._generate_password()
        pwd2 = manager._generate_password()
        assert pwd1 != pwd2

    def test_generate_password_has_lowercase(self, tmp_path: Path) -> None:
        """Test password contains lowercase letters."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password()
        assert any(c.islower() for c in password)

    def test_generate_password_has_uppercase(self, tmp_path: Path) -> None:
        """Test password contains uppercase letters."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password()
        assert any(c.isupper() for c in password)

    def test_generate_password_has_digit(self, tmp_path: Path) -> None:
        """Test password contains digits."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password()
        assert any(c.isdigit() for c in password)

    def test_generate_password_has_special(self, tmp_path: Path) -> None:
        """Test password contains special characters."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password()
        # Check for punctuation
        import string

        assert any(c in string.punctuation for c in password)

    def test_generate_password_entropy(self, tmp_path: Path) -> None:
        """Test password has high entropy (multiple unique characters)."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        password = manager._generate_password(length=32)
        # Should have at least 20 unique characters for good entropy
        assert len(set(password)) >= 20


class TestSecretsGeneration:
    """Tests for DeploymentSecrets generation."""

    def test_generate_secrets_postgres(self, tmp_path: Path) -> None:
        """Test generating PostgreSQL secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)

        assert secrets.project_name == "test"
        assert secrets.postgres_password is not None
        assert len(secrets.postgres_password) == 32

    def test_generate_secrets_redis(self, tmp_path: Path) -> None:
        """Test generating Redis secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(redis=True)

        assert secrets.project_name == "test"
        assert secrets.redis_password is not None
        assert len(secrets.redis_password) == 32

    def test_generate_secrets_temporal(self, tmp_path: Path) -> None:
        """Test generating Temporal secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(temporal=True)

        assert secrets.project_name == "test"
        assert secrets.temporal_admin_password is not None
        assert len(secrets.temporal_admin_password) == 32

    def test_generate_secrets_all_services(self, tmp_path: Path) -> None:
        """Test generating secrets for all services."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True, temporal=True)

        assert secrets.postgres_password is not None
        assert secrets.redis_password is not None
        assert secrets.temporal_admin_password is not None
        # All should be different
        assert secrets.postgres_password != secrets.redis_password
        assert secrets.postgres_password != secrets.temporal_admin_password
        assert secrets.redis_password != secrets.temporal_admin_password

    def test_generate_secrets_no_services(self, tmp_path: Path) -> None:
        """Test generating secrets with no services enabled."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets()

        assert secrets.postgres_password is None
        assert secrets.redis_password is None
        assert secrets.temporal_admin_password is None

    def test_generate_secrets_preserve_existing(self, tmp_path: Path) -> None:
        """Test that existing secrets are preserved when not overwriting."""
        manager = SecretsManager("test", secrets_dir=tmp_path)

        # Generate and save initial secrets
        initial = manager.generate_secrets(postgres=True)
        manager.save_secrets(initial)

        # Generate again without overwrite - should keep existing
        updated = manager.generate_secrets(postgres=True, redis=True)
        assert updated.postgres_password == initial.postgres_password
        assert updated.redis_password is not None

    def test_generate_secrets_overwrite(self, tmp_path: Path) -> None:
        """Test overwriting existing secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)

        # Generate and save initial secrets
        initial = manager.generate_secrets(postgres=True)
        manager.save_secrets(initial)

        # Generate again with overwrite
        updated = manager.generate_secrets(postgres=True, overwrite=True)
        assert updated.postgres_password != initial.postgres_password


class TestSecretsPersistence:
    """Tests for saving and loading secrets."""

    def test_save_and_load_secrets(self, tmp_path: Path) -> None:
        """Test saving and loading secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)

        manager.save_secrets(secrets)
        loaded = manager.load_secrets()

        assert loaded is not None
        assert loaded.postgres_password == secrets.postgres_password
        assert loaded.redis_password == secrets.redis_password

    def test_load_nonexistent_secrets(self, tmp_path: Path) -> None:
        """Test loading secrets that don't exist."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        loaded = manager.load_secrets()
        assert loaded is None

    def test_save_secrets_creates_directory(self, tmp_path: Path) -> None:
        """Test that save_secrets creates directory if it doesn't exist."""
        secrets_dir = tmp_path / "nested" / "secrets"
        manager = SecretsManager("test", secrets_dir=secrets_dir)
        secrets = manager.generate_secrets(postgres=True)

        manager.save_secrets(secrets)
        assert secrets_dir.exists()
        assert secrets_dir.is_dir()

    def test_load_corrupted_secrets(self, tmp_path: Path) -> None:
        """Test loading corrupted secrets file."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        manager.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        manager.secrets_file.write_text("not valid json")

        loaded = manager.load_secrets()
        assert loaded is None

    def test_load_invalid_schema(self, tmp_path: Path) -> None:
        """Test loading secrets with invalid schema."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        manager.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Write valid JSON but invalid schema
        manager.secrets_file.write_text('{"invalid": "schema"}')

        loaded = manager.load_secrets()
        assert loaded is None


class TestFilePermissions:
    """Tests for secure file permissions."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_secrets_file_permissions(self, tmp_path: Path) -> None:
        """Test secrets file has secure permissions (0o600)."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        # Check file permissions are 0o600 (owner read/write only)
        mode = manager.secrets_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_secrets_directory_permissions(self, tmp_path: Path) -> None:
        """Test secrets directory has secure permissions (0o700)."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        # Check directory permissions are 0o700 (owner rwx only)
        mode = manager.secrets_dir.stat().st_mode
        assert stat.S_IMODE(mode) == 0o700

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_permissions_after_multiple_saves(self, tmp_path: Path) -> None:
        """Test permissions remain secure after multiple saves."""
        manager = SecretsManager("test", secrets_dir=tmp_path)

        # Save multiple times
        for _ in range(3):
            secrets = manager.generate_secrets(postgres=True, overwrite=True)
            manager.save_secrets(secrets)

        # Permissions should still be secure
        file_mode = manager.secrets_file.stat().st_mode
        dir_mode = manager.secrets_dir.stat().st_mode
        assert stat.S_IMODE(file_mode) == 0o600
        assert stat.S_IMODE(dir_mode) == 0o700


class TestSecretsOperations:
    """Tests for secret operations like deletion and rotation."""

    def test_delete_secrets(self, tmp_path: Path) -> None:
        """Test deleting secrets."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        assert manager.delete_secrets()
        assert not manager.secrets_file.exists()

    def test_delete_nonexistent_secrets(self, tmp_path: Path) -> None:
        """Test deleting secrets that don't exist."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        assert not manager.delete_secrets()

    def test_rotate_postgres_secret(self, tmp_path: Path) -> None:
        """Test rotating PostgreSQL secret."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)
        manager.save_secrets(secrets)

        old_postgres = secrets.postgres_password
        old_redis = secrets.redis_password

        rotated = manager.rotate_secret("postgres")

        assert rotated.postgres_password != old_postgres
        assert rotated.redis_password == old_redis

    def test_rotate_redis_secret(self, tmp_path: Path) -> None:
        """Test rotating Redis secret."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)
        manager.save_secrets(secrets)

        old_redis = secrets.redis_password

        rotated = manager.rotate_secret("redis")

        assert rotated.redis_password != old_redis

    def test_rotate_temporal_secret(self, tmp_path: Path) -> None:
        """Test rotating Temporal secret."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(temporal=True)
        manager.save_secrets(secrets)

        old_temporal = secrets.temporal_admin_password

        rotated = manager.rotate_secret("temporal")

        assert rotated.temporal_admin_password != old_temporal

    def test_rotate_secret_without_existing(self, tmp_path: Path) -> None:
        """Test rotating secret without existing secrets fails."""
        manager = SecretsManager("test", secrets_dir=tmp_path)

        with pytest.raises(ValueError, match="No existing secrets found"):
            manager.rotate_secret("postgres")

    def test_rotate_invalid_secret_type(self, tmp_path: Path) -> None:
        """Test rotating invalid secret type fails."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        with pytest.raises(ValueError, match="Unknown secret type"):
            manager.rotate_secret("invalid")

    def test_rotate_secret_persists(self, tmp_path: Path) -> None:
        """Test rotated secret is persisted to disk."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        rotated = manager.rotate_secret("postgres")

        # Load from disk and verify
        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.postgres_password == rotated.postgres_password


class TestDeploymentSecrets:
    """Tests for DeploymentSecrets dataclass."""

    def test_to_env_vars(self) -> None:
        """Test converting secrets to environment variables."""
        secrets = DeploymentSecrets(
            project_name="test",
            postgres_password="secret123",
            redis_password="secret456",
        )

        env_vars = secrets.to_env_vars()
        assert env_vars["POSTGRES_PASSWORD"] == "secret123"
        assert env_vars["REDIS_PASSWORD"] == "secret456"

    def test_to_env_vars_all_secrets(self) -> None:
        """Test converting all secrets to environment variables."""
        secrets = DeploymentSecrets(
            project_name="test",
            postgres_password="pg123",
            redis_password="redis456",
            temporal_admin_password="temp789",
        )

        env_vars = secrets.to_env_vars()
        assert env_vars["POSTGRES_PASSWORD"] == "pg123"
        assert env_vars["REDIS_PASSWORD"] == "redis456"
        assert env_vars["TEMPORAL_ADMIN_PASSWORD"] == "temp789"

    def test_to_env_vars_partial_secrets(self) -> None:
        """Test converting partial secrets to environment variables."""
        secrets = DeploymentSecrets(project_name="test", postgres_password="secret123")

        env_vars = secrets.to_env_vars()
        assert "POSTGRES_PASSWORD" in env_vars
        assert "REDIS_PASSWORD" not in env_vars
        assert "TEMPORAL_ADMIN_PASSWORD" not in env_vars

    def test_to_env_vars_no_secrets(self) -> None:
        """Test converting with no secrets returns empty dict."""
        secrets = DeploymentSecrets(project_name="test")

        env_vars = secrets.to_env_vars()
        assert env_vars == {}


class TestEnvFileGeneration:
    """Tests for .env file generation."""

    def test_generate_env_file(self, tmp_path: Path) -> None:
        """Test generating .env file."""
        secrets = DeploymentSecrets(project_name="test", postgres_password="secret123")

        env_file = tmp_path / ".env"
        generate_env_file(secrets, env_file)

        assert env_file.exists()
        content = env_file.read_text()
        assert "POSTGRES_PASSWORD=secret123" in content

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_generate_env_file_permissions(self, tmp_path: Path) -> None:
        """Test .env file has secure permissions."""
        secrets = DeploymentSecrets(project_name="test", postgres_password="secret123")

        env_file = tmp_path / ".env"
        generate_env_file(secrets, env_file)

        # Check secure permissions (0o600)
        mode = env_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    def test_generate_env_file_header(self, tmp_path: Path) -> None:
        """Test .env file has security warning header."""
        secrets = DeploymentSecrets(project_name="test-project", postgres_password="secret")

        env_file = tmp_path / ".env"
        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        assert "# Environment variables for test-project" in content
        assert "# Generated by Mycelium" in content
        assert "# KEEP THIS FILE SECURE" in content

    def test_generate_env_file_multiple_secrets(self, tmp_path: Path) -> None:
        """Test .env file with multiple secrets."""
        secrets = DeploymentSecrets(
            project_name="test",
            postgres_password="pg123",
            redis_password="redis456",
            temporal_admin_password="temp789",
        )

        env_file = tmp_path / ".env"
        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        assert "POSTGRES_PASSWORD=pg123" in content
        assert "REDIS_PASSWORD=redis456" in content
        assert "TEMPORAL_ADMIN_PASSWORD=temp789" in content

    def test_generate_env_file_empty_secrets(self, tmp_path: Path) -> None:
        """Test .env file with no secrets."""
        secrets = DeploymentSecrets(project_name="test")

        env_file = tmp_path / ".env"
        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        # Should have header but no password lines
        assert "# Environment variables" in content
        assert "PASSWORD" not in content

    def test_generate_env_file_overwrites(self, tmp_path: Path) -> None:
        """Test .env file overwrites existing file."""
        env_file = tmp_path / ".env"
        env_file.write_text("old content")

        secrets = DeploymentSecrets(project_name="test", postgres_password="new123")
        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        assert "old content" not in content
        assert "POSTGRES_PASSWORD=new123" in content


class TestSecretsManagerInitialization:
    """Tests for SecretsManager initialization."""

    def test_init_with_custom_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom secrets directory."""
        custom_dir = tmp_path / "custom"
        manager = SecretsManager("test", secrets_dir=custom_dir)

        assert manager.secrets_dir == custom_dir
        assert manager.secrets_file == custom_dir / "test.json"

    def test_init_with_default_dir(self) -> None:
        """Test initialization with default XDG directory."""
        manager = SecretsManager("test")

        # Should use XDG state directory
        assert "mycelium" in str(manager.secrets_dir)
        assert "secrets" in str(manager.secrets_dir)

    def test_init_multiple_projects(self, tmp_path: Path) -> None:
        """Test multiple projects don't interfere."""
        manager1 = SecretsManager("project1", secrets_dir=tmp_path)
        manager2 = SecretsManager("project2", secrets_dir=tmp_path)

        secrets1 = manager1.generate_secrets(postgres=True)
        secrets2 = manager2.generate_secrets(postgres=True)

        manager1.save_secrets(secrets1)
        manager2.save_secrets(secrets2)

        # Both should exist with different passwords
        loaded1 = manager1.load_secrets()
        loaded2 = manager2.load_secrets()

        assert loaded1 is not None
        assert loaded2 is not None
        assert loaded1.postgres_password != loaded2.postgres_password


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_special_characters_in_project_name(self, tmp_path: Path) -> None:
        """Test project names with special characters."""
        manager = SecretsManager("my-project_123", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.project_name == "my-project_123"

    def test_concurrent_access_simulation(self, tmp_path: Path) -> None:
        """Test handling of concurrent-like access."""
        manager1 = SecretsManager("test", secrets_dir=tmp_path)
        manager2 = SecretsManager("test", secrets_dir=tmp_path)

        secrets1 = manager1.generate_secrets(postgres=True)
        manager1.save_secrets(secrets1)

        # Second manager should load the same secrets
        loaded = manager2.load_secrets()
        assert loaded is not None
        assert loaded.postgres_password == secrets1.postgres_password

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_save_error_handling(self, tmp_path: Path) -> None:
        """Test error handling when save fails due to permissions."""
        # Create writable directory first
        secrets_dir = tmp_path / "secrets"
        manager = SecretsManager("test", secrets_dir=secrets_dir)

        # Generate secrets with overwrite to avoid loading
        secrets = manager.generate_secrets(postgres=True, overwrite=True)

        # Now make parent directory read-only
        tmp_path.chmod(0o444)

        try:
            with pytest.raises(SecretsError):
                manager.save_secrets(secrets)
        finally:
            # Cleanup: restore permissions
            tmp_path.chmod(0o755)

    def test_json_serialization_roundtrip(self, tmp_path: Path) -> None:
        """Test that secrets survive JSON serialization."""
        manager = SecretsManager("test", secrets_dir=tmp_path)
        original = manager.generate_secrets(postgres=True, redis=True, temporal=True)

        manager.save_secrets(original)
        loaded = manager.load_secrets()

        assert loaded is not None
        assert loaded.project_name == original.project_name
        assert loaded.postgres_password == original.postgres_password
        assert loaded.redis_password == original.redis_password
        assert loaded.temporal_admin_password == original.temporal_admin_password
