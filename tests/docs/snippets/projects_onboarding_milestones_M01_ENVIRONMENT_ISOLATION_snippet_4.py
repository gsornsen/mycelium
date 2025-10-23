# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 516
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/env_validator.py
"""Runtime environment validation."""

import os
from pathlib import Path
from typing import List, Optional

class EnvironmentValidationError(Exception):
    """Raised when environment validation fails."""
    pass


def validate_environment(require_project_dir: bool = False) -> None:
    """Validate that Mycelium environment is properly activated.

    Args:
        require_project_dir: If True, also require MYCELIUM_PROJECT_DIR

    Raises:
        EnvironmentValidationError: If environment is not properly set up
    """
    required_vars = [
        "MYCELIUM_ROOT",
        "MYCELIUM_CONFIG_DIR",
        "MYCELIUM_DATA_DIR",
        "MYCELIUM_CACHE_DIR",
        "MYCELIUM_STATE_DIR",
    ]

    if require_project_dir:
        required_vars.append("MYCELIUM_PROJECT_DIR")

    missing_vars = []
    for var in required_vars:
        if var not in os.environ:
            missing_vars.append(var)

    if missing_vars:
        raise EnvironmentValidationError(
            f"Missing environment variables: {', '.join(missing_vars)}\n"
            "Activate environment first:\n"
            "  - With direnv: cd to project and run 'direnv allow'\n"
            "  - Without direnv: run 'source bin/activate.sh'"
        )

    # Validate that directories exist
    for var in required_vars:
        path = Path(os.environ[var])
        if not path.exists():
            raise EnvironmentValidationError(
                f"Directory does not exist: {path} (from ${var})\n"
                "Run: python -m mycelium_onboarding setup"
            )


def is_environment_active() -> bool:
    """Check if Mycelium environment is active.

    Returns:
        True if environment is active, False otherwise
    """
    return "MYCELIUM_ENV_ACTIVE" in os.environ


def get_missing_vars() -> List[str]:
    """Get list of missing environment variables.

    Returns:
        List of missing variable names (empty if all present)
    """
    required_vars = [
        "MYCELIUM_ROOT",
        "MYCELIUM_CONFIG_DIR",
        "MYCELIUM_DATA_DIR",
        "MYCELIUM_CACHE_DIR",
        "MYCELIUM_STATE_DIR",
    ]

    return [var for var in required_vars if var not in os.environ]


def get_environment_info() -> dict[str, Optional[str]]:
    """Get current environment information.

    Returns:
        Dictionary of environment variables and their values
    """
    vars_to_check = [
        "MYCELIUM_ROOT",
        "MYCELIUM_CONFIG_DIR",
        "MYCELIUM_DATA_DIR",
        "MYCELIUM_CACHE_DIR",
        "MYCELIUM_STATE_DIR",
        "MYCELIUM_PROJECT_DIR",
        "MYCELIUM_ENV_ACTIVE",
    ]

    return {var: os.environ.get(var) for var in vars_to_check}