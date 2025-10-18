# Contributing to Mycelium

Thank you for your interest in contributing to Mycelium! This guide will help you get started.

## Areas for Contribution

### 1. New Agents (Spores)

Add specialized agents for new domains. See [.mycelium/modules/agents.md](.mycelium/modules/agents.md) for detailed agent architecture and patterns.

```markdown
---
name: your-specialist
description: Expert in specific domain. Invoke when working on X, Y, or Z.
tools: Read, Write, Grep, Bash(allowed-patterns:*)
---

You are a senior specialist in...

## Communication Protocol

Report progress to multi-agent-coordinator:
```json
{
  "agent": "your-specialist",
  "status": "completed",
  "metrics": {...}
}
```
```

**Guidelines**:
- Clear invocation criteria in description
- Minimal tool access (security)
- Well-defined communication protocol
- Integration with orchestrator agents

**Location**: `agents/XX-category/your-specialist.md`

### 2. Slash Commands

Add productivity commands:

```markdown
---
allowed-tools: Bash(*), Read
description: Your command description
argument-hint: [optional-args]
---

# Your Command

## Your task
1. Do X
2. Do Y
3. Report Z
```

**Guidelines**:
- Project-agnostic where possible
- Clear argument handling
- Dual-mode coordination support (see [.mycelium/modules/coordination.md](.mycelium/modules/coordination.md))
- Error handling and feedback

**Location**: `commands/your-command.md`

### 3. Event Hooks

Add automation hooks:

```json
{
  "description": "Your hook collection",
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

**Guidelines**:
- Fast execution (<1s preferred)
- Proper error handling
- Exit codes (0=success, 1=error, 2=block)
- Security validation

**Location**: `hooks/your-hook.sh` + update `hooks/hooks.json`

### 4. Documentation & Examples

Improve documentation:

- Coordination patterns in `.mycelium/modules/`
- Configuration examples in `docs/examples/`
- Usage guides and tutorials
- Architecture diagrams

### 5. Library Enhancements

Enhance coordination libraries (see [.mycelium/modules/coordination.md](.mycelium/modules/coordination.md) for architecture):

- `lib/coordination.js` - Coordination abstractions
- `lib/pubsub.js` - Pub/sub messaging
- `lib/workflow.js` - Workflow orchestration

**Guidelines**:
- Maintain dual-mode support
- Add tests for all modes
- Document API changes
- Backward compatibility

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/mycelium.git
cd mycelium
```

### 2. Install Development Dependencies

```bash
# Node.js dependencies (if adding JS code)
npm install

# Setup coordination infrastructure
docker run -d -p 6379:6379 redis:latest
```

For detailed setup instructions, see [.mycelium/modules/onboarding.md](.mycelium/modules/onboarding.md).

### 3. Create Development Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Changes

Follow the guidelines for your contribution type above.

### 5. Test Changes

```bash
# Test slash commands
/your-command

# Test agents
claude --agents agents/XX-category/your-agent.md -p "Test prompt"

# Test library
node tests/integration/test-coordination.js

# Test hooks
bash hooks/your-hook.sh
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 7. Create Pull Request

Open a PR with:
- Clear description of changes
- Test results
- Documentation updates
- Breaking changes (if any)

## Code Style

### JavaScript

```javascript
// Use ES6+ features
import { createMyceliumClient } from './lib/index.js';

// Clear function names
async function storeAgentStatus(agent, status) {
  // Implementation
}

// Document public APIs
/**
 * Store agent status in coordination layer
 *
 * @param {string} agent - Agent identifier
 * @param {object} status - Status object
 * @returns {Promise<void>}
 */
async function storeAgentStatus(agent, status) {
  // Implementation
}
```

### Bash

```bash
#!/bin/bash
# Use strict mode
set -euo pipefail

# Clear variable names
COORDINATION_MODE="redis"

# Functions for reusability
check_redis() {
    redis-cli ping &> /dev/null
}

# Error handling
if ! check_redis; then
    echo "Error: Redis not available" >&2
    exit 1
fi
```

### Markdown (Agents/Commands)

```markdown
---
# YAML frontmatter with required fields
name: agent-name
description: Clear, specific invocation criteria
tools: Minimal required tools
---

# Clear structure
## Section headers
- Bulleted lists
- **Bold** for emphasis
- \`code\` for commands/paths
```

## Testing Guidelines

### Test All Coordination Modes

For coordination mode details, see [.mycelium/modules/coordination.md](.mycelium/modules/coordination.md#dual-mode-coordination).

```javascript
// Test should work in all modes
for (const mode of ['redis', 'taskqueue', 'markdown']) {
  // Mock mode
  // Test functionality
  // Assert results
}
```

### Integration Tests

```bash
# Run full integration test suite
node tests/integration/test-coordination.js

# Should pass in all modes
```

### Manual Testing

1. Test with Redis available
2. Test with TaskQueue only
3. Test in markdown fallback mode
4. Test error handling

## Documentation Standards

### Agent Documentation

Every agent should have (see [.mycelium/modules/agents.md](.mycelium/modules/agents.md#creating-custom-agents)):
- Clear description with invocation criteria
- Tool access justification
- Communication protocol
- Integration patterns
- Example usage

### Command Documentation

Every command should have:
- Clear usage instructions
- Argument descriptions
- Configuration examples
- Error handling notes
- Integration points

### Library Documentation

Every public function should have:
- JSDoc comments
- Parameter descriptions
- Return value documentation
- Usage examples
- Error conditions

## Pull Request Process

1. **Create PR** with clear title and description
2. **Fill PR template** (description, testing, breaking changes)
3. **Address review feedback** promptly
4. **Update documentation** if needed
5. **Squash commits** if requested
6. **Wait for approval** from maintainers

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Release Process

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.x.x`
4. Push tag: `git push --tags`
5. Create GitHub release

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers
- Share knowledge and patterns
- Document learnings

## Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Credited in release notes
- Mentioned in documentation (where applicable)

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Join community channels (Discord/Slack - TBD)
- Read the documentation at [.mycelium/modules/](.mycelium/modules/)

## Additional Resources

- **[Onboarding Guide](.mycelium/modules/onboarding.md)** - Complete setup and installation
- **[Agents Guide](.mycelium/modules/agents.md)** - Agent architecture and development
- **[Coordination Guide](.mycelium/modules/coordination.md)** - Dual-mode patterns and API
- **[README.md](README.md)** - Project overview and quick start

## License

By contributing to Mycelium, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping grow the Mycelial network!** 🍄
