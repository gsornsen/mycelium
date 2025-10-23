# Source: projects/onboarding/milestones/M01_ENVIRONMENT_ISOLATION.md
# Line: 320
# Valid syntax: True
# Has imports: True
# Has assignments: True

# mycelium_onboarding/setup_direnv.py
"""Setup direnv integration for automatic environment activation."""

import shutil
import subprocess
from pathlib import Path


def check_direnv_installed() -> bool:
    """Check if direnv is installed and available."""
    return shutil.which("direnv") is not None


def setup_direnv(project_root: Path | None = None) -> tuple[bool, str]:
    """Setup direnv for the project.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        (success, message) tuple
    """
    if project_root is None:
        project_root = Path.cwd()

    envrc_path = project_root / ".envrc"
    template_path = Path(__file__).parent / "templates" / ".envrc.template"

    # Check if direnv is installed
    if not check_direnv_installed():
        return False, "direnv not installed. Install from https://direnv.net/"

    # Copy template if .envrc doesn't exist
    if not envrc_path.exists():
        shutil.copy(template_path, envrc_path)
        message = f"Created {envrc_path}\nRun: direnv allow"
    else:
        message = f".envrc already exists at {envrc_path}"

    # Check if direnv hook is in shell config
    shell_instructions = get_shell_hook_instructions()

    return True, f"{message}\n\n{shell_instructions}"


def get_shell_hook_instructions() -> str:
    """Get shell-specific hook instructions."""
    shell = Path(subprocess.check_output(["echo", "$SHELL"], text=True).strip()).name

    instructions = {
        "bash": 'Add to ~/.bashrc: eval "$(direnv hook bash)"',
        "zsh": 'Add to ~/.zshrc: eval "$(direnv hook zsh)"',
        "fish": 'Add to ~/.config/fish/config.fish: direnv hook fish | source',
    }

    return instructions.get(shell, "See https://direnv.net/docs/hook.html for your shell")
