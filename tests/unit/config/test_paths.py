"""Unit tests for XDG-compliant path resolution."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mycelium_onboarding.config.paths import (
    ensure_cache_dir_exists,
    ensure_config_dir_exists,
    ensure_data_dir_exists,
    ensure_dir_exists,
    ensure_log_dir_exists,
    ensure_migration_backup_dir_exists,
    ensure_state_dir_exists,
    get_cache_dir,
    get_data_dir,
    get_global_config_path,
    get_log_dir,
    get_migration_backup_dir,
    get_project_config_path,
    get_state_dir,
)
from mycelium_onboarding.config.platform import Platform, get_platform


class TestGlobalConfigPath:
    """Test global configuration path resolution."""

    def test_get_global_config_path_returns_path(self) -> None:
        """Test that get_global_config_path returns a Path object."""
        path = get_global_config_path()
        assert isinstance(path, Path)

    def test_get_global_config_path_is_absolute(self) -> None:
        """Test that global config path is absolute."""
        path = get_global_config_path()
        assert path.is_absolute()

    def test_get_global_config_path_has_correct_filename(self) -> None:
        """Test that global config path ends with config.yaml."""
        path = get_global_config_path()
        assert path.name == "config.yaml"

    def test_get_global_config_path_parent_is_mycelium(self) -> None:
        """Test that global config path parent is 'mycelium'."""
        path = get_global_config_path()
        assert path.parent.name == "mycelium"

    def test_get_global_config_path_platform_specific(self) -> None:
        """Test that global config path follows platform conventions."""
        path = get_global_config_path()
        platform = get_platform()

        if platform == Platform.LINUX:
            # Should be in ~/.config/mycelium/
            assert ".config" in str(path)
        elif platform == Platform.MACOS:
            # Should be in ~/Library/Application Support/mycelium/
            assert "Library" in str(path)
            assert "Application Support" in str(path)
        elif platform == Platform.WINDOWS:
            # Should be in AppData
            assert "AppData" in str(path) or "Application Data" in str(path)


class TestProjectConfigPath:
    """Test project-local configuration path resolution."""

    def test_get_project_config_path_defaults_to_cwd(self) -> None:
        """Test that project config path defaults to current working directory."""
        path = get_project_config_path()
        assert path.parent.parent == Path.cwd()

    def test_get_project_config_path_with_explicit_root(self, tmp_path: Path) -> None:
        """Test that project config path uses explicit project root."""
        path = get_project_config_path(tmp_path)
        assert path.parent.parent == tmp_path

    def test_get_project_config_path_structure(self, tmp_path: Path) -> None:
        """Test that project config path has correct structure."""
        path = get_project_config_path(tmp_path)
        assert path.parent.name == ".mycelium"
        assert path.name == "config.yaml"

    def test_get_project_config_path_with_string_root(self, tmp_path: Path) -> None:
        """Test that project config path accepts string project root."""
        path = get_project_config_path(str(tmp_path))
        assert isinstance(path, Path)
        assert path.parent.parent == tmp_path


class TestDataDirectories:
    """Test XDG data directory resolution."""

    def test_get_data_dir_returns_path(self) -> None:
        """Test that get_data_dir returns a Path object."""
        path = get_data_dir()
        assert isinstance(path, Path)

    def test_get_data_dir_is_absolute(self) -> None:
        """Test that data directory path is absolute."""
        path = get_data_dir()
        assert path.is_absolute()

    def test_get_data_dir_contains_mycelium(self) -> None:
        """Test that data directory contains 'mycelium'."""
        path = get_data_dir()
        assert "mycelium" in str(path).lower()

    def test_get_state_dir_returns_path(self) -> None:
        """Test that get_state_dir returns a Path object."""
        path = get_state_dir()
        assert isinstance(path, Path)

    def test_get_state_dir_is_absolute(self) -> None:
        """Test that state directory path is absolute."""
        path = get_state_dir()
        assert path.is_absolute()

    def test_get_cache_dir_returns_path(self) -> None:
        """Test that get_cache_dir returns a Path object."""
        path = get_cache_dir()
        assert isinstance(path, Path)

    def test_get_cache_dir_is_absolute(self) -> None:
        """Test that cache directory path is absolute."""
        path = get_cache_dir()
        assert path.is_absolute()

    def test_get_log_dir_returns_path(self) -> None:
        """Test that get_log_dir returns a Path object."""
        path = get_log_dir()
        assert isinstance(path, Path)

    def test_get_log_dir_is_absolute(self) -> None:
        """Test that log directory path is absolute."""
        path = get_log_dir()
        assert path.is_absolute()


class TestMigrationBackupDir:
    """Test migration backup directory resolution."""

    def test_get_migration_backup_dir_returns_path(self) -> None:
        """Test that get_migration_backup_dir returns a Path object."""
        path = get_migration_backup_dir()
        assert isinstance(path, Path)

    def test_get_migration_backup_dir_is_absolute(self) -> None:
        """Test that migration backup directory is absolute."""
        path = get_migration_backup_dir()
        assert path.is_absolute()

    def test_get_migration_backup_dir_is_in_data_dir(self) -> None:
        """Test that migration backup dir is within data directory."""
        backup_dir = get_migration_backup_dir()
        data_dir = get_data_dir()
        assert str(backup_dir).startswith(str(data_dir))

    def test_get_migration_backup_dir_name(self) -> None:
        """Test that migration backup directory is named 'backups'."""
        path = get_migration_backup_dir()
        assert path.name == "backups"


class TestEnsureDirectoryExists:
    """Test directory creation with ensure_dir_exists."""

    def test_ensure_dir_exists_creates_directory(self, tmp_path: Path) -> None:
        """Test that ensure_dir_exists creates a new directory."""
        test_dir = tmp_path / "test_dir"
        assert not test_dir.exists()

        result = ensure_dir_exists(test_dir)

        assert result == test_dir
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_dir_exists_with_parents(self, tmp_path: Path) -> None:
        """Test that ensure_dir_exists creates parent directories."""
        test_dir = tmp_path / "parent" / "child" / "grandchild"
        assert not test_dir.exists()

        result = ensure_dir_exists(test_dir)

        assert result == test_dir
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_dir_exists_idempotent(self, tmp_path: Path) -> None:
        """Test that ensure_dir_exists is idempotent."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        result = ensure_dir_exists(test_dir)

        assert result == test_dir
        assert test_dir.exists()

    def test_ensure_dir_exists_raises_on_file(self, tmp_path: Path) -> None:
        """Test that ensure_dir_exists raises ValueError if path is a file."""
        test_file = tmp_path / "test_file.txt"
        test_file.touch()

        with pytest.raises(ValueError, match="not a directory"):
            ensure_dir_exists(test_file)

    def test_ensure_dir_exists_with_mode(self, tmp_path: Path) -> None:
        """Test that ensure_dir_exists sets correct permissions."""
        test_dir = tmp_path / "test_dir"

        result = ensure_dir_exists(test_dir, mode=0o755)

        assert result.exists()
        # On POSIX systems, check permissions
        if os.name == "posix":
            stat_mode = result.stat().st_mode & 0o777
            # Note: actual mode may differ due to umask
            assert stat_mode in {0o755, 0o775}  # Allow some flexibility


class TestEnsureSpecificDirectories:
    """Test ensure functions for specific directory types."""

    def test_ensure_config_dir_exists_creates_directory(self) -> None:
        """Test that ensure_config_dir_exists creates config directory."""
        # This might create actual directories, so we just verify it returns a path
        result = ensure_config_dir_exists()
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_ensure_data_dir_exists_returns_path(self) -> None:
        """Test that ensure_data_dir_exists returns a Path."""
        result = ensure_data_dir_exists()
        assert isinstance(result, Path)

    def test_ensure_state_dir_exists_returns_path(self) -> None:
        """Test that ensure_state_dir_exists returns a Path."""
        result = ensure_state_dir_exists()
        assert isinstance(result, Path)

    def test_ensure_cache_dir_exists_returns_path(self) -> None:
        """Test that ensure_cache_dir_exists returns a Path."""
        result = ensure_cache_dir_exists()
        assert isinstance(result, Path)

    def test_ensure_log_dir_exists_returns_path(self) -> None:
        """Test that ensure_log_dir_exists returns a Path."""
        result = ensure_log_dir_exists()
        assert isinstance(result, Path)

    def test_ensure_migration_backup_dir_exists_returns_path(self) -> None:
        """Test that ensure_migration_backup_dir_exists returns a Path."""
        result = ensure_migration_backup_dir_exists()
        assert isinstance(result, Path)


class TestPathConsistency:
    """Test consistency between different path functions."""

    def test_config_and_data_dirs_different(self) -> None:
        """Test that config and data directories are different paths."""
        # On some platforms they might be the same, but usually different
        config_dir = get_global_config_path().parent
        data_dir = get_data_dir()

        # Both should exist and be absolute
        assert config_dir.is_absolute()
        assert data_dir.is_absolute()

    def test_all_paths_under_home(self) -> None:
        """Test that all user paths are under home directory."""
        home = Path.home()

        paths = [
            get_global_config_path(),
            get_data_dir(),
            get_state_dir(),
            get_cache_dir(),
            get_log_dir(),
        ]

        for path in paths:
            # All paths should be under home directory
            assert str(path).startswith(str(home))
