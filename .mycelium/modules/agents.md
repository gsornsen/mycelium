# Mycelium Agents Guide

Complete guide to agent categories, discovery, development, communication protocols, and integration patterns in the
Mycelial network.

## Table of Contents

1. [Agent Architecture](#agent-architecture)
1. [Agent Categories](#agent-categories)
1. [Agent Discovery](#agent-discovery)
1. [Creating Custom Agents](#creating-custom-agents)
1. [Communication Protocols](#communication-protocols)
1. [Team Status Monitoring](#team-status-monitoring)
1. [Integration Patterns](#integration-patterns)
1. [Best Practices](#best-practices)

## Agent Architecture

### The Spores Metaphor

In mycelial networks, spores are specialized reproductive structures. Similarly, Mycelium agents are specialized units
focused on specific domains.

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
│   ├── javascript-expert     - JavaScript/Node.js
│   └── typescript-specialist - TypeScript development
├── Infrastructure
│   ├── devops-engineer       - CI/CD, deployment
│   ├── kubernetes-specialist - K8s orchestration
│   ├── security-auditor      - Security review
│   └── cloud-architect       - Cloud infrastructure
└── ... (130+ total agents)
```

### Agent Lifecycle

```
1. Discovery      → Claude Code loads agent definitions
2. Activation     → User invokes agent (@agent-name)
3. Execution      → Agent performs specialized task
4. Communication  → Report progress to coordinator
5. Completion     → Return results, update status
6. Deactivation   → Return to idle state
```

## Agent Categories

### 01 - Core Development

**Focus**: Primary programming languages and frameworks

Agents:

- `python-pro` - Python development, testing, packaging
- `ai-engineer` - Machine learning, deep learning, model training
- `javascript-expert` - JavaScript, Node.js, npm ecosystem
- `typescript-specialist` - TypeScript, type systems, tooling
- `rust-developer` - Rust development, memory safety, performance

**When to invoke**:

- Writing or reviewing code in these languages
- Building applications or libraries
- Debugging language-specific issues
- Performance optimization

### 02 - Language Specialists

**Focus**: Additional programming languages

Agents:

- `go-specialist` - Go development, concurrency, microservices
- `java-expert` - Java, Spring, JVM optimization
- `cpp-developer` - C++, performance, systems programming
- `kotlin-specialist` - Kotlin, Android, multiplatform
- `swift-developer` - Swift, iOS, SwiftUI

**When to invoke**:

- Multi-language projects
- Language-specific features or idioms
- Cross-platform development
- Legacy code maintenance

### 03 - Infrastructure

**Focus**: DevOps, cloud, and deployment

Agents:

- `devops-engineer` - CI/CD pipelines, automation, deployment
- `kubernetes-specialist` - K8s deployment, scaling, monitoring
- `docker-expert` - Containerization, Docker optimization
- `terraform-specialist` - Infrastructure as code
- `cloud-architect` - AWS/GCP/Azure architecture
- `security-auditor` - Security reviews, vulnerability scanning

**When to invoke**:

- Setting up CI/CD pipelines
- Deploying to production
- Scaling infrastructure
- Security audits

### 04 - Quality & Security

**Focus**: Testing, QA, security, performance

Agents:

- `qa-engineer` - Test strategy, test design, quality gates
- `security-auditor` - Security reviews, penetration testing
- `performance-engineer` - Performance profiling, optimization
- `test-automation-specialist` - Automated testing frameworks

**When to invoke**:

- Writing tests
- Performance analysis
- Security reviews
- Quality assurance

### 05 - Data & AI

**Focus**: Data engineering, ML, NLP, computer vision

Agents:

- `data-engineer` - Data pipelines, ETL, data quality
- `ml-engineer` - ML model training, deployment, monitoring
- `nlp-specialist` - Natural language processing, transformers
- `computer-vision-expert` - Image processing, object detection
- `data-scientist` - Statistical analysis, experimentation

**When to invoke**:

- Building data pipelines
- Training ML models
- Working with datasets
- Implementing AI features

### 06 - Developer Experience

**Focus**: CLI tools, documentation, MCP, tooling

Agents:

- `cli-developer` - Command-line tools, terminal UIs
- `documentation-engineer` - Technical writing, docs-as-code
- `mcp-specialist` - Model Context Protocol development
- `tooling-expert` - Build systems, developer tools

**When to invoke**:

- Creating CLI tools
- Writing documentation
- Building MCP servers
- Improving developer workflows

### 07 - Specialized Domains

**Focus**: Web3, IoT, game dev, audio/video

Agents:

- `web3-specialist` - Blockchain, smart contracts, dApps
- `iot-engineer` - Embedded systems, IoT protocols
- `game-developer` - Game engines, graphics, physics
- `audio-engineer` - Audio processing, DSP, TTS/ASR
- `video-engineer` - Video processing, streaming, codecs

**When to invoke**:

- Domain-specific projects
- Specialized technical requirements
- Industry-specific knowledge needed

### 08 - Business & Product

**Focus**: PM, UX, technical writing, marketing

Agents:

- `product-manager` - Requirements, roadmaps, prioritization
- `ux-designer` - User experience, interaction design
- `technical-writer` - Documentation, tutorials, API docs
- `marketing-specialist` - Content, SEO, growth

**When to invoke**:

- Product planning
- User research
- Creating content
- Marketing strategy

### 09 - Meta-Orchestration

**Focus**: Multi-agent coordination, workflows

Agents:

- `multi-agent-coordinator` - Coordinate multiple agents
- `workflow-orchestrator` - Orchestrate complex workflows
- `task-distributor` - Distribute work across agents
- `context-manager` - Manage shared context
- `performance-monitor` - Track agent performance
- `error-coordinator` - Handle errors, retries, recovery

**When to invoke**:

- Complex multi-agent tasks
- Workflow automation
- Coordination challenges
- Performance optimization

### 10 - Research & Analysis

**Focus**: Academic research, benchmarking, innovation

Agents:

- `research-analyst` - Literature review, research synthesis
- `benchmark-specialist` - Performance benchmarking, comparison
- `innovation-scout` - Emerging technologies, trends
- `academic-writer` - Research papers, citations

**When to invoke**:

- Research projects
- Benchmarking systems
- Exploring new technologies
- Writing research papers

### 11 - Claude Code

**Focus**: Plugin development, subagent creation

Agents:

- `plugin-developer` - Claude Code plugin development
- `subagent-creator` - Creating new subagent definitions
- `hook-specialist` - Event hooks, automation
- `claude-code-expert` - Claude Code internals, best practices

**When to invoke**:

- Extending Claude Code
- Creating plugins
- Building automation
- Deep Claude Code integration

## Agent Discovery

### Listing Available Agents

```bash
# List all agents
/agents

# List agents by category
ls ~/.claude/plugins/mycelium/agents/01-core-development/

# Count total agents
ls ~/.claude/plugins/mycelium/agents/*/*.md | wc -l
# → ~119 agents
```

### Searching for Agents

```bash
# Find agents by keyword
grep -r "kubernetes" ~/.claude/plugins/mycelium/agents/*/

# Find agents with specific tools
grep -r "tools:.*Bash" ~/.claude/plugins/mycelium/agents/*/

# Find agents by description
grep -r "machine learning" ~/.claude/plugins/mycelium/agents/*/
```

### Agent Metadata

Each agent has structured metadata:

```markdown
---
name: python-pro
description: Senior Python developer. Invoke when working with Python code, testing, packaging, or optimization.
tools: Read, Write, Bash(python:*,pytest:*,uv:*), Grep
category: core-development
keywords: python, pytest, packaging, optimization, async
---
```

**Metadata fields**:

- `name` - Agent identifier
- `description` - When to invoke this agent
- `tools` - Tool access permissions
- `category` - Agent category
- `keywords` - Search keywords

## Creating Custom Agents

### Agent Template

````markdown
---
name: your-specialist
description: Expert in specific domain. Invoke when working on X, Y, or Z.
tools: Read, Write, Bash(allowed-patterns:*), Grep
category: specialized-domains
keywords: domain, expertise, skills
---

You are a senior specialist in [domain] with expertise in:

1. [Skill 1]
2. [Skill 2]
3. [Skill 3]

## Core Responsibilities

When invoked, you should:

- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

## Communication Protocol

Report progress to multi-agent-coordinator using this format:

```json
{
  "agent": "your-specialist",
  "status": "in_progress|completed|failed",
  "progress": 0.0-1.0,
  "metrics": {
    "key_metric": "value"
  },
  "next_steps": ["step 1", "step 2"]
}
````

## Tool Usage

### Read

Use Read to examine existing code, configuration, and documentation.

### Write

Use Write to create or modify files. Always back up important files first.

### Bash

Execute domain-specific commands. Allowed patterns:

- `domain-cli:*` - Domain-specific CLI
- `tool-name:*` - Specific tools

### Grep

Search for patterns in code or documentation.

## Integration

Coordinate with these agents:

- `multi-agent-coordinator` - Overall coordination
- `related-agent-1` - Specific collaboration
- `related-agent-2` - Domain overlap

## Best Practices

1. Always verify input before processing
1. Provide clear progress updates
1. Handle errors gracefully
1. Document assumptions
1. Coordinate with relevant agents

## Examples

### Example 1: [Use case]

[Detailed example of agent usage]

### Example 2: [Use case]

[Another example]

````

### Saving Custom Agents

```bash
# Save to appropriate category
cat > ~/.claude/plugins/mycelium/agents/07-specialized-domains/your-specialist.md << 'EOF'
[agent definition]
EOF

# Restart Claude Code to load new agent
# Exit completely and restart
````

### Testing Custom Agents

```bash
# Verify agent loads
/agents | grep your-specialist

# Invoke agent
@your-specialist can you help with [task]?

# Check agent status (if using coordination)
/team-status your-specialist
```

## Communication Protocols

### Progress Reporting

Agents should report progress to `multi-agent-coordinator`:

```json
{
  "agent": "ai-engineer",
  "status": "in_progress",
  "task": "train-model",
  "progress": 0.67,
  "metrics": {
    "epoch": 2,
    "loss": 0.042,
    "accuracy": 0.96
  },
  "estimated_completion": "2025-10-17T02:30:00Z"
}
```

### Task Completion

Report completion with results:

```json
{
  "agent": "ai-engineer",
  "status": "completed",
  "task": "train-model",
  "result": {
    "checkpoint_path": "checkpoints/model-v1.pth",
    "final_loss": 0.038,
    "validation_accuracy": 0.97,
    "training_time_seconds": 3600
  }
}
```

### Error Reporting

Report failures with context:

```json
{
  "agent": "ai-engineer",
  "status": "failed",
  "task": "train-model",
  "error": {
    "type": "OutOfMemoryError",
    "message": "CUDA out of memory",
    "stack_trace": "...",
    "recovery_suggestions": [
      "Reduce batch size",
      "Use gradient checkpointing",
      "Use CPU training"
    ]
  }
}
```

### Using Coordination Library

```javascript
import { CoordinationClient } from 'mycelium/lib/coordination.js';

const client = new CoordinationClient();
await client.initialize();

// Report status
await client.storeAgentStatus('ai-engineer', {
  status: 'busy',
  active_tasks: ['train-model'],
  progress: 0.67
});

// Publish event (real-time)
await client.publishEvent('training:events', {
  agent: 'ai-engineer',
  event: 'checkpoint_saved',
  step: 1000
});

// Subscribe to events
await client.subscribeEvents('training:events', (event) => {
  console.log('Training event:', event);
});
```

## Team Status Monitoring

### Using /team-status Command

```bash
# Show all active agents
/team-status

# Specific agent
/team-status ai-engineer

# Detailed view
/team-status --detailed

# JSON output
/team-status --json
```

### Example Output

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

Recent Activity:
  [2025-10-17 00:15] ai-engineer started train-model
  [2025-10-17 00:10] data-engineer completed prepare-dataset
  [2025-10-17 00:05] devops-engineer started deploy-model
```

### Programmatic Monitoring

```javascript
// Monitor all agents
const agents = await client.listAgents();

for (const agentName of agents) {
  const status = await client.getAgentStatus(agentName);
  console.log(`${agentName}: ${status.status} (${status.active_tasks.length} tasks)`);
}

// Monitor specific metrics
setInterval(async () => {
  const stats = await client.getStats();
  console.log({
    active_agents: stats.agent_count,
    pending_tasks: stats.task_queue_size,
    coordination_latency: stats.avg_latency
  });
}, 60000);  // Every minute
```

## Integration Patterns

### Sequential Agent Chain

```javascript
// Task flows through agents in sequence
// data-engineer → ai-engineer → performance-engineer

const task1 = await client.createTask({
  type: 'prepare-dataset',
  assigned_to: 'data-engineer'
});

const task2 = await client.createTask({
  type: 'train-model',
  assigned_to: 'ai-engineer',
  depends_on: [task1]  // Wait for data-engineer
});

const task3 = await client.createTask({
  type: 'benchmark-model',
  assigned_to: 'performance-engineer',
  depends_on: [task2]  // Wait for ai-engineer
});
```

### Parallel Agent Execution

```javascript
// Multiple agents work in parallel
// [data-engineer, security-auditor, documentation-engineer] → coordinator

const tasks = [
  client.createTask({ type: 'prepare-data', assigned_to: 'data-engineer' }),
  client.createTask({ type: 'security-scan', assigned_to: 'security-auditor' }),
  client.createTask({ type: 'write-docs', assigned_to: 'documentation-engineer' })
];

// Execute in parallel
const results = await Promise.all(tasks);

// Coordinator aggregates results
await client.createTask({
  type: 'aggregate-results',
  assigned_to: 'multi-agent-coordinator',
  depends_on: results
});
```

### Event-Driven Collaboration

```javascript
// Agents react to events from other agents

// ai-engineer publishes training events
await client.publishEvent('training:progress', {
  agent: 'ai-engineer',
  event: 'epoch_completed',
  epoch: 1,
  loss: 0.042
});

// performance-engineer subscribes and evaluates
await client.subscribeEvents('training:progress', async (event) => {
  if (event.event === 'epoch_completed') {
    await evaluateCheckpoint(event.epoch);
  }
});

// error-coordinator watches for failures
await client.subscribeEvents('training:errors', async (error) => {
  await handleError(error);
});
```

### Hierarchical Coordination

```javascript
// Orchestrator delegates to specialists
// multi-agent-coordinator → [workflow-orchestrator, task-distributor]
//                             ↓
//                        specialist agents

// Top-level coordinator
await client.createTask({
  type: 'build-ml-pipeline',
  assigned_to: 'multi-agent-coordinator',
  subtasks: [
    { type: 'prepare-data', assigned_to: 'data-engineer' },
    { type: 'train-model', assigned_to: 'ai-engineer' },
    { type: 'deploy-model', assigned_to: 'devops-engineer' }
  ]
});

// Coordinator monitors and adjusts
const workflow = await client.createWorkflow('ml-pipeline', {
  coordinator: 'multi-agent-coordinator',
  agents: ['data-engineer', 'ai-engineer', 'devops-engineer']
});
```

## Best Practices

### Agent Design

1. **Single Responsibility**: Each agent should focus on one domain
1. **Clear Invocation Criteria**: Description should clearly state when to invoke
1. **Minimal Tool Access**: Request only necessary tools
1. **Explicit Communication**: Always report progress to coordinator
1. **Error Handling**: Handle errors gracefully, suggest recovery

### Communication

1. **Structured Messages**: Use JSON for machine-readable communication
1. **Progress Updates**: Report progress regularly (every 30-60 seconds for long tasks)
1. **Event Publishing**: Publish events for important milestones
1. **Status Cleanup**: Remove agent status on exit

### Coordination

1. **Use Coordination Library**: Don't implement coordination from scratch
1. **Handle Mode Degradation**: Support all coordination modes
1. **Respect Dependencies**: Wait for prerequisite tasks to complete
1. **Avoid Deadlocks**: Don't create circular dependencies

### Performance

1. **Minimize Coordination Overhead**: Batch operations when possible
1. **Use Pub/Sub for Events**: Don't poll for status updates
1. **Clean Up Resources**: Remove old tasks and status
1. **Monitor Metrics**: Track coordination latency and throughput

### Security

1. **Principle of Least Privilege**: Request minimal tool access
1. **Validate Input**: Always validate task payloads
1. **Sanitize Commands**: Escape shell commands properly
1. **Audit Logs**: Log all agent actions

## Next Steps

- **Read [onboarding.md](./onboarding.md)** - Install and configure Mycelium
- **Read [coordination.md](./coordination.md)** - Learn coordination patterns
- **Read [deployment.md](./deployment.md)** - Deploy to production
- **See [examples/](../../docs/examples/)** - Complete agent examples
- **See [CONTRIBUTING.md](../../CONTRIBUTING.md)** - Submit custom agents

## Support

- **Documentation**: [.mycelium/modules/](./)
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Main README**: [README.md](../../README.md)
