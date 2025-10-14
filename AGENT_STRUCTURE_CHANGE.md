# Agent Directory Structure Change

## What Changed

The Mycelium agent directory structure has been flattened to ensure compatibility with Claude Code's plugin system.

### Before (Nested Structure)
```
plugins/mycelium-core/agents/
├── 01-core-development/
│   ├── api-designer.md
│   ├── backend-developer.md
│   └── ...
├── 02-language-specialists/
│   ├── python-pro.md
│   ├── typescript-pro.md
│   └── ...
└── ...
```

### After (Flat Structure)
```
plugins/mycelium-core/agents/
├── 01-core-api-designer.md
├── 01-core-backend-developer.md
├── 02-language-python-pro.md
├── 02-language-typescript-pro.md
└── ...
```

## Why This Change?

Claude Code's plugin system loads agents only from the top-level `agents/` directory and does not recursively scan subdirectories. The nested structure prevented Claude Code from discovering the 130+ Mycelium agents.

## Category Prefixes

Agents now include category prefixes in their filenames to preserve organizational structure:

- `01-core-*` - Core Development (11 agents)
- `02-language-*` - Language Specialists (24 agents)
- `03-infrastructure-*` - Infrastructure & DevOps (12 agents)
- `03-project-*` - Project Specialists (1 agent)
- `04-quality-*` - Quality & Security (12 agents)
- `05-data-*` - Data & AI (12 agents)
- `06-developer-*` - Developer Experience (10 agents)
- `07-specialized-*` - Specialized Domains (11 agents)
- `08-business-*` - Business & Product (11 agents)
- `09-meta-*` - Meta Orchestration (8 agents)
- `10-research-*` - Research & Analysis (6 agents)
- `11-claude-*` - Claude Code Integration (1 agent)

**Total: 119 agents**

## Backup

The original nested structure has been preserved at:
```
plugins/mycelium-core/agents.backup/
```

## Reverting

To revert to the nested structure:
```bash
cd /home/gerald/git/mycelium/plugins/mycelium-core
rm -rf agents/
mv agents.backup/ agents/
```

**Note:** Reverting will break Claude Code agent loading again.

## Applying to Fresh Installs

The flattening script is available at:
```bash
/home/gerald/git/mycelium/scripts/flatten-agents.sh
```

Run it if you clone the repository with the nested structure.

## Next Steps

After this change, you **must restart Claude Code** for it to discover the agents:

1. Exit Claude Code completely
2. Restart Claude Code
3. Run `/agents` to verify all Mycelium agents are loaded
4. Agents should appear under "Plugin agents" in the agents menu

## Agent Discovery

You can verify agent discovery by:
1. Opening Claude Code agents menu (type `/agents`)
2. Looking for agents with the `mycelium-core:` prefix
3. All 119 agents should be listed under "Plugin agents"
