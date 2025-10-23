# Source: projects/onboarding/milestones/M09_TESTING_SUITE.md
# Line: 83
# Valid syntax: True
# Has imports: True
# Has assignments: True

# tests/unit/test_config_manager.py
"""Unit tests for ConfigManager."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from mycelium.config import ConfigManager, MyceliumConfig, ServicesConfig, RedisConfig


class TestConfigManagerLoad:
    """Tests for ConfigManager.load()."""

    def test_load_from_project_local(self, tmp_path, sample_config):
        """Test loading configuration from project-local path."""
        # Arrange
        project_config = tmp_path / ".mycelium" / "config.yaml"
        project_config.parent.mkdir(parents=True)
        ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)

        # Act
        loaded = ConfigManager.load(prefer_project=True, project_dir=tmp_path)

        # Assert
        assert loaded.services.redis.enabled == sample_config.services.redis.enabled
        assert loaded.services.redis.port == sample_config.services.redis.port

    def test_load_from_user_global(self, tmp_path, sample_config):
        """Test loading configuration from user global path (~/.config/mycelium)."""
        # Arrange
        user_config = tmp_path / "config.yaml"
        ConfigManager.save(sample_config, project_local=False, config_dir=tmp_path)

        # Act
        loaded = ConfigManager.load(prefer_project=False, user_config_dir=tmp_path)

        # Assert
        assert loaded.services.redis.enabled == sample_config.services.redis.enabled

    def test_load_creates_default_if_missing(self, tmp_path):
        """Test that load creates default config if no config exists."""
        # Act
        loaded = ConfigManager.load(
            prefer_project=False,
            user_config_dir=tmp_path / "nonexistent",
            create_default=True
        )

        # Assert
        assert isinstance(loaded, MyceliumConfig)
        assert loaded.services.redis.enabled  # Default has Redis enabled

    def test_load_raises_if_missing_and_no_default(self, tmp_path):
        """Test that load raises error if config missing and no default creation."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ConfigManager.load(
                prefer_project=False,
                user_config_dir=tmp_path / "nonexistent",
                create_default=False
            )


class TestConfigManagerSave:
    """Tests for ConfigManager.save()."""

    def test_save_to_project_local(self, tmp_path, sample_config):
        """Test saving configuration to project-local directory."""
        # Act
        config_path = ConfigManager.save(
            sample_config,
            project_local=True,
            config_dir=tmp_path
        )

        # Assert
        assert config_path.exists()
        assert config_path.parent.name == ".mycelium"
        assert config_path.name == "config.yaml"

    def test_save_creates_directory_if_missing(self, tmp_path, sample_config):
        """Test that save creates config directory if it doesn't exist."""
        # Arrange
        config_dir = tmp_path / "new_dir"
        assert not config_dir.exists()

        # Act
        config_path = ConfigManager.save(
            sample_config,
            project_local=True,
            config_dir=config_dir
        )

        # Assert
        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_overwrites_existing_config(self, tmp_path, sample_config):
        """Test that save overwrites existing configuration."""
        # Arrange
        config_path = ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)
        original_content = config_path.read_text()

        # Modify config
        sample_config.services.redis.port = 9999

        # Act
        ConfigManager.save(sample_config, project_local=True, config_dir=tmp_path)

        # Assert
        new_content = config_path.read_text()
        assert new_content != original_content
        assert "9999" in new_content


class TestConfigManagerValidation:
    """Tests for configuration validation."""

    def test_validate_rejects_invalid_port(self):
        """Test that validation rejects ports outside valid range."""
        # Act & Assert
        with pytest.raises(ValidationError):
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=True, port=70000)  # Invalid port
                )
            )

    def test_validate_rejects_negative_memory(self):
        """Test that validation rejects negative memory values."""
        # Act & Assert
        with pytest.raises(ValidationError):
            MyceliumConfig(
                services=ServicesConfig(
                    redis=RedisConfig(enabled=True, max_memory=-100)  # Invalid
                )
            )

    def test_validate_accepts_valid_config(self, sample_config):
        """Test that validation accepts valid configuration."""
        # Act & Assert (no exception raised)
        assert sample_config.services.redis.enabled
        assert 1024 <= sample_config.services.redis.port <= 65535


@pytest.fixture
def sample_config() -> MyceliumConfig:
    """Provide sample valid configuration for testing."""
    return MyceliumConfig(
        services=ServicesConfig(
            redis=RedisConfig(
                enabled=True,
                port=6379,
                max_memory=512,
                persistence=True
            )
        )
    )