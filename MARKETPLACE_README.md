# Mycelium Plugin Marketplace

Welcome to the Mycelium Plugin Marketplace - community-driven plugins that extend Claude Code with distributed
intelligence.

## Overview

Mycelium is both a **plugin marketplace** and a **core coordination plugin**. This marketplace enables the community to
discover, share, and contribute plugins that leverage Mycelium's coordination substrate.

## Available Plugins

### mycelium-core (Official)

**The foundation of the Mycelial network**

130+ expert agents across 11 domains, dual-mode coordination (Redis/TaskQueue/Markdown), real-time pub/sub messaging,
and durable Temporal workflows.

**Features**:

- Meta-orchestration agents for multi-agent coordination
- Specialized domain experts (AI/ML, DevOps, Security, Data, etc.)
- Infrastructure health monitoring (`/infra-check`)
- Team coordination status (`/team-status`)
- CI/CD pipeline monitoring (`/pipeline-status`)
- Event-driven hooks for automation
- Dual-mode coordination library (JavaScript)

**Install**:

```bash
/plugin install mycelium-core@mycelium
```

**Documentation**: See [README.md](README.md) for overview and
[.mycelium/modules/onboarding.md](.mycelium/modules/onboarding.md) for detailed setup.

______________________________________________________________________

## Submit Your Plugin

Want to contribute a plugin to the Mycelium ecosystem? We welcome submissions!

### Quick Start

1. **Fork this repository**

   ```bash
   git clone https://github.com/gsornsen/mycelium.git
   cd mycelium
   git checkout -b plugin/your-plugin-name
   ```

1. **Create your plugin**

   ```bash
   mkdir -p plugins/mycelium-your-plugin
   cd plugins/mycelium-your-plugin
   ```

1. **Add plugin metadata**

   ```bash
   mkdir .claude-plugin
   cat > .claude-plugin/plugin.json << 'EOF'
   {
     "name": "mycelium-your-plugin",
     "description": "Your plugin description",
     "version": "1.0.0",
     "author": {
       "name": "Your Name",
       "email": "your@email.com",
       "url": "https://github.com/yourusername"
     },
     "license": "MIT",
     "homepage": "https://github.com/gsornsen/mycelium",
     "repository": "https://github.com/gsornsen/mycelium",
     "keywords": ["mycelium", "your", "keywords"]
   }
   EOF
   ```

1. **Add your plugin to marketplace**

   Edit `.claude-plugin/marketplace.json` and add your plugin entry:

   ```json
   {
     "name": "mycelium-your-plugin",
     "description": "Your plugin description",
     "source": "./plugins/mycelium-your-plugin",
     "category": "automation|orchestration|analysis|utilities",
     "version": "1.0.0",
     "author": {
       "name": "Your Name",
       "email": "your@email.com",
       "url": "https://github.com/yourusername"
     },
     "license": "MIT",
     "homepage": "https://github.com/gsornsen/mycelium",
     "keywords": ["mycelium", "your", "keywords"]
   }
   ```

1. **Create comprehensive documentation**

   ```bash
   cat > README.md << 'EOF'
   # Your Plugin Name

   Clear description of what your plugin does.

   ## Installation
   `/plugin install mycelium-your-plugin@mycelium`

   ## Usage
   Examples and documentation...
   EOF
   ```

1. **Submit pull request**

   ```bash
   git add .
   git commit -m "feat: add mycelium-your-plugin"
   git push origin plugin/your-plugin-name
   ```

   Then open a PR on GitHub!

### Plugin Requirements

- [ ] Clear, descriptive name starting with `mycelium-`
- [ ] Complete `.claude-plugin/plugin.json` with metadata
- [ ] Comprehensive README.md with usage examples
- [ ] Proper versioning (SemVer)
- [ ] MIT or compatible license
- [ ] Quality documentation
- [ ] Tested functionality

### Plugin Categories

Choose the appropriate category for your plugin:

- **orchestration** - Workflow coordination, task management
- **automation** - Event-driven automation, hooks, triggers
- **analysis** - Data analysis, metrics, reporting
- **utilities** - Helper tools, productivity enhancements
- **integration** - External service integrations
- **domain-specific** - Specialized domain expertise

### Integration with Mycelium Core

Your plugin can leverage Mycelium's coordination substrate. See
[.mycelium/modules/coordination.md](.mycelium/modules/coordination.md) for detailed API documentation.

```javascript
import { CoordinationClient } from 'mycelium-core/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();

// Store plugin status
await client.storeAgentStatus('your-plugin:worker', {
  status: 'busy',
  task: 'processing'
});

// Publish events
await client.publishEvent('your-plugin:events', {
  event: 'completed',
  data: {...}
});

// Subscribe to events from other plugins
await client.subscribeEvents('mycelium:coordination', (event) => {
  console.log('Coordination event:', event);
});
```

### Review Process

1. **Automated Checks** - CI runs validation on your PR
1. **Code Review** - Maintainer reviews plugin code and docs
1. **Testing** - Plugin functionality is tested
1. **Feedback** - Any required changes communicated
1. **Approval** - Once approved, plugin is merged and published

### Best Practices

1. **Clear Purpose** - Plugin should have focused, well-defined functionality
1. **Documentation** - Comprehensive docs with examples
1. **Error Handling** - Graceful error handling with helpful messages
1. **Coordination-Aware** - Leverage dual-mode coordination patterns (see
   [.mycelium/modules/coordination.md](.mycelium/modules/coordination.md))
1. **Performance** - Efficient resource usage
1. **Security** - Validate inputs, handle credentials securely
1. **Testing** - Include tests or testing documentation

______________________________________________________________________

## Plugin Development Guide

### Plugin Structure

```
plugins/mycelium-your-plugin/
├── .claude-plugin/
│   └── plugin.json           # Required metadata
├── agents/                    # Optional: Custom agents
│   └── specialist.md
├── commands/                  # Optional: Slash commands
│   └── your-command.md
├── hooks/                     # Optional: Event hooks
│   ├── hooks.json
│   └── your-hook.sh
├── lib/                       # Optional: JavaScript library
│   └── index.js
├── tests/                     # Optional but recommended
│   └── test-plugin.js
├── README.md                  # Required: Documentation
└── LICENSE                    # Required: MIT or compatible
```

### Minimal Plugin Example

**plugin.json**:

```json
{
  "name": "mycelium-hello",
  "description": "Simple hello world plugin",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "commands": "./commands/"
}
```

**commands/hello.md**:

```markdown
---
description: Say hello with Mycelium coordination
---

# Hello Mycelium

Demonstrates plugin integration with coordination substrate.

## Your task

Use the coordination library to store a greeting and publish an event.
```

### Advanced Plugin Example

See `plugins/mycelium-core/` for a complete example of:

- Multiple agent categories (see [.mycelium/modules/agents.md](.mycelium/modules/agents.md))
- Slash commands with arguments
- Event hooks with validation
- JavaScript coordination library
- Comprehensive documentation

______________________________________________________________________

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers with plugin development
- Share knowledge and patterns
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

## Questions?

- **Issues**: https://github.com/gsornsen/mycelium/issues (tag with `plugin-submission`)
- **Discussions**: https://github.com/gsornsen/mycelium/discussions
- **Documentation**: See [CONTRIBUTING.md](CONTRIBUTING.md) and [.mycelium/modules/](.mycelium/modules/)

## License

All plugins submitted to this marketplace must use MIT or a compatible open-source license.

______________________________________________________________________

**Grow the mycelial network** - one plugin at a time! 🍄
