"""Mycelium Onboarding - Environment isolation and XDG directory management.

This package provides XDG-compliant directory management and hierarchical
configuration loading for the Mycelium onboarding system, ensuring clean
environment isolation following best practices.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Import XDG directory components
# Import configuration loader components
from mycelium_onboarding.config_loader import (
    ConfigLoaderError,
    find_config_file,
    get_all_config_paths,
    get_config_path,
)
from mycelium_onboarding.xdg_dirs import (
    XDGDirectoryError,
    clear_cache,
    get_all_dirs,
    get_cache_dir,
    get_config_dir,
    get_data_dir,
    get_state_dir,
)

__all__ = [
    # XDG directory functions
    "get_config_dir",
    "get_data_dir",
    "get_cache_dir",
    "get_state_dir",
    "get_all_dirs",
    "clear_cache",
    "XDGDirectoryError",
    # Configuration loader functions
    "get_config_path",
    "get_all_config_paths",
    "find_config_file",
    "ConfigLoaderError",
]
