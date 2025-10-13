# Mycelium Installation Guide

Complete installation and setup instructions for the Mycelium Claude Code plugin.

## Quick Install

### Option 1: Local Development (Recommended for Testing)

```bash
# Symlink to Claude Code plugins directory
ln -s /home/gerald/git/mycelium ~/.claude/plugins/mycelium

# Verify installation
ls -la ~/.claude/plugins/mycelium
```

### Option 2: Direct Copy

```bash
# Copy to Claude Code plugins directory
cp -r /home/gerald/git/mycelium ~/.claude/plugins/mycelium

# Verify
claude plugin list | grep mycelium
```

### Option 3: From Git (Future)

```bash
# When published to GitHub
claude plugin install git+https://github.com/gerald/mycelium.git
```

## Verify Installation

After installation, verify that all components are available:

```bash
# Check if agents are available
ls ~/.claude/plugins/mycelium/agents/

# Check if commands are available
ls ~/.claude/plugins/mycelium/commands/

# Check if hooks are available
ls ~/.claude/plugins/mycelium/hooks/

# Test slash command
/infra-check
```

## Coordination Setup

Choose and configure your coordination mode:

### Mode 1: Redis (Recommended for Production)

**Advantages**: Real-time pub/sub, atomic operations, distributed coordination

#### Docker Installation

```bash
# Redis
docker run -d \
  --name mycelium-redis \
  -p 6379:6379 \
  redis:latest

# Or Valkey (Redis fork)
docker run -d \
  --name mycelium-valkey \
  -p 6379:6379 \
  valkey/valkey:latest
```

#### Native Installation (Ubuntu/Debian)

```bash
# Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Verify Redis

```bash
# Test connection
redis-cli ping
# Should return: PONG

# Test from Mycelium
/infra-check
# Should show: ✅ Redis HEALTHY
```

### Mode 2: TaskQueue MCP (Good for Task-Centric Workflows)

**Advantages**: Task-based coordination, built-in status tracking, no server required

```bash
# Install globally
npm install -g taskqueue-mcp

# Or use with npx (no installation)
npx taskqueue-mcp --version
```

#### Verify TaskQueue

```bash
# Check installation
npx taskqueue-mcp --version

# Test from Mycelium
/infra-check
# Should show: ✅ TaskQueue HEALTHY
```

### Mode 3: Markdown (Fallback - Zero Setup)

**Advantages**: No dependencies, human-readable, git-trackable

```bash
# Just create coordination directory
mkdir -p .claude/coordination/

# That's it! No installation required
```

#### Verify Markdown Mode

```bash
# Test from Mycelium
/infra-check
# Should show: Coordination mode: markdown (fallback)
```

## Optional: Temporal Setup (Durable Workflows)

For advanced durable workflow orchestration:

### Docker Compose

```bash
# Create docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
    environment:
      - TEMPORAL_CLI_ADDRESS=temporal:7233

  temporal-ui:
    image: temporalio/ui:latest
    ports:
      - "8080:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
EOF

# Start Temporal
docker-compose up -d

# Verify
temporal workflow list --namespace mycelium-workflows
```

## Configuration

### Global Infrastructure Check Config

```bash
# Create global config
cat > ~/.infra-check.json <<EOF
{
  "checks": {
    "redis": {
      "enabled": true,
      "url": "redis://localhost:6379",
      "timeout_seconds": 5
    },
    "temporal": {
      "enabled": true,
      "host": "localhost:7233",
      "namespace": "mycelium-workflows"
    },
    "taskqueue": {
      "enabled": true,
      "check_npm": true
    }
  }
}
EOF
```

### Project-Specific Config

```bash
# In your project directory
cat > .infra-check.json <<EOF
{
  "checks": {
    "redis": {
      "enabled": true,
      "url": "redis://localhost:6379"
    },
    "gpu": {
      "enabled": true,
      "required_model": "RTX 4090"
    }
  }
}
EOF
```

### Pre-Test Validation

```bash
# Create project-specific pre-test checks
cat > .pre-test-checks.sh <<'EOF'
#!/bin/bash

project_pre_test_checks() {
    # Check dependencies
    uv sync --check || return 1

    # Verify test data
    [ -f "tests/fixtures/test_data.json" ] || {
        echo "Missing test data"
        return 1
    }

    # Custom validation
    python scripts/validate_env.py || return 1

    return 0
}
EOF

chmod +x .pre-test-checks.sh
```

## Testing Installation

### Test Coordination

```bash
# Test infrastructure check
/infra-check --verbose

# Test team status
/team-status

# Test pipeline status
/pipeline-status
```

### Test JavaScript Library

```bash
# Create test script
cat > test-mycelium.js <<'EOF'
import { createMyceliumClient } from './lib/index.js';

async function test() {
  const mycelium = await createMyceliumClient();

  console.log(`Coordination mode: ${mycelium.mode}`);

  // Test agent status
  await mycelium.coordination.storeAgentStatus('test-agent', {
    status: 'busy',
    active_tasks: ['test-task']
  });

  const status = await mycelium.coordination.getAgentStatus('test-agent');
  console.log('Agent status:', status);

  // Test pub/sub
  await mycelium.pubsub.subscribe('test-channel', (message) => {
    console.log('Received:', message);
  });

  await mycelium.pubsub.publish('test-channel', {
    event: 'test',
    data: 'Hello Mycelium!'
  });

  // Cleanup
  await mycelium.pubsub.cleanup();
}

test().catch(console.error);
EOF

# Run test
cd ~/.claude/plugins/mycelium
node test-mycelium.js
```

### Test Agent Invocation

```bash
# Test invoking a specific agent
claude --agents ~/.claude/plugins/mycelium/agents/09-meta-orchestration/multi-agent-coordinator.md \
       -p "Coordinate a simple task distribution"
```

## Troubleshooting

### Plugin Not Found

```bash
# Verify symlink/copy
ls -la ~/.claude/plugins/mycelium

# Check permissions
chmod -R 755 ~/.claude/plugins/mycelium
chmod +x ~/.claude/plugins/mycelium/hooks/*.sh
```

### Commands Not Available

```bash
# Verify commands directory
ls ~/.claude/plugins/mycelium/commands/

# Check YAML frontmatter
head -20 ~/.claude/plugins/mycelium/commands/infra-check.md

# Restart Claude Code
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Check firewall
sudo ufw status

# Check connection
telnet localhost 6379

# Check logs
docker logs mycelium-redis
```

### TaskQueue Issues

```bash
# Verify npm installation
npm list -g taskqueue-mcp

# Check Node.js version
node --version  # Should be >= 18.0.0

# Test npx
npx taskqueue-mcp --version
```

### Hook Not Triggering

```bash
# Verify hooks.json
cat ~/.claude/plugins/mycelium/hooks/hooks.json

# Check hook permissions
ls -la ~/.claude/plugins/mycelium/hooks/*.sh
chmod +x ~/.claude/plugins/mycelium/hooks/*.sh

# Test hook manually
bash ~/.claude/plugins/mycelium/hooks/pre-test-validation.sh
```

## Uninstallation

### Remove Plugin

```bash
# Remove symlink
rm ~/.claude/plugins/mycelium

# Or remove directory
rm -rf ~/.claude/plugins/mycelium
```

### Cleanup Coordination Data

```bash
# Redis
redis-cli FLUSHDB

# Markdown
rm -rf .claude/coordination/

# Temporal (if installed)
docker-compose down -v
```

### Remove Config Files

```bash
# Global config
rm ~/.infra-check.json

# Project configs
rm .infra-check.json
rm .pre-test-checks.sh
rm .pipeline-status.sh
```

## Next Steps

1. **Read the Documentation**: Check out [README.md](README.md) for features and usage
2. **Explore Agents**: Browse the 130+ agents in `agents/` directory
3. **Try Commands**: Use `/infra-check`, `/team-status`, `/pipeline-status`
4. **Build Workflows**: Check [lib/workflow.js](lib/workflow.js) for workflow examples
5. **Join Community**: Report issues, share patterns, contribute agents

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/gerald/mycelium/issues
- **Discussions**: https://github.com/gerald/mycelium/discussions

---

**Mycelium** - Growing distributed intelligence, one agent at a time 🍄
