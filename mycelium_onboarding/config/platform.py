"""Platform detection and platform-specific utilities.

This module provides platform detection and utilities for handling
platform-specific behavior in the Mycelium configuration system.

Example:
    >>> from mycelium_onboarding.config.platform import get_platform, Platform
    >>> platform = get_platform()
    >>> if platform == Platform.LINUX:
    ...     print("Running on Linux")
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path


class Platform(Enum):
    """Supported operating system platforms.

    Attributes:
        LINUX: Linux operating system
        MACOS: macOS operating system
        WINDOWS: Windows operating system
        UNKNOWN: Unknown or unsupported platform
    """

    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


def get_platform() -> Platform:
    """Detect the current operating system platform.

    Returns:
        Platform enum indicating the current OS

    Example:
        >>> platform = get_platform()
        >>> platform in {Platform.LINUX, Platform.MACOS, Platform.WINDOWS}
        True
    """
    if sys.platform.startswith("linux"):
        return Platform.LINUX
    if sys.platform == "darwin":
        return Platform.MACOS
    if sys.platform == "win32":
        return Platform.WINDOWS
    return Platform.UNKNOWN


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if running on Windows, False otherwise
    """
    return get_platform() == Platform.WINDOWS


def is_posix() -> bool:
    """Check if running on a POSIX-compatible system (Linux/macOS).

    Returns:
        True if running on Linux or macOS, False otherwise
    """
    platform = get_platform()
    return platform in {Platform.LINUX, Platform.MACOS}


def get_path_separator() -> str:
    r"""Get the platform-specific path separator.

    Returns:
        Path separator character ('/' for POSIX, '\\' for Windows)

    Example:
        >>> sep = get_path_separator()
        >>> sep in {'/', '\\\\'}
        True
    """
    return "\\" if is_windows() else "/"


def normalize_path(path: Path | str) -> Path:
    """Normalize a path for the current platform.

    Resolves symlinks, makes path absolute, and normalizes separators.

    Args:
        path: Path to normalize (string or Path object)

    Returns:
        Normalized absolute Path object

    Example:
        >>> p = normalize_path("~/config.yaml")
        >>> p.is_absolute()
        True
    """
    path_obj = Path(path).expanduser()
    try:
        # Resolve symlinks and make absolute
        return path_obj.resolve()
    except (OSError, RuntimeError):
        # If resolution fails (e.g., path doesn't exist), just expand and make absolute
        return path_obj.absolute()


def get_home_directory() -> Path:
    """Get the user's home directory in a platform-independent way.

    Returns:
        Path to user's home directory

    Example:
        >>> home = get_home_directory()
        >>> home.exists()
        True
    """
    return Path.home()
