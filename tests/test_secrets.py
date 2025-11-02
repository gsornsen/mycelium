"""Tests for the secrets management functionality."""

from pathlib import Path

import pytest

from mycelium_onboarding.deployment.secrets import (
    DeploymentSecrets,
    SecretsManager,
    generate_env_file,
    generate_password,
)


class TestPasswordGeneration:
    """Tests for password generation."""

    def test_generate_password_default_length(self) -> None:
        """Test password generation with default length."""
        password = generate_password()
        assert len(password) == 32
        # Should only contain allowed characters
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*")
        assert all(c in allowed_chars for c in password)

    def test_generate_password_custom_length(self) -> None:
        """Test password generation with custom length."""
        password = generate_password(16)
        assert len(password) == 16

    def test_generate_password_complexity(self) -> None:
        """Test password complexity requirements."""
        # Generate multiple passwords and check complexity
        for _ in range(10):
            password = generate_password()
            # Should have at least one uppercase, lowercase, digit, and special char
            assert any(c.isupper() for c in password)
            assert any(c.islower() for c in password)
            assert any(c.isdigit() for c in password)
            assert any(c in "!@#$%^&*" for c in password)


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_init_creates_secrets_dir(self, tmp_path: Path) -> None:
        """Test that initialization creates the secrets directory."""
        secrets_dir = tmp_path / "custom_secrets"
        SecretsManager("test-project", secrets_dir=secrets_dir)

        assert secrets_dir.exists()
        assert secrets_dir.is_dir()
        # Check permissions (should be 0o700)
        assert (secrets_dir.stat().st_mode & 0o777) == 0o700

    def test_generate_secrets_default(self) -> None:
        """Test generating secrets with defaults."""
        manager = SecretsManager("test-project")
        secrets = manager.generate_secrets()

        assert secrets.project_name == "test-project"
        assert secrets.postgres_password is None
        assert secrets.redis_password is None
        assert secrets.temporal_admin_password is None
        assert secrets.temporal_db_password is None

    def test_generate_secrets_with_services(self) -> None:
        """Test generating secrets for specific services."""
        manager = SecretsManager("test-project")
        secrets = manager.generate_secrets(postgres=True, redis=True, temporal=True)

        assert secrets.project_name == "test-project"
        assert secrets.postgres_password is not None
        assert len(secrets.postgres_password) == 32
        assert secrets.redis_password is not None
        assert len(secrets.redis_password) == 32
        assert secrets.temporal_admin_password is not None
        assert len(secrets.temporal_admin_password) == 32
        assert secrets.temporal_db_password is not None
        assert len(secrets.temporal_db_password) == 32

    def test_save_and_load_secrets(self, tmp_path: Path) -> None:
        """Test saving and loading secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)

        # Save secrets
        manager.save_secrets(secrets)
        assert manager.secrets_file.exists()

        # Check file permissions (should be 0o600)
        assert (manager.secrets_file.stat().st_mode & 0o777) == 0o600

        # Load secrets
        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.project_name == secrets.project_name
        assert loaded.postgres_password == secrets.postgres_password
        assert loaded.redis_password == secrets.redis_password

    def test_load_nonexistent_secrets(self, tmp_path: Path) -> None:
        """Test loading when no secrets file exists."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        loaded = manager.load_secrets()
        assert loaded is None

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON file."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        manager.secrets_file.write_text("not valid json")

        loaded = manager.load_secrets()
        assert loaded is None

    def test_generate_secrets_with_overwrite(self, tmp_path: Path) -> None:
        """Test overwriting existing secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)

        # Generate and save initial secrets
        secrets1 = manager.generate_secrets(postgres=True, redis=True)
        manager.save_secrets(secrets1)

        # Generate new secrets without overwrite (should keep existing)
        secrets2 = manager.generate_secrets(postgres=True, temporal=True, overwrite=False)
        assert secrets2.postgres_password == secrets1.postgres_password
        assert secrets2.redis_password == secrets1.redis_password
        assert secrets2.temporal_admin_password is not None

        # Generate new secrets with overwrite (should replace all)
        secrets3 = manager.generate_secrets(postgres=True, redis=True, temporal=True, overwrite=True)
        assert secrets3.postgres_password != secrets1.postgres_password
        assert secrets3.redis_password != secrets1.redis_password
        assert secrets3.temporal_admin_password is not None

    def test_delete_secrets(self, tmp_path: Path) -> None:
        """Test deleting secrets file."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)

        # Delete secrets
        deleted = manager.delete_secrets()
        assert deleted is True
        assert not manager.secrets_file.exists()

        # Delete when no file exists
        deleted = manager.delete_secrets()
        assert deleted is False

    def test_rotate_secret_postgres(self, tmp_path: Path) -> None:
        """Test rotating PostgreSQL secret."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)
        old_postgres = secrets.postgres_password
        old_redis = secrets.redis_password
        manager.save_secrets(secrets)

        # Rotate PostgreSQL password
        rotated = manager.rotate_secret("postgres")
        assert rotated.postgres_password != old_postgres
        assert rotated.redis_password == old_redis

        # Verify persistence
        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.postgres_password == rotated.postgres_password

    def test_rotate_secret_redis(self, tmp_path: Path) -> None:
        """Test rotating Redis secret."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True, redis=True)
        old_postgres = secrets.postgres_password
        old_redis = secrets.redis_password
        manager.save_secrets(secrets)

        # Rotate Redis password
        rotated = manager.rotate_secret("redis")
        assert rotated.postgres_password == old_postgres
        assert rotated.redis_password != old_redis

    def test_rotate_secret_temporal(self, tmp_path: Path) -> None:
        """Test rotating Temporal secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(temporal=True)
        old_admin = secrets.temporal_admin_password
        old_db = secrets.temporal_db_password
        manager.save_secrets(secrets)

        # Rotate Temporal passwords
        rotated = manager.rotate_secret("temporal")
        assert rotated.temporal_admin_password != old_admin
        assert rotated.temporal_db_password != old_db

    def test_rotate_secret_invalid_type(self, tmp_path: Path) -> None:
        """Test rotating with invalid secret type."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets()
        manager.save_secrets(secrets)

        with pytest.raises(ValueError, match="Unknown secret type"):
            manager.rotate_secret("invalid")

    def test_rotate_secret_persists(self, tmp_path: Path) -> None:
        """Test rotated secret is persisted to disk."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
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
            postgres_password="secret123",  # nosec B106 - Test fixture password
            redis_password="secret456",  # nosec B106 - Test fixture password
        )

        env_vars = secrets.to_env_vars()

        assert env_vars["POSTGRES_PASSWORD"] == "secret123"  # nosec B106 - Test fixture password
        assert env_vars["REDIS_PASSWORD"] == "secret456"  # nosec B106 - Test fixture password
        assert "TEMPORAL_ADMIN_PASSWORD" not in env_vars
        assert "TEMPORAL_DB_PASSWORD" not in env_vars

    def test_to_env_vars_all_services(self) -> None:
        """Test converting all secrets to environment variables."""
        secrets = DeploymentSecrets(
            project_name="test",
            postgres_password="pg123",  # nosec B106 - Test fixture password
            redis_password="redis456",  # nosec B106 - Test fixture password
            temporal_admin_password="temp789",  # nosec B106 - Test fixture password
            temporal_db_password="tempdb123",  # nosec B106 - Test fixture password
        )

        env_vars = secrets.to_env_vars()

        assert len(env_vars) == 4
        assert all(
            key in env_vars
            for key in [
                "POSTGRES_PASSWORD",
                "REDIS_PASSWORD",
                "TEMPORAL_ADMIN_PASSWORD",
                "TEMPORAL_DB_PASSWORD",
            ]
        )

    def test_to_dict(self) -> None:
        """Test converting secrets to dictionary."""
        secrets = DeploymentSecrets(project_name="test", postgres_password="secret123")  # nosec B106 - Test fixture password

        data = secrets.to_dict()

        assert data["project_name"] == "test"
        assert data["postgres_password"] == "secret123"  # nosec B106 - Test fixture password
        assert data["redis_password"] is None

    @classmethod
    def test_from_dict(cls) -> None:
        """Test creating secrets from dictionary."""
        data = {
            "project_name": "test",
            "postgres_password": "secret123",  # nosec B106 - Test fixture password
            "redis_password": None,
        }

        secrets = DeploymentSecrets.from_dict(data)

        assert secrets.project_name == "test"
        assert secrets.postgres_password == "secret123"  # nosec B106 - Test fixture password
        assert secrets.redis_password is None


class TestGenerateEnvFile:
    """Tests for generate_env_file function."""

    def test_generate_env_file_basic(self, tmp_path: Path) -> None:
        """Test generating basic .env file."""
        secrets = DeploymentSecrets(project_name="test-project", postgres_password="secret")  # nosec B106 - Test fixture password
        env_file = tmp_path / ".env"

        generate_env_file(secrets, env_file)

        assert env_file.exists()
        # Check file permissions (should be 0o600)
        assert (env_file.stat().st_mode & 0o777) == 0o600

        content = env_file.read_text()
        assert "# Generated secrets for test-project" in content
        assert "POSTGRES_PASSWORD=secret" in content
        assert "REDIS_PASSWORD" not in content

    def test_generate_env_file_all_services(self, tmp_path: Path) -> None:
        """Test generating .env file with all services."""
        secrets = DeploymentSecrets(
            project_name="test-project",
            postgres_password="pg123",  # nosec B106 - Test fixture password
            redis_password="redis456",  # nosec B106 - Test fixture password
            temporal_admin_password="temp789",  # nosec B106 - Test fixture password
            temporal_db_password="tempdb123",  # nosec B106 - Test fixture password
        )
        env_file = tmp_path / ".env"

        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        assert "POSTGRES_PASSWORD=pg123" in content  # nosec B106 - Test fixture password
        assert "REDIS_PASSWORD=redis456" in content  # nosec B106 - Test fixture password
        assert "TEMPORAL_ADMIN_PASSWORD=temp789" in content  # nosec B106 - Test fixture password
        assert "TEMPORAL_DB_PASSWORD=tempdb123" in content  # nosec B106 - Test fixture password

    def test_generate_env_file_overwrite(self, tmp_path: Path) -> None:
        """Test overwriting existing .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("OLD_CONTENT=old")

        secrets = DeploymentSecrets(project_name="test", postgres_password="new")  # nosec B106 - Test fixture password
        generate_env_file(secrets, env_file)

        content = env_file.read_text()
        assert "OLD_CONTENT" not in content
        assert "POSTGRES_PASSWORD=new" in content
