# Mycelium Onboarding Guide

Complete installation, setup, and first-time user guide for the Mycelium distributed intelligence system.

## Table of Contents

1. [Installation](#installation)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [First Steps](#first-steps)
6. [Troubleshooting](#troubleshooting)

## Installation

### Option 1: Plugin Marketplace (Recommended)

```bash
# Add Mycelium marketplace to Claude Code
/plugin marketplace add gsornsen/mycelium

# Browse available plugins
/plugin

# Install the core plugin
/plugin install mycelium-core@mycelium

# IMPORTANT: Restart Claude Code after installation
# Exit Claude Code completely and restart to load all 130+ agents
```

### Option 2: Direct from Git

```bash
# Clone repository
git clone https://github.com/gsornsen/mycelium.git ~/.claude/plugins/mycelium

# Or install as Claude Code plugin
claude plugin install git+https://github.com/gsornsen/mycelium.git
```

### Option 3: Local Development

```bash
# Symlink local development version
ln -s /home/gerald/git/mycelium ~/.claude/plugins/mycelium

# Verify installation
claude plugin list | grep mycelium
```

### Option 4: Direct Copy

```bash
# Copy to Claude Code plugins directory
cp -r /path/to/mycelium ~/.claude/plugins/mycelium
```

## Infrastructure Setup

Mycelium supports three coordination modes that auto-detect based on available infrastructure.

### Redis Mode (Recommended for Production)

**Best for**: Real-time collaboration, high message throughput, production deployments

**Performance**:
- Message throughput: 234K messages/min
- Latency: 0.8ms avg
- Scales to 100+ agents

**Setup**:

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name redis redis:latest

# Or Valkey (Redis fork, drop-in replacement)
docker run -d -p 6379:6379 --name valkey valkey/valkey:latest

# Or using system package manager
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis

# Verify connection
redis-cli ping  # Should return PONG
```

**Configuration**:

Set Redis connection details in environment or config:

```bash
# Environment variables
export REDIS_URL="redis://localhost:6379"
export REDIS_PASSWORD=""  # If password protected
export REDIS_DB="0"

# Or in .mycelium/config.json
{
  "coordination": {
    "mode": "redis",
    "redis": {
      "url": "redis://localhost:6379",
      "password": null,
      "db": 0,
      "timeout": 5
    }
  }
}
```

### TaskQueue MCP Mode (Good for Task-Centric Workflows)

**Best for**: Task-oriented workflows, MCP ecosystem integration, structured coordination

**Performance**:
- Task creation: 50/sec
- Task polling: 1Hz default
- Scales to 50+ agents

**Setup**:

```bash
# Install via npm
npm install -g taskqueue-mcp

# Or use npx (no install required)
npx taskqueue-mcp --version

# Verify
npx taskqueue-mcp --help
```

**Configuration**:

```bash
# Environment variables
export TASKQUEUE_MODE="enabled"
export TASKQUEUE_POLL_INTERVAL="1000"  # 1 second

# Or in .mycelium/config.json
{
  "coordination": {
    "mode": "taskqueue",
    "taskqueue": {
      "poll_interval_ms": 1000,
      "max_tasks": 100
    }
  }
}
```

### Markdown Mode (Zero Setup, Fallback)

**Best for**: Offline work, minimal dependencies, git-tracked state

**Performance**:
- File writes: 100/sec
- File reads: 500/sec
- Scales to 20 agents

**Setup**:

```bash
# Just create coordination directory
mkdir -p .claude/coordination/

# No installation required!
# Mycelium will auto-detect and use markdown files
```

**Configuration**:

```bash
# Force markdown mode (optional)
export MYCELIUM_MODE="markdown"

# Or in .mycelium/config.json
{
  "coordination": {
    "mode": "markdown",
    "markdown": {
      "directory": ".claude/coordination"
    }
  }
}
```

## Configuration

### Infrastructure Health Checks

Configure infrastructure monitoring with `/infra-check`:

```bash
# Copy example config
cp ~/.claude/plugins/mycelium/docs/examples/infra-check.json.example \
   ~/.infra-check.json

# Edit for your environment
nano ~/.infra-check.json
```

**Example `.infra-check.json`**:

```json
{
  "checks": {
    "redis": {
      "enabled": true,
      "url": "redis://localhost:6379",
      "timeout_seconds": 5
    },
    "temporal": {
      "enabled": false,
      "host": "localhost:7233"
    },
    "taskqueue": {
      "enabled": true
    },
    "gpu": {
      "enabled": true,
      "required_model": null
    },
    "postgresql": {
      "enabled": false,
      "connection_string": "postgresql://localhost:5432/mycelium"
    },
    "custom_services": []
  }
}
```

### Pre-Test Validation Hooks

Enable automatic infrastructure validation before running tests:

```bash
# Copy example script
cp ~/.claude/plugins/mycelium/docs/examples/pre-test-checks.sh.example \
   .pre-test-checks.sh

# Make executable
chmod +x .pre-test-checks.sh

# Edit for project-specific validation
nano .pre-test-checks.sh
```

**Example `.pre-test-checks.sh`**:

```bash
#!/bin/bash

project_pre_test_checks() {
    # Check dependencies
    uv sync --check || return 1

    # Verify test data exists
    [ -f "tests/fixtures/data.json" ] || return 1

    # Custom validation logic
    python scripts/validate_env.py || return 1

    return 0
}
```

This script is automatically triggered before:
- `uv run pytest`
- `pytest`
- `python -m pytest`

### CI/CD Pipeline Monitoring

Configure pipeline status monitoring with `/pipeline-status`:

```bash
# Copy example script
cp ~/.claude/plugins/mycelium/docs/examples/pipeline-status.sh.example \
   .pipeline-status.sh

# Make executable
chmod +x .pipeline-status.sh
```

Supports GitHub Actions, GitLab CI, Jenkins, and custom pipelines.

## Verification

### 1. Verify Plugin Installation

```bash
# Check if plugin is installed
claude plugin list | grep mycelium

# Check if agents are available
ls ~/.claude/plugins/mycelium/agents/

# Check if commands are available
ls ~/.claude/plugins/mycelium/commands/

# Check if hooks are available
ls ~/.claude/plugins/mycelium/hooks/
```

### 2. Verify Infrastructure

```bash
# Run comprehensive infrastructure check
/infra-check

# Expected output for Redis mode:
# ✅ Redis               HEALTHY    (0.8ms latency)
# ✅ TaskQueue MCP       HEALTHY    (npx available)
# ✅ Coordination        ACTIVE     (mode: redis)
# ===================================
# Overall Status: HEALTHY ✅

# Detailed diagnostics
/infra-check --verbose

# Custom config
/infra-check --config .infra-check.json
```

### 3. Verify Agent Loading

```bash
# Check that agents are loaded (should see 119+ mycelium agents)
/agents

# Or use team status command
/team-status

# Expected output:
# === Mycelial Network Status ===
#
# Total Agents: 130
# Active: 0/130
# Network Health: HEALTHY ✅
#
# Coordination Mode: Redis (preferred)
# Substrate: HEALTHY
```

### 4. Test Coordination

```bash
# Create a test coordination file
cat > /tmp/test_coordination.js << 'EOF'
import { CoordinationClient } from 'mycelium/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();
console.log('Coordination mode:', client.mode);

await client.storeAgentStatus('test-agent', {
  status: 'testing',
  timestamp: new Date().toISOString()
});

const status = await client.getAgentStatus('test-agent');
console.log('Retrieved status:', status);
EOF

# Run test
node /tmp/test_coordination.js
```

## First Steps

### 1. Explore Available Agents

```bash
# List all agent categories
ls ~/.claude/plugins/mycelium/agents/

# View agents in a specific category
ls ~/.claude/plugins/mycelium/agents/01-core-development/

# Read an agent's capabilities
cat ~/.claude/plugins/mycelium/agents/01-core-development/python-pro.md
```

Agent categories:
- `01-core-development` - Python, JavaScript, TypeScript, Rust specialists
- `02-language-specialists` - Go, Java, C++, Kotlin, Swift experts
- `03-infrastructure` - DevOps, Kubernetes, Security, Cloud
- `04-quality-security` - Testing, QA, Security auditing, Performance
- `05-data-ai` - ML, Data Engineering, NLP, Computer Vision
- `06-developer-experience` - CLI, Documentation, Tooling, MCP
- `07-specialized-domains` - Web3, IoT, Game Dev, Audio/Video
- `08-business-product` - PM, UX, Technical Writing, Marketing
- `09-meta-orchestration` - Multi-agent coordination, workflow management
- `10-research-analysis` - Academic research, benchmarking, innovation
- `11-claude-code` - Plugin development, subagent creation, hooks

### 2. Try Slash Commands

```bash
# Check infrastructure
/infra-check

# Monitor agent coordination
/team-status

# Check CI/CD pipelines (if configured)
/pipeline-status
```

### 3. Invoke an Agent

In your Claude Code session:

```
@python-pro can you review this Python code for best practices?

[paste code]
```

The agent will activate and provide specialized assistance.

### 4. Run a Multi-Agent Workflow

Example: Coordinate multiple agents for a task

```javascript
// In your project
import { CoordinationClient } from 'mycelium/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();

// Create task for data engineer
await client.createTask('prepare-dataset', {
  agent: 'data-engineer',
  dataset: 'training-data',
  output: 'data/processed/'
});

// Create dependent task for AI engineer
await client.createTask('train-model', {
  agent: 'ai-engineer',
  depends_on: 'prepare-dataset',
  config: 'configs/model.yaml'
});

// Monitor progress
await client.monitorWorkflow(['prepare-dataset', 'train-model']);
```

## Troubleshooting

### Plugin Not Detected

```bash
# Verify plugin installation
claude plugin list | grep mycelium

# Check symlink (if using local development)
ls -la ~/.claude/plugins/mycelium

# Reinstall if needed
claude plugin uninstall mycelium
claude plugin install git+https://github.com/gsornsen/mycelium.git

# Restart Claude Code completely
# Exit and restart (important for agent loading)
```

### Agents Not Loading

**Symptom**: `/agents` shows fewer than 119 mycelium agents

**Solution**:
```bash
# Mycelium agents require complete restart
# 1. Exit Claude Code completely (not just close window)
# 2. Restart Claude Code
# 3. Wait for agent discovery (may take 5-10 seconds)
# 4. Verify: /agents | grep mycelium

# If still not working, check plugin structure
ls ~/.claude/plugins/mycelium/agents/*/*.md | wc -l
# Should show ~119 files
```

See [AGENT_STRUCTURE_CHANGE.md](../../AGENT_STRUCTURE_CHANGE.md) for technical details.

### Coordination Mode Issues

```bash
# Check which mode is active
/team-status
# Look for: "Coordination mode: redis|taskqueue|markdown"

# Test Redis connection
redis-cli ping
# Should return: PONG

# Test TaskQueue
npx taskqueue-mcp --version
# Should return version number

# Force fallback to markdown
export MYCELIUM_MODE=markdown
mkdir -p .claude/coordination/
```

### Stale Agent Status

```bash
# Clear stale data (Redis)
redis-cli DEL "agents:status:*"

# Clear stale data (Markdown)
rm -f .claude/coordination/agent-*.md

# Republish status
/team-status --refresh
```

### Performance Issues

**Symptom**: Slow agent coordination, high latency

**Diagnosis**:
```bash
# Check coordination mode
/team-status

# Redis mode: check latency
redis-cli --latency
# Should be <5ms

# TaskQueue mode: check poll interval
cat .mycelium/config.json | grep poll_interval
# Increase if coordination is slow

# Markdown mode: check file system performance
time ls .claude/coordination/
# Should be <100ms
```

**Solutions**:
- Redis: Use local Redis instance, not remote
- TaskQueue: Increase poll interval for less overhead
- Markdown: Use SSD for coordination directory
- Consider upgrading coordination mode (markdown → taskqueue → redis)

### Infrastructure Check Failures

```bash
# Run detailed diagnostics
/infra-check --verbose

# Check specific service manually
# Redis
redis-cli ping

# Temporal (if enabled)
tctl cluster health

# GPU (if enabled)
nvidia-smi

# Disable failing checks temporarily
nano ~/.infra-check.json
# Set "enabled": false for problematic services
```

## Next Steps

Once installation and verification are complete:

1. **Read [coordination.md](./coordination.md)** - Learn about dual-mode coordination patterns
2. **Read [agents.md](./agents.md)** - Understand agent categories and development
3. **Read [deployment.md](./deployment.md)** - Deploy to production environments
4. **Try example workflows** - See [docs/examples/](../../docs/examples/)
5. **Create custom agents** - See [CONTRIBUTING.md](../../CONTRIBUTING.md)

## Support

- **Documentation**: [.mycelium/modules/](./)
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Discussions**: https://github.com/gsornsen/mycelium/discussions
- **Main README**: [README.md](../../README.md)
