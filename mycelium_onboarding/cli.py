"""Command-line interface for Mycelium onboarding.

This module provides CLI commands for environment setup, direnv configuration,
and system status checks. All commands validate the environment before execution
to ensure proper activation.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from mycelium_onboarding.env_validator import (
    EnvironmentValidationError,
    get_environment_info,
    is_environment_active,
    validate_environment,
)
from mycelium_onboarding.setup_direnv import setup_direnv
from mycelium_onboarding.xdg_dirs import get_all_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)

# Commands that don't require environment validation
SKIP_VALIDATION_COMMANDS = {"help", "setup-direnv"}


def cmd_setup_direnv(_args: list[str]) -> int:
    """Set up direnv integration.

    This command does not require environment validation since it's used
    to set up the environment in the first place.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Setting up direnv integration for Mycelium...\n")

    try:
        success, message = setup_direnv()
        print(message)
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("Failed to setup direnv")
        return 1


def cmd_status(_args: list[str]) -> int:
    """Display environment status.

    Enhanced to show environment validation status and provide more
    detailed information using the environment validator.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, 1 if environment invalid)
    """
    print("Mycelium Environment Status:\n")

    # Use environment validator to get comprehensive info
    env_info = get_environment_info()
    active = is_environment_active()

    print("Environment Activation:")
    if active:
        print("  ✓ Environment is ACTIVE")
    else:
        print("  ✗ Environment is INACTIVE")
    print()

    # Show environment variables with validation
    print("Environment Variables:")
    for var, value in env_info.items():
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            print(f"  ✗ {var}: (not set)")
    print()

    # Try to validate environment and show results
    print("Environment Validation:")
    try:
        validate_environment()
        print("  ✓ All required variables set")
        print("  ✓ All directories exist and are writable")
        print("  ✓ MYCELIUM_ROOT is a valid git repository")
        print("  ✓ Environment is fully operational")
        validation_passed = True
    except EnvironmentValidationError as e:
        print("  ✗ Validation FAILED")
        print(f"\n{e}")
        validation_passed = False
    print()

    # Check XDG directories
    try:
        dirs = get_all_dirs()
        print("XDG Directories:")
        for name, path in dirs.items():
            exists = "✓" if path.exists() else "✗"
            print(f"  {exists} {name}: {path}")
        print()
    except Exception as e:
        print(f"Error reading XDG directories: {e}\n", file=sys.stderr)

    # Check direnv
    from mycelium_onboarding.setup_direnv import (
        check_direnv_hook_installed,
        check_direnv_installed,
        get_direnv_version,
    )

    print("direnv Status:")
    if check_direnv_installed():
        version = get_direnv_version()
        print(f"  ✓ Installed: {version or 'unknown version'}")

        hook_installed, hook_message = check_direnv_hook_installed()
        if hook_installed:
            print(f"  ✓ Shell hook: {hook_message}")
        else:
            print(f"  ✗ Shell hook: {hook_message}")

        # Check if .envrc exists
        envrc_path = Path.cwd() / ".envrc"
        if envrc_path.exists():
            print(f"  ✓ .envrc: exists at {envrc_path}")
        else:
            print("  ✗ .envrc: not found")
    else:
        print("  ✗ Not installed")

    # Return appropriate exit code
    return 0 if validation_passed else 1


def cmd_help(_args: list[str]) -> int:
    """Display help message.

    Args:
        args: Command-line arguments (unused)

    Returns:
        Exit code (always 0)
    """
    print(
        """Mycelium Onboarding CLI

Usage: python -m mycelium_onboarding <command> [options]

Commands:
  setup-direnv    Set up direnv integration for automatic environment activation
  status          Display environment and configuration status (validates environment)
  help            Show this help message

Environment Validation:
  Most commands require a properly activated Mycelium environment.
  Use 'status' to check your environment configuration.

  To activate:
    - With direnv: cd to project and run 'direnv allow'
    - Without direnv: run 'source bin/activate.sh'

Examples:
  python -m mycelium_onboarding setup-direnv
  python -m mycelium_onboarding status

For more information, visit: https://github.com/gsornsen/mycelium
"""
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point with environment validation.

    Validates the environment before running commands (except for commands
    that don't require it like 'help' and 'setup-direnv').

    Args:
        argv: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Parse command
    if not argv or argv[0] in ["help", "-h", "--help"]:
        return cmd_help(argv)

    command = argv[0]
    args = argv[1:]

    # Validate environment before running commands (unless skipped)
    if command not in SKIP_VALIDATION_COMMANDS:
        try:
            validate_environment()
            logger.debug("Environment validation passed")
        except EnvironmentValidationError as e:
            print(f"Environment Validation Error:\n{e}", file=sys.stderr)
            print(
                "\nRun 'python -m mycelium_onboarding status' "
                "for detailed diagnostics.",
                file=sys.stderr,
            )
            return 1

    # Dispatch to command handlers
    commands = {
        "setup-direnv": cmd_setup_direnv,
        "status": cmd_status,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print(
            "Run 'python -m mycelium_onboarding help' for usage.", file=sys.stderr
        )
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("Command failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
