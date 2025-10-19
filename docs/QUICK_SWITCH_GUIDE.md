# Quick Switch Guide - TL;DR

**Goal**: Switch between development (source) and production (git) versions of Mycelium plugin.

## Commands (3 total)

```bash
# Check current mode
mycelium-switch status

# Development mode (symlink to ~/git/mycelium)
mycelium-switch source

# Production mode (clone from GitHub)
mycelium-switch git
```

## When to Use Each Mode

| Mode | When | What Happens |
|------|------|--------------|
| **source** | Developing features, debugging, testing local changes | Creates symlink to `~/git/mycelium/plugins/mycelium-core` |
| **git** | Normal usage, stable version, sharing with team | Clones from `https://github.com/gsornsen/mycelium` |

## Safety Features

- Automatic backups before switching
- Dry-run mode: `--dry-run`
- Idempotent (safe to run multiple times)
- State tracking in `~/.claude/plugins/.mycelium-mode`

## Common Workflows

### Development Session
```bash
mycelium-switch source   # Start
# ... edit code in ~/git/mycelium ...
# ... test in Claude Code ...
mycelium-switch git      # End (back to stable)
```

### Test Before Commit
```bash
mycelium-switch source --dry-run  # Preview
mycelium-switch source            # Apply
# ... test changes ...
cd ~/git/mycelium && git commit   # Commit if satisfied
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Local source not found" | `cd ~/git && git clone https://github.com/gsornsen/mycelium` |
| "Cannot access git repository" | Check internet connection: `ping github.com` |
| "Plugin not appearing" | Restart Claude Code completely |
| Changes not reflecting | Verify symlink: `ls -la ~/.claude/plugins/mycelium-core` |

## Advanced Options

```bash
# Custom source path
mycelium-switch source --source-path /path/to/mycelium

# Custom git URL
mycelium-switch git https://github.com/username/fork

# Preview changes
mycelium-switch source --dry-run

# Verbose output
mycelium-switch source --verbose
```

## Files & Locations

- **Active plugin**: `~/.claude/plugins/mycelium-core`
- **State file**: `~/.claude/plugins/.mycelium-mode`
- **Backups**: `~/.claude/plugins/.backups/`
- **Script**: `~/git/mycelium/bin/mycelium-switch`

## Full Documentation

See [PLUGIN_VERSION_SWITCHING.md](PLUGIN_VERSION_SWITCHING.md) for comprehensive guide.

---

**TL;DR**: Run `mycelium-switch source` for development, `mycelium-switch git` for production. That's it!
