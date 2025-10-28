# M01: Environment Isolation

## Overview

**Duration**: 3 days **Dependencies**: None (project start) **Blocks**: M02, M03, M04 **Lead Agent**: platform-engineer
**Support Agents**: devops-engineer, python-pro

## Why This Milestone

Environment isolation is the foundation of the entire onboarding system. Without proper isolation:

- User system environment contamination
- Conflicts with existing Python installations
- Unreproducible bugs across different machines
- Difficulty tracking configuration state

This milestone establishes XDG-compliant directory structure, automated environment activation, and runtime validation
that ensures the Mycelium system operates in a clean, predictable environment.

## Requirements

### Functional Requirements (FR)

**FR-1**: Isolate Mycelium project from system Python environment

- Must use project-specific virtual environment
- Must not pollute user's PATH or environment variables
- Must support concurrent projects without conflicts

**FR-2**: Support project-local and user-global configuration

- Project-local: `.mycelium/` directory in project root
- User-global: XDG directories (~/.config, ~/.local/share, etc.)
- Precedence: project-local → user-global → defaults

**FR-3**: Provide automatic environment activation

- direnv integration for automatic activation on directory enter
- Manual activation scripts for users without direnv
- Clear indication when environment is active (shell prompt)

### Technical Requirements (TR)

**TR-1**: Follow XDG Base Directory Specification

- Config: `~/.config/mycelium/`
- Data: `~/.local/share/mycelium/`
- Cache: `~/.cache/mycelium/`
- State: `~/.local/state/mycelium/`
- Project: `.mycelium/` in project root

**TR-2**: Support Linux, macOS, Windows (WSL2)

- Use pathlib for cross-platform path handling
- Respect platform-specific defaults
- Test on all three platforms

**TR-3**: Multi-layer environment validation

- Layer 1: Shell activation (sets environment variables)
- Layer 2: Runtime validation (Python checks at import)
- Layer 3: Wrapper scripts (fail fast if not activated)

### Integration Requirements (IR)

**IR-1**: Integration with uv package manager

- Virtual environment managed by uv
- Dependencies isolated per project
- Consistent package versions

**IR-2**: Integration with future slash commands

- Environment active indicator in command output
- Configuration path resolution
- Proper error messages if run outside environment

### Constraints (CR)

**CR-1**: No modifications to user's global Python installation **CR-2**: No modifications to user's shell rc files
without permission **CR-3**: Must work without sudo/admin privileges **CR-4**: Minimal external dependencies (direnv
optional)

## Tasks

### Task 1.1: Design Environment Isolation Strategy

**Agent**: platform-engineer **Effort**: 4 hours **Dependencies**: None

**Description**: Design comprehensive isolation strategy covering all layers (shell, runtime, wrapper scripts).

**Acceptance Criteria**:

- [ ] Document defines all environment variables to be set
- [ ] Document specifies XDG directory usage
- [ ] Document outlines activation/deactivation flow
- [ ] Document addresses edge cases (nested activation, missing dirs)
- [ ] Reviewed by devops-engineer and python-pro

**Deliverables**:

- Design document: `docs/design/environment-isolation-strategy.md`
- Environment variable specification
- Activation flow diagram

______________________________________________________________________

### Task 1.2: Implement XDG Directory Structure

**Agent**: python-pro **Effort**: 6 hours **Dependencies**: Task 1.1

**Description**: Create Python module for XDG-compliant directory management.

**Implementation**:

```python
# mycelium_onboarding/xdg_dirs.py
from pathlib import Path
import os
from typing import Optional

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


def get_project_dir(project_root: Optional[Path] = None) -> Path:
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
```

**Test Plan**:

```python
# tests/test_xdg_dirs.py
import pytest
from pathlib import Path
import os

def test_get_config_dir_default(monkeypatch, tmp_path):
    """Test default config dir when XDG_CONFIG_HOME not set."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    config_dir = get_config_dir()

    assert config_dir == tmp_path / ".config" / "mycelium"
    assert config_dir.exists()


def test_get_config_dir_custom(monkeypatch, tmp_path):
    """Test custom config dir via XDG_CONFIG_HOME."""
    custom_config = tmp_path / "custom_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))

    config_dir = get_config_dir()

    assert config_dir == custom_config / "mycelium"
    assert config_dir.exists()


def test_ensure_all_dirs(tmp_path, monkeypatch):
    """Test that all directories are created."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("MYCELIUM_ROOT", str(tmp_path / "project"))

    dirs = ensure_all_dirs()

    assert all(path.exists() for path in dirs.values())
    assert "config" in dirs
    assert "data" in dirs
    assert "cache" in dirs
    assert "state" in dirs
    assert "project" in dirs
```

**Acceptance Criteria**:

- [ ] All XDG functions implemented with type hints
- [ ] Creates directories if they don't exist
- [ ] Respects XDG environment variables
- [ ] Falls back to standard paths if XDG vars not set
- [ ] Test coverage ≥90%
- [ ] Works on Linux, macOS, Windows (WSL2)

**Deliverables**:

- `mycelium_onboarding/xdg_dirs.py`
- `tests/test_xdg_dirs.py`

______________________________________________________________________

### Task 1.3: Create direnv Integration

**Agent**: platform-engineer **Effort**: 8 hours **Dependencies**: Task 1.2

**Description**: Create .envrc template and setup script for automatic environment activation.

**Implementation**:

```bash
# .envrc.template
# Mycelium Project Environment
# This file is managed by direnv (https://direnv.net/)
# Run: direnv allow

# Project root (absolute path to this .envrc's directory)
export MYCELIUM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# XDG directories (user-global configuration)
export MYCELIUM_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mycelium"
export MYCELIUM_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mycelium"
export MYCELIUM_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/mycelium"
export MYCELIUM_STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/mycelium"

# Project-local directory
export MYCELIUM_PROJECT_DIR="$MYCELIUM_ROOT/.mycelium"

# Add project bin directory to PATH
PATH_add "$MYCELIUM_ROOT/bin"

# Activate uv virtual environment (if it exists)
if [ -d "$MYCELIUM_ROOT/.venv" ]; then
    source "$MYCELIUM_ROOT/.venv/bin/activate"
fi

# Mark environment as active
export MYCELIUM_ENV_ACTIVE=1

# Optional: Visual indicator
echo "✓ Mycelium environment activated"
```

```python
# mycelium_onboarding/setup_direnv.py
"""Setup direnv integration for automatic environment activation."""

from pathlib import Path
import shutil
import subprocess
from typing import Optional

def check_direnv_installed() -> bool:
    """Check if direnv is installed and available."""
    return shutil.which("direnv") is not None


def setup_direnv(project_root: Optional[Path] = None) -> tuple[bool, str]:
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
```

**Acceptance Criteria**:

- [ ] .envrc.template covers all environment variables
- [ ] Activates uv virtual environment if present
- [ ] Adds project bin/ to PATH
- [ ] Clear activation indicator
- [ ] setup_direnv.py provides helpful instructions
- [ ] Detects if direnv is installed
- [ ] Works with bash, zsh, fish shells

**Deliverables**:

- `.envrc.template`
- `mycelium_onboarding/setup_direnv.py`
- `mycelium_onboarding/templates/.envrc.template`

______________________________________________________________________

### Task 1.4: Shell Activation Scripts

**Agent**: devops-engineer **Effort**: 6 hours **Dependencies**: Task 1.2

**Description**: Create manual activation/deactivation scripts for users without direnv.

**Implementation**:

```bash
#!/bin/bash
# bin/activate.sh
# Manual activation script for Mycelium environment

# Detect script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MYCELIUM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set XDG directories
export MYCELIUM_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mycelium"
export MYCELIUM_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mycelium"
export MYCELIUM_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/mycelium"
export MYCELIUM_STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/mycelium"
export MYCELIUM_PROJECT_DIR="$MYCELIUM_ROOT/.mycelium"

# Add project bin to PATH (save old PATH)
export MYCELIUM_OLD_PATH="$PATH"
export PATH="$MYCELIUM_ROOT/bin:$PATH"

# Activate uv virtual environment
if [ -d "$MYCELIUM_ROOT/.venv" ]; then
    source "$MYCELIUM_ROOT/.venv/bin/activate"
fi

# Mark environment as active
export MYCELIUM_ENV_ACTIVE=1

# Modify prompt to show activation
export MYCELIUM_OLD_PS1="$PS1"
export PS1="(mycelium) $PS1"

# Define deactivation function
deactivate() {
    # Restore original PATH
    if [ -n "$MYCELIUM_OLD_PATH" ]; then
        export PATH="$MYCELIUM_OLD_PATH"
        unset MYCELIUM_OLD_PATH
    fi

    # Restore original prompt
    if [ -n "$MYCELIUM_OLD_PS1" ]; then
        export PS1="$MYCELIUM_OLD_PS1"
        unset MYCELIUM_OLD_PS1
    fi

    # Deactivate Python virtual environment if active
    if command -v deactivate &> /dev/null; then
        command deactivate
    fi

    # Unset Mycelium variables
    unset MYCELIUM_ROOT
    unset MYCELIUM_CONFIG_DIR
    unset MYCELIUM_DATA_DIR
    unset MYCELIUM_CACHE_DIR
    unset MYCELIUM_STATE_DIR
    unset MYCELIUM_PROJECT_DIR
    unset MYCELIUM_ENV_ACTIVE

    # Unset the deactivate function itself
    unset -f deactivate

    echo "✓ Mycelium environment deactivated"
}

echo "✓ Mycelium environment activated"
echo "  Run 'deactivate' to deactivate"
```

```bash
#!/bin/bash
# bin/mycelium
# Wrapper script that ensures environment is active before running commands

# Check if environment is active
if [ -z "$MYCELIUM_ENV_ACTIVE" ]; then
    echo "❌ Mycelium environment not active"
    echo "Run: source bin/activate.sh"
    exit 1
fi

# Pass through to Python CLI
exec python -m mycelium_onboarding "$@"
```

**Acceptance Criteria**:

- [ ] activate.sh sets all required environment variables
- [ ] Modifies shell prompt to indicate activation
- [ ] Provides deactivate function
- [ ] Restores original environment on deactivate
- [ ] Wrapper scripts fail gracefully if not activated
- [ ] Works in bash, zsh, fish

**Deliverables**:

- `bin/activate.sh`
- `bin/mycelium` (wrapper script)
- `docs/manual-activation.md` (usage guide)

______________________________________________________________________

### Task 1.5: Runtime Environment Validation

**Agent**: python-pro **Effort**: 6 hours **Dependencies**: Task 1.2, Task 1.4

**Description**: Implement Python module that validates environment at runtime.

**Implementation**:

```python
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
```

**Usage in CLI**:

```python
# mycelium_onboarding/cli.py
import click
from mycelium_onboarding.env_validator import validate_environment

@click.group()
def cli():
    """Mycelium onboarding CLI."""
    # Validate environment before running any commands
    try:
        validate_environment()
    except EnvironmentValidationError as e:
        click.echo(str(e), err=True)
        raise click.Abort()


@cli.command()
def status():
    """Show environment status."""
    from mycelium_onboarding.env_validator import get_environment_info

    info = get_environment_info()
    click.echo("Mycelium Environment Status:")
    for var, value in info.items():
        status = "✓" if value else "✗"
        click.echo(f"  {status} {var}: {value or '(not set)'}")
```

**Acceptance Criteria**:

- [ ] validate_environment() raises clear errors
- [ ] Distinguishes between missing vars and missing dirs
- [ ] Provides actionable fix instructions
- [ ] is_environment_active() quick check
- [ ] get_environment_info() for debugging
- [ ] Integrated into CLI entry point

**Deliverables**:

- `mycelium_onboarding/env_validator.py`
- `tests/test_env_validator.py`

______________________________________________________________________

### Task 1.6: Project-Local Config Support

**Agent**: platform-engineer **Effort**: 4 hours **Dependencies**: Task 1.2

**Description**: Implement hierarchical configuration loading (project-local → user-global → defaults).

**Implementation**:

```python
# mycelium_onboarding/config_loader.py
"""Hierarchical configuration loading."""

from pathlib import Path
import os
from typing import Optional

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


def find_config_file(filename: str) -> Optional[Path]:
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
```

**Usage Example**:

```python
# Example: Loading config with fallback
import yaml

def load_config():
    """Load configuration with hierarchical fallback."""
    config_file = find_config_file("config.yaml")

    if config_file:
        with open(config_file) as f:
            return yaml.safe_load(f)

    # No config file found, return defaults
    return {
        "deployment_method": "docker-compose",
        "services": ["redis", "postgres"],
    }
```

**Acceptance Criteria**:

- [ ] get_config_path() follows precedence order
- [ ] Respects MYCELIUM_PROJECT_DIR if set
- [ ] Falls back to user-global XDG config
- [ ] find_config_file() returns first existing file
- [ ] get_all_config_paths() returns all possible locations
- [ ] Well-documented with examples

**Deliverables**:

- `mycelium_onboarding/config_loader.py`
- `tests/test_config_loader.py`
- Usage examples in docstrings

______________________________________________________________________

### Task 1.7: Integration Testing & Documentation

**Agent**: platform-engineer (lead), test-automator (support) **Effort**: 6 hours **Dependencies**: Tasks 1.1-1.6

**Description**: Create integration tests validating entire activation flow and write user documentation.

**Integration Tests**:

```python
# tests/integration/test_environment_activation.py
import pytest
import subprocess
from pathlib import Path


def test_manual_activation_full_flow(tmp_path):
    """Test complete manual activation flow."""
    # Setup mock project
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Copy activation script
    activate_script = project_dir / "bin" / "activate.sh"
    activate_script.parent.mkdir()
    # ... copy script ...

    # Run activation in subprocess
    result = subprocess.run(
        ["bash", "-c", f"source {activate_script} && env"],
        capture_output=True,
        text=True
    )

    # Verify environment variables set
    assert "MYCELIUM_ROOT" in result.stdout
    assert "MYCELIUM_CONFIG_DIR" in result.stdout
    assert "MYCELIUM_ENV_ACTIVE=1" in result.stdout


def test_direnv_activation(tmp_path):
    """Test direnv activation (if direnv installed)."""
    if not shutil.which("direnv"):
        pytest.skip("direnv not installed")

    # Setup .envrc
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    envrc = project_dir / ".envrc"
    # ... copy .envrc.template ...

    # Allow direnv
    subprocess.run(["direnv", "allow"], cwd=project_dir, check=True)

    # Verify environment
    result = subprocess.run(
        ["direnv", "exec", str(project_dir), "env"],
        capture_output=True,
        text=True
    )

    assert "MYCELIUM_ENV_ACTIVE=1" in result.stdout


def test_runtime_validation():
    """Test runtime validation catches missing environment."""
    from mycelium_onboarding.env_validator import validate_environment

    # Clear environment
    for var in os.environ.copy():
        if var.startswith("MYCELIUM_"):
            del os.environ[var]

    # Should raise error
    with pytest.raises(EnvironmentValidationError):
        validate_environment()
```

**User Documentation**:

````markdown
# Environment Activation Guide

## Automatic Activation (Recommended)

### Using direnv

1. Install direnv: https://direnv.net/docs/installation.html

2. Add hook to your shell config:
   ```bash
   # bash: ~/.bashrc
   eval "$(direnv hook bash)"

   # zsh: ~/.zshrc
   eval "$(direnv hook zsh)"
   ```

3. Setup direnv in project:
   ```bash
   python -m mycelium_onboarding setup-direnv
   direnv allow
   ```

4. Environment activates automatically when entering project directory

## Manual Activation

### One-Time Activation

```bash
cd /path/to/mycelium
source bin/activate.sh
```

You'll see:
```
✓ Mycelium environment activated
  Run 'deactivate' to deactivate
```

Your prompt will show `(mycelium)` prefix.

### Deactivation

```bash
deactivate
```

## Verifying Activation

```bash
mycelium status
```

Should show all environment variables set:
```
Mycelium Environment Status:
  ✓ MYCELIUM_ROOT: /path/to/mycelium
  ✓ MYCELIUM_CONFIG_DIR: /home/user/.config/mycelium
  ✓ MYCELIUM_DATA_DIR: /home/user/.local/share/mycelium
  ...
```

## Troubleshooting

### "Environment not active" errors

Run:
```bash
source bin/activate.sh
```

### direnv not working

1. Check hook is in shell config
2. Run `direnv allow` in project directory
3. Verify with `direnv status`
````

**Acceptance Criteria**:

- [ ] Integration tests cover full activation flow
- [ ] Tests verify environment variables set correctly
- [ ] Tests verify runtime validation works
- [ ] User documentation covers both direnv and manual activation
- [ ] Troubleshooting guide addresses common issues

**Deliverables**:

- `tests/integration/test_environment_activation.py`
- `docs/environment-activation.md`
- `docs/troubleshooting-environment.md`

______________________________________________________________________

## Exit Criteria

- [ ] **Environment Isolation**

  - [ ] XDG directory structure implemented and tested
  - [ ] All XDG functions respect environment variables
  - [ ] Project-local .mycelium/ directory supported

- [ ] **Activation Methods**

  - [ ] direnv integration working (.envrc.template)
  - [ ] Manual activation script working (bin/activate.sh)
  - [ ] Deactivation restores original environment
  - [ ] Shell prompt modified to show active state

- [ ] **Runtime Validation**

  - [ ] validate_environment() prevents running without activation
  - [ ] Clear error messages with fix instructions
  - [ ] is_environment_active() quick check implemented

- [ ] **Configuration Hierarchy**

  - [ ] Project-local → user-global → defaults precedence
  - [ ] get_config_path() follows correct order
  - [ ] find_config_file() returns first existing file

- [ ] **Testing**

  - [ ] All unit tests passing (≥80% coverage)
  - [ ] Integration tests validate full activation flow
  - [ ] Tested on Linux, macOS, Windows (WSL2)

- [ ] **Documentation**

  - [ ] Environment activation guide complete
  - [ ] Troubleshooting guide addresses common issues
  - [ ] Code well-commented with examples

## Deliverables

### Code Modules

- `mycelium_onboarding/xdg_dirs.py` - XDG directory management
- `mycelium_onboarding/env_validator.py` - Runtime validation
- `mycelium_onboarding/config_loader.py` - Hierarchical config loading
- `mycelium_onboarding/setup_direnv.py` - direnv setup utility

### Scripts

- `.envrc.template` - direnv configuration template
- `bin/activate.sh` - Manual activation script
- `bin/mycelium` - Wrapper script with validation

### Tests

- `tests/test_xdg_dirs.py` - Unit tests for XDG functions
- `tests/test_env_validator.py` - Unit tests for validation
- `tests/test_config_loader.py` - Unit tests for config loading
- `tests/integration/test_environment_activation.py` - Integration tests

### Documentation

- `docs/design/environment-isolation-strategy.md` - Design document
- `docs/environment-activation.md` - User guide
- `docs/troubleshooting-environment.md` - Troubleshooting guide
- `docs/manual-activation.md` - Manual activation reference

## Testing & Validation

### Unit Test Coverage

Target: ≥80% coverage across all modules

```bash
uv run pytest tests/ --cov=mycelium_onboarding --cov-report=term-missing
```

### Integration Tests

```bash
uv run pytest tests/integration/ -v
```

### Platform Testing

Test matrix:

- Ubuntu 22.04 (Linux)
- macOS 13+ (Darwin)
- Windows 11 WSL2 (Linux kernel)

### Manual Validation Checklist

- [ ] XDG directories created in correct locations
- [ ] direnv activation works without errors
- [ ] Manual activation modifies shell prompt
- [ ] Deactivation restores original environment
- [ ] Runtime validation catches missing vars
- [ ] Config loading follows precedence order
- [ ] Works without direnv installed
- [ ] Works on all three platforms

## Risk Assessment

### High Risk

**Platform-specific path issues**: Windows path handling different from Unix

- **Mitigation**: Use pathlib exclusively, extensive WSL2 testing
- **Contingency**: Platform-specific implementations if needed

**direnv not installed**: Users may not have direnv

- **Mitigation**: Manual activation as fully-supported alternative
- **Contingency**: None needed (manual activation is primary fallback)

### Medium Risk

**Shell compatibility**: Different shells (bash, zsh, fish) handle scripts differently

- **Mitigation**: Test on all three shells
- **Contingency**: Shell-specific activation scripts if needed

**Nested activation**: User activates multiple environments

- **Mitigation**: Check for existing activation, warn user
- **Contingency**: Support nested activation with counter

### Low Risk

**XDG env vars not set**: Most users don't set XDG\_\* variables

- **Mitigation**: Sensible defaults (~/.config, ~/.local/share)
- **Contingency**: None needed (defaults are primary behavior)

## Dependencies for Next Milestones

### M02: Configuration System

**Depends on**:

- XDG directory functions (`xdg_dirs.py`)
- Config path resolution (`config_loader.py`)
- Environment validation

**Will use**:

- `get_config_dir()` for storing config.yaml
- `get_config_path()` for loading configuration
- `validate_environment()` before any config operations

### M03: Service Detection

**Depends on**:

- Environment validation to ensure clean execution context
- XDG cache directory for caching detection results

**Will use**:

- `get_cache_dir()` for storing detection cache
- `validate_environment()` before running detection

### M04: Interactive Onboarding

**Depends on**:

- All environment isolation features to ensure wizard runs in correct context

**Will use**:

- Environment validation before wizard starts
- Config path resolution for saving user selections

______________________________________________________________________

**Milestone Version**: 1.0 **Last Updated**: 2025-10-13 **Status**: Ready for Implementation
