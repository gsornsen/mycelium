# Unified Deployment Command Interface

This module provides a unified `mycelium deploy` command interface for managing the complete deployment lifecycle.

## Overview

The `DeployCommand` class provides a comprehensive deployment management system that:

- **Auto-detects** existing services on the system
- **Intelligently plans** deployments based on detected services
- **Supports multiple deployment methods**: Docker Compose, Kubernetes, systemd
- **Works from any directory** (not just project root)
- Provides **rich progress indicators** and helpful error messages
- Supports **dry-run mode** for safe testing
- Includes **force mode** for override scenarios

## Available Commands

### `mycelium deploy start`

Analyze, configure, and start infrastructure in one command.

**Features:**

- Auto-detects existing services
- Creates deployment plan
- Generates configurations
- Starts all services
- Verifies deployment

**Usage:**

```bash
# Start with auto-detection and planning
mycelium deploy start

# Start with specific method
mycelium deploy start --method kubernetes

# Start with auto-approval (no confirmation)
mycelium deploy start -y

# Dry run (preview without executing)
mycelium deploy start --dry-run

# Start with verbose output
mycelium deploy start --verbose
```

**Flags:**

- `--method`: Override deployment method (docker-compose, kubernetes, systemd)
- `-y, --auto-approve`: Skip confirmation prompts
- `--dry-run`: Preview actions without executing
- `-v, --verbose`: Enable verbose output
- `--force`: Override safety checks

### `mycelium deploy stop`

Stop all managed services.

**Usage:**

```bash
# Stop all services
mycelium deploy stop

# Stop and remove data volumes
mycelium deploy stop --remove-data

# Stop specific method
mycelium deploy stop --method kubernetes

# Force stop without confirmation
mycelium deploy stop --force
```

**Flags:**

- `--method`: Override deployment method
- `--remove-data`: Remove data volumes/directories
- `--force`: Skip confirmation prompts

### `mycelium deploy restart`

Restart services without full redeployment.

**Usage:**

```bash
# Restart all services
mycelium deploy restart

# Restart specific services
mycelium deploy restart --service redis --service postgres

# Restart with specific method
mycelium deploy restart --method docker-compose
```

**Flags:**

- `--method`: Override deployment method
- `--service`: Specific service(s) to restart (can be used multiple times)

### `mycelium deploy status`

Show current deployment state.

**Usage:**

```bash
# Show status
mycelium deploy status

# Show status in JSON format
mycelium deploy status --format json

# Watch for changes (updates in real-time)
mycelium deploy status --watch

# Status for specific method
mycelium deploy status --method kubernetes
```

**Flags:**

- `--method`: Override deployment method
- `--format`: Output format (table, json)
- `--watch`: Watch for changes

### `mycelium deploy generate`

Generate deployment configs without starting services.

**Usage:**

```bash
# Generate configs
mycelium deploy generate

# Generate for specific method
mycelium deploy generate --method kubernetes

# Generate without secrets
mycelium deploy generate --no-secrets

# Generate to custom directory
mycelium deploy generate --output ./my-deployment
```

**Flags:**

- `--method`: Deployment method
- `--output`: Custom output directory
- `--no-secrets`: Skip secrets generation

### `mycelium deploy clean`

Remove all managed infrastructure and artifacts.

**Usage:**

```bash
# Clean deployment files
mycelium deploy clean

# Clean including configuration
mycelium deploy clean --remove-configs

# Clean including secrets
mycelium deploy clean --remove-secrets

# Clean everything
mycelium deploy clean --remove-configs --remove-secrets

# Force clean without confirmation
mycelium deploy clean --force
```

**Flags:**

- `--method`: Override deployment method
- `--remove-configs`: Remove configuration files
- `--remove-secrets`: Remove secrets
- `--force`: Skip confirmation prompts

## Architecture

### Core Classes

#### `DeployCommand`

Main command handler that orchestrates the deployment lifecycle.

**Key Methods:**

- `start()`: Complete deployment process
- `stop()`: Stop services
- `restart()`: Restart services
- `status()`: Get current status
- `clean()`: Clean up artifacts

#### `DeploymentPlan`

Represents a deployment plan with detected services, steps, and configuration.

**Attributes:**

- `plan_id`: Unique identifier
- `detected_services`: Services found on system
- `reusable_services`: Existing services to reuse
- `new_services`: Services to deploy
- `deployment_steps`: Ordered execution steps
- `estimated_duration`: Time estimate

#### `DeploymentStep`

Individual step in the deployment process.

**Phases:**

- DETECTION: Service discovery
- PLANNING: Deployment planning
- VALIDATION: Environment validation
- GENERATION: Config generation
- DEPLOYMENT: Service deployment
- STARTUP: Service startup
- VERIFICATION: Health checks
- COMPLETE: Finished

### Smart Service Detection

The deployment system integrates with `ServiceDetector` to:

1. **Detect running services** (PostgreSQL, Redis, etc.)
1. **Check service status** and versions
1. **Identify reusable services** to avoid duplication
1. **Plan optimal deployment** based on current state

### Multi-Method Support

#### Docker Compose

- Generates `docker-compose.yml`
- Creates `.env` file with secrets
- Provides start/stop/restart commands
- Manages volumes and networks

#### Kubernetes

- Generates namespace manifests
- Creates deployment and service resources
- Generates `kustomization.yaml`
- Supports kubectl operations

#### systemd

- Generates service unit files
- Creates installation scripts
- Manages service lifecycle
- Integrates with system services

## Integration with Existing CLI

The deployment commands integrate seamlessly with the existing `mycelium` CLI:

```python
# In cli.py
from mycelium_onboarding.deployment.commands.deploy import DeployCommand

@cli.group()
def deploy():
    """Deployment management commands."""
    pass

@deploy.command()
def start(...):
    """Start deployment."""
    cmd = DeployCommand(verbose=verbose, dry_run=dry_run)
    asyncio.run(cmd.start(...))
```

## Error Handling

The deployment system provides comprehensive error handling:

- **Configuration errors**: Clear messages about missing configs
- **Service errors**: Detailed failure information
- **Network errors**: Helpful troubleshooting tips
- **Permission errors**: Guidance on required permissions

All errors include:

- Clear error messages
- Context about what failed
- Suggestions for resolution
- Verbose mode for debugging

## Working Directory Context

The deployment system works from **any directory**:

1. Automatically finds configuration
1. Determines deployment directory
1. Resolves relative paths
1. Maintains consistent state

No need to `cd` to project root!

## Dry Run Mode

Test deployments safely:

```bash
mycelium deploy start --dry-run
```

Dry run mode:

- Shows what **would** be done
- Doesn't execute actual commands
- Displays full deployment plan
- Validates configuration
- Checks for conflicts

## Force Mode

Override safety checks:

```bash
mycelium deploy clean --force --remove-configs --remove-secrets
```

Force mode:

- Skips confirmation prompts
- Overrides safety checks
- Useful for automation
- **Use with caution!**

## Examples

### Complete Deployment Workflow

```bash
# 1. Initialize configuration
mycelium init

# 2. Preview deployment
mycelium deploy start --dry-run

# 3. Execute deployment
mycelium deploy start

# 4. Check status
mycelium deploy status

# 5. Restart a service
mycelium deploy restart --service redis

# 6. Stop everything
mycelium deploy stop

# 7. Clean up
mycelium deploy clean
```

### CI/CD Integration

```bash
# Automated deployment
mycelium deploy start --auto-approve --method kubernetes

# Check deployment status
mycelium deploy status --format json

# Clean deployment (with confirmation override)
mycelium deploy clean --force
```

### Development Workflow

```bash
# Start services
mycelium deploy start

# Make changes...

# Restart affected services
mycelium deploy restart --service postgres

# View status
mycelium deploy status --watch
```

## Testing

The module includes comprehensive tests:

- **Unit tests**: Test individual methods
- **Integration tests**: Test full workflows
- **CLI tests**: Test command-line interface

Run tests:

```bash
pytest tests/test_cli_deploy.py
pytest tests/integration/test_deployment_integration.py
```

## Future Enhancements

Planned features:

- [ ] Watch mode implementation
- [ ] Health check integration
- [ ] Log streaming
- [ ] Multi-project support
- [ ] Remote deployment support
- [ ] Rollback functionality

## Contributing

When adding new deployment methods:

1. Add method-specific functions in `DeployCommand`
1. Follow naming pattern: `_start_<method>`, `_stop_<method>`, etc.
1. Handle errors gracefully
1. Add comprehensive tests
1. Update documentation

## License

Part of the Mycelium project. See main project LICENSE file.
