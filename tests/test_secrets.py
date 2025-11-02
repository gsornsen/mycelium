"""Tests for the secrets management functionality."""

from pathlib import Path

from mycelium_onboarding.deployment.secrets import (
    DeploymentSecrets,
    SecretsManager,
    generate_env_file,
)


class TestPasswordGeneration:
    """Tests for password generation."""

    def test_generate_password_default_length(self, tmp_path: Path) -> None:
        """Test password generation with default length."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        password = manager._generate_password()
        assert len(password) == 32
        # Should only contain allowed characters
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*")
        assert all(c in allowed_chars for c in password)

    def test_generate_password_custom_length(self, tmp_path: Path) -> None:
        """Test password generation with custom length."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        password = manager._generate_password(16)
        assert len(password) == 16

    def test_generate_password_complexity(self, tmp_path: Path) -> None:
        """Test password complexity requirements."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        # Generate multiple passwords and check complexity
        for _ in range(10):
            password = manager._generate_password()
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
        assert oct(secrets_dir.stat().st_mode)[-3:] == "700"

    def test_init_uses_xdg_state_dir_by_default(self) -> None:
        """Test that default initialization uses XDG state directory."""
        manager = SecretsManager("test-project")
        assert "mycelium" in str(manager.secrets_dir)
        assert "secrets" in str(manager.secrets_dir)

    def test_generate_secrets_all_components(self, tmp_path: Path) -> None:
        """Test generating secrets for all components."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(
            postgres=True,
            redis=True,
            api_keys=True,
            jwt=True,
        )

        # Check all secrets are present and non-empty
        assert secrets.postgres_password
        assert secrets.redis_password
        assert secrets.api_key
        assert secrets.jwt_secret

        # Check lengths
        assert len(secrets.postgres_password) == 32
        assert len(secrets.redis_password) == 32
        assert len(secrets.api_key) == 64  # API keys are longer
        assert len(secrets.jwt_secret) == 64  # JWT secrets are longer

    def test_generate_secrets_selective(self, tmp_path: Path) -> None:
        """Test generating only selected secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(
            postgres=True,
            redis=False,
            api_keys=False,
            jwt=False,
        )

        assert secrets.postgres_password
        assert secrets.redis_password is None
        assert secrets.api_key is None
        assert secrets.jwt_secret is None

    def test_save_and_load_secrets(self, tmp_path: Path) -> None:
        """Test saving and loading secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        original = manager.generate_secrets(
            postgres=True,
            redis=True,
            api_keys=True,
            jwt=True,
        )

        # Save secrets
        manager.save_secrets(original)
        assert manager.secrets_file.exists()
        # Check file permissions (should be 0o600)
        assert oct(manager.secrets_file.stat().st_mode)[-3:] == "600"

        # Load secrets
        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.postgres_password == original.postgres_password
        assert loaded.redis_password == original.redis_password
        assert loaded.api_key == original.api_key
        assert loaded.jwt_secret == original.jwt_secret

    def test_rotate_secrets(self, tmp_path: Path) -> None:
        """Test rotating secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        original = manager.generate_secrets(postgres=True)
        manager.save_secrets(original)

        # Rotate secrets
        rotated = manager.rotate_secrets(postgres=True)

        # New password should be different
        assert rotated.postgres_password != original.postgres_password

        # Reload to verify persistence
        loaded = manager.load_secrets()
        assert loaded is not None
        assert loaded.postgres_password == rotated.postgres_password

    def test_delete_secrets(self, tmp_path: Path) -> None:
        """Test deleting secrets."""
        manager = SecretsManager("test-project", secrets_dir=tmp_path)
        secrets = manager.generate_secrets(postgres=True)
        manager.save_secrets(secrets)
        assert manager.secrets_file.exists()

        # Delete secrets
        result = manager.delete_secrets()
        assert result is True
        assert not manager.secrets_file.exists()

        # Second delete should return False
        result = manager.delete_secrets()
        assert result is False


class TestDeploymentSecrets:
    """Tests for DeploymentSecrets dataclass."""

    def test_to_env_vars(self) -> None:
        """Test converting secrets to environment variables."""
        secrets = DeploymentSecrets(
            postgres_password="test_pg_pass",
            redis_password="test_redis_pass",
            api_key="test_api_key",
            jwt_secret="test_jwt_secret",
        )

        env_vars = secrets.to_env_vars()

        assert env_vars["POSTGRES_PASSWORD"] == "test_pg_pass"
        assert env_vars["REDIS_PASSWORD"] == "test_redis_pass"
        assert env_vars["API_KEY"] == "test_api_key"
        assert env_vars["JWT_SECRET"] == "test_jwt_secret"

    def test_to_env_vars_with_none_values(self) -> None:
        """Test converting secrets with None values."""
        secrets = DeploymentSecrets(
            postgres_password="test_pg_pass",
            redis_password=None,
            api_key=None,
            jwt_secret="test_jwt_secret",
        )

        env_vars = secrets.to_env_vars()

        assert "POSTGRES_PASSWORD" in env_vars
        assert "REDIS_PASSWORD" not in env_vars
        assert "API_KEY" not in env_vars
        assert "JWT_SECRET" in env_vars


class TestGenerateEnvFile:
    """Tests for generate_env_file function."""

    def test_generate_env_file(self, tmp_path: Path) -> None:
        """Test generating .env file from secrets."""
        secrets = DeploymentSecrets(
            postgres_password="test_pg_pass",
            redis_password="test_redis_pass",
            api_key="test_api_key",
            jwt_secret="test_jwt_secret",
        )

        output_path = tmp_path / ".env"
        generate_env_file(secrets, output_path)

        assert output_path.exists()
        # Check file permissions (should be 0o600)
        assert oct(output_path.stat().st_mode)[-3:] == "600"

        # Verify content
        content = output_path.read_text()
        assert "POSTGRES_PASSWORD=test_pg_pass" in content
        assert "REDIS_PASSWORD=test_redis_pass" in content
        assert "API_KEY=test_api_key" in content
        assert "JWT_SECRET=test_jwt_secret" in content

    def test_generate_env_file_with_none_values(self, tmp_path: Path) -> None:
        """Test generating .env file with None values."""
        secrets = DeploymentSecrets(
            postgres_password="test_pg_pass",
            redis_password=None,
            api_key=None,
            jwt_secret="test_jwt_secret",
        )

        output_path = tmp_path / ".env"
        generate_env_file(secrets, output_path)

        content = output_path.read_text()
        assert "POSTGRES_PASSWORD=test_pg_pass" in content
        assert "REDIS_PASSWORD" not in content
        assert "API_KEY" not in content
        assert "JWT_SECRET=test_jwt_secret" in content
