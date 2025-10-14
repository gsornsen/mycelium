# Mycelium Manual Activation Guide

**Version**: 1.0
**Last Updated**: 2025-10-13
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Activation Methods](#activation-methods)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)
7. [Advanced Usage](#advanced-usage)

---

## Overview

This guide covers manual activation of the Mycelium environment for users who don't use direnv or prefer explicit control over their development environment.

### What is Environment Activation?

Environment activation sets up your shell with the correct:
- Environment variables (paths to config, data, cache directories)
- Python virtual environment
- PATH modifications (adds `bin/` to your PATH)
- Shell prompt indicator

### Why Manual Activation?

Manual activation is useful when:
- You don't have direnv installed
- You're running in CI/CD environments
- You prefer explicit control
- You're running automated scripts

---

## Prerequisites

Before activating, ensure you have all required dependencies:

```bash
# Run the dependency checker
./bin/check-dependencies.sh
```

### Required

- **Python 3.10+**: Check with `python3 --version`
- **Git**: Check with `git --version`

### Optional but Recommended

- **uv**: Fast Python package manager ([install](https://github.com/astral-sh/uv))
- **direnv**: Automatic environment activation ([install](https://direnv.net/))

---

## Quick Start

### 1. Install Dependencies

```bash
# Check dependencies first
./bin/check-dependencies.sh

# Install Python dependencies using uv
uv sync
```

### 2. Activate Environment

```bash
# From the project root directory
source bin/activate.sh
```

You should see:
```
Mycelium environment activated (shell: bash)
  MYCELIUM_ROOT: /path/to/mycelium
  Run 'deactivate' to deactivate
```

Your shell prompt will change to show `(mycelium)`:
```bash
(mycelium) user@host:~/mycelium$
```

### 3. Verify Activation

```bash
# Check environment status
mycelium status

# Or run diagnostics
mycelium-diagnose
```

### 4. Deactivate When Done

```bash
deactivate
```

---

## Activation Methods

### Method A: Manual Activation (Recommended for Scripts)

**Use case**: CI/CD, scripts, explicit control

```bash
# Navigate to project directory
cd /path/to/mycelium

# Source the activation script
source bin/activate.sh

# Your environment is now active
# Work with mycelium...

# Deactivate when done
deactivate
```

**Advantages**:
- Explicit control
- Works everywhere (no dependencies)
- Good for scripting

**Disadvantages**:
- Must remember to activate/deactivate
- No automatic activation on `cd`

### Method B: direnv (Recommended for Daily Development)

**Use case**: Daily development, automatic activation

```bash
# One-time setup
direnv allow

# Environment activates automatically when you cd into the directory
cd /path/to/mycelium
# direnv: loading .envrc
# Mycelium environment activated (direnv)
```

**Advantages**:
- Automatic activation/deactivation
- Seamless workflow
- No manual steps

**Disadvantages**:
- Requires direnv installation
- Requires shell hook configuration

See [direnv Integration Guide](./direnv-setup.md) for full setup instructions.

---

## Troubleshooting

### Issue: "Environment already active" warning

**Problem**: You tried to activate while already activated.

**Solution**:
```bash
# Deactivate first
deactivate

# Then activate again
source bin/activate.sh
```

### Issue: "Failed to determine script directory"

**Problem**: The activation script couldn't determine its location.

**Possible causes**:
- Script not sourced (ran directly with `./bin/activate.sh`)
- Corrupted script
- Unsupported shell

**Solution**:
```bash
# Make sure to SOURCE the script (note the 'source' command)
source bin/activate.sh

# NOT this (will fail):
# ./bin/activate.sh
```

### Issue: "Not a Mycelium project (missing pyproject.toml)"

**Problem**: You're not in the Mycelium project directory.

**Solution**:
```bash
# Navigate to the project root
cd /path/to/mycelium

# Verify you're in the right place
ls pyproject.toml

# Then activate
source bin/activate.sh
```

### Issue: "Virtual environment not found at .venv/"

**Problem**: Python virtual environment hasn't been created yet.

**Solution**:
```bash
# Create virtual environment and install dependencies
uv sync

# Then activate
source bin/activate.sh
```

### Issue: Shell compatibility warning

**Problem**: Your shell is not bash or zsh.

**Supported shells**:
- Bash 4.0+
- Zsh 5.0+
- Fish 3.0+ (use `source bin/activate.fish` - coming soon)

**Solution**:
```bash
# Check your shell
echo $SHELL

# If using fish, wait for activate.fish implementation
# For other shells, consider switching to bash/zsh for mycelium development
```

### Issue: Permission denied errors

**Problem**: Can't create directories or write files.

**Solution**:
```bash
# Check permissions on your home directory
ls -ld ~/.config ~/.local ~/.cache

# Fix permissions if needed
chmod u+w ~/.config ~/.local ~/.cache

# Or run diagnostics
mycelium-diagnose
```

### Issue: WSL Performance Warning

**Problem**: Running in Windows filesystem (/mnt/c/).

**Solution**:
```bash
# Move your project to WSL filesystem for better performance
cp -r /mnt/c/Users/YourName/mycelium ~/mycelium
cd ~/mycelium
source bin/activate.sh
```

---

## FAQ

### Q: Do I need to activate every time I open a new terminal?

**A**: Yes, with manual activation. Each terminal session needs its own activation. This is by design to keep your environment clean.

**Alternative**: Use direnv for automatic activation.

### Q: Can I have multiple terminal windows with different activations?

**A**: Yes! Each terminal session has its own environment. You can even activate different projects in different terminals.

### Q: What if I activate in directory A and then cd to directory B?

**A**: The activation stays with your shell session, not the directory. You'll still have mycelium environment active in directory B.

**To deactivate**: Run `deactivate` before changing to other projects.

### Q: Can I customize the activation prompt?

**A**: Not directly, but you can modify `bin/activate.sh` if needed. Look for the lines:

```bash
export PS1="(mycelium) $PS1"
```

Change `"(mycelium)"` to whatever you prefer.

### Q: Will activation modify my shell configuration files?

**A**: No! Activation only affects the current shell session. It never modifies:
- ~/.bashrc
- ~/.zshrc
- ~/.profile
- Any other configuration files

Everything is temporary and session-specific.

### Q: How do I completely uninstall mycelium environment?

**A**:
```bash
# 1. Deactivate if active
deactivate

# 2. Remove XDG directories (optional - contains your config and data)
rm -rf ~/.config/mycelium
rm -rf ~/.local/share/mycelium
rm -rf ~/.cache/mycelium
rm -rf ~/.local/state/mycelium

# 3. Remove project directory
cd ..
rm -rf mycelium
```

### Q: Can I use this in CI/CD?

**A**: Yes! Manual activation is perfect for CI/CD:

```yaml
# Example GitHub Actions
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
  - name: Activate and run tests
    run: |
      source bin/activate.sh
      mycelium status
      pytest
```

### Q: What's the difference between MYCELIUM_ROOT and project root?

**A**: They're the same! MYCELIUM_ROOT is an environment variable that points to the absolute path of your mycelium project directory.

---

## Advanced Usage

### Verbose Mode for Debugging

Enable verbose output to troubleshoot activation issues:

```bash
# Method 1: Environment variable
export MYCELIUM_VERBOSE=1
source bin/activate.sh

# Method 2: Command line flag
source bin/activate.sh --verbose
```

This will show:
- Script execution steps (set -x)
- Timestamps
- Working directory
- Script location

### Running Commands Without Activation

Some commands can detect and warn you if environment isn't active:

```bash
# This will fail with helpful message
./bin/mycelium status
# Error: Mycelium environment not active
# Activate the environment first:
#   With direnv: cd to project and run 'direnv allow'
#   Without direnv: run 'source bin/activate.sh'
```

### Checking Activation Status

```bash
# Method 1: Check environment variable
echo $MYCELIUM_ENV_ACTIVE
# Output: 1 (if active) or empty (if not active)

# Method 2: Use diagnostic command
mycelium-diagnose

# Method 3: Use mycelium status (requires activation)
mycelium status
```

### Nested Shell Sessions

If you spawn a subshell, the activation is NOT inherited:

```bash
# Activate in parent shell
source bin/activate.sh

# Start subshell
bash

# Now NOT active - need to activate again in subshell
source bin/activate.sh
```

### Using with Virtual Environments Other Than uv

The activation script will work with any Python virtual environment at `.venv/`:

```bash
# Create with python venv
python3 -m venv .venv

# Or with virtualenv
virtualenv .venv

# Activation script will detect and activate it
source bin/activate.sh
```

### Multiple Project Instances

You can have multiple clones of mycelium with different settings:

```bash
# Project 1: Production testing
cd ~/mycelium-prod
source bin/activate.sh
# Use .mycelium/config.yaml for prod-specific settings

# Project 2: Development (different terminal)
cd ~/mycelium-dev
source bin/activate.sh
# Use .mycelium/config.yaml for dev-specific settings
```

---

## Environment Variables Reference

After activation, these environment variables are set:

| Variable | Value | Purpose |
|----------|-------|---------|
| `MYCELIUM_ROOT` | `/path/to/mycelium` | Project root directory |
| `MYCELIUM_CONFIG_DIR` | `~/.config/mycelium` | User configuration |
| `MYCELIUM_DATA_DIR` | `~/.local/share/mycelium` | User data (templates, history) |
| `MYCELIUM_CACHE_DIR` | `~/.cache/mycelium` | Temporary cache |
| `MYCELIUM_STATE_DIR` | `~/.local/state/mycelium` | Application state |
| `MYCELIUM_PROJECT_DIR` | `$MYCELIUM_ROOT/.mycelium` | Project-local config |
| `MYCELIUM_ENV_ACTIVE` | `1` | Activation flag |

### Internal Variables (Don't Modify)

| Variable | Purpose |
|----------|---------|
| `MYCELIUM_OLD_PATH` | Backup of original PATH (for deactivation) |
| `MYCELIUM_OLD_PS1` | Backup of original prompt (for deactivation) |

---

## Scripts Reference

### bin/activate.sh

Main activation script. Must be sourced, not executed.

```bash
source bin/activate.sh [OPTIONS]

Options:
  -v, --verbose    Enable verbose output for debugging
```

### bin/mycelium

Wrapper script that ensures environment is active before running commands.

```bash
./bin/mycelium <command> [args]

Example:
  ./bin/mycelium status
  ./bin/mycelium --help
```

### bin/mycelium-diagnose

Comprehensive diagnostic tool for troubleshooting environment issues.

```bash
./bin/mycelium-diagnose

Shows:
  - Shell information
  - Environment variables
  - Directory status
  - PATH check
  - Virtual environment status
  - direnv status
  - System information
  - Recommendations
```

### bin/check-dependencies.sh

Pre-flight check for all dependencies before activation.

```bash
./bin/check-dependencies.sh

Checks:
  - Python version (3.10+)
  - Git installation
  - uv installation (optional)
  - direnv installation (optional)
  - Disk space
  - Write permissions
  - Conflicting environment variables
```

---

## Getting Help

### 1. Run Diagnostics

```bash
./bin/mycelium-diagnose
```

This provides comprehensive information about your environment and actionable recommendations.

### 2. Check Dependencies

```bash
./bin/check-dependencies.sh
```

Ensures all required dependencies are installed and properly configured.

### 3. Read the Design Document

See [Environment Isolation Strategy](./design/environment-isolation-strategy.md) for detailed technical information.

### 4. Ask for Help

If you're still having issues:

1. Run diagnostics and save output: `./bin/mycelium-diagnose > diagnostics.txt`
2. Include your OS and shell version
3. Describe what you tried and what error you got
4. Open an issue with this information

---

## See Also

- [Environment Isolation Strategy](./design/environment-isolation-strategy.md) - Technical design document
- [direnv Setup Guide](./direnv-setup.md) - Automatic activation setup
- [Contributing Guide](../CONTRIBUTING.md) - Development setup

---

**Last Updated**: 2025-10-13
**Maintained By**: DevOps Engineering Team
