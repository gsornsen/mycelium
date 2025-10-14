# Environment Activation Guide

**Version**: 1.0
**Last Updated**: 2025-10-13
**Audience**: Developers using Mycelium

---

## Quick Start (30 seconds)

### Option A: Automatic Activation (with direnv)

```bash
# One-time setup
direnv allow

# Done! Environment activates automatically when you cd to the project
cd /path/to/mycelium
# ✓ Mycelium environment activated (direnv)
```

### Option B: Manual Activation (without direnv)

```bash
# Each time you open a terminal
source bin/activate.sh
# ✓ Mycelium environment activated (shell: bash)

# When done
deactivate
```

---

## Table of Contents

1. [What Gets Set Up](#what-gets-set-up)
2. [Automatic Activation with direnv](#automatic-activation-with-direnv)
3. [Manual Activation](#manual-activation)
4. [Verification Steps](#verification-steps)
5. [Common Workflows](#common-workflows)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Troubleshooting](#troubleshooting)

---

## What Gets Set Up

When you activate the Mycelium environment, the following happens:

### 1. Environment Variables

All XDG-compliant directories are configured:

- **MYCELIUM_ROOT** - Project root directory
- **MYCELIUM_CONFIG_DIR** - `~/.config/mycelium` (user configuration)
- **MYCELIUM_DATA_DIR** - `~/.local/share/mycelium` (application data)
- **MYCELIUM_CACHE_DIR** - `~/.cache/mycelium` (temporary cache)
- **MYCELIUM_STATE_DIR** - `~/.local/state/mycelium` (application state)
- **MYCELIUM_PROJECT_DIR** - `.mycelium/` (project-local config)
- **MYCELIUM_ENV_ACTIVE** - `1` (activation flag)

### 2. Directory Creation

All XDG directories are automatically created if they don't exist:

```
~/.config/mycelium/           # User configuration files
~/.local/share/mycelium/      # Application data (templates, etc.)
~/.cache/mycelium/            # Temporary cache (safe to delete)
~/.local/state/mycelium/      # Application state and logs
```

### 3. PATH Modification

The project's `bin/` directory is prepended to your PATH:

```bash
# Before activation
$ which mycelium
# (not found)

# After activation
$ which mycelium
/path/to/mycelium/bin/mycelium
```

### 4. Python Virtual Environment

If `.venv/` exists, it's automatically activated:

```bash
# Activates uv-managed virtual environment
(mycelium) $ which python
/path/to/mycelium/.venv/bin/python
```

### 5. Shell Prompt

Your prompt is modified to show the active environment:

```bash
# Before
user@host:~/mycelium$

# After
(mycelium) user@host:~/mycelium$
```

---

## Automatic Activation with direnv

**Recommended for**: Daily development work

### Prerequisites

1. Install direnv:
   ```bash
   # Ubuntu/Debian
   sudo apt install direnv

   # macOS
   brew install direnv

   # Other: https://direnv.net/docs/installation.html
   ```

2. Add direnv hook to your shell config:
   ```bash
   # For bash (~/.bashrc)
   eval "$(direnv hook bash)"

   # For zsh (~/.zshrc)
   eval "$(direnv hook zsh)"

   # For fish (~/.config/fish/config.fish)
   direnv hook fish | source
   ```

3. Restart your shell or source the config file.

### Setup

```bash
# Navigate to project
cd /path/to/mycelium

# Allow .envrc (one-time)
direnv allow

# ✓ Mycelium environment activated (direnv)
```

### How It Works

```bash
# When you cd into the project directory
cd ~/mycelium
# direnv: loading ~/mycelium/.envrc
# ✓ Mycelium environment activated (direnv)

# Environment is active, all commands work
mycelium status
pytest

# When you cd out, environment is automatically deactivated
cd ~
# direnv: unloading
```

### Advantages

- ✅ Fully automatic - no manual steps
- ✅ Activates on `cd` into project
- ✅ Deactivates on `cd` out of project
- ✅ Perfect for multi-project workflows
- ✅ No shell pollution - keeps environments isolated

### Security Note

Always review `.envrc` changes before running `direnv allow`:

```bash
# After git pull with .envrc changes
cat .envrc                  # Review changes
direnv allow                # Only if changes look safe
```

---

## Manual Activation

**Recommended for**: CI/CD, scripts, or when direnv isn't available

### Basic Usage

```bash
# Navigate to project
cd /path/to/mycelium

# Activate
source bin/activate.sh

# ✓ Mycelium environment activated (shell: bash)
#   MYCELIUM_ROOT: /path/to/mycelium
#   Run 'deactivate' to deactivate

# Your shell prompt changes
(mycelium) $

# Work with mycelium...
mycelium status
pytest

# Deactivate when done
deactivate
```

### Verbose Mode

Enable verbose output for troubleshooting:

```bash
# Method 1: Environment variable
export MYCELIUM_VERBOSE=1
source bin/activate.sh

# Method 2: Command flag
source bin/activate.sh --verbose
```

Verbose mode shows:
- Script execution steps
- Timestamps
- Working directory
- Script location

### Multiple Terminals

Each terminal needs its own activation:

```bash
# Terminal 1
cd ~/mycelium
source bin/activate.sh
# Work in Terminal 1...

# Terminal 2 (separate session)
cd ~/mycelium
source bin/activate.sh
# Work in Terminal 2...
```

### Re-activation

If you try to activate when already active:

```bash
source bin/activate.sh
# Warning: Mycelium environment already active
#   Current MYCELIUM_ROOT: /path/to/mycelium
#   Run 'deactivate' first if you want to re-activate

# Deactivate first
deactivate

# Then re-activate
source bin/activate.sh
```

---

## Verification Steps

After activation, verify everything is set up correctly:

### 1. Check Environment Status

```bash
# Quick check
echo $MYCELIUM_ENV_ACTIVE
# Output: 1

# Detailed check
mycelium status
```

### 2. Run Diagnostics

```bash
mycelium-diagnose
```

This shows:
- Shell information
- All environment variables
- Directory status (existence, permissions, size)
- PATH configuration
- Virtual environment status
- direnv status
- System information
- Actionable recommendations

### 3. Verify Directories Exist

```bash
# Check all XDG directories were created
ls -la $MYCELIUM_CONFIG_DIR
ls -la $MYCELIUM_DATA_DIR
ls -la $MYCELIUM_CACHE_DIR
ls -la $MYCELIUM_STATE_DIR
```

### 4. Verify PATH

```bash
# Check mycelium commands are available
which mycelium
which mycelium-diagnose

# Should show paths under project bin/
```

### 5. Verify Python Environment

```bash
# Check virtual environment is active
which python
# Should show: /path/to/mycelium/.venv/bin/python

python --version
# Should show: Python 3.10+ (your project version)
```

---

## Common Workflows

### Daily Development

```bash
# Option A: With direnv (recommended)
cd ~/mycelium
# Environment activates automatically
pytest

# Option B: Manual activation
cd ~/mycelium
source bin/activate.sh
pytest
deactivate
```

### Running Tests

```bash
# After activation
pytest tests/ -v

# With coverage
pytest tests/ --cov=mycelium_onboarding --cov-report=term-missing

# Single test file
pytest tests/test_xdg_dirs.py -v
```

### Using CLI Tools

```bash
# After activation, all mycelium commands work
mycelium status
mycelium-diagnose
check-dependencies.sh
```

### CI/CD Pipeline

```yaml
# Example: GitHub Actions
steps:
  - uses: actions/checkout@v4

  - name: Setup Python
    uses: actions/setup-python@v4
    with:
      python-version: '3.10'

  - name: Install dependencies
    run: |
      pip install uv
      uv sync

  - name: Activate and test
    run: |
      source bin/activate.sh
      pytest tests/ -v
```

### Docker Development

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install uv && uv sync

# In your entrypoint or CMD
CMD ["bash", "-c", "source bin/activate.sh && mycelium status"]
```

### Multiple Projects

```bash
# Terminal 1: Project A
cd ~/mycelium-prod
source bin/activate.sh
# Use production config in .mycelium/

# Terminal 2: Project B
cd ~/mycelium-dev
source bin/activate.sh
# Use development config in .mycelium/
```

---

## Environment Variables Reference

### Core Variables

| Variable | Example | Purpose |
|----------|---------|---------|
| `MYCELIUM_ROOT` | `/home/user/mycelium` | Project root directory (absolute path) |
| `MYCELIUM_ENV_ACTIVE` | `1` | Activation flag (1 = active, unset = inactive) |

### XDG Directories

| Variable | Example | Purpose |
|----------|---------|---------|
| `MYCELIUM_CONFIG_DIR` | `~/.config/mycelium` | User configuration files |
| `MYCELIUM_DATA_DIR` | `~/.local/share/mycelium` | Application data (templates, history) |
| `MYCELIUM_CACHE_DIR` | `~/.cache/mycelium` | Temporary cache (safe to delete) |
| `MYCELIUM_STATE_DIR` | `~/.local/state/mycelium` | Application state and logs |
| `MYCELIUM_PROJECT_DIR` | `.mycelium/` | Project-local configuration |

### XDG Overrides

You can override XDG base directories before activation:

```bash
# Custom XDG directories
export XDG_CONFIG_HOME=~/my-config
export XDG_DATA_HOME=~/my-data
export XDG_CACHE_HOME=~/my-cache
export XDG_STATE_HOME=~/my-state

# Now activate
source bin/activate.sh

# Mycelium directories will be under your custom locations
# e.g., ~/my-config/mycelium, ~/my-data/mycelium, etc.
```

### Internal Variables (Don't Modify)

| Variable | Purpose |
|----------|---------|
| `MYCELIUM_OLD_PATH` | Backup of original PATH (for deactivation) |
| `MYCELIUM_OLD_PS1` | Backup of original prompt (for deactivation) |

---

## Troubleshooting

### Environment Not Active

**Symptom**: Commands fail with "environment not active" error

**Solutions**:
```bash
# Check if active
echo $MYCELIUM_ENV_ACTIVE

# If not set, activate
source bin/activate.sh

# Or with direnv
direnv allow
```

### Already Active Warning

**Symptom**: "Warning: Mycelium environment already active"

**Solution**:
```bash
# Deactivate first
deactivate

# Then re-activate
source bin/activate.sh
```

### Missing Virtual Environment

**Symptom**: "Warning: Virtual environment not found at .venv/"

**Solution**:
```bash
# Create virtual environment
uv sync

# Then activate
source bin/activate.sh
```

### Permission Errors

**Symptom**: Can't create directories or write files

**Solution**:
```bash
# Check permissions
ls -ld ~/.config ~/.local ~/.cache

# Fix if needed
chmod u+w ~/.config ~/.local ~/.cache

# Or run diagnostics
mycelium-diagnose
```

### Shell Not Supported

**Symptom**: "Warning: Shell detection failed"

**Supported shells**:
- Bash 4.0+
- Zsh 5.0+

**Solution**:
```bash
# Check your shell
echo $SHELL

# Switch to bash if needed
bash
source bin/activate.sh
```

### WSL Performance Issues

**Symptom**: Slow operations in WSL

**Solution**:
```bash
# Check if in Windows filesystem
pwd
# If shows /mnt/c/..., you're in Windows filesystem

# Move to WSL filesystem for better performance
cp -r /mnt/c/Users/YourName/mycelium ~/mycelium
cd ~/mycelium
source bin/activate.sh
```

### direnv Not Loading

**Symptom**: direnv doesn't activate automatically

**Solutions**:
```bash
# 1. Check direnv is installed
which direnv

# 2. Check hook is in shell config
grep direnv ~/.bashrc  # or ~/.zshrc

# 3. Add hook if missing
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc

# 4. Allow .envrc
cd /path/to/mycelium
direnv allow
```

### Nested Shells

**Symptom**: Activation lost in subshells

**Explanation**: Subshells don't inherit activation automatically

**Solution**:
```bash
# In parent shell
source bin/activate.sh

# When starting subshell
bash  # or zsh

# Must activate again in subshell
source bin/activate.sh
```

For more troubleshooting, see [troubleshooting-environment.md](troubleshooting-environment.md)

---

## Advanced Topics

### Custom Configuration Hierarchy

Mycelium uses a two-tier configuration hierarchy:

1. **User-global** (in `MYCELIUM_CONFIG_DIR`)
   - Applies to all Mycelium projects
   - Example: `~/.config/mycelium/config.yaml`

2. **Project-local** (in `MYCELIUM_PROJECT_DIR`)
   - Overrides user-global settings
   - Example: `.mycelium/config.yaml`

```bash
# Edit user-global config
vim $MYCELIUM_CONFIG_DIR/config.yaml

# Edit project-local config (overrides global)
vim $MYCELIUM_PROJECT_DIR/config.yaml
```

### Running Without Activation

Some wrapper scripts handle activation automatically:

```bash
# This wrapper checks and warns if not activated
./bin/mycelium status

# But activation is still recommended for best experience
source bin/activate.sh
mycelium status
```

### Programmatic Activation Check

```python
from mycelium_onboarding.env_validator import is_environment_active, validate_environment

# Quick boolean check
if is_environment_active():
    print("Environment is active")

# Comprehensive validation (raises exception if invalid)
try:
    validate_environment()
    print("Environment is valid")
except EnvironmentValidationError as e:
    print(f"Environment error: {e}")
```

---

## See Also

- [Manual Activation Guide](manual-activation.md) - Detailed manual activation documentation
- [Troubleshooting Guide](troubleshooting-environment.md) - Comprehensive troubleshooting
- [Design Document](design/environment-isolation-strategy.md) - Technical architecture
- [Contributing Guide](../CONTRIBUTING.md) - Development setup

---

## Getting Help

1. **Run diagnostics**: `mycelium-diagnose`
2. **Check dependencies**: `./bin/check-dependencies.sh`
3. **Read troubleshooting**: [troubleshooting-environment.md](troubleshooting-environment.md)
4. **Ask for help**: Open an issue with diagnostics output

---

**Last Updated**: 2025-10-13
**Maintained By**: DevOps Engineering Team
