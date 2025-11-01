"""Tests for hierarchical configuration loading.

This test suite provides comprehensive coverage of the configuration loader
module, testing precedence order, environment variable handling, and edge cases.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mycelium_onboarding.config_loader import (
    ConfigLoaderError,
    find_config_file,
    get_all_config_paths,
    get_config_path,
)
from mycelium_onboarding.xdg_dirs import get_config_dir


@pytest.fixture
def mock_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory for testing.

    This fixture:
    - Creates a temporary directory to use as HOME
    - Clears all XDG and MYCELIUM environment variables
    - Sets platform-appropriate environment variables
    - Returns the temp home path for use in tests
    """
    home = tmp_path / "home"
    home.mkdir()

    # Set HOME to temp directory
    monkeypatch.setenv("HOME", str(home))

    # On Windows, also set LOCALAPPDATA and APPDATA to control path resolution
    if sys.platform == "win32":
        # Use XDG_CONFIG_HOME to override Windows defaults for testing
        config_base = home / ".config"
        config_base.mkdir(exist_ok=True)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_base.parent / ".config"))
        monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
        monkeypatch.setenv("XDG_STATE_HOME", str(home / ".local" / "state"))
    else:
        # Clear all XDG variables to test defaults on Unix
        for var in ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"]:
            monkeypatch.delenv(var, raising=False)

    # Clear MYCELIUM variables
    for var in ["MYCELIUM_PROJECT_DIR", "MYCELIUM_ROOT", "MYCELIUM_CONFIG_DIR"]:
        monkeypatch.delenv(var, raising=False)

    # Clear LRU cache to ensure fresh lookups
    get_config_dir.cache_clear()

    return home


@pytest.fixture
def mock_project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary project directory and set MYCELIUM_PROJECT_DIR."""
    project_dir = tmp_path / "project" / ".mycelium"
    project_dir.mkdir(parents=True)

    monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(project_dir))

    return project_dir


@pytest.fixture
def user_config_dir(mock_home: Path) -> Path:
    """Get the user-global config directory."""
    return get_config_dir()


class TestGetConfigPath:
    """Tests for get_config_path()."""

    def test_returns_user_global_when_no_project_dir(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return user-global path when MYCELIUM_PROJECT_DIR not set."""
        path = get_config_path("config.yaml")

        expected = user_config_dir / "config.yaml"
        assert path == expected

    def test_returns_user_global_when_prefer_project_false(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return user-global path when prefer_project=False."""
        path = get_config_path("config.yaml", prefer_project=False)

        expected = user_config_dir / "config.yaml"
        assert path == expected

    def test_returns_project_local_when_exists(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return project-local path when file exists there."""
        # Create project-local config
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: config")

        path = get_config_path("config.yaml", prefer_project=True)

        assert path == project_config

    def test_returns_user_global_when_project_local_missing(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should fall back to user-global when project-local doesn't exist."""
        # Create only user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        path = get_config_path("config.yaml", prefer_project=True)

        assert path == user_config

    def test_project_local_precedence_over_user_global(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should prefer project-local over user-global when both exist."""
        # Create both configs
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: config")

        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        path = get_config_path("config.yaml", prefer_project=True)

        # Should return project-local
        assert path == project_config

    def test_returns_project_path_for_creation_when_neither_exists(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return project-local path for creation when prefer_project=True."""
        path = get_config_path("config.yaml", prefer_project=True)

        expected = mock_project_dir / "config.yaml"
        assert path == expected
        assert not path.exists()  # Should not create the file

    def test_returns_user_path_for_creation_when_neither_exists(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return user-global path for creation when prefer_project=False."""
        path = get_config_path("config.yaml", prefer_project=False)

        expected = user_config_dir / "config.yaml"
        assert path == expected
        assert not path.exists()  # Should not create the file

    def test_works_with_different_filenames(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should work with any filename."""
        filenames = ["config.yaml", "preferences.yaml", "settings.json", "api_keys.txt"]

        for filename in filenames:
            path = get_config_path(filename)
            assert path == user_config_dir / filename

    def test_raises_on_empty_filename(self, mock_home: Path) -> None:
        """Should raise error when filename is empty."""
        with pytest.raises(ConfigLoaderError, match="cannot be empty"):
            get_config_path("")

    def test_raises_on_filename_with_slash(self, mock_home: Path) -> None:
        """Should raise error when filename contains path separators."""
        with pytest.raises(ConfigLoaderError, match="path separators"):
            get_config_path("subdir/config.yaml")

    def test_raises_on_filename_with_backslash(self, mock_home: Path) -> None:
        """Should raise error when filename contains backslash."""
        with pytest.raises(ConfigLoaderError, match="path separators"):
            get_config_path("subdir\\config.yaml")

    def test_does_not_create_directories(
        self, mock_home: Path, mock_project_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not create any directories."""
        # Set project dir to non-existent path
        nonexistent = mock_home / "nonexistent" / ".mycelium"
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(nonexistent))

        path = get_config_path("config.yaml", prefer_project=True)

        # Should return the path but not create the directory
        assert path == nonexistent / "config.yaml"
        assert not nonexistent.exists()

    def test_does_not_create_files(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should not create any files."""
        path = get_config_path("config.yaml")

        assert not path.exists()


class TestGetAllConfigPaths:
    """Tests for get_all_config_paths()."""

    def test_returns_only_user_global_when_no_project_dir(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return only user-global path when MYCELIUM_PROJECT_DIR not set."""
        paths = get_all_config_paths("config.yaml")

        assert len(paths) == 1
        assert paths[0] == user_config_dir / "config.yaml"

    def test_returns_both_paths_when_project_dir_set(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return both project-local and user-global paths."""
        paths = get_all_config_paths("config.yaml")

        assert len(paths) == 2
        assert paths[0] == mock_project_dir / "config.yaml"  # project-local first
        assert paths[1] == user_config_dir / "config.yaml"  # user-global second

    def test_precedence_order(self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path) -> None:
        """Should return paths in correct precedence order."""
        paths = get_all_config_paths("config.yaml")

        # First path should be project-local (higher precedence)
        assert paths[0] == mock_project_dir / "config.yaml"
        # Second path should be user-global (lower precedence)
        assert paths[1] == user_config_dir / "config.yaml"

    def test_returns_list_of_paths(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return a list of Path objects."""
        paths = get_all_config_paths("config.yaml")

        assert isinstance(paths, list)
        assert all(isinstance(p, Path) for p in paths)

    def test_paths_may_not_exist(self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path) -> None:
        """Should return paths even if files don't exist."""
        paths = get_all_config_paths("nonexistent.yaml")

        # Should have entries even though files don't exist
        assert len(paths) == 2
        # Paths are returned but files don't exist
        assert all(not p.exists() for p in paths)

    def test_works_with_different_filenames(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should work with any filename."""
        filenames = ["config.yaml", "preferences.yaml", "settings.json"]

        for filename in filenames:
            paths = get_all_config_paths(filename)
            assert paths[-1] == user_config_dir / filename

    def test_raises_on_empty_filename(self, mock_home: Path) -> None:
        """Should raise error when filename is empty."""
        with pytest.raises(ConfigLoaderError, match="cannot be empty"):
            get_all_config_paths("")

    def test_raises_on_filename_with_slash(self, mock_home: Path) -> None:
        """Should raise error when filename contains path separators."""
        with pytest.raises(ConfigLoaderError, match="path separators"):
            get_all_config_paths("subdir/config.yaml")

    def test_raises_on_filename_with_backslash(self, mock_home: Path) -> None:
        """Should raise error when filename contains backslash."""
        with pytest.raises(ConfigLoaderError, match="path separators"):
            get_all_config_paths("subdir\\config.yaml")


class TestFindConfigFile:
    """Tests for find_config_file()."""

    def test_returns_none_when_no_files_exist(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return None when no config files exist."""
        result = find_config_file("nonexistent.yaml")

        assert result is None

    def test_returns_user_global_when_only_it_exists(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return user-global path when only it exists."""
        # Create only user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        result = find_config_file("config.yaml")

        assert result == user_config

    def test_returns_project_local_when_only_it_exists(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return project-local path when only it exists."""
        # Create only project-local config
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: config")

        result = find_config_file("config.yaml")

        assert result == project_config

    def test_returns_project_local_when_both_exist(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should prefer project-local over user-global when both exist."""
        # Create both configs
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: config")

        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        result = find_config_file("config.yaml")

        # Should return project-local (higher precedence)
        assert result == project_config

    def test_returns_none_when_no_project_dir_and_no_files(
        self, mock_home: Path, user_config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return None when no project dir set and no files exist."""
        # Unset project dir
        monkeypatch.delenv("MYCELIUM_PROJECT_DIR", raising=False)

        result = find_config_file("nonexistent.yaml")

        assert result is None

    def test_works_with_different_filenames(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should work with any filename."""
        # Create a config file
        config = user_config_dir / "preferences.yaml"
        config.write_text("preferences: data")

        result = find_config_file("preferences.yaml")

        assert result == config

    def test_returns_path_object_or_none(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should return Path object or None."""
        # Test None case
        result1 = find_config_file("nonexistent.yaml")
        assert result1 is None

        # Test Path case
        config = user_config_dir / "config.yaml"
        config.write_text("data")
        result2 = find_config_file("config.yaml")
        assert isinstance(result2, Path)

    def test_raises_on_empty_filename(self, mock_home: Path) -> None:
        """Should raise error when filename is empty."""
        with pytest.raises(ConfigLoaderError, match="cannot be empty"):
            find_config_file("")

    def test_raises_on_filename_with_slash(self, mock_home: Path) -> None:
        """Should raise error when filename contains path separators."""
        with pytest.raises(ConfigLoaderError, match="path separators"):
            find_config_file("subdir/config.yaml")


class TestPrecedenceScenarios:
    """Test realistic configuration precedence scenarios."""

    def test_project_overrides_user_global(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Project-local config should override user-global config."""
        # Create both configs with different values
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("source: user")

        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("source: project")

        # Should find project-local first
        result = find_config_file("config.yaml")
        assert result == project_config

    def test_user_global_fallback(self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path) -> None:
        """Should fall back to user-global when project-local doesn't exist."""
        # Create only user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("source: user")

        result = find_config_file("config.yaml")
        assert result == user_config

    def test_no_project_dir_uses_user_global(
        self, mock_home: Path, user_config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use user-global when no project directory is set."""
        # Unset project dir
        monkeypatch.delenv("MYCELIUM_PROJECT_DIR", raising=False)

        # Create user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("source: user")

        result = find_config_file("config.yaml")
        assert result == user_config

    def test_multiple_config_files_independent(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Different config files can exist at different levels."""
        # Create different configs at different levels
        user_prefs = user_config_dir / "preferences.yaml"
        user_prefs.write_text("user: prefs")

        project_secrets = mock_project_dir / "secrets.yaml"
        project_secrets.write_text("project: secrets")

        # Each should be found at their respective level
        assert find_config_file("preferences.yaml") == user_prefs
        assert find_config_file("secrets.yaml") == project_secrets


class TestEnvironmentVariableHandling:
    """Test environment variable handling."""

    def test_respects_mycelium_project_dir(
        self, mock_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should respect MYCELIUM_PROJECT_DIR environment variable."""
        # Set custom project dir
        custom_project = tmp_path / "custom_project" / ".mycelium"
        custom_project.mkdir(parents=True)
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(custom_project))

        paths = get_all_config_paths("config.yaml")

        # First path should be the custom project dir
        assert paths[0] == custom_project / "config.yaml"

    def test_handles_missing_mycelium_project_dir(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should work when MYCELIUM_PROJECT_DIR is not set."""
        # Ensure variable is not set
        monkeypatch.delenv("MYCELIUM_PROJECT_DIR", raising=False)

        paths = get_all_config_paths("config.yaml")

        # Should only return user-global path
        assert len(paths) == 1

    def test_project_dir_with_special_characters(
        self, mock_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle project directories with special characters."""
        # Create project dir with spaces
        special_project = tmp_path / "my project" / ".mycelium"
        special_project.mkdir(parents=True)
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(special_project))

        paths = get_all_config_paths("config.yaml")

        assert paths[0] == special_project / "config.yaml"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_project_directory(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle non-existent project directory gracefully."""
        # Set non-existent project dir
        nonexistent = Path("/nonexistent/path/.mycelium")
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(nonexistent))

        # Should not raise error, just return None since file doesn't exist
        result = find_config_file("config.yaml")
        assert result is None

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks require special privileges on Windows")
    def test_symlink_handling(self, mock_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should follow symlinks correctly."""
        # Create real directory with config
        real_dir = tmp_path / "real" / ".mycelium"
        real_dir.mkdir(parents=True)
        real_config = real_dir / "config.yaml"
        real_config.write_text("real: config")

        # Create symlink to real directory
        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir.parent, target_is_directory=True)

        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(link_dir / ".mycelium"))

        result = find_config_file("config.yaml")

        # Should find config through symlink
        assert result is not None
        assert result.read_text() == "real: config"

    def test_empty_config_file(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should find empty config files."""
        # Create empty config
        empty_config = user_config_dir / "config.yaml"
        empty_config.write_text("")

        result = find_config_file("config.yaml")

        assert result == empty_config
        assert result.exists()

    def test_very_long_filename(self, mock_home: Path, user_config_dir: Path) -> None:
        """Should handle very long filenames."""
        # Create config with long name (but not too long for filesystem)
        long_name = "x" * 200 + ".yaml"
        long_config = user_config_dir / long_name
        long_config.write_text("data")

        result = find_config_file(long_name)

        assert result == long_config


class TestIntegration:
    """Integration tests for realistic usage patterns."""

    def test_typical_config_loading_workflow(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Test typical config loading workflow."""
        # 1. Create user-global defaults
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("default: config")

        # 2. Override with project-local
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: override")

        # 3. Load config (should get project-local)
        result = find_config_file("config.yaml")
        assert result == project_config

    def test_checking_all_config_locations(self, mock_home: Path, mock_project_dir: Path) -> None:
        """Test checking all possible config locations."""
        paths = get_all_config_paths("config.yaml")

        # Should have both locations
        assert len(paths) == 2

        # Can iterate through to find first existing config
        for path in paths:
            if path.exists():
                # Found config
                break
        else:
            # No config found, use defaults
            pass

    def test_config_migration_scenario(self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path) -> None:
        """Test migrating config from user-global to project-local."""
        # Start with user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        assert find_config_file("config.yaml") == user_config

        # Migrate to project-local
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("migrated: config")

        # Should now prefer project-local
        assert find_config_file("config.yaml") == project_config


class TestLogging:
    """Test logging behavior."""

    def test_logs_debug_info(self, mock_home: Path, user_config_dir: Path, caplog) -> None:
        """Should log debug information."""
        import logging

        caplog.set_level(logging.DEBUG)

        get_config_path("config.yaml")

        # Should have debug logs
        assert any("Getting config path" in record.message for record in caplog.records)

    def test_logs_config_found(self, mock_home: Path, user_config_dir: Path, caplog) -> None:
        """Should log when config is found."""
        import logging

        caplog.set_level(logging.INFO)

        # Create config
        config = user_config_dir / "config.yaml"
        config.write_text("data")

        find_config_file("config.yaml")

        # Should log that config was found
        assert any("Found config file" in record.message for record in caplog.records)
