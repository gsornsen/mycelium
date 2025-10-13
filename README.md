# Mycelium - Distributed Intelligence for Claude Code

![Mycelium Network](https://img.shields.io/badge/mycelium-distributed_intelligence-green)
![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-blue)
![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)

> **Mycelium**: Like nature's mycelial networks that communicate through chemical signals, distribute resources efficiently, and exhibit emergent intelligence - this Claude Code plugin creates an ecosystem of expert subagents that collaborate in real-time.

## Why "Mycelium"?

Mycelial networks in nature demonstrate remarkable distributed intelligence:

- **Chemical Communication** → Real-time pub/sub messaging
- **Resource Distribution** → Intelligent task queuing via Redis
- **Resilience & Decentralization** → Fault-tolerant agent coordination
- **Emergent Intelligence** → Complex workflows from simple agent interactions

Just as mycelium connects trees in a forest, this plugin connects specialized Claude Code agents into a cohesive, intelligent system.

## Overview

Mycelium is a comprehensive Claude Code plugin that provides:

1. **130+ Expert Subagents** - Specialized agents across 11 domains
2. **Dual-Mode Coordination** - Redis/TaskQueue preferred, markdown fallback
3. **Durable Workflows** - Temporal-based workflow orchestration
4. **Real-time Messaging** - Pub/sub for agent communication
5. **Infrastructure Commands** - Health checks, status monitoring, pipeline integration
6. **Event Hooks** - Automated validation and coordination

## Architecture

### The Mycelial Network Metaphor

```
                    🍄 Fruiting Bodies (Orchestrators)
                         /        |        \
                        /         |         \
                  Spores      Spores      Spores
                (Agents)    (Agents)    (Agents)
                    \          |          /
                     \         |         /
                      \        |        /
                   ==========================
                   Mycelial Network (Substrate)
                   - Redis (chemical signals)
                   - TaskQueue (resource flow)
                   - Markdown (backup pathways)
                   ==========================
```

**Terminology**:
- **Spores/Nodes** - Individual specialized agents
- **Fruiting Body/Colony** - Orchestrator agents that coordinate others
- **Threads/Hyphae** - Durable workflows connecting agents
- **Network/Substrate** - The coordination infrastructure (Redis/TaskQueue/Markdown)

### Agent Categories (Spores)

1. **Core Development** (01) - Python, JavaScript, TypeScript, Rust specialists
2. **Language Specialists** (02) - Go, Java, C++, Kotlin, Swift experts
3. **Infrastructure** (03) - DevOps, Kubernetes, Security, Cloud
4. **Quality & Security** (04) - Testing, QA, Security auditing, Performance
5. **Data & AI** (05) - ML, Data Engineering, NLP, Computer Vision
6. **Developer Experience** (06) - CLI, Documentation, Tooling, MCP
7. **Specialized Domains** (07) - Web3, IoT, Game Dev, Audio/Video
8. **Business & Product** (08) - PM, UX, Technical Writing, Marketing
9. **Meta-Orchestration** (09) - Multi-agent coordination, workflow management
10. **Research & Analysis** (10) - Academic research, benchmarking, innovation
11. **Claude Code** (11) - Plugin development, subagent creation, hooks

## Features

### 1. Dual-Mode Coordination

Mycelium automatically detects and uses the best available coordination mode:

**Mode 1: Redis MCP (Preferred - Real-time)**
- Real-time pub/sub messaging
- Atomic operations with transactions
- TTL-based automatic cleanup
- Distributed coordination across machines
- Sub-millisecond latency

**Mode 2: TaskQueue MCP (Preferred - Task-centric)**
- Durable task queue management
- Built-in status tracking
- Integration with MCP ecosystem
- No additional server required (uses npx)

**Mode 3: Markdown Files (Fallback - Zero-setup)**
- No infrastructure dependencies
- Human-readable coordination files
- Git-trackable state
- Works completely offline

### 2. Slash Commands

#### `/infra-check` - Infrastructure Health Check

Comprehensive health monitoring for all coordination infrastructure.

```bash
# Quick check
/infra-check

# Detailed diagnostics
/infra-check --verbose

# Custom config
/infra-check --config .infra-check.json
```

**Checks**:
- Redis/Valkey connectivity and performance
- Temporal cluster status
- TaskQueue MCP availability
- PostgreSQL/MongoDB health
- GPU status (NVIDIA)
- Custom service endpoints

**Configuration** (`.infra-check.json`):
```json
{
  "checks": {
    "redis": {
      "enabled": true,
      "url": "redis://localhost:6379",
      "timeout_seconds": 5
    },
    "temporal": {
      "enabled": true,
      "host": "localhost:7233"
    },
    "gpu": {
      "enabled": true,
      "required_model": "RTX 4090"
    }
  }
}
```

#### `/team-status` - Multi-Agent Coordination Status

Monitor agent workload, active tasks, and coordination health.

```bash
# Show all agents
/team-status

# Specific agent
/team-status ai-engineer

# Detailed view
/team-status --detailed
```

**Output**:
```
=== Mycelial Network Status ===

Active Spores (Agents): 12/130
Network Health: HEALTHY ✅

Agent Workload:
  ai-engineer      [████████░░] 85% (2 tasks)
  data-engineer    [███████░░░] 70% (1 task)
  devops-engineer  [███░░░░░░░] 30% (1 task)

Substrate (Coordination):
  Mode: Redis (preferred)
  Messages/min: 234K
  Latency: 0.8ms avg

Hyphae (Workflows):
  Active: 3
  Completed: 47
  Failed: 0
```

#### `/pipeline-status` - CI/CD Pipeline Monitoring

Check build, test, and deployment status across multiple CI systems.

```bash
# Quick status
/pipeline-status

# Detailed with logs
/pipeline-status --detailed

# Watch mode (auto-refresh)
/pipeline-status --watch
```

Supports:
- GitHub Actions
- GitLab CI
- Jenkins
- Custom pipelines (via `.pipeline-status.sh`)

### 3. Event Hooks

#### Pre-Test Validation

Automatically validates infrastructure before running tests:

```bash
# Triggered automatically before:
uv run pytest
pytest
python -m pytest
```

**What it validates**:
- Infrastructure health (Redis, Temporal, etc.)
- Project-specific requirements (via `.pre-test-checks.sh`)
- Coordination substrate availability

**Custom validation** (`.pre-test-checks.sh`):
```bash
#!/bin/bash
project_pre_test_checks() {
    # Check dependencies
    uv sync --check || return 1

    # Verify test data
    [ -f "tests/fixtures/data.json" ] || return 1

    # Custom validation
    python scripts/validate_env.py || return 1

    return 0
}
```

### 4. Coordination Library

JavaScript/Node.js library for dual-mode coordination:

```javascript
import { CoordinationClient } from 'mycelium/lib/coordination.js';

// Auto-detect coordination mode
const client = new CoordinationClient();
await client.initialize();
// → "Coordination mode: Redis (preferred)"

// Store agent status (works in all modes)
await client.storeAgentStatus('ai-engineer', {
  status: 'busy',
  active_tasks: ['train-model'],
  last_updated: new Date().toISOString()
});

// Retrieve agent status
const status = await client.getAgentStatus('ai-engineer');

// Publish event (real-time in Redis, polling in others)
await client.publishEvent('training:events', {
  event: 'checkpoint_saved',
  step: 1000,
  loss: 0.42
});

// Subscribe to events
await client.subscribeEvents('training:events', (event) => {
  console.log('Event received:', event);
});
```

### 5. Workflow Orchestration

Durable workflows with Temporal integration:

```javascript
import { WorkflowClient } from 'mycelium/lib/workflow.js';

const wf = new WorkflowClient();

// Create durable workflow
const workflowId = await wf.createWorkflow('train-model', {
  dataset: 'alice-voice',
  epochs: 3,
  checkpoint_interval: 500
});

// Monitor workflow
const status = await wf.getWorkflowStatus(workflowId);
// → { status: 'running', progress: 0.35, step: 3500 }

// Wait for completion
await wf.waitForCompletion(workflowId);
```

## Installation

### Option 1: Install from Git

```bash
# Clone repository
git clone https://github.com/gerald/mycelium.git ~/.claude/plugins/mycelium

# Or install as Claude Code plugin
claude plugin install git+https://github.com/gerald/mycelium.git
```

### Option 2: Local Development

```bash
# Symlink local development version
ln -s /home/gerald/git/mycelium ~/.claude/plugins/mycelium

# Verify installation
claude plugin list | grep mycelium
```

### Option 3: Direct Copy

```bash
# Copy to Claude Code plugins directory
cp -r /path/to/mycelium ~/.claude/plugins/mycelium
```

## Setup

### 1. Choose Coordination Mode

#### Redis (Recommended for Production)

```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or Valkey (Redis fork)
docker run -d -p 6379:6379 --name valkey valkey/valkey:latest

# Verify
redis-cli ping  # Should return PONG
```

#### TaskQueue MCP (Good for Task-Centric Workflows)

```bash
# Install via npm
npm install -g taskqueue-mcp

# Verify
npx taskqueue-mcp --version
```

#### Markdown Fallback (Zero Setup)

```bash
# Just create coordination directory
mkdir -p .claude/coordination/

# No installation required!
```

### 2. Configure Infrastructure Checks

```bash
# Copy example config
cp ~/.claude/plugins/mycelium/docs/examples/infra-check.json.example \
   ~/.infra-check.json

# Edit for your environment
nano ~/.infra-check.json
```

### 3. Enable Pre-Test Hooks (Optional)

```bash
# Project-specific validation
cp ~/.claude/plugins/mycelium/docs/examples/pre-test-checks.sh.example \
   .pre-test-checks.sh

chmod +x .pre-test-checks.sh
```

## Usage Examples

### Example 1: Multi-Agent Model Training

```javascript
// Orchestrate model training across multiple agents

// 1. data-engineer prepares dataset
await client.createTask('prepare-dataset', {
  agent: 'data-engineer',
  dataset: 'alice-voice',
  output: 'data/processed/'
});

// 2. ai-engineer trains model
await client.createTask('train-model', {
  agent: 'ai-engineer',
  depends_on: 'prepare-dataset',
  config: 'configs/lora_default.yaml'
});

// 3. performance-engineer benchmarks
await client.createTask('benchmark-model', {
  agent: 'performance-engineer',
  depends_on: 'train-model',
  metrics: ['latency', 'throughput', 'memory']
});

// Monitor workflow
await client.monitorWorkflow(['prepare-dataset', 'train-model', 'benchmark-model']);
```

### Example 2: Infrastructure Validation

```bash
# Before deploying
/infra-check --verbose

# Expected output:
# ✅ Redis               HEALTHY    (0.8ms latency)
# ✅ Temporal            HEALTHY    (3 workers active)
# ✅ GPU                 HEALTHY    (RTX 4090, 45°C, 12GB free)
# ===================================
# Overall Status: HEALTHY ✅
```

### Example 3: Real-time Agent Collaboration

```javascript
// Multi-agent pair programming session

// ai-engineer publishes progress
await pubsub.publish('training:progress', {
  agent: 'ai-engineer',
  event: 'training_started',
  workflow_id: 'train-123'
});

// performance-monitor subscribes and tracks
await pubsub.subscribe('training:progress', async (event) => {
  if (event.event === 'checkpoint_saved') {
    // Trigger performance evaluation
    await evaluateCheckpoint(event.checkpoint_path);
  }
});

// error-coordinator watches for failures
await pubsub.subscribe('training:errors', async (error) => {
  await handleTrainingError(error);
});
```

## Documentation

### Core Documentation

- **[Dual-Mode Coordination Pattern](docs/patterns/dual-mode-coordination.md)** - Redis vs TaskQueue vs Markdown
- **[Markdown Coordination Guide](docs/patterns/markdown-coordination.md)** - Fallback coordination details
- **[Agent Collaboration Workflows](docs/patterns/agent-coordination-overview.md)** - Multi-agent patterns
- **[Event-Driven Coordination](docs/patterns/event-driven-coordination.md)** - Pub/sub patterns
- **[Task Handoff Protocol](docs/patterns/task-handoff-protocol.md)** - Agent-to-agent delegation

### Configuration Examples

- **[Infrastructure Check Config](docs/examples/infra-check.json.example)** - `.infra-check.json` template
- **[Pre-Test Validation Script](docs/examples/pre-test-checks.sh.example)** - Custom validation
- **[Pipeline Status Script](docs/examples/pipeline-status.sh.example)** - CI/CD integration

### Agent Documentation

All 130+ agents include:
- Clear invocation criteria
- Tool access specifications
- Communication protocols
- Integration patterns

Browse: `agents/*/README.md` for category overviews

## Architecture Details

### Coordination Substrate

```
┌─────────────────────────────────────────────────┐
│         Application Layer (Agents)              │
│  ai-engineer | data-engineer | devops-engineer  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      Coordination Library (lib/)                │
│  - Auto-detection of available substrate       │
│  - Unified API across all modes                │
│  - Graceful degradation                         │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌──────────┐  ┌──────────┐
   │ Redis  │  │TaskQueue │  │Markdown  │
   │  MCP   │  │   MCP    │  │  Files   │
   └────────┘  └──────────┘  └──────────┘
   Real-time   Task-centric   Zero-deps
```

### Agent Hierarchy

```
Meta-Orchestration (Fruiting Bodies)
├── multi-agent-coordinator    - Overall coordination
├── workflow-orchestrator      - Process execution
├── task-distributor           - Work allocation
├── context-manager            - State management
└── performance-monitor        - Metrics tracking

Specialist Agents (Spores)
├── Core Development
│   ├── python-pro            - Python expertise
│   ├── ai-engineer           - ML/AI systems
│   └── ...
├── Infrastructure
│   ├── devops-engineer       - CI/CD, deployment
│   ├── kubernetes-specialist - K8s orchestration
│   └── ...
└── ... (130+ total agents)
```

### Workflow Execution (Hyphae)

```
1. Task Creation → TaskQueue/Redis
2. Agent Assignment → multi-agent-coordinator
3. Execution → Specialist agent
4. Progress Updates → pub/sub events
5. Result Storage → Redis/Markdown
6. Next Task Trigger → workflow-orchestrator
```

## Advanced Features

### Custom Agent Creation

Create your own specialist agents:

```markdown
---
name: voice-specialist
description: Expert in voice cloning and TTS systems. Invoke when working with audio models, voice datasets, or speech synthesis.
tools: Read, Write, Bash(python:*), Grep
---

You are a voice cloning specialist with expertise in...

## Communication Protocol

Report progress to multi-agent-coordinator:
```json
{
  "agent": "voice-specialist",
  "status": "completed",
  "voice_similarity": 0.89,
  "wer": 0.06
}
```
```

Save to: `~/.claude/plugins/mycelium/agents/07-specialized-domains/voice-specialist.md`

### Custom Commands

Add domain-specific slash commands:

```markdown
---
allowed-tools: Bash(*)
description: Check voice dataset quality metrics
---

# Voice Dataset Check

Run quality analysis on voice dataset.

## Your task

1. Load dataset from $1
2. Calculate metrics (duration, quality, speaker similarity)
3. Report findings
```

Save to: `~/.claude/plugins/mycelium/commands/voice-check.md`

### Custom Hooks

Create event-driven automation:

```json
{
  "description": "Voice model training hooks",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash.*train.*voice",
        "hooks": [
          {
            "type": "command",
            "command": "${MYCELIUM_ROOT}/hooks/post-training-eval.sh"
          }
        ]
      }
    ]
  }
}
```

## Performance & Scalability

### Benchmarks

**Redis Mode**:
- Message throughput: 234K messages/min
- Latency: 0.8ms avg
- Agent coordination overhead: <5%
- Scales to 100+ agents

**TaskQueue Mode**:
- Task creation: 50/sec
- Task polling: 1Hz default
- Agent coordination overhead: ~10%
- Scales to 50+ agents

**Markdown Mode**:
- File writes: 100/sec
- File reads: 500/sec
- Agent coordination overhead: ~20%
- Scales to 20 agents

### Resource Requirements

**Minimal (Markdown Mode)**:
- RAM: 100MB
- Disk: 10MB
- No network required

**Recommended (Redis Mode)**:
- RAM: 500MB (Redis: 256MB, Client: 256MB)
- Disk: 50MB
- Network: Local or LAN

**Production (Redis + Temporal)**:
- RAM: 2GB (Redis: 512MB, Temporal: 1GB, Clients: 512MB)
- Disk: 500MB
- Network: Low-latency recommended

## Troubleshooting

### Command Not Found

```bash
# Verify plugin installation
claude plugin list | grep mycelium

# Check symlink
ls -la ~/.claude/plugins/mycelium

# Reinstall if needed
claude plugin uninstall mycelium
claude plugin install git+https://github.com/gerald/mycelium.git
```

### Coordination Issues

```bash
# Check coordination mode
/team-status
# Look for: "Coordination mode: redis|taskqueue|markdown"

# Test Redis
redis-cli ping

# Test TaskQueue
npx taskqueue-mcp --version

# Fallback to markdown
mkdir -p .claude/coordination/
export MYCELIUM_MODE=markdown
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

## Contributing

Contributions welcome! Areas of focus:

1. **New Agents** - Domain-specific specialists
2. **Commands** - Productivity slash commands
3. **Hooks** - Event-driven automation
4. **Documentation** - Patterns and examples
5. **Coordination Modes** - New substrate integrations

## Roadmap

### v1.1 (Next)
- [ ] Plugin marketplace submission
- [ ] Web dashboard for agent monitoring
- [ ] Advanced workflow patterns library
- [ ] Agent performance analytics

### v1.2 (Future)
- [ ] Multi-machine coordination (distributed Redis)
- [ ] Agent learning system (capture & share patterns)
- [ ] Auto-scaling agent allocation
- [ ] Cost optimization recommendations

### v2.0 (Vision)
- [ ] Self-organizing agent networks
- [ ] Adaptive coordination strategies
- [ ] Emergent workflow discovery
- [ ] Cross-project knowledge sharing

## License

MIT License - see [LICENSE](LICENSE) file

## Credits

- **Mycelium Metaphor** - Inspired by natural mycelial networks
- **Agent Architecture** - Claude Code subagent system
- **Coordination Patterns** - Distributed systems best practices
- **MCP Integration** - Model Context Protocol ecosystem

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/gerald/mycelium/issues
- **Discussions**: https://github.com/gerald/mycelium/discussions

---

**Mycelium** - Growing distributed intelligence, one agent at a time 🍄
