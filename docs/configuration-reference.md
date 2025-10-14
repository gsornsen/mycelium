# Mycelium Configuration Reference

> **Complete reference documentation** for all configuration fields, validation rules, and defaults.

## Table of Contents

- [Schema Overview](#schema-overview)
- [Field Reference](#field-reference)
- [Validation Rules](#validation-rules)
- [Default Values](#default-values)
- [Configuration Precedence](#configuration-precedence)
- [File Locations](#file-locations)

## Schema Overview

Mycelium configuration uses Pydantic v2 for type-safe validation with comprehensive error messages. The configuration schema is hierarchical with four main sections:

```yaml
version: "1.0"                 # Schema version
project_name: mycelium         # Project identifier
deployment: {...}              # Deployment configuration
services: {...}                # Service configurations
created_at: 2025-10-13T10:30:00  # Auto-generated timestamp
```

### Schema Version History

| Version | Release Date | Changes |
|---------|--------------|---------|
| 1.0     | 2025-10-13  | Initial release with Redis, PostgreSQL, Temporal |
| 1.1     | TBD         | Planned: Monitoring and logging configuration |
| 1.2     | TBD         | Planned: Backup configuration |

See [Migration Guide](migration-guide.md) for version migration details.

## Field Reference

### Root Fields

#### `version`

Configuration schema version for migration support.

- **Type**: String
- **Required**: No (defaults to current version)
- **Default**: `"1.0"`
- **Format**: `"<major>.<minor>"` (e.g., "1.0", "1.1", "2.0")
- **Validation**: Must match pattern `^\d+\.\d+$`
- **Example**: `version: "1.0"`

**Purpose**: Enables automatic migration of older configurations to newer schema versions.

#### `project_name`

Project identifier used throughout the system.

- **Type**: String
- **Required**: No
- **Default**: `"mycelium"`
- **Length**: 1-100 characters
- **Format**: Alphanumeric, hyphens (`-`), and underscores (`_`) only
- **Validation**: Must match pattern `^[a-zA-Z0-9_-]+$`
- **Example**: `project_name: "my-awesome-project"`

**Used for**:
- Docker Compose project name
- Kubernetes namespace prefix
- Service naming
- Network naming
- Resource labels

#### `created_at`

Timestamp when configuration was created.

- **Type**: DateTime (ISO 8601 format)
- **Required**: No
- **Default**: Current timestamp when config is created
- **Auto-generated**: Yes
- **Format**: ISO 8601 datetime string
- **Example**: `created_at: "2025-10-13T10:30:00.123456"`

**Purpose**: Track configuration creation time, helpful for debugging and auditing.

### Deployment Configuration

The `deployment` section controls how services are deployed and managed.

```yaml
deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60
```

#### `deployment.method`

Deployment method for services.

- **Type**: Enum (DeploymentMethod)
- **Required**: No
- **Default**: `"docker-compose"`
- **Values**:
  - `"docker-compose"`: Docker Compose (recommended for development)
  - `"kubernetes"`: Kubernetes cluster
  - `"systemd"`: Linux systemd services
  - `"manual"`: Manual deployment (user-managed)
- **Example**: `method: docker-compose`

**Selection guide**:
- **docker-compose**: Local development, testing, simple deployments
- **kubernetes**: Production deployments, scalability, high availability
- **systemd**: Native Linux deployments, minimal overhead
- **manual**: External services, custom deployments

#### `deployment.auto_start`

Automatically start services after deployment.

- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Values**: `true` or `false`
- **Example**: `auto_start: true`

**Behavior**:
- `true`: Services start automatically after deployment generation
- `false`: Services require manual start (useful for staged deployments)

#### `deployment.healthcheck_timeout`

Timeout in seconds to wait for services to become healthy.

- **Type**: Integer
- **Required**: No
- **Default**: `60`
- **Range**: 10-300 seconds
- **Validation**: Must be between 10 and 300 (inclusive)
- **Example**: `healthcheck_timeout: 60`

**Tuning guide**:
- **10-30 seconds**: Fast systems, local development
- **60 seconds**: Default, balanced for most use cases
- **120-300 seconds**: Slow systems, large databases, CI/CD

### Services Configuration

The `services` section contains configuration for all available services.

```yaml
services:
  redis: {...}
  postgres: {...}
  temporal: {...}
```

#### Base Service Fields

All services inherit these common fields:

##### `enabled`

Whether the service is enabled.

- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Values**: `true` or `false`
- **Example**: `enabled: true`

**Note**: At least one service must be enabled. Configuration validation fails if all services are disabled.

##### `version`

Specific version of the service to use.

- **Type**: String (optional)
- **Required**: No
- **Default**: `null` (uses deployment method's default version)
- **Format**: Alphanumeric, dots (`.`), hyphens (`-`), underscores (`_`)
- **Validation**: Must match pattern `^[a-zA-Z0-9._-]+$`
- **Examples**:
  - `"7"`: Major version only
  - `"7.0"`: Major.minor version
  - `"7.0.5"`: Major.minor.patch version
  - `"latest"`: Latest version (not recommended for production)
  - `"7.0-alpine"`: Version with variant

**Version selection**:
- Omit for deployment method defaults
- Specify for reproducible builds
- Pin exact versions in production

##### `custom_config`

Additional service-specific configuration options.

- **Type**: Dictionary (string → any)
- **Required**: No
- **Default**: `{}` (empty dictionary)
- **Format**: Key-value pairs specific to each service
- **Example**:
  ```yaml
  custom_config:
    key1: "value1"
    key2: 42
  ```

**Purpose**: Pass additional configuration to service that isn't explicitly modeled in schema.

### Redis Configuration

Redis configuration for pub/sub messaging, task queuing, and caching.

```yaml
services:
  redis:
    enabled: true
    version: "7"
    port: 6379
    persistence: true
    max_memory: "256mb"
    custom_config: {}
```

#### `services.redis.port`

Redis port number.

- **Type**: Integer
- **Required**: No
- **Default**: `6379`
- **Range**: 1-65535
- **Validation**: Must be valid port number
- **Example**: `port: 6379`

**Common ports**:
- `6379`: Standard Redis port
- `6380-6389`: Alternative Redis instances

#### `services.redis.persistence`

Enable RDB (Redis Database) persistence.

- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Values**: `true` or `false`
- **Example**: `persistence: true`

**Behavior**:
- `true`: Periodic snapshots saved to disk, data survives restarts
- `false`: In-memory only, data lost on restart (faster, useful for caching)

#### `services.redis.max_memory`

Maximum memory limit for Redis.

- **Type**: String
- **Required**: No
- **Default**: `"256mb"`
- **Format**: `<number><unit>` where unit is `kb`, `mb`, `gb`, or `tb` (case-insensitive)
- **Validation**: Must match pattern `^\d+[kmgtKMGT][bB]$`
- **Normalization**: Converted to lowercase on validation
- **Examples**:
  - `"256mb"`: 256 megabytes
  - `"1gb"`: 1 gigabyte
  - `"512MB"`: 512 megabytes (normalized to "512mb")

**Sizing guide**:
- **128-256mb**: Lightweight usage, few agents
- **512mb-1gb**: Moderate usage, standard deployment
- **2gb+**: Heavy usage, many agents, large queues

#### `services.redis.custom_config`

Additional Redis configuration options.

**Common options**:

```yaml
custom_config:
  # Eviction policy when max_memory reached
  maxmemory-policy: "allkeys-lru"  # Options: allkeys-lru, volatile-lru, noeviction

  # RDB save intervals (seconds keys seconds keys ...)
  save: "900 1 300 10 60 10000"    # Save if 1 key changed in 900s, OR 10 in 300s, OR 10000 in 60s

  # AOF (Append Only File) persistence
  appendonly: "yes"                # Enable AOF for better durability
  appendfsync: "everysec"          # Sync every second (balanced)

  # Replication
  replica-read-only: "yes"
```

### PostgreSQL Configuration

PostgreSQL configuration for durable storage and Temporal backend.

```yaml
services:
  postgres:
    enabled: true
    version: "15"
    port: 5432
    database: mycelium
    max_connections: 100
    custom_config: {}
```

#### `services.postgres.port`

PostgreSQL port number.

- **Type**: Integer
- **Required**: No
- **Default**: `5432`
- **Range**: 1-65535
- **Validation**: Must be valid port number
- **Example**: `port: 5432`

**Common ports**:
- `5432`: Standard PostgreSQL port
- `5433-5439`: Alternative PostgreSQL instances

#### `services.postgres.database`

Default database name.

- **Type**: String
- **Required**: No
- **Default**: `"mycelium"`
- **Length**: 1-63 characters (PostgreSQL limit)
- **Format**: Must start with letter, then alphanumeric and underscores
- **Validation**: Must match pattern `^[a-zA-Z][a-zA-Z0-9_]*$`
- **Example**: `database: "mycelium_dev"`

**Naming rules** (PostgreSQL requirements):
- Start with letter (a-z, A-Z)
- Contain only letters, numbers, underscores
- No hyphens, spaces, or special characters
- Case-sensitive

#### `services.postgres.max_connections`

Maximum number of concurrent database connections.

- **Type**: Integer
- **Required**: No
- **Default**: `100`
- **Range**: 1-10000
- **Validation**: Must be between 1 and 10000
- **Example**: `max_connections: 100`

**Sizing guide**:
- **20-50**: Lightweight usage, few agents
- **100-200**: Standard usage, moderate agents
- **300-500**: Heavy usage, many agents
- **1000+**: Enterprise usage (requires PostgreSQL tuning)

**Note**: Each connection uses memory. Calculate as:
```
Memory for connections ≈ max_connections * work_mem
```

#### `services.postgres.custom_config`

Additional PostgreSQL configuration options.

**Common options**:

```yaml
custom_config:
  # Memory configuration
  shared_buffers: "256MB"          # RAM for caching (25% of total RAM)
  work_mem: "64MB"                 # RAM per query operation
  maintenance_work_mem: "128MB"    # RAM for maintenance (VACUUM, CREATE INDEX)
  effective_cache_size: "1GB"      # OS cache size hint (50-75% of total RAM)

  # Connection pooling
  max_connections: "200"

  # WAL (Write-Ahead Logging)
  wal_level: "replica"             # For replication
  max_wal_size: "1GB"
  min_wal_size: "80MB"

  # Performance tuning
  random_page_cost: "1.1"          # For SSDs (default 4.0 for HDDs)
  effective_io_concurrency: "200"  # For SSDs (default 1 for HDDs)
```

### Temporal Configuration

Temporal configuration for durable workflow orchestration.

```yaml
services:
  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
    namespace: default
    custom_config: {}
```

#### `services.temporal.ui_port`

Temporal Web UI port number.

- **Type**: Integer
- **Required**: No
- **Default**: `8080`
- **Range**: 1-65535
- **Validation**: Must be valid port number
- **Example**: `ui_port: 8080`

**Common ports**:
- `8080`: Standard HTTP alternate port
- `8081-8089`: Alternative HTTP ports

**Access**: Web UI available at `http://localhost:<ui_port>`

#### `services.temporal.frontend_port`

Temporal gRPC frontend port number.

- **Type**: Integer
- **Required**: No
- **Default**: `7233`
- **Range**: 1-65535
- **Validation**: Must be valid port number
- **Example**: `frontend_port: 7233`

**Purpose**: gRPC endpoint for Temporal clients, workers, and CLI.

#### `services.temporal.namespace`

Default Temporal namespace for workflows.

- **Type**: String
- **Required**: No
- **Default**: `"default"`
- **Length**: 1-255 characters
- **Format**: Alphanumeric, hyphens (`-`), and underscores (`_`)
- **Validation**: Must match pattern `^[a-zA-Z0-9_-]+$`
- **Example**: `namespace: "production"`

**Namespaces** are logical isolation boundaries for workflows:
- Separate environments (dev, staging, prod)
- Different teams or projects
- Multi-tenancy

#### `services.temporal.custom_config`

Additional Temporal configuration options (service-specific).

## Validation Rules

### Global Validation

- **At least one service enabled**: Configuration fails validation if all services have `enabled: false`

### Field-Level Validation

#### String Pattern Validation

| Field | Pattern | Description |
|-------|---------|-------------|
| `project_name` | `^[a-zA-Z0-9_-]+$` | Alphanumeric, hyphens, underscores |
| `postgres.database` | `^[a-zA-Z][a-zA-Z0-9_]*$` | Start with letter, then alphanumeric + underscores |
| `temporal.namespace` | `^[a-zA-Z0-9_-]+$` | Alphanumeric, hyphens, underscores |
| `version` | `^\d+\.\d+$` | Major.minor version (e.g., "1.0") |
| `redis.max_memory` | `^\d+[kmgtKMGT][bB]$` | Number followed by size unit |
| `*.version` | `^[a-zA-Z0-9._-]+$` | Alphanumeric, dots, hyphens, underscores |

#### Numeric Range Validation

| Field | Minimum | Maximum | Default |
|-------|---------|---------|---------|
| `redis.port` | 1 | 65535 | 6379 |
| `postgres.port` | 1 | 65535 | 5432 |
| `postgres.max_connections` | 1 | 10000 | 100 |
| `temporal.ui_port` | 1 | 65535 | 8080 |
| `temporal.frontend_port` | 1 | 65535 | 7233 |
| `deployment.healthcheck_timeout` | 10 | 300 | 60 |

#### String Length Validation

| Field | Minimum | Maximum | Default Length |
|-------|---------|---------|----------------|
| `project_name` | 1 | 100 | 8 ("mycelium") |
| `postgres.database` | 1 | 63 | 8 ("mycelium") |
| `temporal.namespace` | 1 | 255 | 7 ("default") |

### Validation Error Messages

Pydantic provides detailed error messages with field paths:

```
Configuration validation failed in: /path/to/config.yaml
services -> redis -> port: Input should be less than or equal to 65535
services -> postgres -> database: Database name must start with a letter
project_name: Project name must contain only alphanumeric characters, hyphens, and underscores
```

## Default Values

### Complete Default Configuration

```yaml
version: "1.0"
project_name: "mycelium"

deployment:
  method: "docker-compose"
  auto_start: true
  healthcheck_timeout: 60

services:
  redis:
    enabled: true
    version: null
    port: 6379
    persistence: true
    max_memory: "256mb"
    custom_config: {}

  postgres:
    enabled: true
    version: null
    port: 5432
    database: "mycelium"
    max_connections: 100
    custom_config: {}

  temporal:
    enabled: true
    version: null
    ui_port: 8080
    frontend_port: 7233
    namespace: "default"
    custom_config: {}

created_at: <current_timestamp>
```

### Minimal Valid Configuration

The absolute minimum valid configuration:

```yaml
version: "1.0"
```

All other fields use defaults.

### Service-Specific Defaults

When a service is explicitly disabled, its other fields are still validated if provided:

```yaml
services:
  redis:
    enabled: false
    # Other fields still validate but are not used
```

## Configuration Precedence

### Hierarchical Loading

Configurations are searched and loaded in order:

1. **Explicit path** (if `ConfigManager(config_path=...)` used)
2. **Project-local**: `.mycelium/config.yaml` (in current directory)
3. **User-global**: `~/.config/mycelium/config.yaml`
4. **Defaults**: Built-in default `MyceliumConfig()`

**First match wins** - no merging is performed.

### Future: Environment Variable Overrides

Planned for future releases:

```bash
# Override project name
export MYCELIUM_PROJECT_NAME="custom-project"

# Override service ports
export MYCELIUM_REDIS_PORT="6380"
export MYCELIUM_POSTGRES_PORT="5433"

# Override deployment method
export MYCELIUM_DEPLOYMENT_METHOD="kubernetes"
```

**Precedence** (planned):
1. Environment variables (highest)
2. Explicit config path
3. Project-local config
4. User-global config
5. Defaults (lowest)

## File Locations

### XDG Base Directory Specification

Mycelium follows the XDG Base Directory specification for configuration files.

#### User-Global Configuration

**Location**: `~/.config/mycelium/config.yaml`

**Expands to**:
- Linux: `/home/<user>/.config/mycelium/config.yaml`
- macOS: `/Users/<user>/.config/mycelium/config.yaml`
- Windows: `C:\Users\<user>\.config\mycelium\config.yaml`

**Environment variable**: Respects `$XDG_CONFIG_HOME` if set:
```bash
export XDG_CONFIG_HOME=/custom/config
# Config will be at: /custom/config/mycelium/config.yaml
```

#### Project-Local Configuration

**Location**: `.mycelium/config.yaml` (in current directory)

**Determination**:
1. If `$MYCELIUM_PROJECT_DIR` is set: `$MYCELIUM_PROJECT_DIR/config.yaml`
2. Otherwise: `.mycelium/config.yaml` (relative to current directory)

**Use case**: Project-specific configuration, committed to version control.

### File Permissions

**Recommended permissions**:
```bash
# Config directory
chmod 700 ~/.config/mycelium/

# Config file
chmod 600 ~/.config/mycelium/config.yaml
```

**Security**: Configuration files may contain sensitive information in future releases. Restrict access appropriately.

### Backup Files

When configuration is saved, a backup is automatically created:

**Backup location**: `<config_path>.backup`

**Example**:
- Config: `~/.config/mycelium/config.yaml`
- Backup: `~/.config/mycelium/config.yaml.backup`

**Retention**: Only the most recent backup is kept (backup is overwritten on each save).

## Serialization Formats

### YAML Format (Primary)

Human-readable format for configuration files:

```yaml
version: "1.0"
project_name: mycelium

deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60

services:
  redis:
    enabled: true
    port: 6379
```

**Features**:
- Human-readable and editable
- Comments supported
- Hierarchical structure
- Version control friendly
- Deterministic output (consistent ordering)

### JSON Format (Secondary)

Machine-readable format for APIs and tools:

```json
{
  "version": "1.0",
  "project_name": "mycelium",
  "deployment": {
    "method": "docker-compose",
    "auto_start": true,
    "healthcheck_timeout": 60
  },
  "services": {
    "redis": {
      "enabled": true,
      "port": 6379
    }
  }
}
```

**CLI Usage**:
```bash
# Export as JSON
mycelium config show --format json

# Validate JSON config
mycelium config validate config.json
```

## See Also

- **User Guide**: [Configuration Guide](configuration-guide.md) - Quick start and common patterns
- **Migration Guide**: [Migration Guide](migration-guide.md) - Schema version migrations
- **Examples**: `examples/configs/` - Working configuration examples
- **Schema Source**: `mycelium_onboarding/config/schema.py` - Pydantic schema definition
