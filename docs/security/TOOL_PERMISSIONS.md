# Tool Permissions Security Model

## Overview

Mycelium's tool permission system provides visibility into the capabilities granted to each agent, helping you
understand and manage security risks in your multi-agent development environment.

## What Are Tool Permissions?

Tool permissions define what actions an agent can perform. Each agent in Mycelium declares its required tools in its
frontmatter:

```yaml
---
name: backend-engineer
description: Full-stack backend engineer
tools: Read, Write, MultiEdit, Bash, Docker, database
---
```

These tools determine the agent's access level to:

- File system operations (read, write, edit)
- Shell command execution
- Container management
- Database access
- Other system resources

## Risk Levels

Mycelium classifies tool permissions into three risk levels:

### High Risk

**Unrestricted access to critical system resources**

Tools that pose significant security risks if misused:

- `Bash` or `Bash(*)` - Unrestricted shell access

  - Can execute any command on the system
  - Full access to all shell utilities
  - No restrictions on what can be run

- `Write` or `Write(*)` - Unrestricted file write

  - Can modify or create any file
  - No path restrictions
  - Potential for system file corruption

- `Edit` or `Edit(*)` - Unrestricted file edit

  - Can modify any existing file
  - No path restrictions
  - Potential for code injection

- `MultiEdit` or `MultiEdit(*)` - Unrestricted multi-file edit

  - Can modify multiple files simultaneously
  - No path restrictions
  - Amplified risk of widespread changes

**Why High Risk?** These tools can:

- Modify critical system files
- Execute malicious commands
- Delete important data
- Compromise system security
- Access sensitive information

### Medium Risk

**Limited system access or specialized tools**

Tools with controlled access or specific use cases:

- `Read` or `Read(*)` - Unrestricted file read

  - Can read any file including secrets
  - Information disclosure risk
  - Less dangerous than write access

- `Docker` - Container management

  - Can start/stop containers
  - Access to container runtime
  - Potential for resource abuse

- `kubernetes` - Kubernetes cluster access

  - Can manage cluster resources
  - Access to orchestration layer
  - Potential for service disruption

**Why Medium Risk?** These tools can:

- Access sensitive information
- Consume system resources
- Disrupt running services
- But cannot directly modify system files

### Low Risk

**Restricted or specialized tools**

Safe tools with limited scope:

- Restricted shell patterns: `Bash(git:*)`, `Bash(npm:*)`

  - Limited to specific command namespaces
  - Reduced attack surface
  - Controlled functionality

- Specialized tools: `vite`, `webpack`, `pytest`, `redis`

  - Purpose-built utilities
  - Limited to specific functions
  - Well-defined boundaries

**Why Low Risk?** These tools:

- Have restricted access patterns
- Cannot modify arbitrary files
- Limited to specific use cases
- Well-controlled scope

## Permission Patterns

### Unrestricted Patterns (High Risk)

```yaml
# Unrestricted - Full access
tools: Bash, Write, Edit, MultiEdit, Read

# Explicit wildcard - Also unrestricted
tools: Bash(*), Write(*), Edit(*), Read(*)
```

### Restricted Patterns (Lower Risk)

```yaml
# Restricted to git commands only
tools: Bash(git:*)

# Restricted to npm commands only
tools: Bash(npm:*)

# Restricted to specific paths (future feature)
tools: Write(/path/to/dir/*), Read(/project/src/*)
```

### Best Practice Patterns

```yaml
# Minimal permissions - Safest approach
tools: Read, vite, jest, typescript

# Command restrictions - Safer than full shell
tools: Read, Write, MultiEdit, Bash(git:*), Bash(npm:*)

# Specific tools only - No shell access
tools: Read, Write, Docker, pytest, mypy
```

## Security Best Practices

### For Agent Authors

1. **Principle of Least Privilege**

   - Request only necessary tools
   - Use restricted patterns when possible
   - Avoid unrestricted shell access unless required

1. **Use Specific Tools Over Shell**

   ```yaml
   # Prefer this:
   tools: Read, Write, pytest, mypy, black

   # Over this:
   tools: Bash
   ```

1. **Document Tool Requirements**

   - Explain why each tool is needed
   - Justify high-risk permissions
   - Provide alternative approaches

1. **Restrict Shell Access**

   ```yaml
   # Instead of unrestricted:
   tools: Bash

   # Use restricted namespaces:
   tools: Bash(git:*), Bash(npm:*), Bash(docker:*)
   ```

### For Platform Operators

1. **Regular Audits**

   ```bash
   # Check all agent permissions
   mycelium agent permissions

   # Focus on high-risk agents
   mycelium agent permissions --high-risk
   ```

1. **Risk Assessment**

   - Review high-risk agents regularly
   - Verify tool requirements are justified
   - Monitor for permission creep

1. **Access Control**

   - Limit which agents can be activated
   - Implement approval workflows for high-risk agents
   - Maintain audit logs of agent executions

1. **Defense in Depth**

   - Run agents in containers
   - Use file system isolation
   - Implement resource limits
   - Monitor agent behavior

## Using the Permissions CLI

### Check All Agents

```bash
# View permissions for all agents
mycelium agent permissions

# Output:
# Agent Permissions Summary
# ┌──────────────────────┬────────┬────────────┐
# │ Agent                │ Risk   │ Tools      │
# ├──────────────────────┼────────┼────────────┤
# │ backend-engineer     │ HIGH   │ 6 tools    │
# │ frontend-developer   │ MEDIUM │ 8 tools    │
# │ data-scientist       │ LOW    │ 6 tools    │
# └──────────────────────┴────────┴────────────┘
```

### Check Specific Agent

```bash
# View permissions for a specific agent
mycelium agent permissions backend-engineer

# Output shows:
# - Agent name and description
# - Overall risk level
# - Detailed tool breakdown with risk levels
# - Descriptions of each permission
```

### Find High-Risk Agents

```bash
# List only high-risk agents
mycelium agent permissions --high-risk

# Shows agents with unrestricted access
# Helps prioritize security reviews
```

### JSON Output for Automation

```bash
# Export permissions as JSON
mycelium agent permissions --json > permissions.json

# Use in CI/CD pipelines
# Integrate with security scanning tools
# Track permission changes over time
```

## Example Risk Assessments

### High-Risk Agent Example

```yaml
---
name: infrastructure-admin
tools: Bash, Write, Docker, kubernetes
---
```

**Risk Assessment:**

- **Overall Risk:** HIGH
- **Concerns:**
  - Unrestricted shell access (Bash)
  - Unrestricted file write (Write)
  - Container management (Docker)
  - Cluster access (kubernetes)
- **Recommendation:**
  - Restrict to specific commands: `Bash(kubectl:*), Bash(docker:*)`
  - Limit file write to config directories
  - Require approval for execution

### Medium-Risk Agent Example

```yaml
---
name: database-engineer
tools: Read, Write, Docker, postgresql, redis
---
```

**Risk Assessment:**

- **Overall Risk:** MEDIUM
- **Concerns:**
  - File write access (Write)
  - Container management (Docker)
- **Strengths:**
  - No shell access
  - Specific database tools
- **Recommendation:**
  - Consider restricting Write to schema directories
  - Monitor container creation

### Low-Risk Agent Example

```yaml
---
name: typescript-developer
tools: Read, Write, typescript, vite, jest, eslint
---
```

**Risk Assessment:**

- **Overall Risk:** LOW
- **Concerns:**
  - File write access (limited to code)
- **Strengths:**
  - No shell access
  - Specific development tools only
  - Clear, bounded purpose
- **Recommendation:**
  - Safe for general use
  - Consider restricting Write to src/ directories

## Implementation Details

### Permission Detection

Mycelium analyzes agent frontmatter to extract tool declarations:

```python
# Parses YAML frontmatter
---
tools: Read, Write, Bash, Docker
---

# Detects patterns:
# - Unrestricted: Bash, Write
# - Restricted: Bash(git:*)
# - Specific: Docker, redis
```

### Risk Calculation

Overall agent risk is determined by the highest-risk tool:

1. Scan all tools in agent definition
1. Match against known dangerous patterns
1. Assign risk level to each tool
1. Agent risk = highest tool risk

### Regular Expression Patterns

```python
# High risk patterns
r"^Bash$"           # Matches: Bash
r"^Bash\(\*\)$"     # Matches: Bash(*)
r"^Write$"          # Matches: Write
r"^Write\(\*\)$"    # Matches: Write(*)

# Low risk patterns
r"^Bash\([^*]+\)$"  # Matches: Bash(git:*), Bash(npm:*)
```

## Future Enhancements

### Planned Features

1. **Path Restrictions**

   ```yaml
   # Future syntax for path-based permissions
   tools: Write(/project/src/*), Read(/project/**/*.py)
   ```

1. **Time-Based Permissions**

   ```yaml
   # Temporary elevated access
   tools: Bash(*, expires=2024-12-31)
   ```

1. **Approval Workflows**

   - Require approval for high-risk operations
   - Multi-factor authentication for critical agents
   - Audit trail for all executions

1. **Runtime Monitoring**

   - Track actual tool usage vs declared
   - Alert on unexpected behavior
   - Automatic containment of violations

1. **Permission Inheritance**

   ```yaml
   # Base agent permissions
   extends: base-developer
   tools: +pytest  # Adds to base tools
   ```

## FAQ

### Q: Why does my agent need Bash access?

**A:** Bash provides unrestricted shell access, which is powerful but risky. Consider:

- Do you need full shell or just specific commands?
- Can you use specialized tools instead? (git, npm, docker tools)
- Can you restrict to command namespaces? `Bash(git:*)`

### Q: Is Read access safe?

**A:** Mostly, but not entirely:

- **Safe:** Reading code, documentation, configs
- **Risk:** Can read secrets, .env files, API keys
- **Mitigation:** Use `.gitignore` patterns, secret management

### Q: How do I restrict file access?

**A:** Currently:

- Use specialized tools that limit scope
- Avoid unrestricted `Write(*)` and `Edit(*)`
- Future: Path-based restrictions

### Q: What if I need temporary elevated access?

**A:** Best practices:

- Create separate specialized agent
- Document the requirement clearly
- Use for specific task only
- Remove after completion

### Q: How often should I audit permissions?

**A:** Recommended schedule:

- **Weekly:** Quick review of high-risk agents
- **Monthly:** Full permission audit
- **On change:** Review any new/modified agents
- **Quarterly:** Security assessment

## Additional Resources

- [Mycelium Security Overview](../SECURITY.md)
- [Agent Development Guide](../../CONTRIBUTING.md)
- [Tool Reference](../tools/TOOLS.md)
- [Security Best Practices](./SECURITY_BEST_PRACTICES.md)

## Report Security Issues

If you discover a security vulnerability in an agent's tool permissions:

1. **DO NOT** open a public issue
1. Email security@mycelium.dev with details
1. Include agent name and specific concern
1. We'll respond within 48 hours

## Changelog

- **2024-11-29:** Initial permissions model and documentation
- Tool risk classification implemented
- CLI commands for permission inspection
- Automated detection of dangerous patterns
