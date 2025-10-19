# Plugin Version Switching Guide

**Last Updated**: 2025-10-18

This guide explains how to use `mycelium-switch` to seamlessly switch between development (source) and production (git) versions of the Mycelium plugin.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [Check Status](#check-status)
  - [Switch to Source Mode](#switch-to-source-mode)
  - [Switch to Git Mode](#switch-to-git-mode)
  - [Options](#options)
- [How It Works](#how-it-works)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Safety & Backups](#safety--backups)

---

## Overview

### Why Switch Between Versions?

When working with Mycelium as both a developer and user, you often need to switch between:

1. **Development Mode (Source)**: Plugin symlinked to your local source code
   - Live code changes reflected immediately
   - No restart needed for most changes
   - Full control over the codebase
   - Use when: Developing features, debugging, contributing

2. **Production Mode (Git)**: Plugin cloned from GitHub repository
   - Stable, published version
   - Consistent behavior across sessions
   - Easy updates via `git pull`
   - Use when: Normal usage, testing releases, stable workflows

### Problem This Solves

Without `mycelium-switch`, you would need to:
- Manually remove the plugin directory
- Remember the correct paths and URLs
- Recreate symlinks or clone repositories
- Risk losing configurations
- Track which mode you're in

`mycelium-switch` automates all of this with safety checks and backups.

---

## Quick Start

```bash
# Check current mode
mycelium-switch status

# Switch to development mode (local source)
mycelium-switch source

# Switch to production mode (from GitHub)
mycelium-switch git

# Preview changes before applying
mycelium-switch source --dry-run
```

That's it! The tool handles backups, validation, and state tracking automatically.

---

## Installation

### Prerequisites

- **Git**: Required for git mode operations
- **jq** (optional): Enables enhanced status display and state tracking
- **Bash 4.0+**: Should be available on most modern Linux/macOS systems

### Setup

The script is located at `bin/mycelium-switch` in the Mycelium repository:

```bash
# Ensure it's executable (already done in repo)
chmod +x ~/git/mycelium/bin/mycelium-switch

# Optionally, add to PATH for easy access
echo 'export PATH="$HOME/git/mycelium/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or create an alias
echo 'alias mycelium-switch="~/git/mycelium/bin/mycelium-switch"' >> ~/.bashrc
source ~/.bashrc
```

---

## Usage

### Check Status

Display current plugin mode and details:

```bash
mycelium-switch status
```

**Example Output (Source Mode)**:
```
Mycelium Plugin Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Mode:   🔗 Source (Symlink)
  Target: /home/gerald/git/mycelium/plugins/mycelium-core
  Status: ✅ Development mode active

  Changes to source code will be reflected immediately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Last Switch:
  Mode: source
  When: 2025-10-18T12:30:00Z

Available backups:
  mycelium-core-20251018-120000 (2.3M)
```

**Example Output (Git Mode)**:
```
Mycelium Plugin Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Mode:   📦 Git (Clone)
  URL:    https://github.com/gsornsen/mycelium
  Commit: abc1234 (2025-10-15)
  Status: ✅ Production mode active

  Plugin installed from published version.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Switch to Source Mode

Switch to development mode using your local source code:

```bash
mycelium-switch source
```

**What Happens**:
1. Validates local source exists at `~/git/mycelium`
2. Checks for valid plugin structure and `plugin.json`
3. Creates backup of existing plugin (if not a symlink)
4. Removes existing plugin directory
5. Creates symlink: `~/.claude/plugins/mycelium-core` → `~/git/mycelium/plugins/mycelium-core`
6. Updates state tracking file

**Output**:
```
ℹ Switching to source mode...
ℹ Creating backup: /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123000
✅ Backup created: /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123000

✅ Switched to source mode

  Symlink: /home/gerald/.claude/plugins/mycelium-core
  Target:  /home/gerald/git/mycelium/plugins/mycelium-core
  Backup:  /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123000

ℹ Plugin will use live code from local source
```

**Verification**:
```bash
ls -la ~/.claude/plugins/mycelium-core
# Output: lrwxrwxrwx ... mycelium-core -> /home/gerald/git/mycelium/plugins/mycelium-core
```

---

### Switch to Git Mode

Switch to production mode from GitHub:

```bash
# Use default repository
mycelium-switch git

# Use custom repository
mycelium-switch git https://github.com/username/mycelium-fork
```

**What Happens**:
1. Validates git repository is accessible
2. Creates backup of existing plugin (if exists)
3. Clones repository to temporary directory
4. Moves `plugins/mycelium-core` to `~/.claude/plugins/mycelium-core`
5. Cleans up temporary clone
6. Updates state tracking file

**Output**:
```
ℹ Switching to git mode...
ℹ Creating backup: /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123500
✅ Backup created: /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123500

✅ Switched to git mode

  Repository: https://github.com/gsornsen/mycelium
  Commit:     abc1234
  Location:   /home/gerald/.claude/plugins/mycelium-core
  Backup:     /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-123500

ℹ Plugin installed from published version
```

---

### Options

#### `--dry-run`

Preview changes without applying them:

```bash
mycelium-switch source --dry-run
```

**Output**:
```
ℹ [DRY RUN] Would perform:
  1. Remove: /home/gerald/.claude/plugins/mycelium-core
  2. Create symlink:
     From: /home/gerald/.claude/plugins/mycelium-core
     To:   /home/gerald/git/mycelium/plugins/mycelium-core
  3. Update state file
  4. Backup: /home/gerald/.claude/plugins/.backups/mycelium-core-20251018-124000
```

#### `--verbose`

Show detailed output during operations:

```bash
mycelium-switch source --verbose
```

**Additional Output**:
```
[VERBOSE] Source path: /home/gerald/git/mycelium
[VERBOSE] Removing existing plugin: /home/gerald/.claude/plugins/mycelium-core
[VERBOSE] Creating symlink: /home/gerald/.claude/plugins/mycelium-core -> ...
[VERBOSE] Updated state file: /home/gerald/.claude/plugins/.mycelium-mode
```

#### `--source-path`

Override default source path:

```bash
mycelium-switch source --source-path /custom/path/to/mycelium
```

Useful when:
- Testing alternate branches in different directories
- Working with multiple forks
- Non-standard development setups

#### `--no-backup`

Skip backup creation (use with caution):

```bash
mycelium-switch source --no-backup
```

**Warning**: Only use if:
- You're certain no important data will be lost
- The existing plugin is already backed up
- You're switching from source mode (symlink) to git mode

---

## How It Works

### Architecture

```
mycelium-switch
    |
    ├─ Configuration
    |   ├─ Plugin name: mycelium-core
    |   ├─ Plugins directory: ~/.claude/plugins
    |   ├─ Default source: ~/git/mycelium
    |   └─ Default git URL: https://github.com/gsornsen/mycelium
    |
    ├─ Detection
    |   ├─ Check if plugin exists
    |   ├─ Determine mode (symlink vs directory vs none)
    |   └─ Validate plugin structure
    |
    ├─ State Management
    |   ├─ Store mode and metadata in ~/.claude/plugins/.mycelium-mode
    |   ├─ Track last switch time
    |   └─ Record paths and URLs
    |
    └─ Operations
        ├─ Source Mode: Create symlink to local source
        ├─ Git Mode: Clone repository and extract plugin
        ├─ Backup: Copy existing plugin to .backups/
        └─ Verification: Ensure plugin.json is valid
```

### File Locations

| File/Directory | Purpose |
|---------------|---------|
| `~/.claude/plugins/mycelium-core` | Active plugin location |
| `~/.claude/plugins/.mycelium-mode` | State tracking (JSON) |
| `~/.claude/plugins/.backups/` | Automatic backups |
| `~/git/mycelium/plugins/mycelium-core` | Default source location |

### State Tracking Format

The tool stores state in `~/.claude/plugins/.mycelium-mode` as JSON:

```json
{
  "mode": "source",
  "switched_at": "2025-10-18T12:30:00Z",
  "source_path": "/home/gerald/git/mycelium",
  "git_url": ""
}
```

This enables:
- Status command to show last switch details
- Idempotent operations (don't re-switch if already in desired mode)
- Audit trail for debugging

---

## Advanced Usage

### Multiple Source Locations

Test different branches or forks:

```bash
# Switch to main development branch
mycelium-switch source --source-path ~/git/mycelium

# Switch to feature branch in different directory
mycelium-switch source --source-path ~/git/mycelium-feature

# Switch to fork
mycelium-switch source --source-path ~/git/mycelium-fork
```

### Custom Git Repositories

Use private forks or alternate versions:

```bash
# Public fork
mycelium-switch git https://github.com/username/mycelium-fork

# Private repository (requires SSH key)
mycelium-switch git git@github.com:username/mycelium-private

# Specific branch (clone manually then use source mode)
cd /tmp
git clone -b feature-branch https://github.com/username/mycelium
mycelium-switch source --source-path /tmp/mycelium
```

### Scripting & Automation

Use in scripts with exit codes:

```bash
#!/bin/bash

# Switch to source for development session
if mycelium-switch source --dry-run; then
    echo "Source mode available"
    mycelium-switch source
else
    echo "Source not available, using git"
    mycelium-switch git
fi

# Check exit code
if [[ $? -eq 0 ]]; then
    echo "Switch successful"
else
    echo "Switch failed"
    exit 1
fi
```

### Workspace Profiles

Create wrapper scripts for different workflows:

```bash
# ~/bin/mycelium-dev
#!/bin/bash
# Development profile: source mode + verbose
mycelium-switch source --verbose

# ~/bin/mycelium-prod
#!/bin/bash
# Production profile: git mode from stable branch
mycelium-switch git https://github.com/gsornsen/mycelium
```

---

## Troubleshooting

### Common Issues

#### Issue: "Local source not found"

**Symptom**:
```
❌ Local source not found at: /home/gerald/git/mycelium
```

**Solution**:
```bash
# Verify source exists
ls -la ~/git/mycelium

# If in different location, use --source-path
mycelium-switch source --source-path /actual/path/to/mycelium

# Clone if missing
cd ~/git
git clone https://github.com/gsornsen/mycelium
```

---

#### Issue: "Invalid plugin structure"

**Symptom**:
```
❌ Invalid plugin structure in source
ℹ Missing or invalid: /home/gerald/git/mycelium/plugins/mycelium-core/.claude-plugin/plugin.json
```

**Solution**:
```bash
# Verify plugin.json exists
ls -la ~/git/mycelium/plugins/mycelium-core/.claude-plugin/plugin.json

# Check it's valid JSON
cat ~/git/mycelium/plugins/mycelium-core/.claude-plugin/plugin.json | jq .

# If corrupted, pull fresh copy
cd ~/git/mycelium
git checkout -- plugins/mycelium-core/.claude-plugin/plugin.json
```

---

#### Issue: "Cannot access git repository"

**Symptom**:
```
❌ Cannot access git repository: https://github.com/username/mycelium
ℹ Check URL and network connection
```

**Solutions**:
```bash
# Test git access manually
git ls-remote https://github.com/gsornsen/mycelium

# Check network connection
ping github.com

# Verify URL is correct (check for typos)
mycelium-switch git https://github.com/gsornsen/mycelium

# Use SSH if HTTPS fails
mycelium-switch git git@github.com:gsornsen/mycelium
```

---

#### Issue: "Already in [mode] with same [path/URL]"

**Symptom**:
```
✅ Already in source mode with same path
ℹ Target: /home/gerald/git/mycelium/plugins/mycelium-core
```

**Explanation**: This is not an error! The tool detected you're already in the desired mode and skipped redundant operations (idempotent behavior).

**If you want to force re-switch**:
```bash
# Switch to other mode first, then back
mycelium-switch git
mycelium-switch source
```

---

#### Issue: Symlink Broken After Moving Source

**Symptom**:
```bash
ls -la ~/.claude/plugins/mycelium-core
# lrwxrwxrwx ... mycelium-core -> /old/path/mycelium/plugins/mycelium-core (red/broken)
```

**Solution**:
```bash
# Update to new source location
mycelium-switch source --source-path /new/path/mycelium

# Or switch to git mode temporarily
mycelium-switch git
```

---

### Debugging Tips

#### Enable Verbose Mode

See detailed operations:
```bash
mycelium-switch source --verbose
```

#### Check State File

Inspect current state:
```bash
cat ~/.claude/plugins/.mycelium-mode | jq .
```

#### List Backups

See available backups:
```bash
ls -lah ~/.claude/plugins/.backups/
```

#### Manual Verification

Check plugin is properly installed:
```bash
# Check exists
ls -la ~/.claude/plugins/mycelium-core

# Check plugin.json
cat ~/.claude/plugins/mycelium-core/.claude-plugin/plugin.json | jq .

# If symlink, check target
readlink ~/.claude/plugins/mycelium-core
```

---

## Safety & Backups

### Automatic Backups

**When backups are created**:
- Before switching from git mode to source mode
- Before switching from source mode to git mode (if source modified)
- Before switching from one git URL to another

**When backups are NOT created**:
- Plugin is already a symlink (source mode)
- `--no-backup` flag is used
- Plugin doesn't exist yet (fresh install)

**Backup location**:
```
~/.claude/plugins/.backups/mycelium-core-YYYYMMDD-HHMMSS/
```

**Backup naming**:
```
mycelium-core-20251018-123000  # 2025-10-18 at 12:30:00
```

### Manual Backup Management

```bash
# List all backups
ls -lah ~/.claude/plugins/.backups/

# Restore from backup
rm -rf ~/.claude/plugins/mycelium-core
cp -r ~/.claude/plugins/.backups/mycelium-core-20251018-123000 \
      ~/.claude/plugins/mycelium-core

# Clean old backups (keep last 5)
cd ~/.claude/plugins/.backups
ls -t | tail -n +6 | xargs rm -rf

# Remove all backups (careful!)
rm -rf ~/.claude/plugins/.backups/*
```

### Disaster Recovery

If something goes wrong:

1. **Check backups**:
   ```bash
   ls -lah ~/.claude/plugins/.backups/
   ```

2. **Restore latest backup**:
   ```bash
   LATEST=$(ls -t ~/.claude/plugins/.backups/ | head -n1)
   rm -rf ~/.claude/plugins/mycelium-core
   cp -r ~/.claude/plugins/.backups/$LATEST ~/.claude/plugins/mycelium-core
   ```

3. **Or start fresh**:
   ```bash
   rm -rf ~/.claude/plugins/mycelium-core
   mycelium-switch git  # Known good state
   ```

### Best Practices

1. **Always check status first**:
   ```bash
   mycelium-switch status
   ```

2. **Use dry-run for unfamiliar operations**:
   ```bash
   mycelium-switch source --dry-run
   ```

3. **Keep source and git in sync**:
   - Update source: `cd ~/git/mycelium && git pull`
   - Update git mode: `cd ~/.claude/plugins/mycelium-core && git pull`

4. **Don't modify git mode plugin directly**:
   - Changes will be lost on next switch
   - Make changes in source, then test with source mode

5. **Clean up backups periodically**:
   ```bash
   # Keep last 10 backups
   cd ~/.claude/plugins/.backups
   ls -t | tail -n +11 | xargs rm -rf
   ```

---

## Workflow Examples

### Daily Development Workflow

```bash
# Morning: Start development
mycelium-switch source --verbose

# ... make changes to ~/git/mycelium ...

# Test changes (live in Claude Code)
# No restart needed, changes reflected immediately

# Evening: Switch back to stable
mycelium-switch git
```

### Testing PR Before Merge

```bash
# Clone PR branch
cd ~/git
git clone -b pr-branch https://github.com/username/mycelium mycelium-pr

# Test PR
mycelium-switch source --source-path ~/git/mycelium-pr

# ... test in Claude Code ...

# Back to main
mycelium-switch source  # Uses default ~/git/mycelium

# Cleanup
rm -rf ~/git/mycelium-pr
```

### Multi-Session Setup

```bash
# Terminal 1: Development session
mycelium-switch source

# Terminal 2: Check what mode we're in
mycelium-switch status

# Terminal 3: Production testing
# (Switch only affects the plugin, not per-terminal)
mycelium-switch git
```

---

## Exit Codes

The tool uses standard exit codes for scripting:

- `0`: Success (operation completed or already in desired state)
- `1`: Error (validation failed, operation failed, or invalid arguments)

**Example**:
```bash
if mycelium-switch source; then
    echo "Now in source mode"
else
    echo "Failed to switch to source mode"
fi
```

---

## Additional Resources

- **Mycelium Repository**: https://github.com/gsornsen/mycelium
- **Plugin Documentation**: See `~/git/mycelium/README.md`
- **Claude Code Plugins**: https://docs.anthropic.com/claude/docs/plugins
- **Issue Tracker**: https://github.com/gsornsen/mycelium/issues

---

## Summary

`mycelium-switch` provides a safe, convenient way to switch between development and production modes:

- **Simple commands**: `status`, `source`, `git`
- **Safe operations**: Automatic backups before changes
- **Idempotent**: Safe to run multiple times
- **Flexible**: Custom paths and URLs
- **Transparent**: Dry-run and verbose modes

**Quick Reference**:
```bash
mycelium-switch status                    # Check current mode
mycelium-switch source                    # Development mode
mycelium-switch git                       # Production mode
mycelium-switch source --dry-run          # Preview changes
```

Happy switching!
