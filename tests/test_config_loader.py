"""Tests for hierarchical configuration loading.

This test suite provides comprehensive coverage of the configuration loader
module, testing precedence order, environment variable handling, and edge cases.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

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
    - Returns the temp home path for use in tests
    """
    home = tmp_path / "home"
    home.mkdir()

    # Set HOME to temp directory
    monkeypatch.setenv("HOME", str(home))

    # Clear all XDG variables to test defaults
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
    config_dir = get_config_dir()
    return config_dir


class TestGetConfigPath:
    """Tests for get_config_path()."""

    def test_returns_user_global_when_no_project_dir(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
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

    def test_works_with_different_filenames(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
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

    def test_does_not_create_files(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should not create any files."""
        path = get_config_path("config.yaml")

        assert not path.exists()


class TestGetAllConfigPaths:
    """Tests for get_all_config_paths()."""

    def test_returns_only_user_global_when_no_project_dir(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should return only user-global path when MYCELIUM_PROJECT_DIR not set."""
        paths = get_all_config_paths("config.yaml")

        assert len(paths) == 1
        assert paths[0] == user_config_dir / "config.yaml"

    def test_returns_both_paths_when_project_dir_set(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return both paths when MYCELIUM_PROJECT_DIR is set."""
        paths = get_all_config_paths("config.yaml")

        assert len(paths) == 2
        assert paths[0] == mock_project_dir / "config.yaml"  # Project-local first
        assert paths[1] == user_config_dir / "config.yaml"  # User-global second

    def test_precedence_order(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return paths in correct precedence order."""
        paths = get_all_config_paths("config.yaml")

        # Project-local should come before user-global
        assert paths[0] == mock_project_dir / "config.yaml"
        assert paths[1] == user_config_dir / "config.yaml"

    def test_returns_list_of_paths(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should return a list of Path objects."""
        paths = get_all_config_paths("config.yaml")

        assert isinstance(paths, list)
        assert all(isinstance(p, Path) for p in paths)

    def test_paths_may_not_exist(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should return paths even if they don't exist."""
        paths = get_all_config_paths("config.yaml")

        # None of the paths exist yet
        assert all(not p.exists() for p in paths)

        # But they should still be returned
        assert len(paths) == 2

    def test_works_with_different_filenames(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should work with any filename."""
        filenames = ["config.yaml", "preferences.yaml", "settings.json"]

        for filename in filenames:
            paths = get_all_config_paths(filename)
            assert all(str(p).endswith(filename) for p in paths)

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

    def test_returns_none_when_no_files_exist(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should return None when no config files exist."""
        result = find_config_file("config.yaml")

        assert result is None

    def test_returns_user_global_when_only_it_exists(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
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
        """Should prefer project-local when both exist."""
        # Create both configs
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: config")

        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        result = find_config_file("config.yaml")

        # Should return project-local (higher precedence)
        assert result == project_config

    def test_returns_none_when_no_project_dir_and_no_files(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should return None when MYCELIUM_PROJECT_DIR not set and no files exist."""
        result = find_config_file("config.yaml")

        assert result is None

    def test_works_with_different_filenames(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should work with any filename."""
        # Create different config files
        (user_config_dir / "config.yaml").write_text("config")
        (user_config_dir / "preferences.yaml").write_text("prefs")

        result1 = find_config_file("config.yaml")
        result2 = find_config_file("preferences.yaml")
        result3 = find_config_file("missing.yaml")

        assert result1 == user_config_dir / "config.yaml"
        assert result2 == user_config_dir / "preferences.yaml"
        assert result3 is None

    def test_returns_path_object_or_none(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should return Path object or None."""
        # No file exists
        result1 = find_config_file("config.yaml")
        assert result1 is None

        # Create file
        (user_config_dir / "config.yaml").write_text("config")
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
    """Tests for various precedence scenarios."""

    def test_project_overrides_user_global(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Project-local config should override user-global."""
        # Create both with different content
        project_config = mock_project_dir / "config.yaml"
        project_config.write_text("project: override")

        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: default")

        # find_config_file should return project-local
        result = find_config_file("config.yaml")
        assert result == project_config
        assert result.read_text() == "project: override"

    def test_user_global_fallback(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should fall back to user-global when project-local missing."""
        # Create only user-global
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: default")

        result = find_config_file("config.yaml")
        assert result == user_config

    def test_no_project_dir_uses_user_global(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should use user-global when MYCELIUM_PROJECT_DIR not set."""
        # Create user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("user: config")

        result = find_config_file("config.yaml")
        assert result == user_config

    def test_multiple_config_files_independent(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Different config files should be resolved independently."""
        # Create different files in different locations
        (mock_project_dir / "config.yaml").write_text("project")
        (user_config_dir / "preferences.yaml").write_text("user")

        result1 = find_config_file("config.yaml")
        result2 = find_config_file("preferences.yaml")
        result3 = find_config_file("missing.yaml")

        # config.yaml from project-local
        assert result1 == mock_project_dir / "config.yaml"

        # preferences.yaml from user-global
        assert result2 == user_config_dir / "preferences.yaml"

        # missing.yaml not found
        assert result3 is None


class TestEnvironmentVariableHandling:
    """Tests for environment variable handling."""

    def test_respects_mycelium_project_dir(
        self, mock_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should respect MYCELIUM_PROJECT_DIR when set."""
        project_dir = tmp_path / "custom_project" / ".mycelium"
        project_dir.mkdir(parents=True)
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(project_dir))

        paths = get_all_config_paths("config.yaml")

        assert paths[0] == project_dir / "config.yaml"

    def test_handles_missing_mycelium_project_dir(
        self, mock_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle MYCELIUM_PROJECT_DIR not being set."""
        monkeypatch.delenv("MYCELIUM_PROJECT_DIR", raising=False)

        paths = get_all_config_paths("config.yaml")

        # Should only return user-global path
        assert len(paths) == 1

    def test_project_dir_with_special_characters(
        self, mock_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle project directory with special characters."""
        project_dir = tmp_path / "project with spaces & chars" / ".mycelium"
        project_dir.mkdir(parents=True)
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(project_dir))

        paths = get_all_config_paths("config.yaml")

        assert paths[0] == project_dir / "config.yaml"
        assert "project with spaces & chars" in str(paths[0])


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_nonexistent_project_directory(
        self, mock_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle MYCELIUM_PROJECT_DIR pointing to nonexistent directory."""
        nonexistent = mock_home / "nonexistent" / ".mycelium"
        monkeypatch.setenv("MYCELIUM_PROJECT_DIR", str(nonexistent))

        # Should not raise error
        paths = get_all_config_paths("config.yaml")

        # Should include the path even if it doesn't exist
        assert paths[0] == nonexistent / "config.yaml"

        # find_config_file should return None
        result = find_config_file("config.yaml")
        assert result is None

    def test_symlink_handling(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should handle symlinked configuration files."""
        # Create real file
        real_file = user_config_dir / "real_config.yaml"
        real_file.write_text("real: config")

        # Create symlink
        symlink = user_config_dir / "config.yaml"
        symlink.symlink_to(real_file)

        result = find_config_file("config.yaml")

        # Should find the symlink
        assert result == symlink
        assert result.exists()
        assert result.read_text() == "real: config"

    def test_empty_config_file(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should handle empty configuration files."""
        # Create empty file
        config_file = user_config_dir / "config.yaml"
        config_file.touch()

        result = find_config_file("config.yaml")

        # Should still find it
        assert result == config_file
        assert result.exists()
        assert result.stat().st_size == 0

    def test_very_long_filename(
        self, mock_home: Path, user_config_dir: Path
    ) -> None:
        """Should handle very long filenames."""
        # Create file with long name (but not too long for filesystem)
        long_name = "config_" + ("x" * 200) + ".yaml"
        long_file = user_config_dir / long_name
        long_file.write_text("config")

        result = find_config_file(long_name)

        assert result == long_file


class TestIntegration:
    """Integration tests for configuration loading workflows."""

    def test_typical_config_loading_workflow(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should support typical configuration loading workflow."""
        # Step 1: Check if config exists
        config_path = find_config_file("config.yaml")
        assert config_path is None  # Doesn't exist yet

        # Step 2: Create user-global default config
        default_config_path = get_config_path("config.yaml", prefer_project=False)
        default_config_path.write_text("default: settings")

        # Step 3: Find config (should find user-global)
        config_path = find_config_file("config.yaml")
        assert config_path == default_config_path
        assert config_path.read_text() == "default: settings"

        # Step 4: Create project-local override
        project_config_path = get_config_path("config.yaml", prefer_project=True)
        project_config_path.write_text("project: override")

        # Step 5: Find config (should find project-local)
        config_path = find_config_file("config.yaml")
        assert config_path == project_config_path
        assert config_path.read_text() == "project: override"

    def test_checking_all_config_locations(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should support checking all config locations."""
        # Create configs in different locations
        (mock_project_dir / "config.yaml").write_text("project")
        (user_config_dir / "config.yaml").write_text("user")

        # Get all locations
        all_paths = get_all_config_paths("config.yaml")

        # Check which ones exist
        existing = [p for p in all_paths if p.exists()]
        assert len(existing) == 2

        # Verify precedence
        first_existing = existing[0]
        assert first_existing == mock_project_dir / "config.yaml"

    def test_config_migration_scenario(
        self, mock_home: Path, mock_project_dir: Path, user_config_dir: Path
    ) -> None:
        """Should support config migration from user-global to project-local."""
        # Start with user-global config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("version: 1\ndefaults: true")

        # Find config (user-global)
        current_config = find_config_file("config.yaml")
        assert current_config == user_config

        # Create project-local config (migration)
        project_config = get_config_path("config.yaml", prefer_project=True)

        # Copy content and modify
        content = current_config.read_text()
        project_config.write_text(content.replace("version: 1", "version: 2"))

        # Find config (now project-local)
        new_config = find_config_file("config.yaml")
        assert new_config == project_config
        assert "version: 2" in new_config.read_text()

        # User-global still exists as fallback
        assert user_config.exists()


class TestLogging:
    """Tests for logging behavior."""

    def test_logs_debug_info(
        self, mock_home: Path, user_config_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug information when finding configs."""
        import logging

        caplog.set_level(logging.DEBUG, logger="mycelium_onboarding.config_loader")

        get_config_path("config.yaml")

        # Should have debug logs
        assert any("Getting config path" in record.message for record in caplog.records)

    def test_logs_config_found(
        self, mock_home: Path, user_config_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log when config file is found."""
        import logging

        caplog.set_level(logging.INFO, logger="mycelium_onboarding.config_loader")

        # Create config
        (user_config_dir / "config.yaml").write_text("config")

        find_config_file("config.yaml")

        # Should have info log about finding config
        assert any("Found config file" in record.message for record in caplog.records)
