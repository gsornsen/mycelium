"""direnv setup utility for Mycelium environment isolation.

This module provides functionality to set up direnv integration for automatic
environment activation. It handles direnv detection, installation verification,
shell hook detection, and .envrc template copying.

Example:
    >>> from mycelium_onboarding.setup_direnv import setup_direnv
    >>> success, message = setup_direnv()
    >>> if success:
    ...     print("direnv setup complete!")
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Final

# Module logger
logger = logging.getLogger(__name__)

# Constants
ENVRC_TEMPLATE_NAME: Final[str] = ".envrc.template"
ENVRC_FILENAME: Final[str] = ".envrc"

# Supported shells and their config files
SHELL_CONFIGS: Final[dict[str, list[str]]] = {
    "bash": [".bashrc", ".bash_profile", ".profile"],
    "zsh": [".zshrc", ".zprofile"],
    "fish": [".config/fish/config.fish"],
}


class DirenvError(Exception):
    """Raised when direnv setup operations fail."""

    pass


def check_direnv_installed() -> bool:
    """Check if direnv is installed and available in PATH.

    Returns:
        True if direnv is installed and accessible, False otherwise

    Example:
        >>> if check_direnv_installed():
        ...     print("direnv is installed")
    """
    direnv_path = shutil.which("direnv")
    if direnv_path:
        logger.debug("direnv found at: %s", direnv_path)
        return True
    logger.debug("direnv not found in PATH")
    return False


def get_direnv_version() -> str | None:
    """Get the installed direnv version.

    Returns:
        Version string if direnv is installed, None otherwise

    Example:
        >>> version = get_direnv_version()
        >>> if version:
        ...     print(f"direnv version: {version}")
    """
    if not check_direnv_installed():
        return None

    try:
        result = subprocess.run(
            ["direnv", "version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        version = result.stdout.strip()
        logger.debug("direnv version: %s", version)
        return version
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning("Failed to get direnv version: %s", e)
        return None


def detect_shell() -> str | None:
    """Detect the user's current shell.

    Returns:
        Shell name (bash, zsh, fish) or None if unknown

    Example:
        >>> shell = detect_shell()
        >>> print(f"Current shell: {shell}")
    """
    shell_path = os.environ.get("SHELL", "")
    shell_name = Path(shell_path).name if shell_path else None

    if shell_name in SHELL_CONFIGS:
        logger.debug("Detected shell: %s", shell_name)
        return shell_name

    logger.debug("Unknown or unsupported shell: %s", shell_path)
    return None


def get_shell_config_path(shell: str) -> Path | None:
    """Get the primary config file path for a shell.

    Args:
        shell: Shell name (bash, zsh, fish)

    Returns:
        Path to shell config file, or None if not found

    Example:
        >>> path = get_shell_config_path("bash")
        >>> if path:
        ...     print(f"Config file: {path}")
    """
    if shell not in SHELL_CONFIGS:
        logger.warning("Unknown shell: %s", shell)
        return None

    home = Path.home()
    config_files = SHELL_CONFIGS[shell]

    # Return first existing config file
    for config_file in config_files:
        config_path = home / config_file
        if config_path.exists():
            logger.debug("Found shell config: %s", config_path)
            return config_path

    # Return first option as default (even if it doesn't exist)
    default_path = home / config_files[0]
    logger.debug("No existing config found, using default: %s", default_path)
    return default_path


def check_direnv_hook_installed(shell: str | None = None) -> tuple[bool, str]:
    """Check if direnv hook is installed in shell configuration.

    This implements the devops-engineer's high-priority recommendation HP2
    for direnv hook verification.

    Args:
        shell: Shell name to check (detected automatically if None)

    Returns:
        Tuple of (is_installed, message)

    Example:
        >>> installed, message = check_direnv_hook_installed()
        >>> if not installed:
        ...     print(f"Hook not installed: {message}")
    """
    if shell is None:
        shell = detect_shell()

    if shell is None:
        return False, "Could not detect shell"

    config_path = get_shell_config_path(shell)
    if config_path is None or not config_path.exists():
        return (
            False,
            f"Shell config file not found (checked: {config_path})",
        )

    # Read shell config
    try:
        content = config_path.read_text()
    except OSError as e:
        logger.error("Failed to read shell config: %s", config_path, exc_info=True)
        return False, f"Failed to read {config_path}: {e}"

    # Check for direnv hook based on shell
    hook_patterns = {
        "bash": 'eval "$(direnv hook bash)"',
        "zsh": 'eval "$(direnv hook zsh)"',
        "fish": "direnv hook fish | source",
    }

    pattern = hook_patterns.get(shell)
    if pattern is None:
        return False, f"Unsupported shell: {shell}"

    if pattern in content:
        logger.debug("direnv hook found in %s", config_path)
        return True, f"Hook installed in {config_path}"

    logger.debug("direnv hook not found in %s", config_path)
    return False, f"Hook not found in {config_path}"


def get_hook_install_instructions(shell: str | None = None) -> str:
    """Get instructions for installing direnv hook.

    Args:
        shell: Shell name (detected automatically if None)

    Returns:
        Human-readable installation instructions

    Example:
        >>> instructions = get_hook_install_instructions()
        >>> print(instructions)
    """
    if shell is None:
        shell = detect_shell()

    if shell is None:
        return (
            "Could not detect your shell. Please visit:\n"
            "https://direnv.net/docs/hook.html\n"
            "for installation instructions."
        )

    config_path = get_shell_config_path(shell)
    hook_commands = {
        "bash": 'eval "$(direnv hook bash)"',
        "zsh": 'eval "$(direnv hook zsh)"',
        "fish": "direnv hook fish | source",
    }

    hook_cmd = hook_commands.get(shell, "")

    return f"""To enable direnv, add this line to {config_path}:

    {hook_cmd}

Then reload your shell:
    source {config_path}

Or start a new terminal session."""


def copy_envrc_template(project_root: Path | None = None) -> tuple[bool, str]:
    """Copy .envrc.template to .envrc in project root.

    Args:
        project_root: Project root directory (uses MYCELIUM_ROOT or cwd if None)

    Returns:
        Tuple of (success, message)

    Raises:
        DirenvError: If template not found or copy fails

    Example:
        >>> success, message = copy_envrc_template()
        >>> if success:
        ...     print("Template copied successfully")
    """
    # Determine project root
    if project_root is None:
        # Try MYCELIUM_ROOT environment variable first
        root_str = os.environ.get("MYCELIUM_ROOT")
        project_root = Path(root_str) if root_str else Path.cwd()

    logger.debug("Using project root: %s", project_root)

    # Check if .envrc already exists
    envrc_path = project_root / ENVRC_FILENAME
    if envrc_path.exists():
        return False, f".envrc already exists at {envrc_path}"

    # Find template file
    # Try in project root first
    template_path = project_root / ENVRC_TEMPLATE_NAME
    if not template_path.exists():
        # Try in package templates directory
        package_templates = Path(__file__).parent / "templates" / ENVRC_TEMPLATE_NAME
        if package_templates.exists():
            template_path = package_templates
        else:
            error_msg = (
                f"Template file not found. Checked:\n"
                f"  - {project_root / ENVRC_TEMPLATE_NAME}\n"
                f"  - {package_templates}"
            )
            logger.error(error_msg)
            raise DirenvError(error_msg)

    # Copy template
    try:
        shutil.copy2(template_path, envrc_path)
        logger.info("Copied template from %s to %s", template_path, envrc_path)
        return True, f"Created .envrc at {envrc_path}"
    except OSError as e:
        error_msg = f"Failed to copy template: {e}"
        logger.error(error_msg, exc_info=True)
        raise DirenvError(error_msg) from e


def setup_direnv(project_root: Path | None = None) -> tuple[bool, str]:
    """Set up direnv integration for Mycelium environment.

    This is the main entry point for direnv setup. It performs the following:
    1. Checks if direnv is installed
    2. Checks if direnv hook is configured in shell
    3. Copies .envrc template if not exists
    4. Provides instructions for next steps

    Args:
        project_root: Project root directory (detected automatically if None)

    Returns:
        Tuple of (success, message with instructions)

    Example:
        >>> success, message = setup_direnv()
        >>> print(message)
    """
    # Check direnv installation
    if not check_direnv_installed():
        return (
            False,
            "direnv is not installed.\n\n"
            "Install from: https://direnv.net/docs/installation.html\n\n"
            "Installation methods:\n"
            "  - Ubuntu/Debian: sudo apt install direnv\n"
            "  - macOS: brew install direnv\n"
            "  - Fedora: sudo dnf install direnv\n\n"
            "Alternatively, use manual activation:\n"
            "  source bin/activate.sh",
        )

    version = get_direnv_version()
    logger.info("direnv is installed (version: %s)", version or "unknown")

    # Check hook installation
    hook_installed, hook_message = check_direnv_hook_installed()
    if not hook_installed:
        instructions = get_hook_install_instructions()
        return (
            False,
            f"direnv is installed but shell hook is not configured.\n\n"
            f"{hook_message}\n\n{instructions}",
        )

    logger.info("direnv hook is installed")

    # Copy template
    try:
        copied, copy_message = copy_envrc_template(project_root)
    except DirenvError as e:
        return False, str(e)

    if not copied:
        # .envrc already exists
        return (
            True,
            f"{copy_message}\n\nTo activate the environment:\n  direnv allow",
        )

    # Success - template copied
    return (
        True,
        f"✓ direnv setup complete!\n\n"
        f"{copy_message}\n\n"
        "To activate the environment:\n"
        "  direnv allow\n\n"
        "The environment will automatically activate when you enter this directory.",
    )
