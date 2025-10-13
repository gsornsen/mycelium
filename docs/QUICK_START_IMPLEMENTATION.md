# Quick Start: Implement Dual-Purpose Architecture in 30 Minutes

## TL;DR

Transform Mycelium into a dual-purpose repository (plugin + marketplace) in ~30 minutes of focused work.

**What you'll do:**
1. Create marketplace metadata (5 min)
2. Restructure as plugin (10 min)
3. Update README (10 min)
4. Test (5 min)

**Result:** Mycelium works as both a marketplace and a plugin.

---

## Prerequisites

```bash
cd /home/gerald/git/mycelium
git checkout -b feature/dual-purpose-structure
```

---

## Step 1: Create Marketplace Structure (5 minutes)

### 1.1 Create directories

```bash
mkdir -p .claude-plugin
mkdir -p plugins/mycelium-core/.claude-plugin
```

### 1.2 Create marketplace.json

```bash
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "mycelium",
  "version": "1.0.0",
  "description": "Distributed intelligence marketplace - 130+ expert agents, coordination infrastructure, and community plugins for Claude Code",
  "owner": {
    "name": "Gerald",
    "email": "your-email@example.com"
  },
  "metadata": {
    "repository": "https://github.com/gsornsen/mycelium",
    "homepage": "https://github.com/gsornsen/mycelium",
    "license": "MIT"
  },
  "plugins": [
    {
      "name": "mycelium-core",
      "description": "Mycelium distributed intelligence system with 130+ expert agents, dual-mode coordination (Redis/TaskQueue/Markdown), real-time pub/sub messaging, and durable workflows",
      "source": "./plugins/mycelium-core",
      "category": "orchestration",
      "version": "1.0.0",
      "author": {
        "name": "Gerald",
        "email": "your-email@example.com",
        "url": "https://github.com/gsornsen/mycelium"
      },
      "license": "MIT",
      "homepage": "https://github.com/gsornsen/mycelium",
      "keywords": [
        "agents",
        "coordination",
        "orchestration",
        "redis",
        "temporal",
        "workflow",
        "distributed",
        "intelligence",
        "mycelium"
      ]
    }
  ]
}
EOF
```

### 1.3 Update email

```bash
# Replace with your actual email
sed -i 's/your-email@example.com/your.actual@email.com/g' .claude-plugin/marketplace.json
```

---

## Step 2: Restructure as Plugin (10 minutes)

### 2.1 Move core components

```bash
# Move directories into plugin structure
mv agents plugins/mycelium-core/
mv commands plugins/mycelium-core/
mv hooks plugins/mycelium-core/
mv lib plugins/mycelium-core/

# Verify
ls -la plugins/mycelium-core/
```

### 2.2 Create plugin.json

```bash
cat > plugins/mycelium-core/.claude-plugin/plugin.json << 'EOF'
{
  "name": "mycelium-core",
  "description": "Distributed intelligence system with 130+ expert agents across 11 domains, dual-mode coordination (Redis/TaskQueue/Markdown), real-time pub/sub messaging, and durable Temporal workflows",
  "version": "1.0.0",
  "author": {
    "name": "Gerald",
    "email": "your-email@example.com",
    "url": "https://github.com/gsornsen/mycelium"
  },
  "license": "MIT",
  "homepage": "https://github.com/gsornsen/mycelium",
  "repository": "https://github.com/gsornsen/mycelium",
  "keywords": [
    "agents",
    "coordination",
    "orchestration",
    "redis",
    "temporal",
    "workflow",
    "distributed",
    "intelligence",
    "mycelium",
    "multi-agent"
  ],
  "agents": "./agents/",
  "commands": "./commands/",
  "hooks": "./hooks/hooks.json"
}
EOF
```

### 2.3 Update email

```bash
sed -i 's/your-email@example.com/your.actual@email.com/g' plugins/mycelium-core/.claude-plugin/plugin.json
```

### 2.4 Validate JSON

```bash
jq empty .claude-plugin/marketplace.json && echo "✅ marketplace.json valid"
jq empty plugins/mycelium-core/.claude-plugin/plugin.json && echo "✅ plugin.json valid"
```

---

## Step 3: Update Documentation (10 minutes)

### 3.1 Add dual-purpose section to README.md

Add this after line 7 (after the badges):

```markdown
## Dual-Purpose Repository

This repository serves two purposes:

1. **Plugin Marketplace** - Discover and install Mycelium plugins and community contributions
2. **Core Plugin** - The Mycelium distributed intelligence system (130+ agents, coordination, workflows)

### Installation: Full Marketplace Experience

```bash
# Add Mycelium marketplace
/plugin marketplace add gsornsen/mycelium

# Browse and install
/plugin
/plugin install mycelium-core@mycelium
```

### Installation: Core Plugin Only

```bash
# Direct install
claude plugin install git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core

# Or for development
git clone https://github.com/gsornsen/mycelium.git
ln -s /path/to/mycelium/plugins/mycelium-core ~/.claude/plugins/mycelium-core
```
```

### 3.2 Update Installation section (around line 323)

Replace the current "Installation" section with:

```markdown
## Installation

### Option 1: Via Marketplace (Recommended)

```bash
# Add the Mycelium marketplace
/plugin marketplace add gsornsen/mycelium

# Install core plugin
/plugin install mycelium-core@mycelium

# Verify
/infra-check
```

### Option 2: Direct Git Install

```bash
# Install directly
claude plugin install git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core

# Verify
claude plugin list | grep mycelium
```

### Option 3: Local Development

```bash
# Clone and symlink
git clone https://github.com/gsornsen/mycelium.git
cd mycelium
ln -s $(pwd)/plugins/mycelium-core ~/.claude/plugins/mycelium-core

# Test
/infra-check
```
```

---

## Step 4: Test (5 minutes)

### 4.1 Validate structure

```bash
# Check directories exist
test -d .claude-plugin && echo "✅ Marketplace directory exists"
test -d plugins/mycelium-core && echo "✅ Plugin directory exists"
test -f .claude-plugin/marketplace.json && echo "✅ Marketplace metadata exists"
test -f plugins/mycelium-core/.claude-plugin/plugin.json && echo "✅ Plugin metadata exists"

# Check moved directories
test -d plugins/mycelium-core/agents && echo "✅ Agents moved"
test -d plugins/mycelium-core/commands && echo "✅ Commands moved"
test -d plugins/mycelium-core/hooks && echo "✅ Hooks moved"
test -d plugins/mycelium-core/lib && echo "✅ Lib moved"
```

### 4.2 Test installation

```bash
# Create test symlink
ln -sf $(pwd)/plugins/mycelium-core ~/.claude/plugins/mycelium-core-test

# Verify it works
ls -la ~/.claude/plugins/mycelium-core-test

# Clean up
rm ~/.claude/plugins/mycelium-core-test
```

---

## Step 5: Commit (5 minutes)

```bash
# Add files
git add .claude-plugin/
git add plugins/
git add README.md

# Commit
git commit -m "feat: add dual-purpose marketplace + plugin structure

- Add marketplace metadata (.claude-plugin/marketplace.json)
- Restructure core as plugin (plugins/mycelium-core/)
- Update README with installation options
- Maintain all existing functionality

This enables:
- Marketplace installation via /plugin marketplace add
- Direct plugin installation
- Community plugin submissions
- Flexible user experience"

# Push
git push -u origin feature/dual-purpose-structure
```

---

## Done! What You've Accomplished

✅ Created marketplace structure
✅ Moved core into plugin format
✅ Updated documentation
✅ Validated structure
✅ Committed changes

**Your repository now:**
- Works as a plugin marketplace
- Contains the core plugin
- Supports multiple installation methods
- Ready for community contributions

---

## Next Steps (Optional)

### If you want backwards compatibility (transition period):

```bash
# Create root-level symlinks
ln -s plugins/mycelium-core/agents agents
ln -s plugins/mycelium-core/commands commands
ln -s plugins/mycelium-core/hooks hooks
ln -s plugins/mycelium-core/lib lib

# Commit
git add agents commands hooks lib
git commit -m "Add compatibility symlinks for transition period"
```

**Note:** Remove these symlinks in v2.0.0

### Create MARKETPLACE_README.md:

```bash
cat > MARKETPLACE_README.md << 'EOF'
# Mycelium Plugin Marketplace

Welcome to the Mycelium Plugin Marketplace - community-driven plugins that extend Claude Code with distributed intelligence.

## Available Plugins

### mycelium-core (Official)
130+ expert agents, dual-mode coordination, real-time messaging, durable workflows

Install: `/plugin install mycelium-core@mycelium`

## Submit a Plugin

1. Fork this repository
2. Create your plugin in `plugins/your-plugin-name/`
3. Add entry to `.claude-plugin/marketplace.json`
4. Submit PR

See `docs/marketplace/` for detailed guidelines.

## Plugin Development

Integrate with Mycelium's coordination substrate:

```javascript
import { CoordinationClient } from 'mycelium-core/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();
await client.publishEvent('my-plugin:events', { event: 'completed' });
```

## Questions?

- Issues: https://github.com/gsornsen/mycelium/issues
- Discussions: https://github.com/gsornsen/mycelium/discussions

---

**Grow the mycelial network** 🍄
EOF

git add MARKETPLACE_README.md
git commit -m "docs: add marketplace-specific README"
```

### Create marketplace documentation:

```bash
mkdir -p docs/marketplace

# Create submission guide
cat > docs/marketplace/SUBMISSION_GUIDE.md << 'EOF'
# Plugin Submission Guide

## Quick Start

1. Fork the repository
2. Create your plugin directory: `plugins/your-plugin-name/`
3. Add `.claude-plugin/plugin.json` with metadata
4. Create README.md with usage instructions
5. Add your plugin to `.claude-plugin/marketplace.json`
6. Submit a pull request

## Requirements

- [ ] Plugin includes `.claude-plugin/plugin.json`
- [ ] Plugin has comprehensive README.md
- [ ] Plugin name follows convention: `mycelium-*`
- [ ] Quality standards met (clear documentation, tested)

## Plugin Structure

```
plugins/your-plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── agents/ (optional)
├── commands/ (optional)
├── hooks/ (optional)
└── README.md (required)
```

## Review Process

1. Automated checks run on your PR
2. Maintainer reviews code and documentation
3. Feedback provided if changes needed
4. Once approved, plugin is merged and available

## Questions?

Open an issue with the `plugin-submission` label.
EOF

git add docs/marketplace/
git commit -m "docs: add plugin submission guide"
```

---

## Testing Your Changes

### Test Marketplace Installation

```bash
# This will work once pushed to GitHub
/plugin marketplace add gsornsen/mycelium
/plugin
/plugin install mycelium-core@mycelium
```

### Test Direct Installation

```bash
# This will work once pushed to GitHub
claude plugin install git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core
```

### Test Development Installation

```bash
# Works now (local)
ln -s /home/gerald/git/mycelium/plugins/mycelium-core ~/.claude/plugins/mycelium-core

# Test commands
/infra-check
/team-status
```

---

## Rollback (if needed)

If something goes wrong:

```bash
# Revert all changes
git checkout main
git branch -D feature/dual-purpose-structure

# Or just move files back
mv plugins/mycelium-core/agents/ agents/
mv plugins/mycelium-core/commands/ commands/
mv plugins/mycelium-core/hooks/ hooks/
mv plugins/mycelium-core/lib/ lib/
rm -rf .claude-plugin plugins/
```

---

## Troubleshooting

### "JSON syntax error"

```bash
# Validate JSON files
jq empty .claude-plugin/marketplace.json
jq empty plugins/mycelium-core/.claude-plugin/plugin.json

# Fix any syntax errors shown
```

### "Directory not found"

```bash
# Check structure
find . -type d -name ".claude-plugin"
ls -la plugins/mycelium-core/

# Recreate if needed
mkdir -p .claude-plugin
mkdir -p plugins/mycelium-core/.claude-plugin
```

### "Symlink broken"

```bash
# Check symlink
ls -la ~/.claude/plugins/mycelium-core

# Recreate with absolute path
rm ~/.claude/plugins/mycelium-core
ln -s /home/gerald/git/mycelium/plugins/mycelium-core ~/.claude/plugins/mycelium-core
```

---

## What's Different?

### Before (Single-Purpose)
```
mycelium/
├── agents/
├── commands/
├── hooks/
└── lib/
```

One installation method: Clone or symlink to `~/.claude/plugins/mycelium`

### After (Dual-Purpose)
```
mycelium/
├── .claude-plugin/marketplace.json
└── plugins/
    └── mycelium-core/
        ├── agents/
        ├── commands/
        ├── hooks/
        └── lib/
```

Three installation methods:
1. Via marketplace
2. Direct git install
3. Development symlink

Same functionality, more flexibility!

---

## Summary

You've successfully transformed Mycelium into a dual-purpose repository in ~30 minutes:

✅ **Marketplace functionality** - Can be added as a Claude Code marketplace
✅ **Plugin structure** - Core functionality packaged as a plugin
✅ **Multiple installation methods** - Users choose what fits their needs
✅ **Community ready** - Infrastructure for plugin submissions
✅ **Backwards compatible** - Existing functionality unchanged

**Next:** Merge to main, tag v1.1.0, announce to community!

---

## Quick Reference Commands

```bash
# Validate structure
find . -name "*.json" -path "*/.claude-plugin/*" -exec jq empty {} \;

# View structure
tree -L 3 -a .claude-plugin plugins/

# Test locally
ln -sf $(pwd)/plugins/mycelium-core ~/.claude/plugins/mycelium-core-test

# Commit everything
git add -A
git commit -m "feat: dual-purpose marketplace + plugin structure"
git push
```

---

**Time to complete:** ~30 minutes
**Difficulty:** Easy
**Risk:** Low (fully reversible)
**Impact:** High (enables ecosystem growth)

**Ready? Let's go!** 🍄
