"""Tests for XDG directory management.

This test suite provides comprehensive coverage of the XDG directory management
module, including edge cases, platform-specific behavior, and error handling.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from mycelium_onboarding.xdg_dirs import (
    XDGDirectoryError,
    clear_cache,
    get_all_dirs,
    get_cache_dir,
    get_config_dir,
    get_data_dir,
    get_state_dir,
)


@pytest.fixture
def mock_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary home directory for testing.

    This fixture:
    - Creates a temporary directory to use as HOME
    - Clears all XDG environment variables
    - Returns the temp home path for use in tests
    """
    home = tmp_path / "home"
    home.mkdir()

    if sys.platform == "win32":
        # On Windows, mock LOCALAPPDATA and APPDATA for XDG functions
        local_appdata = home / "AppData" / "Local"
        local_appdata.mkdir(parents=True)
        monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))

        appdata = home / "AppData" / "Roaming"
        appdata.mkdir(parents=True)
        monkeypatch.setenv("APPDATA", str(appdata))
    else:
        # On Unix, mock HOME
        monkeypatch.setenv("HOME", str(home))

    # Clear all XDG variables to test defaults
    for var in ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"]:
        monkeypatch.delenv(var, raising=False)

    # Clear LRU cache to ensure fresh lookups
    get_config_dir.cache_clear()
    get_data_dir.cache_clear()
    get_cache_dir.cache_clear()
    get_state_dir.cache_clear()

    return home


@pytest.fixture
def mock_xdg_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Create temporary XDG directories for testing.

    Returns a dict mapping XDG variable names to their temp paths.
    """
    xdg_dirs = {
        "XDG_CONFIG_HOME": tmp_path / "config",
        "XDG_DATA_HOME": tmp_path / "data",
        "XDG_CACHE_HOME": tmp_path / "cache",
        "XDG_STATE_HOME": tmp_path / "state",
    }

    for var, path in xdg_dirs.items():
        path.mkdir(parents=True)
        monkeypatch.setenv(var, str(path))

    # Clear LRU cache
    get_config_dir.cache_clear()
    get_data_dir.cache_clear()
    get_cache_dir.cache_clear()
    get_state_dir.cache_clear()

    return xdg_dirs


class TestConfigDir:
    """Tests for get_config_dir()."""

    def test_default_location(self, mock_home: Path) -> None:
        """Should use platform-appropriate default location."""
        config_dir = get_config_dir()

        if sys.platform == "win32":
            # On Windows, config goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "mycelium" / "config"
        else:
            expected = mock_home / ".config" / "mycelium"

        assert config_dir == expected
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_respects_xdg_config_home(self, mock_xdg_dirs: dict[str, Path]) -> None:
        """Should respect XDG_CONFIG_HOME when set."""
        config_dir = get_config_dir()

        expected = mock_xdg_dirs["XDG_CONFIG_HOME"] / "mycelium"
        assert config_dir == expected
        assert config_dir.exists()

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should accept custom project names."""
        config_dir = get_config_dir("custom_project")

        if sys.platform == "win32":
            # On Windows, config goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "custom_project" / "config"
        else:
            expected = mock_home / ".config" / "custom_project"

        assert config_dir == expected
        assert config_dir.exists()

    def test_creates_parent_directories(self, mock_home: Path) -> None:
        """Should create parent directories if missing."""
        # Remove config parent directory
        if sys.platform == "win32":
            config_parent = mock_home / "AppData" / "Local"
        else:
            config_parent = mock_home / ".config"

        if config_parent.exists():
            import shutil

            shutil.rmtree(config_parent)

        config_dir = get_config_dir()

        assert config_dir.exists()
        assert config_parent.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_permissions(self, mock_home: Path) -> None:
        """Should set restrictive permissions (0700)."""
        config_dir = get_config_dir()

        stat = config_dir.stat()
        mode = stat.st_mode & 0o777

        # Should be rwx------ (0700)
        assert mode == 0o700

    def test_caching(self, mock_home: Path) -> None:
        """Should cache result for repeated calls."""
        dir1 = get_config_dir()
        dir2 = get_config_dir()

        # Should return same object (cached)
        assert dir1 is dir2

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_not_writable_raises_error(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error if directory is not writable."""
        config_dir = mock_home / ".config" / "mycelium"
        config_dir.mkdir(parents=True)

        # Make directory read-only
        config_dir.chmod(0o444)

        # Clear cache to force re-check
        get_config_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError, match="not writable"):
                get_config_dir()
        finally:
            # Cleanup: restore permissions
            config_dir.chmod(0o755)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_mkdir_oserror(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise XDGDirectoryError when mkdir fails."""
        get_config_dir.cache_clear()

        # Mock Path.mkdir to raise OSError
        original_mkdir = Path.mkdir

        def mock_mkdir(*args: Any, **kwargs: Any) -> None:
            raise OSError("Mock error")

        with (
            patch.object(Path, "mkdir", mock_mkdir),
            pytest.raises(XDGDirectoryError, match="Failed to create config directory"),
        ):
            get_config_dir()

        # Restore original
        Path.mkdir = original_mkdir


class TestDataDir:
    """Tests for get_data_dir()."""

    def test_default_location(self, mock_home: Path) -> None:
        """Should use platform-appropriate default location."""
        data_dir = get_data_dir()

        if sys.platform == "win32":
            # On Windows, data goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "mycelium" / "data"
        else:
            expected = mock_home / ".local" / "share" / "mycelium"

        assert data_dir == expected
        assert data_dir.exists()

    def test_respects_xdg_data_home(self, mock_xdg_dirs: dict[str, Path]) -> None:
        """Should respect XDG_DATA_HOME when set."""
        data_dir = get_data_dir()

        expected = mock_xdg_dirs["XDG_DATA_HOME"] / "mycelium"
        assert data_dir == expected

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should accept custom project names."""
        data_dir = get_data_dir("custom_project")

        if sys.platform == "win32":
            # On Windows, data goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "custom_project" / "data"
        else:
            expected = mock_home / ".local" / "share" / "custom_project"

        assert data_dir == expected

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_permissions(self, mock_home: Path) -> None:
        """Should set permissions (0755)."""
        data_dir = get_data_dir()

        stat = data_dir.stat()
        mode = stat.st_mode & 0o777

        # Should be rwxr-xr-x (0755)
        assert mode == 0o755

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_not_writable_raises_error(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error if directory is not writable."""
        data_dir = mock_home / ".local" / "share" / "mycelium"
        data_dir.mkdir(parents=True)
        data_dir.chmod(0o444)

        get_data_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError, match="not writable"):
                get_data_dir()
        finally:
            data_dir.chmod(0o755)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_mkdir_oserror(self, mock_home: Path) -> None:
        """Should raise XDGDirectoryError when mkdir fails."""
        get_data_dir.cache_clear()

        # Mock to raise OSError
        with (
            patch.object(Path, "mkdir", side_effect=OSError("Mock error")),
            pytest.raises(XDGDirectoryError, match="Failed to create data directory"),
        ):
            get_data_dir()


class TestCacheDir:
    """Tests for get_cache_dir()."""

    def test_default_location(self, mock_home: Path) -> None:
        """Should use platform-appropriate default location."""
        cache_dir = get_cache_dir()

        if sys.platform == "win32":
            # On Windows, cache goes in a Cache subdirectory (capital C)
            expected = mock_home / "AppData" / "Local" / "mycelium" / "Cache"
        else:
            expected = mock_home / ".cache" / "mycelium"

        assert cache_dir == expected
        assert cache_dir.exists()

    def test_respects_xdg_cache_home(self, mock_xdg_dirs: dict[str, Path]) -> None:
        """Should respect XDG_CACHE_HOME when set."""
        cache_dir = get_cache_dir()

        expected = mock_xdg_dirs["XDG_CACHE_HOME"] / "mycelium"
        assert cache_dir == expected

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should accept custom project names."""
        cache_dir = get_cache_dir("custom_project")

        if sys.platform == "win32":
            # On Windows, cache goes in a Cache subdirectory (capital C)
            expected = mock_home / "AppData" / "Local" / "custom_project" / "Cache"
        else:
            expected = mock_home / ".cache" / "custom_project"

        assert cache_dir == expected

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_permissions(self, mock_home: Path) -> None:
        """Should set permissions (0755)."""
        cache_dir = get_cache_dir()

        stat = cache_dir.stat()
        mode = stat.st_mode & 0o777

        # Should be rwxr-xr-x (0755)
        assert mode == 0o755

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_not_writable_raises_error(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error if directory is not writable."""
        cache_dir = mock_home / ".cache" / "mycelium"
        cache_dir.mkdir(parents=True)
        cache_dir.chmod(0o444)

        get_cache_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError, match="not writable"):
                get_cache_dir()
        finally:
            cache_dir.chmod(0o755)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_mkdir_oserror(self, mock_home: Path) -> None:
        """Should raise XDGDirectoryError when mkdir fails."""
        get_cache_dir.cache_clear()

        # Mock to raise OSError
        with (
            patch.object(Path, "mkdir", side_effect=OSError("Mock error")),
            pytest.raises(XDGDirectoryError, match="Failed to create cache directory"),
        ):
            get_cache_dir()


class TestStateDir:
    """Tests for get_state_dir()."""

    def test_default_location(self, mock_home: Path) -> None:
        """Should use platform-appropriate default location."""
        state_dir = get_state_dir()

        if sys.platform == "win32":
            # On Windows, state goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "mycelium" / "state"
        else:
            expected = mock_home / ".local" / "state" / "mycelium"

        assert state_dir == expected
        assert state_dir.exists()

    def test_respects_xdg_state_home(self, mock_xdg_dirs: dict[str, Path]) -> None:
        """Should respect XDG_STATE_HOME when set."""
        state_dir = get_state_dir()

        expected = mock_xdg_dirs["XDG_STATE_HOME"] / "mycelium"
        assert state_dir == expected

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should accept custom project names."""
        state_dir = get_state_dir("custom_project")

        if sys.platform == "win32":
            # On Windows, state goes in a subdirectory
            expected = mock_home / "AppData" / "Local" / "custom_project" / "state"
        else:
            expected = mock_home / ".local" / "state" / "custom_project"

        assert state_dir == expected

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_permissions(self, mock_home: Path) -> None:
        """Should set restrictive permissions (0700)."""
        state_dir = get_state_dir()

        stat = state_dir.stat()
        mode = stat.st_mode & 0o777

        # Should be rwx------ (0700)
        assert mode == 0o700

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_not_writable_raises_error(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error if directory is not writable."""
        state_dir = mock_home / ".local" / "state" / "mycelium"
        state_dir.mkdir(parents=True)
        state_dir.chmod(0o444)

        get_state_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError, match="not writable"):
                get_state_dir()
        finally:
            state_dir.chmod(0o755)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_mkdir_oserror(self, mock_home: Path) -> None:
        """Should raise XDGDirectoryError when mkdir fails."""
        get_state_dir.cache_clear()

        # Mock to raise OSError
        with (
            patch.object(Path, "mkdir", side_effect=OSError("Mock error")),
            pytest.raises(XDGDirectoryError, match="Failed to create state directory"),
        ):
            get_state_dir()


class TestClearCache:
    """Tests for clear_cache()."""

    def test_clears_cache_contents(self, mock_home: Path) -> None:
        """Should remove all cache contents but preserve directory."""
        cache_dir = get_cache_dir()

        # Create some cache files
        (cache_dir / "file1.json").write_text("{}")
        (cache_dir / "file2.txt").write_text("data")
        subdir = cache_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.json").write_text("{}")

        # Clear cache
        clear_cache()

        # Directory should exist but be empty
        assert cache_dir.exists()
        assert list(cache_dir.iterdir()) == []

    def test_safe_when_cache_empty(self, mock_home: Path) -> None:
        """Should be safe to call on empty cache."""
        get_cache_dir()  # Create cache dir

        # Should not raise error
        clear_cache()

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should work with custom project names."""
        # Create custom cache with files
        cache_dir = get_cache_dir("custom")
        (cache_dir / "file.txt").write_text("data")

        # Clear custom cache
        clear_cache("custom")

        # Should be empty
        assert list(cache_dir.iterdir()) == []

    def test_oserror_on_unlink(self, mock_home: Path) -> None:
        """Should raise XDGDirectoryError if clearing fails."""
        cache_dir = get_cache_dir()
        (cache_dir / "file.txt").write_text("data")

        # Mock unlink to raise OSError
        with (
            patch.object(Path, "unlink", side_effect=OSError("Mock error")),
            pytest.raises(XDGDirectoryError, match="Failed to clear cache directory"),
        ):
            clear_cache()

    def test_clears_files_and_directories(self, mock_home: Path) -> None:
        """Should handle both files and directories."""
        cache_dir = get_cache_dir()

        # Create mixed content
        (cache_dir / "file.txt").write_text("data")
        subdir1 = cache_dir / "subdir1"
        subdir1.mkdir()
        (subdir1 / "nested.txt").write_text("nested")
        subdir2 = cache_dir / "subdir2"
        subdir2.mkdir()

        clear_cache()

        # All should be cleared
        assert list(cache_dir.iterdir()) == []


class TestGetAllDirs:
    """Tests for get_all_dirs()."""

    def test_returns_all_directories(self, mock_home: Path) -> None:
        """Should return dict with all XDG directories."""
        dirs = get_all_dirs()

        assert set(dirs.keys()) == {"config", "data", "cache", "state"}

        # All should be Path objects
        assert all(isinstance(p, Path) for p in dirs.values())

        # All should exist
        assert all(p.exists() for p in dirs.values())

    def test_custom_project_name(self, mock_home: Path) -> None:
        """Should work with custom project names."""
        dirs = get_all_dirs("custom")

        assert all("custom" in str(p) for p in dirs.values())

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_all_directories_writable(self, mock_home: Path) -> None:
        """Should ensure all directories are writable."""
        dirs = get_all_dirs()

        for path in dirs.values():
            assert os.access(path, os.W_OK), f"Directory not writable: {path}"


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_raises_on_permission_denied(self, mock_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise XDGDirectoryError on permission issues."""
        # Create a read-only parent directory
        readonly_dir = mock_home / "readonly"
        readonly_dir.mkdir(mode=0o444)

        # Try to create config dir inside read-only directory
        monkeypatch.setenv("XDG_CONFIG_HOME", str(readonly_dir))
        get_config_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError, match="Failed to create"):
                get_config_dir()
        finally:
            # Cleanup
            readonly_dir.chmod(0o755)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions not supported on Windows")
    def test_error_message_is_informative(self, mock_home: Path) -> None:
        """Should provide clear error messages."""
        config_dir = mock_home / ".config" / "mycelium"
        config_dir.mkdir(parents=True)
        config_dir.chmod(0o444)

        get_config_dir.cache_clear()

        try:
            with pytest.raises(XDGDirectoryError) as exc_info:
                get_config_dir()

            error_msg = str(exc_info.value)
            assert "not writable" in error_msg
            assert str(config_dir) in error_msg
        finally:
            config_dir.chmod(0o755)


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only test")
class TestPlatformSpecific:
    """Platform-specific tests."""

    def test_symlink_handling(self, mock_home: Path) -> None:
        """Should follow symlinks correctly."""
        # Create a symlinked config directory
        real_config = mock_home / "real_config"
        real_config.mkdir()

        symlink_config = mock_home / ".config"
        symlink_config.symlink_to(real_config)

        config_dir = get_config_dir()

        # Should work with symlinks
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_handles_special_characters_in_path(self, tmp_path: Path) -> None:
        """Should handle special characters in paths."""
        # Create home with special characters
        special_home = tmp_path / "home with spaces & chars"
        special_home.mkdir()

        import pytest

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("HOME", str(special_home))

        # Clear XDG vars
        for var in [
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
            "XDG_CACHE_HOME",
            "XDG_STATE_HOME",
        ]:
            monkeypatch.delenv(var, raising=False)

        get_config_dir.cache_clear()

        # Should handle special characters
        config_dir = get_config_dir()
        assert config_dir.exists()
        assert "home with spaces & chars" in str(config_dir)

        monkeypatch.undo()


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    def test_cache_can_be_cleared(self, mock_home: Path) -> None:
        """Should be able to clear LRU cache."""
        dir1 = get_config_dir()

        # Clear cache
        get_config_dir.cache_clear()

        dir2 = get_config_dir()

        # Should be different objects (cache was cleared)
        assert dir1 is not dir2
        # But same path
        assert dir1 == dir2

    def test_cache_per_project_name(self, mock_home: Path) -> None:
        """Should cache separately for different project names."""
        dir1 = get_config_dir("project1")
        dir2 = get_config_dir("project2")

        # Should be different directories
        assert dir1 != dir2
        assert "project1" in str(dir1)
        assert "project2" in str(dir2)


class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, mock_home: Path) -> None:
        """Should support full workflow of directory operations."""
        # Get all directories
        dirs = get_all_dirs()

        # On Windows, directories should be separate subdirectories
        # On Unix, they're in different parent paths
        # All should be unique paths
        unique_paths = {str(p) for p in dirs.values()}
        assert len(unique_paths) == 4, f"Expected 4 unique paths, got: {unique_paths}"

        # Create files in each directory
        (dirs["config"] / "config.yaml").write_text("key: value")
        (dirs["data"] / "data.json").write_text("{}")
        (dirs["cache"] / "cache.db").write_text("data")
        (dirs["state"] / "state.json").write_text("{}")

        # Verify files exist
        assert (dirs["config"] / "config.yaml").exists()
        assert (dirs["data"] / "data.json").exists()
        assert (dirs["cache"] / "cache.db").exists()
        assert (dirs["state"] / "state.json").exists()

        # Clear cache
        clear_cache()

        # Cache file should be gone
        assert not (dirs["cache"] / "cache.db").exists()

        # Other files should still exist
        assert (dirs["config"] / "config.yaml").exists()
        assert (dirs["data"] / "data.json").exists()
        assert (dirs["state"] / "state.json").exists()

    def test_concurrent_directory_creation(self, mock_home: Path) -> None:
        """Should handle concurrent directory creation safely."""
        from concurrent.futures import ThreadPoolExecutor

        # Clear caches
        get_config_dir.cache_clear()
        get_data_dir.cache_clear()
        get_cache_dir.cache_clear()
        get_state_dir.cache_clear()

        funcs = [get_config_dir, get_data_dir, get_cache_dir, get_state_dir]

        # Create directories concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda f: f(), funcs))

        # All should succeed and be valid paths
        assert all(isinstance(r, Path) for r in results)
        assert all(r.exists() for r in results)
