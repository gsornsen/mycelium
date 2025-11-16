"""Unit tests for configuration loader with 3-tier precedence."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mycelium_onboarding.config.loader import (
    ConfigLoader,
    ConfigParseError,
    ConfigValidationError,
)
from mycelium_onboarding.config.schema import MyceliumConfig


@pytest.fixture
def temp_config_files(tmp_path: Path) -> dict[str, Path]:
    """Create temporary configuration files for testing."""
    # Global config directory
    global_config_dir = tmp_path / "global"
    global_config_dir.mkdir()
    global_config_path = global_config_dir / "config.yaml"

    # Project config directory
    project_config_dir = tmp_path / "project"
    project_config_dir.mkdir()
    project_config_path = project_config_dir / "config.yaml"

    return {
        "global_dir": global_config_dir,
        "global_config": global_config_path,
        "project_dir": project_config_dir,
        "project_config": project_config_path,
    }


class TestConfigLoaderInit:
    """Test ConfigLoader initialization."""

    def test_default_init(self) -> None:
        """Test initialization with default values."""
        loader = ConfigLoader()
        assert loader.config_filename == "config.yaml"
        assert loader.cache_enabled is True

    def test_custom_filename(self) -> None:
        """Test initialization with custom filename."""
        loader = ConfigLoader(config_filename="custom.yaml")
        assert loader.config_filename == "custom.yaml"

    def test_cache_disabled(self) -> None:
        """Test initialization with cache disabled."""
        loader = ConfigLoader(cache_enabled=False)
        assert loader.cache_enabled is False


class TestConfigLoaderLoad:
    """Test ConfigLoader.load() method."""

    def test_load_with_defaults_only(self) -> None:
        """Test loading when no config files exist."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            # Mock that no config files exist
            mock_get_dir.return_value = Path("/nonexistent")
            mock_find.return_value = None

            loader = ConfigLoader()
            config = loader.load()

            assert isinstance(config, MyceliumConfig)
            assert config.project_name == "mycelium"  # Default value
            assert config.version == "1.0"

    def test_load_with_global_config(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with global config file."""
        # Create global config
        global_config_data = {
            "version": "1.0",
            "project_name": "global-project",
            "services": {"redis": {"port": 6380}},
        }

        global_config_path = temp_config_files["global_config"]
        with global_config_path.open("w") as f:
            yaml.dump(global_config_data, f)

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = global_config_path

            loader = ConfigLoader()
            config = loader.load()

            assert config.project_name == "global-project"
            assert config.services.redis.port == 6380

    def test_load_with_project_config(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with both global and project configs."""
        # Create global config
        global_config_data = {
            "version": "1.0",
            "project_name": "global-project",
            "services": {"redis": {"port": 6380}},
        }
        global_config_path = temp_config_files["global_config"]
        with global_config_path.open("w") as f:
            yaml.dump(global_config_data, f)

        # Create project config (overrides global)
        project_config_data = {
            "project_name": "project-override",
            "services": {"postgres": {"port": 5433}},
        }
        project_config_path = temp_config_files["project_config"]
        with project_config_path.open("w") as f:
            yaml.dump(project_config_data, f)

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = project_config_path

            loader = ConfigLoader()
            config = loader.load()

            # Project overrides global
            assert config.project_name == "project-override"
            # Global value preserved where not overridden
            assert config.services.redis.port == 6380
            # Project value applied
            assert config.services.postgres.port == 5433

    def test_load_empty_file(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with empty config file."""
        global_config_path = temp_config_files["global_config"]
        global_config_path.touch()  # Create empty file

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = global_config_path

            loader = ConfigLoader()
            config = loader.load()

            # Should use defaults
            assert config.project_name == "mycelium"

    def test_load_with_caching(self) -> None:
        """Test that caching works correctly."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = Path("/nonexistent")
            mock_find.return_value = None

            loader = ConfigLoader(cache_enabled=True)

            # First load
            config1 = loader.load()
            # Second load (should be cached)
            config2 = loader.load()

            # Should be same instance due to caching
            assert config1 is config2

    def test_load_without_caching(self) -> None:
        """Test that cache can be disabled."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = Path("/nonexistent")
            mock_find.return_value = None

            loader = ConfigLoader(cache_enabled=False)

            # First load
            config1 = loader.load()
            # Second load (should not be cached)
            config2 = loader.load()

            # Should be different instances
            assert config1 is not config2


class TestConfigLoaderErrors:
    """Test ConfigLoader error handling."""

    def test_load_invalid_yaml(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with invalid YAML."""
        global_config_path = temp_config_files["global_config"]
        with global_config_path.open("w") as f:
            f.write("invalid: yaml: content:")

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = global_config_path

            loader = ConfigLoader()

            with pytest.raises(ConfigParseError, match="Failed to parse YAML"):
                loader.load()

    def test_load_non_dict_yaml(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with non-dictionary YAML."""
        global_config_path = temp_config_files["global_config"]
        with global_config_path.open("w") as f:
            yaml.dump([1, 2, 3], f)  # List instead of dict

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = global_config_path

            loader = ConfigLoader()

            with pytest.raises(ConfigParseError, match="expected dictionary"):
                loader.load()

    def test_load_invalid_config(self, temp_config_files: dict[str, Path]) -> None:
        """Test loading with invalid configuration."""
        # Create config with invalid project name
        global_config_data = {
            "version": "1.0",
            "project_name": "invalid@name",  # Invalid character
        }
        global_config_path = temp_config_files["global_config"]
        with global_config_path.open("w") as f:
            yaml.dump(global_config_data, f)

        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = temp_config_files["global_dir"]
            mock_find.return_value = global_config_path

            loader = ConfigLoader()

            with pytest.raises(ConfigValidationError, match="validation failed"):
                loader.load()


class TestConfigLoaderMethods:
    """Test ConfigLoader utility methods."""

    def test_get_config_paths(self) -> None:
        """Test getting configuration paths."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.get_all_config_paths") as mock_get_all,
        ):
            mock_get_dir.return_value = Path("/global/config")
            # Return 2 paths: project (first) and global (second)
            mock_get_all.return_value = [Path("/project/config.yaml"), Path("/global/config/config.yaml")]

            loader = ConfigLoader()
            paths = loader.get_config_paths()

            assert "global" in paths
            assert "project" in paths
            assert paths["global"] == Path("/global/config/config.yaml")
            assert paths["project"] == Path("/project/config.yaml")

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = Path("/nonexistent")
            mock_find.return_value = None

            loader = ConfigLoader(cache_enabled=True)

            # Load and cache
            config1 = loader.load()

            # Clear cache
            loader.clear_cache()

            # Load again (should be fresh)
            config2 = loader.load()

            # Should be different instances after cache clear
            assert config1 is not config2

    def test_reload(self) -> None:
        """Test reload method."""
        with (
            patch("mycelium_onboarding.config.loader.get_config_dir") as mock_get_dir,
            patch("mycelium_onboarding.config.loader.find_config_file") as mock_find,
        ):
            mock_get_dir.return_value = Path("/nonexistent")
            mock_find.return_value = None

            loader = ConfigLoader(cache_enabled=True)

            # Load and cache
            config1 = loader.load()

            # Reload (clears cache and reloads)
            config2 = loader.reload()

            # Should be different instances
            assert config1 is not config2

    def test_validate_config_file_valid(self, temp_config_files: dict[str, Path]) -> None:
        """Test validating a valid config file."""
        config_data = {
            "version": "1.0",
            "project_name": "test-project",
        }
        config_path = temp_config_files["global_config"]
        with config_path.open("w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader()
        errors = loader.validate_config_file(config_path)

        assert errors == []

    def test_validate_config_file_invalid(self, temp_config_files: dict[str, Path]) -> None:
        """Test validating an invalid config file."""
        config_data = {
            "version": "1.0",
            "project_name": "invalid@name",  # Invalid character
        }
        config_path = temp_config_files["global_config"]
        with config_path.open("w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader()
        errors = loader.validate_config_file(config_path)

        assert len(errors) > 0
        assert any("project_name" in error for error in errors)

    def test_validate_config_file_parse_error(self, temp_config_files: dict[str, Path]) -> None:
        """Test validating a file with parse errors."""
        config_path = temp_config_files["global_config"]
        with config_path.open("w") as f:
            f.write("invalid: yaml: content:")

        loader = ConfigLoader()
        errors = loader.validate_config_file(config_path)

        assert len(errors) > 0
        assert any("Parse error" in error for error in errors)

    def test_validate_config_file_read_error(self, temp_config_files: dict[str, Path]) -> None:
        """Test validating a file that cannot be read."""
        config_path = Path("/nonexistent/config.yaml")

        loader = ConfigLoader()
        errors = loader.validate_config_file(config_path)

        assert len(errors) > 0
        assert any("Load error" in error for error in errors)
