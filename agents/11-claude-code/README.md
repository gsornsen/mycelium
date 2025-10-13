# Claude Code Development Agents

This directory contains specialized subagents for working with Claude Code extensibility features.

## Available Agents

### subagent-developer.md

**Expert in creating and enhancing Claude Code subagents, plugins, hooks, slash commands, output styles, and plugin marketplaces.**

**Specializations:**
- Subagent creation and auditing
- Plugin development and distribution
- Slash command design
- Hook system implementation
- Output style customization
- Plugin marketplace creation
- Cross-agent coordination

**When to invoke:**
- Creating new Claude Code subagents
- Auditing/improving existing subagents
- Designing plugins with commands, agents, and hooks
- Creating slash commands for workflows
- Implementing event-driven hooks
- Setting up plugin marketplaces
- Designing agent collaboration patterns

**Tools:** Read, Write, MultiEdit, Bash, Glob, Grep, WebFetch

## Usage Examples

### Create a New Subagent
```bash
claude -p "Create a code-reviewer subagent that focuses on security and performance"
```

### Audit Existing Subagent
```bash
claude -p "Audit the mcp-developer subagent and suggest improvements"
```

### Create a Plugin
```bash
claude -p "Create a git-workflow plugin with commit, push, and PR commands"
```

### Design Hooks
```bash
claude -p "Create a PreToolUse hook that validates Python files with ruff before editing"
```

### Create Slash Command
```bash
claude -p "Create a /test-all command that runs pytest and analyzes results"
```

## Integration with Project

The claude-code-developer agent integrates with:

**Meta-Orchestration Team:**
- multi-agent-coordinator: Agent team composition
- workflow-orchestrator: Pipeline integration
- performance-monitor: Metrics tracking
- error-coordinator: Issue escalation

**Development Team:**
- python-pro: Python-based hook development
- devops-engineer: CI/CD integration
- documentation-engineer: Plugin documentation
- cli-developer: Command design

## Documentation References

- [Subagents](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- [Marketplaces](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [Slash Commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Hooks](https://docs.claude.com/en/docs/claude-code/hooks)
- [Hooks Guide](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [Output Styles](https://docs.claude.com/en/docs/claude-code/output-styles)

## Quick Reference

**File Locations:**
- User subagents: `~/.claude/agents/`
- Project subagents: `.claude/agents/`
- User commands: `~/.claude/commands/`
- Project commands: `.claude/commands/`
- User settings: `~/.claude/settings.json`
- Output styles: `~/.claude/output-styles/`
- Plugins: `~/.claude/plugins/`

**Common Tool Patterns:**
- Research: `Read, Grep, Glob, WebFetch`
- Documentation: `Read, Write, Grep`
- Code changes: `Read, Edit, MultiEdit, Grep`
- Testing: `Bash(npm test:*), Bash(pytest:*)`
- Git ops: `Bash(git status:*), Bash(git diff:*), Bash(git log:*)`

## Testing

To test the subagent after installation:

```bash
# Basic invocation test
claude -p "Use claude-code-developer to explain subagent structure"

# Create a simple subagent
claude -p "Create a simple test-runner subagent"

# Audit an existing agent
claude -p "Review and suggest improvements for any existing subagent"
```

## Contributing

To enhance this agent:

1. Read the subagent file
2. Identify improvement opportunities
3. Test changes thoroughly
4. Update documentation
5. Share learnings with team

---

**Last Updated:** 2025-10-12
**Maintainer:** Claude Code Development Team
