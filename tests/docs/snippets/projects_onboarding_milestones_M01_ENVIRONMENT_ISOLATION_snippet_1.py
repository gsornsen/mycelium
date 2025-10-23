# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 112
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/xdg_dirs.py
import os
from pathlib import Path


def get_config_dir(project_name: str = "mycelium") -> Path:
    """Get XDG config directory, creating if needed.

    Returns: ~/.config/mycelium/ or $XDG_CONFIG_HOME/mycelium/
    """
    base = os.environ.get("XDG_CONFIG_HOME")
    if base is None:
        base = Path.home() / ".config"
    else:
        base = Path(base)

    config_dir = base / project_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir(project_name: str = "mycelium") -> Path:
    """Get XDG data directory, creating if needed.

    Returns: ~/.local/share/mycelium/ or $XDG_DATA_HOME/mycelium/
    """
    base = os.environ.get("XDG_DATA_HOME")
    if base is None:
        base = Path.home() / ".local" / "share"
    else:
        base = Path(base)

    data_dir = base / project_name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_dir(project_name: str = "mycelium") -> Path:
    """Get XDG cache directory, creating if needed.

    Returns: ~/.cache/mycelium/ or $XDG_CACHE_HOME/mycelium/
    """
    base = os.environ.get("XDG_CACHE_HOME")
    if base is None:
        base = Path.home() / ".cache"
    else:
        base = Path(base)

    cache_dir = base / project_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_state_dir(project_name: str = "mycelium") -> Path:
    """Get XDG state directory, creating if needed.

    Returns: ~/.local/state/mycelium/ or $XDG_STATE_HOME/mycelium/
    """
    base = os.environ.get("XDG_STATE_HOME")
    if base is None:
        base = Path.home() / ".local" / "state"
    else:
        base = Path(base)

    state_dir = base / project_name
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_project_dir(project_root: Path | None = None) -> Path:
    """Get project-local directory.

    Args:
        project_root: Project root path (defaults to MYCELIUM_ROOT env var or cwd)

    Returns: <project_root>/.mycelium/
    """
    if project_root is None:
        root_env = os.environ.get("MYCELIUM_ROOT")
        if root_env:
            project_root = Path(root_env)
        else:
            project_root = Path.cwd()

    project_dir = project_root / ".mycelium"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


# Convenience functions
def ensure_all_dirs() -> dict[str, Path]:
    """Ensure all XDG directories exist and return them.

    Returns:
        Dictionary mapping directory names to paths
    """
    return {
        "config": get_config_dir(),
        "data": get_data_dir(),
        "cache": get_cache_dir(),
        "state": get_state_dir(),
        "project": get_project_dir(),
    }
