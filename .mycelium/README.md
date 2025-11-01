# Mycelium Module Documentation

This directory contains comprehensive documentation modules for the Mycelium distributed intelligence system.

## Purpose

These modules provide in-depth documentation for specific Mycelium features and subsystems. They are designed to be
loaded on-demand by agents and developers who need detailed information about specific components.

## Available Modules

1. **[onboarding.md](./modules/onboarding.md)** - Installation and setup guide
1. **[coordination.md](./modules/coordination.md)** - Dual-mode coordination system
1. **[deployment.md](./modules/deployment.md)** - Docker & Kubernetes deployment
1. **[agents.md](./modules/agents.md)** - Agent catalog and creation guide
1. **[analytics.md](./modules/analytics.md)** - Performance analytics and telemetry

## Additional Resources

- **[PRIVACY.md](./PRIVACY.md)** - Privacy policy for performance analytics

## Usage

### For Developers

Load modules on-demand when working on specific features:

```bash
# Working on agent discovery performance?
cat .mycelium/modules/analytics.md

# Setting up coordination infrastructure?
cat .mycelium/modules/coordination.md

# Creating new agents?
cat .mycelium/modules/agents.md
```

### For Claude Code Agents

Agents can reference these modules in their prompts:

```markdown
For detailed analytics architecture, see .mycelium/modules/analytics.md
For coordination patterns, see .mycelium/modules/coordination.md
```

## Module Structure

Each module follows a consistent structure:

1. **Overview** - High-level summary and key features
1. **Quick Start** - Getting started quickly
1. **Architecture** - Technical design and components
1. **API Reference** - Detailed API documentation
1. **Examples** - Code examples and usage patterns
1. **Troubleshooting** - Common issues and solutions
1. **References** - Related documentation and resources

## Contributing

When adding new modules:

1. Follow the existing structure and format
1. Include comprehensive examples
1. Add troubleshooting sections
1. Update this README with the new module
1. Cross-reference related modules

## Documentation Standards

- Use clear, concise language
- Include code examples with expected output
- Add diagrams for complex concepts
- Provide troubleshooting guidance
- Keep examples up-to-date with code changes

______________________________________________________________________

**Last Updated**: 2025-10-19 **Maintainers**: @documentation-engineer, @python-pro
