# Environment Troubleshooting Guide

**Version**: 1.0
**Last Updated**: 2025-10-13
**Purpose**: Comprehensive troubleshooting for Mycelium environment activation issues

---

## Quick Diagnosis

Before diving into specific issues, run these diagnostic commands:

```bash
# 1. Comprehensive diagnostics
./bin/mycelium-diagnose

# 2. Dependency check
./bin/check-dependencies.sh

# 3. Quick environment check
echo $MYCELIUM_ENV_ACTIVE
```

Save this output if you need to ask for help!

---

## Table of Contents

1. [Environment Not Active Errors](#environment-not-active-errors)
2. [direnv Issues](#direnv-issues)
3. [Permission Errors](#permission-errors)
4. [Path Issues](#path-issues)
5. [Platform-Specific Issues](#platform-specific-issues)
6. [Virtual Environment Issues](#virtual-environment-issues)
7. [Shell Compatibility](#shell-compatibility)
8. [Using mycelium-diagnose](#using-mycelium-diagnose)
9. [Common Error Messages](#common-error-messages)

---

## Environment Not Active Errors

### Error: "Environment not active"

**Symptom**: Running mycelium commands fails with error about inactive environment

```bash
$ mycelium status
Error: Mycelium environment not active
```

**Diagnosis**:
```bash
# Check activation status
echo $MYCELIUM_ENV_ACTIVE
# If empty or not "1", environment is not active
```

**Solutions**:

#### Solution 1: Manual Activation
```bash
source bin/activate.sh
```

#### Solution 2: direnv Activation
```bash
direnv allow
```

#### Solution 3: Check for Sourcing Issues
```bash
# WRONG - will not work (runs in subshell)
./bin/activate.sh

# CORRECT - must use 'source' or '.'
source bin/activate.sh
# or
. bin/activate.sh
```

**Prevention**: Use direnv for automatic activation

---

### Error: "Missing or empty environment variables"

**Symptom**: Python scripts fail with EnvironmentValidationError

```
EnvironmentValidationError: Missing or empty environment variables: MYCELIUM_ROOT, MYCELIUM_CONFIG_DIR
```

**Diagnosis**:
```bash
# Check which variables are missing
env | grep MYCELIUM
```

**Solution**:
```bash
# Activate the environment
source bin/activate.sh

# Verify all variables are set
env | grep MYCELIUM | sort
```

**Root Causes**:
1. Environment never activated
2. Activation failed partway through
3. Variables were accidentally unset

---

### Error: "Already active" warning

**Symptom**: Trying to activate shows warning

```
Warning: Mycelium environment already active
  Current MYCELIUM_ROOT: /path/to/mycelium
  Run 'deactivate' first if you want to re-activate
```

**Diagnosis**:
```bash
# Check if active
echo $MYCELIUM_ENV_ACTIVE
# Output: 1
```

**Solutions**:

#### Solution 1: Use Current Activation
Environment is already active - continue working!

#### Solution 2: Re-activate
```bash
# Deactivate first
deactivate

# Then activate again
source bin/activate.sh
```

**Note**: Re-activation is rarely needed. Usually happens when:
- Sourcing activate.sh multiple times by mistake
- Trying to switch between different project clones

---

## direnv Issues

### Issue: direnv not loading automatically

**Symptom**: Environment doesn't activate when cd'ing to project

```bash
cd ~/mycelium
# (no output, environment not activated)
```

**Diagnosis**:
```bash
# Check if direnv is installed
which direnv

# Check if hook is configured
grep direnv ~/.bashrc  # or ~/.zshrc

# Check direnv status
direnv status
```

**Solutions**:

#### Solution 1: Install direnv
```bash
# Ubuntu/Debian
sudo apt install direnv

# macOS
brew install direnv

# Arch Linux
sudo pacman -S direnv

# From source
curl -sfL https://direnv.net/install.sh | bash
```

#### Solution 2: Add Shell Hook
```bash
# For bash
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc

# For fish
echo 'direnv hook fish | source' >> ~/.config/fish/config.fish
```

#### Solution 3: Allow .envrc
```bash
cd /path/to/mycelium
direnv allow
```

---

### Issue: direnv blocked / .envrc not allowed

**Symptom**: direnv shows blocked message

```
direnv: error /path/to/mycelium/.envrc is blocked. Run `direnv allow` to approve its content
```

**Diagnosis**:
```bash
direnv status
# Look for "Found RC allowed false"
```

**Solution**:
```bash
# Review .envrc contents first (security check)
cat .envrc

# If contents look safe, allow it
direnv allow

# Should see:
# direnv: loading .envrc
# ✓ Mycelium environment activated (direnv)
```

**Security Note**: Always review .envrc before allowing, especially after:
- Cloning a new repository
- Pulling changes that modified .envrc
- Switching branches

---

### Issue: direnv works but environment incomplete

**Symptom**: Some variables set but not all

**Diagnosis**:
```bash
# Check what's set
env | grep MYCELIUM | sort

# Check direnv logs
direnv status
```

**Solution**:
```bash
# Force reload
cd ..
cd /path/to/mycelium

# Or reload direnv
direnv reload

# Or re-allow
direnv allow
```

**Root Cause**: Usually happens when:
- .envrc was modified while direnv was active
- Shell state became inconsistent

---

## Permission Errors

### Error: "Failed to create directory"

**Symptom**: Activation fails with permission error

```
Error: Failed to create directory: /home/user/.config/mycelium
Permission denied
```

**Diagnosis**:
```bash
# Check permissions on parent directories
ls -ld ~/.config
ls -ld ~/.local
ls -ld ~/.cache

# Check if directories are writable
test -w ~/.config && echo "writable" || echo "NOT writable"
```

**Solutions**:

#### Solution 1: Fix Parent Directory Permissions
```bash
# Make directories writable
chmod u+w ~/.config
chmod u+w ~/.local
chmod u+w ~/.cache

# Try activation again
source bin/activate.sh
```

#### Solution 2: Create Directories Manually
```bash
# Create XDG directories manually
mkdir -p ~/.config/mycelium
mkdir -p ~/.local/share/mycelium
mkdir -p ~/.cache/mycelium
mkdir -p ~/.local/state/mycelium

# Set correct permissions
chmod 700 ~/.config/mycelium
chmod 755 ~/.local/share/mycelium
chmod 755 ~/.cache/mycelium
chmod 700 ~/.local/state/mycelium

# Try activation again
source bin/activate.sh
```

#### Solution 3: Use Custom XDG Directories
```bash
# Set custom locations (with write access)
export XDG_CONFIG_HOME=~/my-config
export XDG_DATA_HOME=~/my-data
export XDG_CACHE_HOME=~/my-cache
export XDG_STATE_HOME=~/my-state

# Create base directories
mkdir -p ~/my-config ~/my-data ~/my-cache ~/my-state

# Now activate
source bin/activate.sh
```

---

### Error: "Directory is not writable"

**Symptom**: Runtime validation fails

```
XDGDirectoryError: Config directory is not writable: /home/user/.config/mycelium
```

**Diagnosis**:
```bash
# Check directory permissions
ls -ld ~/.config/mycelium

# Try to write a test file
touch ~/.config/mycelium/test.txt
```

**Solution**:
```bash
# Fix permissions
chmod u+w ~/.config/mycelium

# If that doesn't work, check parent permissions
chmod u+w ~/.config

# Try again
source bin/activate.sh
```

---

## Path Issues

### Issue: mycelium commands not found

**Symptom**: Commands fail even after activation

```bash
(mycelium) $ mycelium status
bash: mycelium: command not found
```

**Diagnosis**:
```bash
# Check if bin is in PATH
echo $PATH | grep mycelium

# Check if files exist
ls -la bin/mycelium

# Check PATH contains project root
echo $MYCELIUM_ROOT
```

**Solutions**:

#### Solution 1: Verify Activation
```bash
# Check if environment is actually active
echo $MYCELIUM_ENV_ACTIVE

# If not active, activate
source bin/activate.sh

# Verify PATH now includes bin/
echo $PATH | grep "$(pwd)/bin"
```

#### Solution 2: Manual PATH Addition
```bash
# Add manually (temporary fix)
export PATH="$MYCELIUM_ROOT/bin:$PATH"

# Verify
which mycelium
```

#### Solution 3: Use Absolute Paths
```bash
# Use absolute path as workaround
/path/to/mycelium/bin/mycelium status
```

---

### Issue: Wrong Python version

**Symptom**: Python from wrong environment

```bash
(mycelium) $ which python
/usr/bin/python  # Should be .venv/bin/python
```

**Diagnosis**:
```bash
# Check VIRTUAL_ENV
echo $VIRTUAL_ENV

# Check if .venv exists
ls -la .venv/
```

**Solution**:
```bash
# If .venv doesn't exist, create it
uv sync

# If .venv exists but not activated, activate manually
source .venv/bin/activate

# Or re-activate mycelium environment
deactivate
source bin/activate.sh
```

---

## Platform-Specific Issues

### WSL2 Issues

#### Issue: Poor performance

**Symptom**: Everything is slow in WSL

**Diagnosis**:
```bash
# Check if in Windows filesystem
pwd
# If starts with /mnt/c/ or /mnt/d/, you're in Windows filesystem
```

**Solution**:
```bash
# Move project to WSL filesystem
cp -r /mnt/c/Users/YourName/mycelium ~/mycelium

# Navigate to new location
cd ~/mycelium

# Activate
source bin/activate.sh
```

**Performance Impact**:
- Windows filesystem (`/mnt/c/`): 10-100x slower
- WSL filesystem (`~/`): Native speed

---

#### Issue: WSL warning during activation

**Symptom**: Warning about Windows filesystem

```
Warning: You're in Windows filesystem (/mnt/c/)
  Performance will be poor. Consider moving project to WSL filesystem (~)
  Continue? [y/N]
```

**Solution**:
```bash
# Option 1: Move project (recommended)
mv /mnt/c/Users/YourName/mycelium ~/mycelium

# Option 2: Continue anyway (not recommended)
# Answer 'y' to the prompt
```

---

### macOS Issues

#### Issue: zsh warnings

**Symptom**: zsh shows warnings about activate.sh

**Solution**:
```bash
# Make sure using source, not direct execution
source bin/activate.sh

# Not ./bin/activate.sh
```

---

#### Issue: Permission issues with Gatekeeper

**Symptom**: macOS blocks script execution

**Solution**:
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine bin/activate.sh

# Or allow in System Preferences
# System Preferences > Security & Privacy > General
```

---

### Linux Issues

#### Issue: SELinux blocking directories

**Symptom**: Permission denied despite correct chmod

**Diagnosis**:
```bash
# Check SELinux status
getenforce

# Check context
ls -Z ~/.config
```

**Solution**:
```bash
# Set correct SELinux context
chcon -R -t user_home_t ~/.config/mycelium

# Or temporarily disable SELinux (not recommended)
sudo setenforce 0
```

---

## Virtual Environment Issues

### Issue: .venv not found

**Symptom**: Warning during activation

```
Warning: Virtual environment not found at .venv/
  Run: uv sync
```

**Diagnosis**:
```bash
# Check if .venv exists
ls -la .venv/

# Check if uv is installed
which uv
```

**Solutions**:

#### Solution 1: Create with uv
```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv sync

# Activate mycelium environment
source bin/activate.sh
```

#### Solution 2: Create with venv
```bash
# Create virtual environment
python3 -m venv .venv

# Install dependencies
.venv/bin/pip install -e .

# Activate mycelium environment
source bin/activate.sh
```

---

### Issue: Virtual environment version mismatch

**Symptom**: Wrong Python version in .venv

**Solution**:
```bash
# Remove old virtual environment
rm -rf .venv

# Create new one with correct Python version
python3.10 -m venv .venv
# or
uv sync

# Activate
source bin/activate.sh
```

---

## Shell Compatibility

### Issue: Unsupported shell

**Symptom**: Warning about shell compatibility

```
Warning: Shell detection failed
  Supported shells: bash, zsh
  Current shell: /bin/fish
```

**Solutions**:

#### Solution 1: Use Bash
```bash
# Start bash
bash

# Then activate
source bin/activate.sh
```

#### Solution 2: Use Zsh
```bash
# Start zsh
zsh

# Then activate
source bin/activate.sh
```

**Supported Shells**:
- ✅ Bash 4.0+
- ✅ Zsh 5.0+
- ❌ Fish (activate.fish coming soon)
- ❌ Dash (not supported)
- ❌ Sh (not supported)

---

### Issue: Bash version too old

**Symptom**: Syntax errors in activate.sh

**Diagnosis**:
```bash
bash --version
```

**Solution**:
```bash
# Ubuntu/Debian - install newer bash
sudo apt update
sudo apt install bash

# macOS - use homebrew bash
brew install bash

# Verify version
bash --version
# Should be 4.0 or higher
```

---

## Using mycelium-diagnose

The diagnostic tool provides comprehensive environment analysis.

### Basic Usage

```bash
./bin/mycelium-diagnose
```

### Output Sections

**1. Shell Information**
- Current shell and version
- Helps diagnose shell compatibility issues

**2. Environment Variables**
- All MYCELIUM_* variables
- Shows which are set/unset

**3. Directory Status**
- Existence, size, permissions
- Writability checks

**4. PATH Check**
- Shows mycelium paths in PATH
- Helps diagnose command not found issues

**5. Virtual Environment**
- Python version and location
- .venv status

**6. direnv Status**
- Installation status
- .envrc allowed/blocked status

**7. System Information**
- OS and platform details
- WSL detection

**8. Critical Files**
- Checks for required files
- Validates project structure

**9. Recommendations**
- Actionable steps to fix issues
- Prioritized by importance

### Saving Diagnostics

```bash
# Save to file
./bin/mycelium-diagnose > diagnostics.txt

# Include in issue reports
cat diagnostics.txt
```

### Interpreting Output

**Good Output Example**:
```
=== Mycelium Environment Diagnostics ===

1. Shell Information
  Current shell: /bin/bash
  Bash version: 5.0.17

2. Environment Variables
  MYCELIUM_CACHE_DIR=/home/user/.cache/mycelium
  MYCELIUM_CONFIG_DIR=/home/user/.config/mycelium
  MYCELIUM_ENV_ACTIVE=1
  MYCELIUM_ROOT=/home/user/mycelium
  ...

=== Recommendations ===

  No issues detected. Environment is properly configured.
```

**Problem Output Example**:
```
=== Recommendations ===

  [ACTION] Environment not activated
    -> Run: source bin/activate.sh

  [ACTION] Virtual environment not created
    -> Run: uv sync

  [OPTIONAL] direnv not installed
    -> Install from: https://direnv.net/
```

---

## Common Error Messages

### "Not a Mycelium project (missing pyproject.toml)"

**Meaning**: You're not in the correct directory

**Solution**:
```bash
# Navigate to project root
cd /path/to/mycelium

# Verify you're in the right place
ls pyproject.toml

# Then activate
source bin/activate.sh
```

---

### "Failed to determine script directory"

**Meaning**: Script wasn't sourced correctly

**Solution**:
```bash
# Use 'source' command
source bin/activate.sh

# NOT direct execution
# ./bin/activate.sh  # WRONG
```

---

### "Deactivation may be incomplete"

**Meaning**: Deactivation couldn't fully clean up

**Solution**:
```bash
# Start fresh shell
exec $SHELL

# Or close and reopen terminal
```

---

### Import errors for mycelium_onboarding

**Meaning**: Python package not installed or venv not activated

**Solution**:
```bash
# Ensure dependencies installed
uv sync

# Activate environment
source bin/activate.sh

# Verify package is importable
python -c "import mycelium_onboarding; print('OK')"
```

---

## Getting Help

If issues persist after trying these solutions:

### 1. Gather Information

```bash
# Run diagnostics
./bin/mycelium-diagnose > diagnostics.txt

# Check dependencies
./bin/check-dependencies.sh > dependencies.txt

# Collect system info
uname -a > system.txt
echo "Shell: $SHELL" >> system.txt
```

### 2. Create Issue Report

Include:
- Output from mycelium-diagnose
- Output from check-dependencies.sh
- Your OS and shell version
- Steps to reproduce
- What you've already tried

### 3. Community Resources

- [GitHub Issues](https://github.com/gsornsen/mycelium/issues)
- [Design Document](design/environment-isolation-strategy.md)
- [Environment Activation Guide](environment-activation.md)

---

## Prevention Tips

### Best Practices

1. **Use direnv** for automatic activation
2. **Always source** activation script (never execute directly)
3. **Run diagnostics** regularly to catch issues early
4. **Keep dependencies updated** (uv, direnv, Python)
5. **Review .envrc changes** before allowing
6. **Use WSL filesystem** (not Windows /mnt/c/)

### Maintenance

```bash
# Monthly: Update dependencies
uv sync --upgrade

# After git pull: Check for .envrc changes
git diff HEAD~1 .envrc

# Weekly: Clear cache if needed
rm -rf ~/.cache/mycelium/*

# Quarterly: Review and clean up
ls -lh ~/.local/share/mycelium
```

---

## Quick Reference

| Issue | Quick Fix |
|-------|----------|
| Environment not active | `source bin/activate.sh` |
| Already active warning | `deactivate` then re-activate |
| direnv blocked | `direnv allow` |
| Commands not found | Check `$PATH`, re-activate |
| Permission denied | `chmod u+w ~/.config ~/.local` |
| Wrong Python | `uv sync`, re-activate |
| Missing .venv | `uv sync` |
| Shell unsupported | Use `bash` or `zsh` |
| WSL slow | Move to `~/` from `/mnt/c/` |

---

**Last Updated**: 2025-10-13
**Maintained By**: DevOps Engineering Team
