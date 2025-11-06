"""Runtime environment validation for Mycelium.

This module provides runtime validation to ensure the Mycelium environment is
properly activated before any operations. It validates environment variables,
directory existence, and provides actionable error messages.

This is Layer 2 in the three-layer validation model:
- Layer 1: Shell activation (sets environment variables)
- Layer 2: Runtime validation (this module - validates before execution)
- Layer 3: Wrapper scripts (fail-fast checks)

Example:
    >>> from mycelium_onboarding.env_validator import validate_environment
    >>> validate_environment()  # Raises EnvironmentValidationError if invalid
    >>> # Safe to proceed with operations
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Final

# Module logger
logger = logging.getLogger(__name__)

# Required environment variables (core validation)
REQUIRED_ENV_VARS: Final[list[str]] = [
    "MYCELIUM_ROOT",
    "MYCELIUM_CONFIG_DIR",
    "MYCELIUM_DATA_DIR",
    "MYCELIUM_CACHE_DIR",
    "MYCELIUM_STATE_DIR",
]

# Optional environment variables (may be required based on context)
OPTIONAL_ENV_VARS: Final[list[str]] = [
    "MYCELIUM_PROJECT_DIR",
    "MYCELIUM_ENV_ACTIVE",
]

# All tracked environment variables
ALL_ENV_VARS: Final[list[str]] = REQUIRED_ENV_VARS + OPTIONAL_ENV_VARS

# Export list
__all__ = [
    "EnvironmentValidationError",
    "validate_environment",
    "is_environment_active",
    "get_missing_vars",
    "get_environment_info",
]


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails.

    This exception indicates that the Mycelium environment is not properly
    activated or configured. The error message includes actionable steps
    for the user to fix the issue.

    Example:
        >>> try:
        ...     validate_environment()
        ... except EnvironmentValidationError as e:
        ...     print(f"Environment error: {e}")
        ...     # Take corrective action
    """

    pass


def validate_environment(require_project_dir: bool = False) -> None:
    """Validate that Mycelium environment is properly activated.

    Performs comprehensive validation of the runtime environment:
    1. Checks all required environment variables are set and non-empty
    2. Validates all directory paths exist
    3. Verifies directories are writable
    4. Validates MYCELIUM_ROOT is a git repository with pyproject.toml

    Args:
        require_project_dir: If True, also require MYCELIUM_PROJECT_DIR to be
            set and valid. Use this for operations that need project-local
            configuration.

    Raises:
        EnvironmentValidationError: If environment is not properly set up.
            Error message includes specific details about what's missing and
            how to fix it.

    Example:
        >>> # Basic validation (for commands that don't need project dir)
        >>> validate_environment()
        >>>
        >>> # With project dir validation (for commands needing .mycelium/)
        >>> validate_environment(require_project_dir=True)
    """
    logger.debug(
        "Starting environment validation (require_project_dir=%s)",
        require_project_dir,
    )

    # Determine which variables to check
    required_vars = REQUIRED_ENV_VARS.copy()
    if require_project_dir:
        required_vars.append("MYCELIUM_PROJECT_DIR")

    # Check for missing or empty environment variables
    missing_vars = [var for var in required_vars if var not in os.environ or not os.environ[var].strip()]

    if missing_vars:
        logger.error("Missing or empty environment variables: %s", missing_vars)
        raise EnvironmentValidationError(
            f"Missing or empty environment variables: {', '.join(missing_vars)}\n"
            "\n"
            "The Mycelium environment is not activated.\n"
            "\n"
            "Activate the environment using one of these methods:\n"
            "  - With direnv: cd to project directory and run 'direnv allow'\n"
            "  - Without direnv: run 'source bin/activate.sh'\n"
            "\n"
            "For more help, see: https://github.com/gsornsen/mycelium"
        )

    # Validate directories exist
    missing_dirs: list[tuple[str, Path]] = []
    for var in required_vars:
        path = Path(os.environ[var])
        if not path.exists():
            logger.warning("Directory does not exist: %s (from $%s)", path, var)
            missing_dirs.append((var, path))

    if missing_dirs:
        dir_list = "\n".join(f"  - ${var}: {path}" for var, path in missing_dirs)
        logger.error("Missing directories detected")
        raise EnvironmentValidationError(
            f"The following directories do not exist:\n{dir_list}\n"
            "\n"
            "These directories should be created automatically during activation.\n"
            "\n"
            "To fix this:\n"
            "  1. Deactivate the environment (if using manual activation)\n"
            "  2. Re-activate using 'source bin/activate.sh' or 'direnv allow'\n"
            "  3. If the problem persists, manually create the directories\n"
            "\n"
            "For more help, see: https://github.com/gsornsen/mycelium"
        )

    # Check directory writability
    unwritable_dirs: list[tuple[str, Path]] = []
    for var in required_vars:
        path = Path(os.environ[var])
        if path.exists() and not os.access(path, os.W_OK):
            logger.warning("Directory is not writable: %s (from $%s)", path, var)
            unwritable_dirs.append((var, path))

    if unwritable_dirs:
        dir_list = "\n".join(f"  - ${var}: {path}" for var, path in unwritable_dirs)
        logger.error("Unwritable directories detected")
        raise EnvironmentValidationError(
            f"The following directories are not writable:\n{dir_list}\n"
            "\n"
            "Check permissions:\n"
            f"  $ ls -ld {unwritable_dirs[0][1]}\n"
            f"  $ chmod u+w {unwritable_dirs[0][1]}\n"
            "\n"
            "Ensure you have write permissions to all Mycelium directories."
        )

    # Validate MYCELIUM_ROOT is a valid git repository
    root = Path(os.environ["MYCELIUM_ROOT"])
    if not (root / ".git").exists():
        logger.error("MYCELIUM_ROOT is not a git repository: %s", root)
        raise EnvironmentValidationError(
            f"MYCELIUM_ROOT is not a git repository: {root}\n"
            "\n"
            "The directory should contain a .git subdirectory.\n"
            "\n"
            "Ensure you are running from the Mycelium project directory:\n"
            "  $ cd /path/to/mycelium\n"
            "  $ source bin/activate.sh\n"
            "\n"
            "Current MYCELIUM_ROOT points to the wrong directory."
        )

    # Validate MYCELIUM_ROOT contains pyproject.toml
    if not (root / "pyproject.toml").exists():
        logger.error("MYCELIUM_ROOT does not contain pyproject.toml: %s", root)
        raise EnvironmentValidationError(
            f"MYCELIUM_ROOT does not contain pyproject.toml: {root}\n"
            "\n"
            "The directory should be a valid Python project.\n"
            "\n"
            "Ensure MYCELIUM_ROOT points to the Mycelium project root:\n"
            "  $ cd /path/to/mycelium\n"
            "  $ ls pyproject.toml  # Should exist\n"
            "\n"
            "Current MYCELIUM_ROOT points to the wrong directory."
        )

    logger.debug("Environment validation successful")


def is_environment_active() -> bool:
    """Check if Mycelium environment is active.

    This is a quick boolean check that only looks at MYCELIUM_ENV_ACTIVE.
    Use this for fast checks without throwing exceptions. For comprehensive
    validation, use validate_environment() instead.

    Returns:
        True if MYCELIUM_ENV_ACTIVE is set to "1", False otherwise

    Example:
        >>> if is_environment_active():
        ...     print("Environment is active")
        ... else:
        ...     print("Please activate the environment")
    """
    return os.environ.get("MYCELIUM_ENV_ACTIVE") == "1"


def get_missing_vars(include_optional: bool = False) -> list[str]:
    """Get list of missing required environment variables.

    Args:
        include_optional: If True, also check optional variables like
            MYCELIUM_PROJECT_DIR and MYCELIUM_ENV_ACTIVE

    Returns:
        List of missing variable names (empty list if all present)

    Example:
        >>> missing = get_missing_vars()
        >>> if missing:
        ...     print(f"Missing variables: {', '.join(missing)}")
        ... else:
        ...     print("All required variables are set")
    """
    vars_to_check = REQUIRED_ENV_VARS.copy()
    if include_optional:
        vars_to_check.extend(OPTIONAL_ENV_VARS)

    return [var for var in vars_to_check if var not in os.environ]


def get_environment_info() -> dict[str, str | None]:
    """Get current environment information for debugging.

    Returns a dictionary with all Mycelium environment variables and their
    current values. Variables that are not set will have None as value.

    Returns:
        Dictionary mapping variable names to their values (or None if unset)

    Example:
        >>> info = get_environment_info()
        >>> for var, value in info.items():
        ...     status = "✓" if value else "✗"
        ...     print(f"{status} {var}: {value or '(not set)'}")
    """
    return {var: os.environ.get(var) for var in ALL_ENV_VARS}
