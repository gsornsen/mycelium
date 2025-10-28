# M08: Documentation

## Overview

**Duration**: 3 days **Dependencies**: M04 (onboarding), M05 (deployment), M06 (testing) **Blocks**: M10 (polish &
release) **Lead Agent**: technical-writer **Support Agents**: documentation-engineer, python-pro **Parallel With**: M07
(Config Management), M09 (Testing Suite)

## Why This Milestone

Comprehensive documentation transforms complex infrastructure into accessible tools. While the codebase is technically
complete after M04-M06, users cannot leverage Mycelium without clear guides, examples, and troubleshooting resources.
This milestone ensures every user—from beginners to power users—can successfully onboard, deploy, and maintain their
coordination infrastructure.

Well-crafted documentation:

- Reduces support burden through self-service
- Accelerates onboarding with clear tutorials
- Builds confidence through worked examples
- Prevents errors with troubleshooting guides
- Enables advanced usage through API reference

## Requirements

### Functional Requirements (FR)

- **FR-8.1**: Installation guide for Linux, macOS, Windows (WSL2)
- **FR-8.2**: Getting started tutorial with complete walkthrough
- **FR-8.3**: Reference documentation for all slash commands
- **FR-8.4**: Troubleshooting guide addressing common issues
- **FR-8.5**: API reference for programmatic usage

### Technical Requirements (TR)

- **TR-8.1**: Use Markdown format for all documentation
- **TR-8.2**: Include code examples that are tested and working
- **TR-8.3**: Provide screenshots for key UI interactions
- **TR-8.4**: Link related documentation sections
- **TR-8.5**: Version documentation clearly (Mycelium v1.0)

### Integration Requirements (IR)

- **IR-8.1**: Reference M04 wizard screens and flows
- **IR-8.2**: Reference M05 deployment generation examples
- **IR-8.3**: Reference M06 coordination testing patterns
- **IR-8.4**: Reference M07 configuration management commands

### Compliance Requirements (CR)

- **CR-8.1**: Accessibility - screen reader friendly, clear structure
- **CR-8.2**: Accuracy - all examples must work as documented
- **CR-8.3**: Completeness - every feature has corresponding documentation
- **CR-8.4**: Maintainability - documentation structure supports future updates

## Tasks

### Task 8.1: Create Installation Guide

**Agent**: technical-writer, documentation-engineer **Effort**: 6 hours

**Description**: Write comprehensive installation guide covering all supported platforms with prerequisites,
installation steps, and verification.

**Deliverable**:

````markdown
# Installation Guide

## Prerequisites

### Required

- **Python 3.11+**: Modern Python with type hints and async support
- **uv**: Package manager for Python dependencies
- **Git**: Version control

### Optional (Based on Deployment Method)

- **Docker**: v20.10+ for containerized deployments
  - **Docker Compose**: v2.0+ (included with Docker Desktop)
- **Redis**: v7+ (if not using Docker)
- **PostgreSQL**: v14+ (if not using Docker)
- **Temporal**: v1.20+ (if not using Docker)

### Platform-Specific Requirements

#### Linux

- Ubuntu 20.04+, Debian 11+, Fedora 36+, or equivalent
- systemd (for service management with Justfile)
- Build tools: `sudo apt install build-essential` (Debian/Ubuntu)

#### macOS

- macOS 12 (Monterey) or later
- Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

#### Windows

- Windows 10/11 with WSL2 enabled
- Ubuntu 20.04+ in WSL2
- Follow Linux instructions inside WSL2

## Installation Steps

### 1. Install Python 3.11+

#### Linux (apt-based)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
````

#### macOS (Homebrew)

```bash
brew install python@3.11
```

#### Windows (WSL2)

```bash
# Inside WSL2 Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # Add to PATH
```

Verify installation:

```bash
uv --version  # Should show 0.1.0 or later
```

### 3. Clone Mycelium Repository

```bash
cd ~/git  # Or your preferred projects directory
git clone https://github.com/your-org/mycelium.git
cd mycelium
```

### 4. Install Mycelium

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows WSL2: source .venv/bin/activate
uv sync
```

### 5. Install Optional Services (Choose One Method)

#### Option A: Docker Compose (Recommended)

Install Docker:

- **Linux**: Follow [Docker Engine installation](https://docs.docker.com/engine/install/)
- **macOS**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Windows**: Install [Docker Desktop with WSL2](https://docs.docker.com/desktop/windows/wsl/)

Verify:

```bash
docker --version        # Should show 20.10+
docker-compose --version  # Should show 2.0+
```

#### Option B: Manual Installation (Bare-metal)

**Redis:**

```bash
# Linux
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis
```

**PostgreSQL:**

```bash
# Linux
sudo apt install postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

# macOS
brew install postgresql@16
brew services start postgresql@16
```

**Temporal** (Docker recommended for Temporal):

```bash
docker run -d -p 7233:7233 temporalio/auto-setup:latest
```

### 6. Verify Installation

```bash
# Check Python
python3 --version

# Check uv
uv --version

# Check Docker (if using)
docker --version
docker-compose --version

# Check services (if manual install)
redis-cli ping  # Should return PONG
psql --version
```

## Post-Installation

### Set Up Claude Code Integration

1. Ensure Mycelium plugin is installed in `~/.claude/plugins/mycelium-core`
1. Verify commands are available:
   ```bash
   # Inside Claude Code
   /help mycelium
   ```

### Run Onboarding

```bash
/mycelium-onboarding
```

Follow the interactive wizard to configure your infrastructure.

## Troubleshooting Installation

### Python Version Issues

**Problem**: `python3.11: command not found`

**Solution**:

```bash
# Linux: Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11

# macOS: Use Homebrew
brew install python@3.11

# Verify
python3.11 --version
```

### Docker Permission Issues

**Problem**: `permission denied while trying to connect to the Docker daemon socket`

**Solution**:

```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login

# Verify
docker ps
```

### uv Installation Fails

**Problem**: `curl: command not found` or `Failed to download uv`

**Solution**:

```bash
# Install curl first
sudo apt install curl  # Linux
brew install curl      # macOS

# Retry uv installation
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Next Steps

- [Getting Started Tutorial](./getting-started.md)
- [Command Reference](./command-reference.md)
- [Configuration Guide](./configuration.md)

````

**Acceptance Criteria**:
- [ ] Covers all three platforms (Linux, macOS, Windows/WSL2)
- [ ] Lists all prerequisites with version requirements
- [ ] Provides step-by-step installation instructions
- [ ] Includes verification steps
- [ ] Has troubleshooting section for common issues

### Task 8.2: Write Getting Started Tutorial

**Agent**: technical-writer, python-pro
**Effort**: 6 hours

**Description**: Create comprehensive getting started tutorial walking users through first-time setup, service selection, deployment, and validation.

**Deliverable Structure**:

```markdown
# Getting Started with Mycelium

## Overview

This tutorial walks you through setting up your first Mycelium multi-agent coordination infrastructure in under 15 minutes.

## What You'll Build

By the end of this tutorial, you'll have:
- ✓ Configured Mycelium infrastructure
- ✓ Running coordination services (Redis, TaskQueue)
- ✓ Tested pub/sub and task queue patterns
- ✓ Deployed with Docker Compose or Justfile

## Prerequisites

- Mycelium installed ([Installation Guide](./installation.md))
- Docker installed (recommended) or manual services
- 15 minutes of time

## Step 1: Run Onboarding Wizard

Launch the interactive onboarding wizard:

```bash
/mycelium-onboarding
````

### Welcome Screen

You'll see detected services:

```
🔍 System Detection Results
┌─────────┬────────────┬─────────────────┐
│ Service │ Status     │ Details         │
├─────────┼────────────┼─────────────────┤
│ Docker  │ ✓ Available│ 24.0.5          │
│ Redis   │ ○ Available│ localhost:6379  │
│ ...     │ ...        │ ...             │
└─────────┴────────────┴─────────────────┘
```

Press Enter to continue.

### Service Selection

Choose coordination services:

```
Select services (Space to toggle, Enter to confirm):
[X] Redis - Pub/Sub messaging and state management
[X] TaskQueue - Task distribution (MCP)
[ ] PostgreSQL - Persistent data storage
[ ] Temporal - Workflow orchestration
```

**Recommended for beginners**: Select Redis + TaskQueue

### Deployment Method

Choose how to deploy:

```
Choose deployment method:
> Docker Compose (Recommended) - Containerized with auto dependency management
  Justfile - Bare-metal with manual service management
```

**Recommended**: Docker Compose

### Project Metadata

Enter project details:

```
Project name: mycelium
Project description: Multi-agent coordination system
```

### Configuration Review

Review your selections:

```
Configuration Review
┌──────────────────┬────────────────────┐
│ Setting          │ Value              │
├──────────────────┼────────────────────┤
│ Project Name     │ mycelium           │
│ Deployment Method│ docker-compose     │
│ Services Enabled │ redis, taskqueue   │
└──────────────────┴────────────────────┘

Save this configuration? (Y/n)
```

Press Y to save.

## Step 2: Generate Deployment Files

```bash
/mycelium-generate
```

This creates:

- `docker-compose.yml` - Service definitions
- `.env` - Secrets (gitignored)
- `.env.example` - Template for team

## Step 3: Start Services

### Docker Compose

```bash
docker-compose up -d
```

Verify services:

```bash
docker-compose ps
```

You should see:

```
NAME              STATUS    PORTS
mycelium-redis    Up        0.0.0.0:6379->6379/tcp
```

### Justfile (Alternative)

```bash
just up
```

Verify:

```bash
just status
```

## Step 4: Test Coordination

Run functional tests:

```bash
/mycelium-test --pattern pubsub
```

Expected output:

```
Running pub/sub tests...

✓ test_pubsub_basic_message_delivery: passed (45.2ms)
✓ test_pubsub_multiple_subscribers: passed (78.1ms)

COORDINATION TEST REPORT
========================
Total Tests: 2
Passed: 2
Failed: 0
Success Rate: 100.0%
```

## Step 5: View Configuration

```bash
/mycelium-configuration show
```

## Common Next Steps

### Add More Services

Edit configuration:

```bash
/mycelium-configuration edit
```

Enable PostgreSQL or Temporal, then regenerate:

```bash
/mycelium-generate --force
docker-compose up -d
```

### Test Other Patterns

```bash
/mycelium-test --pattern taskqueue
/mycelium-test --pattern all
```

### View Logs

```bash
# Docker Compose
docker-compose logs -f redis

# Justfile
just logs redis
```

## Troubleshooting

\[Include troubleshooting for common getting-started issues\]

## Next Steps

- [Command Reference](./command-reference.md) - All available commands
- [Configuration Guide](./configuration.md) - Detailed configuration options
- [Coordination Patterns](./coordination-patterns.md) - Learn coordination patterns

````

**Acceptance Criteria**:
- [ ] Step-by-step tutorial with clear instructions
- [ ] Screenshots of key wizard screens
- [ ] Expected outputs shown for each step
- [ ] Covers both Docker Compose and Justfile paths
- [ ] Includes verification steps
- [ ] Links to related documentation

### Task 8.3: Document All Slash Commands

**Agent**: technical-writer, documentation-engineer
**Effort**: 4 hours

**Description**: Create comprehensive reference documentation for all Mycelium slash commands with usage, options, examples.

**Deliverable Structure**:

```markdown
# Command Reference

## Overview

Mycelium provides four slash commands for infrastructure management:

1. `/mycelium-onboarding` - Interactive setup wizard
2. `/mycelium-generate` - Deployment file generation
3. `/mycelium-configuration` - Configuration management
4. `/mycelium-test` - Coordination testing

## /mycelium-onboarding

Launch interactive wizard to configure Mycelium infrastructure.

### Usage

```bash
/mycelium-onboarding [options]
````

### Options

| Option              | Description               | Default     |
| ------------------- | ------------------------- | ----------- |
| `--project-local`   | Save to project directory | User config |
| `--force`           | Skip resume prompt        | false       |
| `--no-cache`        | Re-run service detection  | false       |
| `--non-interactive` | Use defaults (CI/CD)      | false       |

### Examples

```bash
# Standard onboarding
/mycelium-onboarding

# Fresh start
/mycelium-onboarding --force

# Project-specific config
/mycelium-onboarding --project-local

# CI/CD mode
/mycelium-onboarding --non-interactive
```

### When to Use

- First-time Mycelium setup
- Adding/removing services
- Changing deployment method
- Resetting configuration

### Related Commands

- `/mycelium-configuration show` - View current config
- `/mycelium-generate` - Generate deployment after onboarding

______________________________________________________________________

## /mycelium-generate

Generate deployment files from configuration.

\[Full documentation for each command...\]

______________________________________________________________________

## /mycelium-configuration

\[Documentation for configuration subcommands: show, edit, validate, init...\]

______________________________________________________________________

## /mycelium-test

\[Documentation for testing command with all patterns...\]

````

**Acceptance Criteria**:
- [ ] All commands documented with usage, options, examples
- [ ] "When to Use" section for each command
- [ ] Related commands linked
- [ ] Troubleshooting for common issues
- [ ] Consistent formatting across all commands

### Task 8.4: Create Troubleshooting Guide

**Agent**: technical-writer, debugger
**Effort**: 6 hours

**Description**: Compile troubleshooting guide addressing common issues users encounter during setup, configuration, and operation.

**Deliverable Structure**:

```markdown
# Troubleshooting Guide

## Service Detection Issues

### Redis Not Detected

**Symptom**: Wizard shows "Redis: ✗ Not Found"

**Causes**:
1. Redis not installed
2. Redis not running
3. Non-standard port

**Solutions**:

1. **Install Redis:**
   ```bash
   # Docker
   docker run -d -p 6379:6379 redis:7-alpine

   # Linux
   sudo apt install redis-server
   sudo systemctl start redis-server

   # macOS
   brew install redis
   brew services start redis
````

2. **Check Redis status:**

   ```bash
   redis-cli ping  # Should return PONG
   ```

1. **Non-standard port:**

   ```bash
   # Tell wizard about custom port
   export REDIS_PORT=6380
   /mycelium-onboarding --no-cache
   ```

______________________________________________________________________

## Docker Compose Issues

### Healthcheck Failures

\[Detailed troubleshooting for each category\]

______________________________________________________________________

## Configuration Issues

\[Configuration-specific troubleshooting\]

______________________________________________________________________

## Testing Issues

\[Test-specific troubleshooting\]

````

**Acceptance Criteria**:
- [ ] Covers all major issue categories
- [ ] Each issue has symptoms, causes, solutions
- [ ] Solutions include commands/code examples
- [ ] Cross-references relevant documentation
- [ ] Organized by user workflow (setup → config → operation)

### Task 8.5: Write API Reference Documentation

**Agent**: documentation-engineer, python-pro
**Effort**: 6 hours

**Description**: Create API reference for programmatic usage of Mycelium components (ConfigManager, generators, test orchestrator).

**Deliverable Structure**:

```markdown
# API Reference

## Overview

Mycelium can be used programmatically for advanced integration and automation.

## Configuration Management

### ConfigManager

Manage configuration loading, saving, and migration.

#### Methods

##### `load(prefer_project: bool = True) -> MyceliumConfig`

Load configuration from file with hierarchical precedence.

**Parameters:**
- `prefer_project` (bool): Check project config before user config

**Returns:**
- `MyceliumConfig`: Loaded configuration

**Raises:**
- `FileNotFoundError`: No configuration file found

**Example:**
```python
from mycelium_onboarding.config.manager import ConfigManager

# Load configuration
config = ConfigManager.load()
print(f"Project: {config.project_name}")
````

\[Continue with all public APIs...\]

## Deployment Generation

### DockerComposeGenerator

\[API documentation for generators...\]

## Testing Framework

### TestOrchestrator

\[API documentation for test orchestrator...\]

```

**Acceptance Criteria**:
- [ ] All public APIs documented
- [ ] Parameters, returns, raises documented
- [ ] Usage examples for each API
- [ ] Type hints included
- [ ] Links between related APIs

## Exit Criteria

- [ ] Installation guide complete for all platforms
- [ ] Getting started tutorial tested and validated
- [ ] All slash commands documented with examples
- [ ] Troubleshooting guide covers common issues
- [ ] API reference complete for public interfaces
- [ ] All code examples tested and working
- [ ] Screenshots captured for key UI interactions
- [ ] Documentation reviewed by technical-writer + python-pro
- [ ] External review by target user personas

## Deliverables

1. **User Guides**:
   - `docs/installation.md`
   - `docs/getting-started.md`
   - `docs/command-reference.md`
   - `docs/troubleshooting.md`

2. **API Documentation**:
   - `docs/api/configuration-api.md`
   - `docs/api/generator-api.md`
   - `docs/api/testing-api.md`

3. **Additional Docs**:
   - `docs/coordination-patterns.md` - Pattern explanations
   - `docs/deployment-methods.md` - Docker Compose vs Justfile
   - `docs/faq.md` - Frequently asked questions

4. **Visual Assets**:
   - Screenshots in `docs/images/`
   - Architecture diagrams
   - Flow charts for key processes

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Documentation becomes outdated | Medium | High | Version docs, automated example testing |
| Missing edge cases in troubleshooting | Medium | Medium | Collect user feedback, iterate |
| Examples don't work | Low | High | Test all examples in CI/CD |
| Screenshots inconsistent | Low | Low | Use same theme/environment for all captures |

## Dependencies for Next Milestones

**M10 (Polish & Release)** requires:
- Complete documentation for release
- User guides for onboarding new users
- Troubleshooting guide for support reduction
- API reference for advanced users

---

**Milestone Owner**: technical-writer
**Reviewers**: documentation-engineer, python-pro
**Status**: Ready for Implementation
**Created**: 2025-10-13
**Target Completion**: Day 19 (parallel with M07, M09, longest of the three)
```
