# Mycelium Module Documentation

This directory contains comprehensive documentation modules for the Mycelium distributed intelligence system.

## Purpose

These modules provide in-depth documentation for specific Mycelium features and subsystems. They are designed to be loaded on-demand by agents and developers who need detailed information about specific components.

## Available Modules

1. **[onboarding.md](./modules/onboarding.md)** - Installation and setup guide
2. **[coordination.md](./modules/coordination.md)** - Dual-mode coordination system
3. **[deployment.md](./modules/deployment.md)** - Docker & Kubernetes deployment
4. **[agents.md](./modules/agents.md)** - Agent catalog and creation guide
5. **[analytics.md](./modules/analytics.md)** - Performance analytics and telemetry

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
2. **Quick Start** - Getting started quickly
3. **Architecture** - Technical design and components
4. **API Reference** - Detailed API documentation
5. **Examples** - Code examples and usage patterns
6. **Troubleshooting** - Common issues and solutions
7. **References** - Related documentation and resources

## Contributing

When adding new modules:

1. Follow the existing structure and format
2. Include comprehensive examples
3. Add troubleshooting sections
4. Update this README with the new module
5. Cross-reference related modules

## Documentation Standards

- Use clear, concise language
- Include code examples with expected output
- Add diagrams for complex concepts
- Provide troubleshooting guidance
- Keep examples up-to-date with code changes

---

**Last Updated**: 2025-10-19
**Maintainers**: @documentation-engineer, @python-pro
