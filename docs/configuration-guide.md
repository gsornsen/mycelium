# Mycelium Configuration Guide

> **Quick Start**: Get your Mycelium configuration running in 5 minutes

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration File Structure](#configuration-file-structure)
- [Configuration Options](#configuration-options)
- [Hierarchical Configuration](#hierarchical-configuration)
- [CLI Commands](#cli-commands)
- [Common Configuration Patterns](#common-configuration-patterns)
- [Troubleshooting](#troubleshooting)

## Quick Start

Get started with Mycelium configuration in 5 minutes:

```bash
# 1. Initialize default configuration
mycelium config init

# 2. View your configuration
mycelium config show

# 3. Validate configuration
mycelium config validate

# 4. Check configuration location
mycelium config location
```

That's it! You now have a working configuration with sensible defaults for all services.

### Customizing Your Configuration

Edit your configuration file to customize service settings:

```bash
# Find your config file location
mycelium config location

# Edit with your preferred editor
$EDITOR ~/.config/mycelium/config.yaml
```

## Configuration File Structure

Mycelium uses YAML format for human-readable, version-controlled configuration.

### Minimal Configuration

The simplest valid configuration:

```yaml
version: "1.0"
```

This uses defaults for everything: Docker Compose deployment with Redis, PostgreSQL, and Temporal all enabled on standard ports.

### Full Configuration Structure

```yaml
# Schema version (required for migrations)
version: "1.0"

# Project identifier (alphanumeric, hyphens, underscores)
project_name: mycelium

# Deployment configuration
deployment:
  method: docker-compose        # docker-compose | kubernetes | systemd | manual
  auto_start: true              # Auto-start services on deployment
  healthcheck_timeout: 60       # Seconds to wait for services (10-300)

# Service configurations
services:
  # Redis configuration
  redis:
    enabled: true               # Enable Redis service
    version: "7"                # Optional: specific version
    port: 6379                  # Port number (1-65535)
    persistence: true           # Enable RDB snapshots
    max_memory: "256mb"         # Memory limit (e.g., "256mb", "1gb")
    custom_config: {}           # Additional Redis settings

  # PostgreSQL configuration
  postgres:
    enabled: true               # Enable PostgreSQL service
    version: "15"               # Optional: specific version
    port: 5432                  # Port number (1-65535)
    database: mycelium          # Database name (alphanumeric + underscores)
    max_connections: 100        # Max concurrent connections (1-10000)
    custom_config: {}           # Additional PostgreSQL settings

  # Temporal configuration
  temporal:
    enabled: true               # Enable Temporal service
    ui_port: 8080              # Web UI port (1-65535)
    frontend_port: 7233        # gRPC frontend port (1-65535)
    namespace: default          # Default workflow namespace
    custom_config: {}           # Additional Temporal settings

# Timestamp when configuration was created (auto-generated)
created_at: 2025-10-13T10:30:00
```

## Configuration Options

### Top-Level Fields

#### `version` (required)

Schema version for migration support. Current version: `"1.0"`

```yaml
version: "1.0"
```

**Format**: `"<major>.<minor>"` (e.g., "1.0", "1.1")
**Validation**: Must match pattern `^\d+\.\d+$`

#### `project_name`

Project identifier used in service names, network names, and resource labels.

```yaml
project_name: my-awesome-project
```

**Default**: `"mycelium"`
**Format**: Alphanumeric characters, hyphens, underscores only
**Length**: 1-100 characters
**Examples**: `"mycelium"`, `"my-project"`, `"prod_deployment"`

#### `created_at`

Timestamp when configuration was created (auto-generated, not typically edited manually).

```yaml
created_at: 2025-10-13T10:30:00.123456
```

### Deployment Configuration

Controls how services are deployed and managed.

#### `deployment.method`

Deployment method to use.

```yaml
deployment:
  method: docker-compose
```

**Options**:
- `docker-compose`: Docker Compose (default, recommended for development)
- `kubernetes`: Kubernetes cluster
- `systemd`: systemd services (Linux)
- `manual`: Manual deployment (user-managed)

**Default**: `"docker-compose"`

#### `deployment.auto_start`

Automatically start services after deployment.

```yaml
deployment:
  auto_start: true
```

**Default**: `true`
**Type**: Boolean
**Use case**: Set to `false` for manual control over service startup

#### `deployment.healthcheck_timeout`

Timeout in seconds to wait for services to become healthy.

```yaml
deployment:
  healthcheck_timeout: 60
```

**Default**: `60`
**Range**: 10-300 seconds
**Use case**: Increase for slower systems, decrease for faster feedback

### Services Configuration

#### Redis Configuration

Redis is used for pub/sub messaging, task queuing, and caching.

```yaml
services:
  redis:
    enabled: true
    version: "7"
    port: 6379
    persistence: true
    max_memory: "256mb"
    custom_config:
      maxmemory-policy: "allkeys-lru"
```

**Fields**:
- `enabled`: Enable Redis service (default: `true`)
- `version`: Redis version (e.g., "7", "7.0", "latest")
- `port`: Port number (default: `6379`, range: 1-65535)
- `persistence`: Enable RDB snapshots (default: `true`)
- `max_memory`: Memory limit (format: `<number><unit>`, e.g., "256mb", "1gb")
- `custom_config`: Additional Redis configuration options

**Common custom_config options**:
- `maxmemory-policy`: Eviction policy ("allkeys-lru", "volatile-lru", "noeviction")
- `save`: RDB save intervals (e.g., "900 1 300 10 60 10000")
- `appendonly`: Enable AOF persistence ("yes"/"no")

#### PostgreSQL Configuration

PostgreSQL is used for durable storage and Temporal backend.

```yaml
services:
  postgres:
    enabled: true
    version: "15"
    port: 5432
    database: mycelium
    max_connections: 100
    custom_config:
      shared_buffers: "256MB"
```

**Fields**:
- `enabled`: Enable PostgreSQL service (default: `true`)
- `version`: PostgreSQL version (e.g., "15", "14", "latest")
- `port`: Port number (default: `5432`, range: 1-65535)
- `database`: Database name (default: `"mycelium"`)
  - Must start with a letter
  - Alphanumeric and underscores only
  - 1-63 characters
- `max_connections`: Max concurrent connections (default: `100`, range: 1-10000)
- `custom_config`: Additional PostgreSQL configuration options

**Common custom_config options**:
- `shared_buffers`: Shared memory buffer size
- `work_mem`: Memory per query operation
- `maintenance_work_mem`: Memory for maintenance operations

#### Temporal Configuration

Temporal is used for durable workflow orchestration.

```yaml
services:
  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
    namespace: default
    custom_config: {}
```

**Fields**:
- `enabled`: Enable Temporal service (default: `true`)
- `ui_port`: Web UI port (default: `8080`, range: 1-65535)
- `frontend_port`: gRPC frontend port (default: `7233`, range: 1-65535)
- `namespace`: Default workflow namespace (default: `"default"`)
  - Alphanumeric, hyphens, underscores
  - 1-255 characters
- `custom_config`: Additional Temporal configuration options

## Hierarchical Configuration

Mycelium follows the XDG Base Directory specification with hierarchical configuration loading.

### Configuration Locations

Configurations are searched in order of precedence:

1. **Project-local**: `.mycelium/config.yaml` (current directory)
2. **User-global**: `~/.config/mycelium/config.yaml`
3. **Defaults**: Built-in default configuration

The first configuration found is used. If none exist, defaults are used.

### When to Use Each Location

**Project-local (`.mycelium/config.yaml`)**:
- Project-specific service configurations
- Different ports per project
- Team-shared configurations (commit to version control)
- CI/CD pipeline configurations

```bash
# Initialize project-local config
mycelium config init --project-local
```

**User-global (`~/.config/mycelium/config.yaml`)**:
- Personal preferences across all projects
- Default service versions
- Common port configurations
- Local development settings

```bash
# Initialize user-global config
mycelium config init
```

### Configuration Merging

Currently, configurations do NOT merge - the first found config is used entirely. Future versions may support configuration merging with precedence rules.

### Environment Variable Overrides

Environment variables can override configuration values:

```bash
# Override project name
export MYCELIUM_PROJECT_NAME="custom-project"

# Override Redis port
export MYCELIUM_REDIS_PORT=6380

# Override deployment method
export MYCELIUM_DEPLOYMENT_METHOD="kubernetes"
```

**Note**: Environment variable support is planned for future releases.

## CLI Commands

### `mycelium config show`

Display current configuration in YAML or JSON format.

```bash
# Show configuration (YAML)
mycelium config show

# Show configuration (JSON)
mycelium config show --format json

# Show project-local config only
mycelium config show --project-local
```

**Options**:
- `--format`: Output format (`yaml` or `json`, default: `yaml`)
- `--project-local`: Show project-local configuration only

### `mycelium config validate`

Validate configuration file and display summary.

```bash
# Validate current configuration
mycelium config validate

# Validate specific file
mycelium config validate path/to/config.yaml
```

**Validation checks**:
- YAML syntax correctness
- Schema version compatibility
- Field type validation
- Port range validation (1-65535)
- Name format validation
- At least one service enabled
- Custom field validators

**Output**:
```
✓ Configuration valid

Deployment: docker-compose
Services: redis, postgres, temporal
```

### `mycelium config location`

Show where configuration file is or would be saved.

```bash
# Show user-global location
mycelium config location

# Show project-local location
mycelium config location --project-local
```

**Output**:
```
✓ /home/user/.config/mycelium/config.yaml
```

or if file doesn't exist:
```
✗ /home/user/.config/mycelium/config.yaml
  (file does not exist)
```

### `mycelium config init`

Initialize configuration with defaults.

```bash
# Initialize user-global config
mycelium config init

# Initialize project-local config
mycelium config init --project-local

# Force overwrite existing config
mycelium config init --force
```

**Options**:
- `--project-local`: Create project-local configuration
- `--force`: Overwrite existing configuration

## Common Configuration Patterns

### Pattern: Development Environment

Full-featured setup for local development:

```yaml
version: "1.0"
project_name: mycelium-dev

deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60

services:
  redis:
    enabled: true
    port: 6379
    persistence: true
    max_memory: "512mb"

  postgres:
    enabled: true
    port: 5432
    database: mycelium_dev
    max_connections: 100

  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
```

### Pattern: Redis-Only Setup

Lightweight setup with only Redis for messaging:

```yaml
version: "1.0"
project_name: mycelium-redis

deployment:
  method: docker-compose
  auto_start: true

services:
  redis:
    enabled: true
    port: 6379

  postgres:
    enabled: false

  temporal:
    enabled: false
```

### Pattern: Custom Ports

Avoid port conflicts with custom ports:

```yaml
version: "1.0"
project_name: mycelium-custom

services:
  redis:
    port: 6380

  postgres:
    port: 5433

  temporal:
    ui_port: 8081
    frontend_port: 7234
```

### Pattern: Production Configuration

Production-ready configuration with increased resources:

```yaml
version: "1.0"
project_name: mycelium-prod

deployment:
  method: kubernetes
  auto_start: true
  healthcheck_timeout: 120

services:
  redis:
    enabled: true
    version: "7.0"
    port: 6379
    persistence: true
    max_memory: "2gb"
    custom_config:
      maxmemory-policy: "allkeys-lru"
      save: "900 1 300 10 60 10000"

  postgres:
    enabled: true
    version: "15"
    port: 5432
    database: mycelium_prod
    max_connections: 200
    custom_config:
      shared_buffers: "1GB"
      work_mem: "64MB"

  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
    namespace: production
```

### Pattern: External Services

Use external managed services:

```yaml
version: "1.0"
project_name: mycelium-external

deployment:
  method: manual
  auto_start: false

services:
  # Use external Redis (e.g., AWS ElastiCache)
  redis:
    enabled: false

  # Use external PostgreSQL (e.g., AWS RDS)
  postgres:
    enabled: false

  # Use external Temporal Cloud
  temporal:
    enabled: false
```

**Note**: When using external services, you'll need to configure connection details separately (planned for future releases).

### Pattern: Multi-Project Setup

Different configurations for multiple projects on same machine:

**Project A** (`.mycelium/config.yaml`):
```yaml
version: "1.0"
project_name: project-a

services:
  redis:
    port: 6379
  postgres:
    port: 5432
  temporal:
    ui_port: 8080
```

**Project B** (`.mycelium/config.yaml`):
```yaml
version: "1.0"
project_name: project-b

services:
  redis:
    port: 6380
  postgres:
    port: 5433
  temporal:
    ui_port: 8081
```

## Troubleshooting

### Configuration Not Found

**Problem**: `Configuration file not found`

**Solution**: Initialize configuration:
```bash
mycelium config init
```

**Explanation**: No configuration file exists in expected locations. The `init` command creates one with defaults.

### Validation Errors

#### Invalid Port Number

**Problem**: `Port must be between 1 and 65535`

**Solution**: Use valid port number:
```yaml
services:
  redis:
    port: 6379  # Valid: 1-65535
```

#### Invalid Project Name

**Problem**: `Project name must contain only alphanumeric characters, hyphens, and underscores`

**Solution**: Use valid characters:
```yaml
project_name: my-project-123  # Valid
# project_name: my.project    # Invalid: contains dot
```

#### Invalid Database Name

**Problem**: `Database name must start with a letter`

**Solution**: Start with letter:
```yaml
services:
  postgres:
    database: mycelium_db  # Valid: starts with letter
    # database: 123_db     # Invalid: starts with number
```

#### Invalid Memory Format

**Problem**: `Memory must be in format '<number><unit>'`

**Solution**: Use correct format:
```yaml
services:
  redis:
    max_memory: "256mb"  # Valid
    # max_memory: "256"  # Invalid: missing unit
```

#### No Services Enabled

**Problem**: `At least one service must be enabled`

**Solution**: Enable at least one service:
```yaml
services:
  redis:
    enabled: true  # At least one must be true
```

### YAML Syntax Errors

**Problem**: `Invalid YAML in config.yaml: ...`

**Solution**: Check YAML syntax:
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Common YAML mistakes**:
- Inconsistent indentation (use 2 spaces)
- Missing colons after keys
- Incorrect boolean values (use `true`/`false`, not `yes`/`no`)
- Unquoted strings with special characters

### Configuration Already Exists

**Problem**: `Configuration already exists`

**Solution**: Use `--force` to overwrite:
```bash
mycelium config init --force
```

### File Permission Errors

**Problem**: `Permission denied` when saving configuration

**Solution**: Check directory permissions:
```bash
# Check permissions
ls -la ~/.config/mycelium/

# Fix permissions
chmod 700 ~/.config/mycelium/
chmod 600 ~/.config/mycelium/config.yaml
```

### Port Conflicts

**Problem**: Services fail to start due to port conflicts

**Solution**: Change ports in configuration:
```yaml
services:
  redis:
    port: 6380  # Use different port
  postgres:
    port: 5433
  temporal:
    ui_port: 8081
    frontend_port: 7234
```

**Find ports in use**:
```bash
# Linux/macOS
lsof -i :6379

# Check what's using a port
netstat -tuln | grep 6379
```

### Migration Errors

**Problem**: Configuration version mismatch or migration failure

**Solution**: See [Migration Guide](migration-guide.md) for detailed migration procedures.

### Getting Help

If you encounter issues not covered here:

1. **Check validation output**: `mycelium config validate` provides detailed error messages
2. **Review logs**: Enable debug logging with `MYCELIUM_LOG_LEVEL=DEBUG`
3. **Check examples**: See `examples/configs/` for working configurations
4. **File an issue**: Report bugs at [GitHub Issues](https://github.com/gsornsen/mycelium/issues)

## Next Steps

- **Configuration Reference**: Complete field reference at [configuration-reference.md](configuration-reference.md)
- **Migration Guide**: Schema migration documentation at [migration-guide.md](migration-guide.md)
- **Examples**: Working configurations in `examples/configs/`
- **Architecture**: Learn about the system at [Architecture Guide](../README.md)
