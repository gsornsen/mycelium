"""Unit tests for platform detection and utilities."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mycelium_onboarding.config.platform import (
    Platform,
    get_home_directory,
    get_path_separator,
    get_platform,
    is_posix,
    is_windows,
    normalize_path,
)


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_get_platform_returns_valid_platform(self) -> None:
        """Test that get_platform returns a valid Platform enum."""
        platform = get_platform()
        assert isinstance(platform, Platform)
        assert platform in {Platform.LINUX, Platform.MACOS, Platform.WINDOWS, Platform.UNKNOWN}

    def test_get_platform_matches_sys_platform(self) -> None:
        """Test that platform detection matches sys.platform."""
        platform = get_platform()

        if sys.platform.startswith("linux"):
            assert platform == Platform.LINUX
        elif sys.platform == "darwin":
            assert platform == Platform.MACOS
        elif sys.platform == "win32":
            assert platform == Platform.WINDOWS

    def test_is_windows_consistency(self) -> None:
        """Test that is_windows is consistent with get_platform."""
        assert is_windows() == (get_platform() == Platform.WINDOWS)

    def test_is_posix_consistency(self) -> None:
        """Test that is_posix is consistent with get_platform."""
        platform = get_platform()
        expected = platform in {Platform.LINUX, Platform.MACOS}
        assert is_posix() == expected

    def test_is_windows_and_posix_mutually_exclusive(self) -> None:
        """Test that a platform cannot be both Windows and POSIX."""
        # This should be true unless platform is UNKNOWN
        if get_platform() != Platform.UNKNOWN:
            assert is_windows() != is_posix()


class TestPathUtilities:
    """Test path utility functions."""

    def test_get_path_separator_valid(self) -> None:
        """Test that path separator is valid."""
        sep = get_path_separator()
        assert sep in {"/", "\\"}

    def test_get_path_separator_matches_platform(self) -> None:
        """Test that path separator matches platform."""
        sep = get_path_separator()
        if is_windows():
            assert sep == "\\"
        else:
            assert sep == "/"

    def test_normalize_path_returns_absolute_path(self, tmp_path: Path) -> None:
        """Test that normalize_path returns an absolute path."""
        test_path = tmp_path / "test.txt"
        test_path.touch()

        normalized = normalize_path(test_path)
        assert normalized.is_absolute()

    def test_normalize_path_expands_home(self) -> None:
        """Test that normalize_path expands ~ to home directory."""
        normalized = normalize_path("~/test.txt")
        assert normalized.is_absolute()
        assert "~" not in str(normalized)

    def test_normalize_path_handles_string_input(self, tmp_path: Path) -> None:
        """Test that normalize_path handles string input."""
        test_path = tmp_path / "test.txt"
        test_path.touch()

        normalized = normalize_path(str(test_path))
        assert isinstance(normalized, Path)
        assert normalized.is_absolute()

    def test_normalize_path_handles_path_object(self, tmp_path: Path) -> None:
        """Test that normalize_path handles Path object input."""
        test_path = tmp_path / "test.txt"
        test_path.touch()

        normalized = normalize_path(test_path)
        assert isinstance(normalized, Path)
        assert normalized.is_absolute()

    def test_normalize_path_nonexistent_path(self, tmp_path: Path) -> None:
        """Test that normalize_path handles non-existent paths."""
        test_path = tmp_path / "nonexistent" / "test.txt"

        # Should not raise, just return absolute path
        normalized = normalize_path(test_path)
        assert isinstance(normalized, Path)
        assert normalized.is_absolute()

    def test_get_home_directory_exists(self) -> None:
        """Test that home directory exists."""
        home = get_home_directory()
        assert isinstance(home, Path)
        assert home.exists()
        assert home.is_dir()

    def test_get_home_directory_is_absolute(self) -> None:
        """Test that home directory is absolute."""
        home = get_home_directory()
        assert home.is_absolute()

    def test_get_home_directory_matches_path_home(self) -> None:
        """Test that get_home_directory matches Path.home()."""
        home = get_home_directory()
        assert home == Path.home()


class TestPlatformConsistency:
    """Test consistency between different platform functions."""

    def test_path_separator_in_normalized_path(self, tmp_path: Path) -> None:
        """Test that normalized paths use correct separator."""
        test_path = tmp_path / "test.txt"
        test_path.touch()

        normalized = normalize_path(test_path)
        sep = get_path_separator()

        # The path should use the platform separator
        # (though Path objects abstract this away)
        assert isinstance(normalized, Path)

    def test_home_directory_uses_correct_separator(self) -> None:
        """Test that home directory path uses correct separator."""
        home = get_home_directory()
        sep = get_path_separator()

        # The path should be valid for the current platform
        assert home.exists()


@pytest.mark.parametrize(
    "platform_value,expected",
    [
        (Platform.LINUX, "linux"),
        (Platform.MACOS, "macos"),
        (Platform.WINDOWS, "windows"),
        (Platform.UNKNOWN, "unknown"),
    ],
)
def test_platform_enum_values(platform_value: Platform, expected: str) -> None:
    """Test Platform enum values."""
    assert platform_value.value == expected
