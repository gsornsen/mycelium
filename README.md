# Mycelium - Distributed Intelligence for Claude Code

![Mycelium Network](https://img.shields.io/badge/mycelium-distributed_intelligence-green)
![Claude Code Plugin](https://img.shields.io/badge/claude--code-plugin-blue)
![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)

> **Mycelium**: Like nature's mycelial networks that communicate through chemical signals, distribute resources
> efficiently, and exhibit emergent intelligence - this Claude Code plugin creates an ecosystem of expert subagents that
> collaborate in real-time.

## What is Mycelium?

Mycelium is a comprehensive Claude Code plugin providing:

- **130+ Expert Agents** across 11 domains (Python, DevOps, AI/ML, Security, and more)
- **Dual-Mode Coordination** with auto-detection (Redis/TaskQueue/Markdown)
- **Real-time Messaging** via pub/sub for agent collaboration
- **Durable Workflows** with Temporal integration
- **Infrastructure Monitoring** with `/infra-check`, `/team-status`, `/pipeline-status` commands
- **Event-Driven Automation** via hooks system
- **Fast Agent Discovery** with lazy loading (105x faster, 67% memory reduction)
- **Performance Analytics** with privacy-first telemetry (local-only, no PII)

## Quick Start

### Installation

```bash
# Option 1: Plugin Marketplace (recommended)
/plugin marketplace add gsornsen/mycelium
/plugin install mycelium-core@mycelium

# Option 2: Direct from GitHub
claude plugin install git+https://github.com/gsornsen/mycelium.git

# Option 3: Local development
ln -s /path/to/mycelium ~/.claude/plugins/mycelium
```

**Important**: Restart Claude Code completely after installation to load all 130+ agents.

### Verification

```bash
# Check infrastructure health
/infra-check

# Verify agents loaded (should see 119+ mycelium agents)
/agents

# Check coordination status
/team-status
```

### First Steps

1. **Choose coordination mode** - Redis (production), TaskQueue (task-centric), or Markdown (zero-setup)
1. **Set up infrastructure** - Start Redis/Temporal if using those modes
1. **Invoke agents** - Use `@agent-name` to activate specialists
1. **Monitor status** - Use `/team-status` and `/infra-check` commands

📖 **New User?** See [.mycelium/modules/onboarding.md](.mycelium/modules/onboarding.md) for complete setup guide.

## Core Concepts

### The Mycelial Network Metaphor

```
        🍄 Orchestrators (coordinate workflows)
           /        |        \
      Agents    Agents    Agents (specialized experts)
           \        |        /
      ============================
         Substrate (coordination)
         - Redis (real-time)
         - TaskQueue (structured)
         - Markdown (offline)
      ============================
```

**Key Terms**:

- **Spores** - Individual specialized agents (130+ available)
- **Fruiting Bodies** - Meta-orchestrators that coordinate multi-agent workflows
- **Hyphae** - Durable workflow threads connecting agents
- **Substrate** - Coordination infrastructure (auto-detects best available mode)

### Agent Categories

| Category             | Agents                                                                            | Description                                                    |
| -------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Core Development     | python-pro, ai-engineer, javascript-expert, typescript-specialist, rust-developer | Primary language specialists                                   |
| Infrastructure       | devops-engineer, kubernetes-specialist, docker-expert, security-auditor           | DevOps and deployment                                          |
| Data & AI            | data-engineer, ml-engineer, nlp-specialist, computer-vision-expert                | ML and data science                                            |
| Quality & Security   | qa-engineer, test-automation-specialist, performance-engineer                     | Testing and optimization                                       |
| Developer Experience | cli-developer, documentation-engineer, mcp-specialist                             | Tools and documentation                                        |
| Meta-Orchestration   | multi-agent-coordinator, workflow-orchestrator, task-distributor                  | Workflow coordination                                          |
| + 5 more categories  |                                                                                   | See [.mycelium/modules/agents.md](.mycelium/modules/agents.md) |

📖 **Learn More**: See [.mycelium/modules/agents.md](.mycelium/modules/agents.md) for complete agent catalog.

### Agent Discovery

Mycelium features **fast, lazy-loading agent discovery** (105x faster than traditional loading):

```python
from scripts.agent_discovery import AgentDiscovery
from pathlib import Path

# Initialize discovery (lightweight, <2ms)
discovery = AgentDiscovery(Path('plugins/mycelium-core/agents/index.json'))

# List all agents (metadata only, <20ms)
agents = discovery.list_agents()
print(f"Found {len(agents)} agents")

# Get specific agent (lazy load content, <5ms first access, <1ms cached)
agent = discovery.get_agent('01-core-api-designer')
print(agent['description'])

# Search by keyword (inverted index, <10ms)
results = discovery.search('api')
print(f"Found {len(results)} API specialists")

# Filter by category (O(1) lookup, <5ms)
core_agents = discovery.list_agents(category='Core Development')
print(f"{len(core_agents)} core development agents")
```

**Performance**:

- List agents: ~14ms (vs 1500ms traditional)
- Get agent (cached): ~0.08ms (vs 17ms traditional)
- Memory usage: 820KB (vs 2.5MB traditional, 67% reduction)
- Cache hit rate: 78% on realistic workloads

📖 **API Reference**: See [scripts/agent_discovery.py](scripts/agent_discovery.py) for complete API documentation.

### Performance Analytics

Mycelium includes privacy-first performance telemetry for tracking agent discovery performance, cache efficiency, and
token consumption.

#### Quick Start

```bash
# Generate performance report
uv run python -m mycelium_analytics report --days=7

# Quick health check dashboard
uv run python scripts/health_check.py
```

#### Key Features

- 📊 **Real-time Metrics**: p50/p95/p99 latencies for agent discovery
- ⚡ **Cache Performance**: Hit rate tracking and optimization insights
- 💾 **Token Savings**: Measure Phase 1 lazy loading impact (60-90% savings)
- 📈 **Performance Trends**: Daily stats with trend detection
- 🔒 **Privacy-First**: Local-only storage, no PII, opt-out support

#### Example Output

```
=== Mycelium Performance Health Check (7 days) ===

┌─────────────────────────────────────────────────────┐
│        AGENT DISCOVERY PERFORMANCE                  │
├─────────────────────────────────────────────────────┤
│  list_agents     0.08ms (p95)     ✅ < 20ms         │
│  get_agent       0.03ms (p95)     ✅ < 5ms          │
│  search          6.12ms (p95)     ✅ < 10ms         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│        CACHE PERFORMANCE                            │
├─────────────────────────────────────────────────────┤
│  Hit rate        87.2%            ✅ > 80%          │
│  Speedup         41.3x            (hit vs miss)     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│        TOKEN SAVINGS (Phase 1 Impact)               │
├─────────────────────────────────────────────────────┤
│  Agents loaded   47 / 119         (39.5% used)      │
│  Token savings   32,400 tokens    (60.5% saved)     │
└─────────────────────────────────────────────────────┘
```

#### Privacy Guarantees

All telemetry data is stored locally (`~/.mycelium/analytics/`) and never transmitted. Agent IDs are hashed, and no
personal information is collected.

**Opt-out**: `export MYCELIUM_TELEMETRY=0`

📖 **Complete Documentation**: See [.mycelium/modules/analytics.md](.mycelium/modules/analytics.md) for full analytics
guide. 📖 **Privacy Policy**: See [.mycelium/PRIVACY.md](.mycelium/PRIVACY.md) for detailed privacy information.

### Coordination Modes

Mycelium auto-detects the best available coordination mode:

**Redis Mode** (Production - Real-time)

- ⚡ 0.8ms latency, 234K messages/min
- 🔄 Real-time pub/sub events
- 📈 Scales to 100+ agents

**TaskQueue Mode** (Task-centric)

- 📋 Structured task management
- 🔗 MCP ecosystem integration
- 📊 Built-in status tracking

**Markdown Mode** (Zero-setup - Offline)

- 📝 Human-readable files
- 🔒 Git-trackable state
- 🚀 No dependencies

📖 **Learn More**: See [.mycelium/modules/coordination.md](.mycelium/modules/coordination.md) for coordination patterns
and API.

## Slash Commands

### `/infra-check` - Infrastructure Health

Monitor coordination infrastructure health:

```bash
/infra-check              # Quick check
/infra-check --verbose    # Detailed diagnostics
/infra-check --config .infra-check.json  # Custom config
```

Checks: Redis, Temporal, TaskQueue MCP, GPU, databases, custom services.

### `/team-status` - Agent Coordination

Monitor active agents, workload, and coordination health:

```bash
/team-status              # All agents
/team-status ai-engineer  # Specific agent
/team-status --detailed   # Detailed metrics
```

### `/pipeline-status` - CI/CD Monitoring

Check build, test, and deployment status:

```bash
/pipeline-status          # Quick status
/pipeline-status --watch  # Auto-refresh
```

Supports: GitHub Actions, GitLab CI, Jenkins, custom pipelines.

## Usage Examples

### Multi-Agent Workflow

Coordinate multiple agents for complex tasks:

```javascript
import { CoordinationClient } from 'mycelium/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();

// Create task chain
const task1 = await client.createTask({
  type: 'prepare-dataset',
  assigned_to: 'data-engineer'
});

const task2 = await client.createTask({
  type: 'train-model',
  assigned_to: 'ai-engineer',
  depends_on: [task1]
});

const task3 = await client.createTask({
  type: 'deploy-model',
  assigned_to: 'devops-engineer',
  depends_on: [task2]
});

// Monitor workflow
await client.monitorWorkflow([task1, task2, task3]);
```

### Real-time Events

Subscribe to agent events for real-time collaboration:

```javascript
// ai-engineer publishes training progress
await client.publishEvent('training:progress', {
  agent: 'ai-engineer',
  event: 'checkpoint_saved',
  step: 1000,
  loss: 0.042
});

// performance-engineer subscribes and evaluates
await client.subscribeEvents('training:progress', async (event) => {
  if (event.event === 'checkpoint_saved') {
    await evaluateCheckpoint(event.step);
  }
});
```

### Infrastructure Validation

Check infrastructure before critical operations:

```bash
# Validate before deployment
/infra-check --verbose

# Expected output:
# ✅ Redis               HEALTHY    (0.8ms latency)
# ✅ Temporal            HEALTHY    (3 workers active)
# ✅ GPU                 HEALTHY    (RTX 4090, 12GB free)
# ===================================
# Overall Status: HEALTHY ✅
```

## Documentation

### Core Modules

- **[Onboarding Guide](.mycelium/modules/onboarding.md)** - Installation, setup, configuration
- **[Coordination Deep Dive](.mycelium/modules/coordination.md)** - Dual-mode patterns, API, workflows
- **[Deployment Guide](.mycelium/modules/deployment.md)** - Docker, Kubernetes, production setup
- **[Agents Guide](.mycelium/modules/agents.md)** - Agent catalog, creation, integration
- **[Performance Analytics](.mycelium/modules/analytics.md)** - Telemetry, metrics, privacy

### Additional Resources

- **[Installation Guide](INSTALL.md)** - Detailed installation options
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute agents, commands, hooks
- **[Marketplace README](MARKETPLACE_README.md)** - Plugin marketplace submission
- **[Agent Structure](AGENT_STRUCTURE_CHANGE.md)** - Technical details on agent loading
- **[Privacy Policy](.mycelium/PRIVACY.md)** - Analytics privacy guarantees

## Architecture

### Coordination Substrate

```
┌───────────────────────────────────────┐
│     Application (Agents)              │
└───────────────┬───────────────────────┘
                │
┌───────────────▼───────────────────────┐
│  Coordination Library (auto-detect)  │
└───────────────┬───────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│ Redis  │  │TaskQueue│ │Markdown│
└────────┘  └────────┘  └────────┘
Real-time   Structured   Offline
```

### Performance Benchmarks

| Mode      | Latency | Throughput   | Agents | Overhead |
| --------- | ------- | ------------ | ------ | -------- |
| Redis     | 0.8ms   | 234K msg/min | 100+   | \<5%     |
| TaskQueue | 100ms   | 3K tasks/min | 50+    | ~10%     |
| Markdown  | 500ms   | 6K ops/min   | 20     | ~20%     |

**Agent Discovery Performance**:

- List all agents: 14ms (105x faster)
- Get agent (cached): 0.08ms (212x faster)
- Search: 6ms (24x faster)
- Memory: 820KB (67% reduction)

## Advanced Features

### Custom Agents

Create domain-specific agents:

```markdown
---
name: voice-specialist
description: Expert in voice cloning and TTS. Invoke for audio models, voice datasets, speech synthesis.
tools: Read, Write, Bash(python:*), Grep
---

You are a voice cloning specialist...

## Communication Protocol
Report progress to multi-agent-coordinator:
{
  "agent": "voice-specialist",
  "status": "completed",
  "voice_similarity": 0.89
}
```

Save to: `~/.claude/plugins/mycelium/agents/07-specialized-domains/voice-specialist.md`

### Custom Commands

Add slash commands:

```markdown
---
allowed-tools: Bash(*)
description: Check voice dataset quality
---
# Voice Dataset Check
1. Load dataset from $1
2. Calculate metrics
3. Report findings
```

Save to: `~/.claude/plugins/mycelium/commands/voice-check.md`

### Event Hooks

Automate workflows:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash.*pytest",
      "hooks": [{
        "type": "command",
        "command": "/infra-check"
      }]
    }]
  }
}
```

## Deployment

### Docker Compose

```bash
# Start complete stack (Redis + Temporal + monitoring)
docker-compose up -d

# Verify
docker-compose ps
/infra-check
```

### Kubernetes

```bash
# Deploy to cluster
kubectl create namespace mycelium
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/temporal-deployment.yaml

# Verify
kubectl get pods -n mycelium
```

📖 **Production Deployment**: See [.mycelium/modules/deployment.md](.mycelium/modules/deployment.md) for complete guide.

## Troubleshooting

### Agents Not Loading

```bash
# Restart Claude Code completely (important!)
# Exit and restart, not just window close

# Verify agent count
/agents | grep -c mycelium
# Should show 119+
```

### Coordination Issues

```bash
# Check active mode
/team-status  # Look for "Coordination mode: ..."

# Test Redis
redis-cli ping

# Force markdown fallback
export MYCELIUM_MODE=markdown
mkdir -p .claude/coordination/
```

### Performance Issues

```bash
# Check Redis latency
redis-cli --latency
# Should be <5ms

# Check coordination overhead
/team-status --detailed

# Check analytics for performance trends
uv run python scripts/health_check.py
```

## Contributing

We welcome contributions in these areas:

1. **New Agents** - Domain-specific specialists
1. **Slash Commands** - Productivity commands
1. **Event Hooks** - Automation patterns
1. **Documentation** - Examples and patterns
1. **Coordination Modes** - New substrate integrations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

### v1.1 (Next)

- Plugin marketplace submission
- Web dashboard for monitoring
- Advanced workflow patterns library
- Agent performance analytics dashboard

### v1.2 (Future)

- Multi-machine coordination
- Agent learning system
- Auto-scaling allocation
- Cost optimization

### v2.0 (Vision)

- Self-organizing agent networks
- Adaptive coordination strategies
- Emergent workflow discovery
- Cross-project knowledge sharing

## Credits

### Core Inspiration

**[VoltAgent Community](https://github.com/VoltAgent/awesome-claude-code-subagents)** - The foundational agents and
architectural patterns that seeded this mycelial network.

### What VoltAgent Provided

- High-quality specialist agents across multiple domains
- Proven architecture patterns for agent design
- Community-driven excellence and collaboration

### What Mycelium Added

- Dual-mode coordination substrate (Redis/TaskQueue/Markdown)
- Real-time pub/sub messaging
- Durable workflow orchestration (Temporal)
- Production-ready infrastructure (health checks, monitoring)
- Event-driven automation (hooks system)
- Fast agent discovery with lazy loading (105x speedup)
- Privacy-first performance analytics

**Thank you** to the VoltAgent community for fostering the Claude Code agent ecosystem. If you're exploring subagents,
visit: **https://github.com/VoltAgent/awesome-claude-code-subagents**

## Support

- **Documentation**: [.mycelium/modules/](.mycelium/modules/)
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Discussions**: https://github.com/gsornsen/mycelium/discussions

## License

MIT License - see [LICENSE](LICENSE) file

______________________________________________________________________

**Mycelium** - Growing distributed intelligence, one agent at a time 🍄
