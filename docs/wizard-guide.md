# Interactive Onboarding Wizard Guide

Complete guide to using the Mycelium interactive onboarding wizard for seamless project setup.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Wizard Screens](#wizard-screens)
- [Setup Modes](#setup-modes)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Overview

The `mycelium init` wizard provides an interactive, step-by-step onboarding experience that:

- **Detects** available services (Docker, Redis, PostgreSQL, Temporal, GPU)
- **Configures** your environment with smart defaults
- **Validates** all inputs to prevent errors
- **Generates** deployment-ready configuration files
- **Resumes** automatically if interrupted

### Key Features

- **Two Setup Modes**: Quick (recommended) or Custom (advanced)
- **Auto-Detection**: Scans your system for available services
- **Resume Capability**: Never lose your progress
- **Validation**: Ensures all settings are valid before saving
- **Multiple Deployment Options**: Docker Compose, Kubernetes, or systemd

### Time Estimate

- **Quick Setup**: 2-3 minutes
- **Custom Setup**: 5-10 minutes (with advanced configuration)

## Getting Started

### Prerequisites

Before running the wizard, ensure:

1. You have Mycelium installed: `pip install mycelium-onboarding`
1. You have appropriate permissions to detect services
1. (Optional) Docker is installed if you want container-based deployment

### First-Time Setup

Start the wizard with default settings:

```bash
mycelium init
```

This will:

1. Welcome you to Mycelium
1. Auto-detect available services
1. Guide you through configuration
1. Save your settings

### Quick Start Example

```bash
# Start fresh wizard
mycelium init

# Follow the prompts:
# 1. Select "Quick Setup" (recommended)
# 2. Review detected services
# 3. Choose services to enable
# 4. Select deployment method
# 5. Review and confirm

# Configuration saved!
```

## Wizard Screens

The wizard consists of 7 screens that guide you through setup:

### 1. Welcome Screen

**Purpose**: Choose your setup mode and understand what the wizard does.

**Options**:

- **Quick Setup**: Recommended for first-time users, uses smart defaults
- **Custom Setup**: Advanced configuration with all options
- **Exit**: Cancel wizard

**What to Choose**:

- First time? → **Quick Setup**
- Need custom ports or advanced settings? → **Custom Setup**

**Example**:

```
╭─────────────────────────────────────────────────────────╮
│                 Mycelium Setup Wizard                   │
├─────────────────────────────────────────────────────────┤
│        Welcome to Mycelium!                             │
│                                                          │
│  Mycelium is a distributed multi-agent coordination     │
│  system for AI-powered workflows.                       │
│                                                          │
│  Estimated time: 2-5 minutes                            │
╰─────────────────────────────────────────────────────────╯

? How would you like to proceed?
  > Quick Setup (recommended for first-time users)
    Custom Setup (advanced configuration options)
    Exit wizard
```

### 2. Detection Screen

**Purpose**: Automatically detect available services on your system.

**What It Detects**:

- Docker daemon and version
- Redis instances and ports
- PostgreSQL instances
- Temporal server
- GPU availability (NVIDIA/AMD)

**Actions**:

- View detection results in a formatted table
- Option to re-run detection if needed

**Example Output**:

```
Detecting Services...

╭─────────────────────────────────────────────────╮
│              Detection Results                  │
├─────────────┬───────────┬──────────────────────┤
│ Service     │  Status   │ Details              │
├─────────────┼───────────┼──────────────────────┤
│ Docker      │ ✓ Found   │ Version 24.0.0       │
│ Redis       │ ✓ Found   │ 1 instance on 6379   │
│ PostgreSQL  │ ✓ Found   │ 1 instance           │
│ Temporal    │ ✗ Not     │ Not running          │
│ GPU         │ ✗ Not     │ No GPU detected      │
╰─────────────┴───────────┴──────────────────────╯

Detection completed in 2.35s

? Would you like to re-run detection? (y/N)
```

### 3. Services Screen

**Purpose**: Select which services to enable and configure service-specific settings.

**Available Services**:

- **Redis**: Message broker and caching
- **PostgreSQL**: Primary database
- **Temporal**: Workflow orchestration

**Configuration Prompts**:

- PostgreSQL database name (if enabled)
- Temporal namespace (if enabled)

**Tips**:

- Services detected on your system are pre-selected
- At least one service must be enabled
- Database names cannot contain hyphens

**Example**:

```
Select Services to Enable

? Select services to enable (space to select, enter to confirm):
  ✓ Redis - Message broker and caching
  ✓ PostgreSQL - Primary database
  ○ Temporal - Workflow orchestration

? PostgreSQL database name: mycelium_db
```

### 4. Deployment Screen

**Purpose**: Choose how to deploy and manage your services.

**Deployment Methods**:

1. **Docker Compose** (Recommended)

   - Best for development and small deployments
   - Requires Docker installed
   - Easy to manage with `docker-compose` commands

1. **Kubernetes**

   - Best for production and scalability
   - Requires Kubernetes cluster
   - Advanced orchestration features

1. **systemd**

   - Native Linux services
   - No Docker required
   - System-level integration

**Additional Options**:

- **Auto-start**: Start services on system boot

**Example**:

```
Deployment Configuration

? Select deployment method:
  > Docker Compose - Best for development
    Kubernetes - Best for production
    systemd - Native Linux services

? Auto-start services on system boot? (Y/n)
```

### 5. Advanced Configuration (Custom Mode Only)

**Purpose**: Fine-tune service settings and ports.

**Skipped In**: Quick Setup mode

**Available Options**:

- Data persistence enable/disable
- Custom port configuration:
  - Redis port (default: 6379)
  - PostgreSQL port (default: 5432)
  - Temporal UI port (default: 8080)
  - Temporal frontend port (default: 7233)

**When to Use**:

- Need non-standard ports
- Port conflicts with existing services
- Disable persistence for testing

**Example**:

```
Advanced Configuration

? Enable data persistence for databases? (Y/n)

? Redis port: 6379
? PostgreSQL port: 5432
```

### 6. Review Screen

**Purpose**: Review all settings before finalizing configuration.

**Actions Available**:

1. **Confirm**: Save configuration and complete wizard
1. **Edit**: Jump back to specific screen to change settings
1. **Cancel**: Exit without saving

**Review Table Example**:

```
Review Your Configuration

╭─────────────────────────────────────────────────╮
│ Setting              │ Value                    │
├──────────────────────┼──────────────────────────┤
│ Project Name         │ my-project               │
│ Deployment Method    │ docker-compose           │
│ Auto-start           │ Yes                      │
│ Enabled Services     │ redis, postgres          │
│   Redis Port         │ 6379                     │
│   PostgreSQL Port    │ 5432                     │
│   PostgreSQL Database│ my_project_db            │
│ Data Persistence     │ Enabled                  │
╰──────────────────────┴──────────────────────────╯

? What would you like to do?
  > Confirm and create configuration
    Edit a setting
    Cancel wizard
```

### 7. Completion Screen

**Purpose**: Confirm successful setup and show next steps.

**Information Provided**:

- Path to saved configuration file
- Next steps to start using Mycelium
- Helpful commands

**Example**:

```
╭─────────────────────────────────────────────────╮
│          ✓ Configuration Complete!             │
├─────────────────────────────────────────────────┤
│ Your configuration has been saved to:           │
│ /home/user/.config/mycelium/config.yaml        │
│                                                  │
│ Next Steps:                                     │
│ 1. Review: mycelium config show                │
│ 2. Start services: mycelium deploy start       │
│ 3. Check status: mycelium status               │
│                                                  │
│ For help: mycelium --help                      │
╰─────────────────────────────────────────────────╯
```

## Setup Modes

### Quick Setup (Recommended)

**Best For**: First-time users, standard deployments

**Features**:

- Smart defaults based on detection
- Skips advanced configuration
- Fastest path to running system
- Uses standard ports

**Flow**:

1. Welcome → 2. Detection → 3. Services → 4. Deployment → 6. Review → 7. Complete

**Time**: 2-3 minutes

### Custom Setup (Advanced)

**Best For**: Advanced users, custom configurations, production deployments

**Features**:

- Full control over all settings
- Custom port configuration
- Advanced options (persistence, etc.)
- All deployment methods available

**Flow**:

1. Welcome → 2. Detection → 3. Services → 4. Deployment → 5. Advanced → 6. Review → 7. Complete

**Time**: 5-10 minutes

## Common Scenarios

### Scenario 1: First-Time User (Quick Setup)

**Goal**: Get started with Mycelium quickly.

**Steps**:

```bash
mycelium init
```

1. Select "Quick Setup"
1. Review detected services (auto-selected)
1. Enter project name: `my-first-project`
1. Keep default services or adjust selection
1. Choose "Docker Compose" deployment
1. Enable auto-start: Yes
1. Review and confirm

**Result**: Ready-to-use configuration in ~2 minutes

### Scenario 2: Production Setup (Custom Mode)

**Goal**: Configure Mycelium for production with custom ports.

**Steps**:

```bash
mycelium init
```

1. Select "Custom Setup"
1. Review detection results
1. Enter project name: `production-app`
1. Select all needed services
1. Configure PostgreSQL database: `prod_db`
1. Configure Temporal namespace: `production`
1. Choose "Kubernetes" deployment
1. Enable auto-start: Yes
1. **Advanced Configuration**:
   - Enable persistence: Yes
   - Redis port: 6380 (avoid conflict)
   - PostgreSQL port: 5433 (avoid conflict)
1. Review and confirm

**Result**: Production-ready configuration with custom ports

### Scenario 3: Resume Interrupted Session

**Goal**: Continue wizard after interruption (Ctrl+C, error, or closed terminal).

**Steps**:

```bash
mycelium init
```

- Wizard detects saved state
- Prompts: "Found existing wizard session. Would you like to resume?"
- Select: Yes
- Continues from last completed step

**Alternative**:

```bash
# Force resume
mycelium init --resume

# Start fresh (ignore saved state)
mycelium init --no-resume
```

### Scenario 4: Minimal Setup (Redis Only)

**Goal**: Set up only Redis for testing.

**Steps**:

```bash
mycelium init
```

1. Select "Quick Setup"
1. Wait for detection
1. Enter project name: `redis-test`
1. **Deselect** all services except Redis (use spacebar)
1. Choose "Docker Compose"
1. Review and confirm

**Result**: Minimal configuration with only Redis enabled

### Scenario 5: Edit Configuration After Review

**Goal**: Change service selection after reviewing.

**Steps**:

```bash
mycelium init
# ... complete wizard until Review screen
```

At Review screen:

1. Select "Edit a setting"
1. Choose "Services"
1. Update service selection
1. Wizard jumps back to Services screen
1. Make changes
1. Flow continues to Review again
1. Confirm

**Result**: Updated configuration with edited settings

### Scenario 6: Clear Corrupted State

**Goal**: Start fresh if wizard state is corrupted.

**Steps**:

```bash
# Clear state and start fresh
mycelium init --reset

# Confirms clearing saved state
# Starts new wizard from beginning
```

**When to Use**:

- Wizard won't resume properly
- Saved state is corrupted
- Want to start completely fresh

## Troubleshooting

### Problem: Wizard Won't Start

**Symptoms**:

- Command hangs
- No output displayed
- Immediate exit

**Solutions**:

1. Check Python version: `python --version` (requires 3.10+)
1. Verify installation: `pip show mycelium-onboarding`
1. Check permissions: Ensure you can write to config directory
1. Clear corrupted state: `mycelium init --reset`

### Problem: Detection Takes Too Long

**Symptoms**:

- Detection screen hangs for >30 seconds
- No progress indicator movement

**Solutions**:

1. Check network connectivity (some services need network)
1. Verify Docker is running: `docker ps`
1. Interrupt and start fresh: Ctrl+C, then `mycelium init --reset`
1. Skip detection issues: Detection failures are non-fatal

### Problem: Port Conflicts

**Symptoms**:

- Validation error: "Port conflicts with..."
- Cannot complete wizard

**Solutions**:

1. Use Custom Setup mode for port configuration
1. Change conflicting ports in Advanced Configuration
1. Check running services: `netstat -tulpn | grep <port>`
1. Stop conflicting services before setup

### Problem: Database Name Invalid

**Symptoms**:

- Validation error: "Database name must start with a letter"
- Error: "Database name cannot contain hyphens"

**Solutions**:

1. Use underscores instead of hyphens: `my_database`
1. Start with a letter: `db_123` not `123_db`
1. Use only alphanumeric and underscores
1. Keep under 63 characters (PostgreSQL limit)

### Problem: Resume Not Working

**Symptoms**:

- Resume prompt doesn't appear
- Saved state not loaded

**Solutions**:

1. Check state file exists: `~/.local/state/mycelium/wizard_state.json`
1. Force resume: `mycelium init --resume`
1. Clear and restart: `mycelium init --reset`
1. Check file permissions on state directory

### Problem: Configuration Not Saved

**Symptoms**:

- Wizard completes but config missing
- Commands don't find configuration

**Solutions**:

1. Check config location: `mycelium config show`
1. Verify directory exists: `~/.config/mycelium/`
1. Check write permissions on config directory
1. Re-run wizard: `mycelium init --no-resume`

### Problem: Services Not Detected

**Symptoms**:

- Detection shows "Not Found" for running services
- All services appear unavailable

**Solutions**:

1. **Docker**: Ensure daemon is running: `docker ps`
1. **Redis**: Check it's listening: `redis-cli ping`
1. **PostgreSQL**: Verify it's running: `pg_isready`
1. **Permissions**: May need elevated permissions for detection
1. **Network**: Some detection requires network access
1. **Re-run**: Use "Would you like to re-run detection?" option

## FAQ

### General Questions

**Q: How long does the wizard take?**

A: Quick Setup takes 2-3 minutes. Custom Setup takes 5-10 minutes depending on your choices.

**Q: Can I change configuration later?**

A: Yes! Use `mycelium config set <key> <value>` to update settings or re-run `mycelium init` to reconfigure.

**Q: Is the wizard required?**

A: No, you can manually create configuration files. The wizard just makes it easier and validates settings.

**Q: What happens to my data if I re-run the wizard?**

A: The wizard backs up existing configuration before overwriting. Your service data is unchanged.

### Resume & State Questions

**Q: Where is wizard state saved?**

A: In `~/.local/state/mycelium/wizard_state.json` (XDG_STATE_HOME).

**Q: How do I clear saved state?**

A: Run `mycelium init --reset` or manually delete `~/.local/state/mycelium/wizard_state.json`.

**Q: Can I resume from a different machine?**

A: No, wizard state is local. However, you can copy your completed `config.yaml` to another machine.

**Q: What happens if I interrupt the wizard?**

A: State is automatically saved. Run `mycelium init` again to resume from where you left off.

### Configuration Questions

**Q: Where is configuration saved?**

A: In `~/.config/mycelium/config.yaml` (user-global) or `./mycelium.yaml` (project-local).

**Q: Can I use environment variables instead?**

A: Yes, Mycelium supports environment variable overrides for all settings.

**Q: What format is the config file?**

A: YAML format, human-readable and editable.

**Q: How do I validate my configuration?**

A: Run `mycelium config validate` to check for errors.

### Service Questions

**Q: Can I enable services later?**

A: Yes, edit the config file or use `mycelium config set services.<service>.enabled true`.

**Q: Why can't I find Temporal?**

A: Temporal must be manually installed and running. The wizard detects existing instances only.

**Q: Do I need Docker?**

A: Only if using Docker Compose or Kubernetes deployment. systemd deployment doesn't require Docker.

**Q: What if I don't have any services installed?**

A: The wizard will still work. You can configure Mycelium and install services later.

### Advanced Questions

**Q: Can I automate the wizard?**

A: Yes, use the programmatic API (see `docs/wizard-integration.md`). The CLI is interactive-only.

**Q: Can I add custom deployment methods?**

A: Currently, only Docker Compose, Kubernetes, and systemd are supported. Custom methods require code changes.

**Q: How do I migrate configuration between versions?**

A: Use `mycelium config migrate` to upgrade configuration schema automatically.

**Q: Can I use the wizard in CI/CD?**

A: The wizard is interactive. For CI/CD, create config files programmatically or copy pre-configured templates.

## Next Steps

After completing the wizard:

1. **Review Configuration**:

   ```bash
   mycelium config show
   ```

1. **Validate Setup**:

   ```bash
   mycelium config validate
   ```

1. **Start Services**:

   ```bash
   mycelium deploy start
   ```

1. **Check Status**:

   ```bash
   mycelium status
   ```

1. **Explore Documentation**:

   - [API Reference](./wizard-reference.md)
   - [Integration Guide](./wizard-integration.md)
   - [Configuration Schema](./config-schema.md)

## Getting Help

- **Documentation**: `mycelium --help`
- **Command Help**: `mycelium <command> --help`
- **Report Issues**: [GitHub Issues](https://github.com/gsornsen/mycelium/issues)
- **Community**: \[Discord/Slack Channel Link\]

______________________________________________________________________

**Last Updated**: 2025-10-14 **Version**: M04 (Interactive Onboarding)
