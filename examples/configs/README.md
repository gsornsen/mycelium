# Mycelium Configuration Examples

This directory contains example configuration files demonstrating various deployment scenarios and patterns.

## Available Examples

### Basic Examples

#### `minimal.yaml`

Absolute minimum valid configuration using all defaults.

- **Services**: Redis, PostgreSQL, Temporal (all on standard ports)
- **Deployment**: Docker Compose
- **Use case**: Quick start, learning, experimentation

```bash
cp examples/configs/minimal.yaml ~/.config/mycelium/config.yaml
```

### Service-Specific Examples

#### `redis-only.yaml`

Lightweight setup with only Redis for pub/sub messaging.

- **Services**: Redis only
- **Deployment**: Docker Compose
- **Use case**: Messaging-only applications, lightweight deployments

#### `postgres-only.yaml`

Database-focused setup with only PostgreSQL.

- **Services**: PostgreSQL only
- **Deployment**: Docker Compose
- **Use case**: Data persistence without messaging, database testing

#### `temporal-only.yaml`

Workflow orchestration with only Temporal.

- **Services**: Temporal only
- **Deployment**: Docker Compose
- **Use case**: External services, Temporal Cloud, workflow-focused applications
- **Note**: Requires external PostgreSQL for Temporal backend

### Complete Examples

#### `full-stack.yaml`

Complete setup with all services and production-ready settings.

- **Services**: Redis, PostgreSQL, Temporal (all configured)
- **Deployment**: Docker Compose
- **Use case**: Full-featured development, reference for production

### Environment Examples

#### `development.yaml`

Optimized for local development with fast startup and minimal resources.

- **Services**: All enabled with minimal settings
- **Deployment**: Docker Compose
- **Features**: Fast startup, no persistence (Redis), minimal memory
- **Use case**: Day-to-day development

#### `production.yaml`

Production-ready configuration with high availability and performance tuning.

- **Services**: All enabled with production settings
- **Deployment**: Kubernetes (or Docker Compose for simpler setups)
- **Features**: Persistence, replication-ready, performance tuned
- **Use case**: Production deployments, enterprise environments

#### `kubernetes.yaml`

Configuration for Kubernetes deployments.

- **Services**: All enabled
- **Deployment**: Kubernetes
- **Features**: Cloud-native, scalable, HA-ready
- **Use case**: Cloud deployments, scalable infrastructure

## Using Examples

### Quick Start

1. **Choose an example** that matches your use case
1. **Copy to config location**:
   ```bash
   cp examples/configs/<example>.yaml ~/.config/mycelium/config.yaml
   ```
1. **Validate configuration**:
   ```bash
   mycelium config validate
   ```
1. **Customize** as needed (edit ports, resource limits, etc.)

### Validation

All examples are valid and can be validated:

```bash
# Validate all examples
for f in examples/configs/*.yaml; do
    echo "Validating $f..."
    mycelium config validate --path "$f"
done
```

### Customization

Examples serve as starting points. Customize them for your needs:

```bash
# Copy example
cp examples/configs/development.yaml .mycelium/config.yaml

# Edit with your preferred editor
$EDITOR .mycelium/config.yaml

# Validate your changes
mycelium config validate
```

## Configuration Patterns

### Pattern: Multi-Environment Setup

Use different configs for different environments:

```bash
# Development
cp examples/configs/development.yaml dev-config.yaml

# Staging
cp examples/configs/full-stack.yaml staging-config.yaml

# Production
cp examples/configs/production.yaml prod-config.yaml
```

Then deploy with explicit config:

```bash
mycelium deploy --config dev-config.yaml      # Development
mycelium deploy --config staging-config.yaml  # Staging
mycelium deploy --config prod-config.yaml     # Production
```

### Pattern: Custom Ports

Avoid port conflicts by customizing ports:

```yaml
services:
  redis:
    port: 6380  # Instead of 6379
  postgres:
    port: 5433  # Instead of 5432
  temporal:
    ui_port: 8081        # Instead of 8080
    frontend_port: 7234  # Instead of 7233
```

### Pattern: Selective Services

Enable only the services you need:

```yaml
services:
  redis:
    enabled: true   # Need messaging
  postgres:
    enabled: false  # Using external DB
  temporal:
    enabled: false  # Don't need workflows
```

### Pattern: Resource Tuning

Adjust resources based on your workload:

```yaml
services:
  redis:
    max_memory: "2gb"  # More memory for large queues
  postgres:
    max_connections: 300  # More connections for busy apps
    custom_config:
      shared_buffers: "1GB"  # More cache
```

## Comparison Matrix

| Example       | Redis | PostgreSQL | Temporal | Deployment | Resources | Use Case    |
| ------------- | ----- | ---------- | -------- | ---------- | --------- | ----------- |
| minimal       | ✓     | ✓          | ✓        | Docker     | Minimal   | Quick start |
| redis-only    | ✓     | ✗          | ✗        | Docker     | Low       | Messaging   |
| postgres-only | ✗     | ✓          | ✗        | Docker     | Low       | Database    |
| temporal-only | ✗     | ✗          | ✓        | Docker     | Medium    | Workflows   |
| full-stack    | ✓     | ✓          | ✓        | Docker     | High      | Complete    |
| development   | ✓     | ✓          | ✓        | Docker     | Low       | Dev         |
| production    | ✓     | ✓          | ✓        | K8s        | High      | Prod        |
| kubernetes    | ✓     | ✓          | ✓        | K8s        | High      | Cloud       |

## Troubleshooting

### Port Conflicts

If services fail to start due to port conflicts:

1. Check what's using the port:

   ```bash
   lsof -i :6379  # Check Redis port
   lsof -i :5432  # Check PostgreSQL port
   ```

1. Choose a different port in your config:

   ```yaml
   services:
     redis:
       port: 6380  # Use alternative port
   ```

### Validation Errors

If configuration validation fails:

1. Check the error message for specific field
1. Refer to [Configuration Reference](../../docs/configuration-reference.md)
1. Compare with working examples

### Resource Issues

If services crash or perform poorly:

1. Check available resources:

   ```bash
   docker stats  # Check container resources
   ```

1. Adjust resource limits in config:

   ```yaml
   services:
     redis:
       max_memory: "512mb"  # Reduce if low on RAM
   ```

## Next Steps

- **Learn more**: [Configuration Guide](../../docs/configuration-guide.md)
- **Full reference**: [Configuration Reference](../../docs/configuration-reference.md)
- **Migrations**: [Migration Guide](../../docs/migration-guide.md)
- **Deployment**: See deployment documentation for generating deployment files

## Contributing

Have a useful configuration pattern? Contribute it!

1. Create a new YAML file in this directory
1. Add comprehensive comments explaining use case
1. Validate with `mycelium config validate`
1. Submit a pull request

## License

These examples are provided as-is under the same license as Mycelium.
