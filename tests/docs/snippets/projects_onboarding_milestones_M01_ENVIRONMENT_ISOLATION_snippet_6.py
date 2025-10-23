# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 671
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/config_loader.py
"""Hierarchical configuration loading."""

import os
from pathlib import Path


def get_config_path(filename: str, prefer_project: bool = True) -> Path:
    """Get configuration file path following precedence.

    Precedence order:
    1. Project-local: .mycelium/<filename>
    2. User-global: ~/.config/mycelium/<filename>
    3. Defaults: package resources

    Args:
        filename: Configuration filename (e.g., "config.yaml")
        prefer_project: If True, prefer project-local over user-global

    Returns:
        Path to configuration file (may not exist)
    """
    # Check project-local first (if MYCELIUM_PROJECT_DIR set and prefer_project)
    if prefer_project and "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename
        if project_path.exists():
            return project_path

    # Check user-global
    from mycelium_onboarding.xdg_dirs import get_config_dir
    user_path = get_config_dir() / filename
    if user_path.exists():
        return user_path

    # Check project-local again (even if prefer_project=False, for creation)
    if "MYCELIUM_PROJECT_DIR" in os.environ:
        project_path = Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename
        if prefer_project:
            return project_path

    # Fall back to user-global (even if doesn't exist, for creation)
    return user_path


def get_all_config_paths(filename: str) -> list[Path]:
    """Get all possible config file locations in precedence order.

    Args:
        filename: Configuration filename

    Returns:
        List of paths in precedence order (may not all exist)
    """
    paths = []

    # Project-local
    if "MYCELIUM_PROJECT_DIR" in os.environ:
        paths.append(Path(os.environ["MYCELIUM_PROJECT_DIR"]) / filename)

    # User-global
    from mycelium_onboarding.xdg_dirs import get_config_dir
    paths.append(get_config_dir() / filename)

    return paths


def find_config_file(filename: str) -> Path | None:
    """Find first existing config file in precedence order.

    Args:
        filename: Configuration filename

    Returns:
        Path to first existing config file, or None if not found
    """
    for path in get_all_config_paths(filename):
        if path.exists():
            return path
    return None
