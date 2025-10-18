# Deployment Template System

This module provides Jinja2 templates for generating deployment configurations from MyceliumConfig.

## Overview

The deployment system supports three deployment methods:
- **Docker Compose**: Single-file YAML for local development
- **Kubernetes**: Complete K8s manifests for production deployment
- **systemd**: Service files for bare-metal installations

## Architecture

```
mycelium_onboarding/deployment/
├── __init__.py              # Public API
├── renderer.py              # Template rendering engine
├── README.md                # This file
└── templates/
    ├── docker-compose.yml.j2       # Docker Compose template
    ├── kubernetes/
    │   ├── namespace.yaml.j2       # K8s namespace
    │   ├── redis.yaml.j2           # Redis deployment
    │   ├── postgres.yaml.j2        # PostgreSQL StatefulSet
    │   └── temporal.yaml.j2        # Temporal deployment
    └── systemd/
        ├── redis.service.j2        # Redis systemd unit
        ├── postgres.service.j2     # PostgreSQL systemd unit
        └── temporal.service.j2     # Temporal systemd unit
```

## Usage

### Basic Usage

```python
from mycelium_onboarding.config.schema import MyceliumConfig
from mycelium_onboarding.deployment import TemplateRenderer

# Create configuration
config = MyceliumConfig(
    project_name="my-project",
    services={
        "redis": {"enabled": True},
        "postgres": {"enabled": True},
    }
)

# Initialize renderer
renderer = TemplateRenderer()

# Render Docker Compose
docker_compose = renderer.render_docker_compose(config)
print(docker_compose)

# Render Kubernetes manifests
k8s_manifests = renderer.render_kubernetes(config)
for filename, content in k8s_manifests.items():
    print(f"=== {filename} ===")
    print(content)

# Render systemd services
systemd_services = renderer.render_systemd(config)
for filename, content in systemd_services.items():
    print(f"=== {filename} ===")
    print(content)
```

### Render All Formats

```python
# Render all deployment configurations at once
all_configs = renderer.render_all(config)

docker_compose = all_configs["docker_compose"]
k8s_manifests = all_configs["kubernetes"]
systemd_services = all_configs["systemd"]
```

### Render for Specific Method

```python
from mycelium_onboarding.config.schema import DeploymentMethod

# Render for specific deployment method
output = renderer.render_for_method(config, DeploymentMethod.KUBERNETES)

# Or use config's deployment method
output = renderer.render_for_method(config)  # Uses config.deployment.method
```

## Template Variables

All templates receive a `config` object with the following structure:

```python
config.project_name          # Project identifier
config.version               # Config schema version
config.created_at            # Creation timestamp

config.deployment.method     # Deployment method
config.deployment.auto_start # Auto-start services

config.services.redis.enabled      # Service enabled
config.services.redis.version      # Image version
config.services.redis.port         # Port number
config.services.redis.persistence  # Enable persistence
config.services.redis.max_memory   # Memory limit

config.services.postgres.enabled        # Service enabled
config.services.postgres.version        # Image version
config.services.postgres.port           # Port number
config.services.postgres.database       # Database name
config.services.postgres.max_connections # Max connections

config.services.temporal.enabled        # Service enabled
config.services.temporal.version        # Image version
config.services.temporal.ui_port        # UI port
config.services.temporal.frontend_port  # gRPC port
config.services.temporal.namespace      # Default namespace
```

## Docker Compose Templates

### Features

- Service dependency management (Temporal depends on PostgreSQL)
- Health checks for all services
- Named volumes for persistence
- Custom networks
- Environment variable templating
- Restart policies based on auto_start

### Generated Structure

```yaml
version: '3.8'

services:
  redis:      # If enabled
  postgres:   # If enabled
  temporal:   # If enabled

networks:
  mycelium-network:

volumes:
  redis-data:     # If persistence enabled
  postgres-data:  # If PostgreSQL enabled
```

### Security

- Passwords via environment variables
- No hardcoded secrets
- Named volumes with project prefix

## Kubernetes Templates

### Features

- Namespace isolation
- StatefulSet for PostgreSQL (persistent storage)
- Deployment for Redis and Temporal
- ConfigMaps for configuration
- Secrets for credentials
- Services for networking
- PersistentVolumeClaims for storage
- Resource limits and requests
- Liveness and readiness probes
- Init containers for dependencies

### Generated Manifests

1. **namespace.yaml**: Kubernetes namespace with labels
2. **redis.yaml**: Redis Deployment, Service, and PVC
3. **postgres.yaml**: PostgreSQL StatefulSet, Service, Secret, ConfigMap
4. **temporal.yaml**: Temporal Deployment, ConfigMap, Services (frontend + UI)

### Security

- Secrets for PostgreSQL credentials (must be updated)
- Security contexts
- Resource limits
- Network policies (future enhancement)

### Deployment

```bash
# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f redis.yaml
kubectl apply -f postgres.yaml
kubectl apply -f temporal.yaml

# Or apply entire directory
kubectl apply -f kubernetes/
```

## systemd Templates

### Features

- Full systemd unit structure
- Security hardening
- Resource limits
- Logging configuration
- Dependency management
- Restart policies
- Service isolation

### Generated Files

1. **{project}-redis.service**: Redis server
2. **{project}-postgres.service**: PostgreSQL database
3. **{project}-temporal.service**: Temporal server

### Security Hardening

- `NoNewPrivileges=true`: Prevent privilege escalation
- `PrivateTmp=true`: Isolated /tmp
- `PrivateDevices=true`: No device access
- `ProtectHome=true`: Home directory protection
- `ProtectSystem=strict`: Filesystem protection
- `ReadWritePaths`: Minimal write access

### Installation

```bash
# Copy service files
sudo cp {project}-*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable {project}-redis.service
sudo systemctl enable {project}-postgres.service
sudo systemctl enable {project}-temporal.service

# Start services
sudo systemctl start {project}-redis.service
sudo systemctl start {project}-postgres.service
sudo systemctl start {project}-temporal.service

# Check status
sudo systemctl status {project}-redis.service
```

## Custom Templates

You can provide custom template directories:

```python
from pathlib import Path

custom_templates = Path("/path/to/custom/templates")
renderer = TemplateRenderer(template_dir=custom_templates)
```

Custom templates must follow the same structure and naming conventions.

## Template Filters

The renderer provides custom Jinja2 filters:

- `kebab_case`: Convert string to kebab-case (e.g., "my_project" → "my-project")

## Testing

All templates are comprehensively tested:

```bash
# Run template tests
uv run pytest tests/test_templates.py -v

# Test coverage
uv run pytest tests/test_templates.py --cov=mycelium_onboarding.deployment
```

Tests verify:
- Valid YAML/INI generation
- Correct service configuration
- Conditional rendering
- Security settings
- Network configuration
- Volume management
- Health checks
- Dependencies

## Best Practices

### Docker Compose

1. Always use environment variables for secrets
2. Enable health checks for all services
3. Use named volumes for production
4. Configure restart policies appropriately
5. Use custom networks for isolation

### Kubernetes

1. Update default passwords in secrets
2. Configure resource limits
3. Use PersistentVolumeClaims for data
4. Implement network policies
5. Use namespaces for isolation
6. Configure RBAC appropriately
7. Use ConfigMaps for configuration

### systemd

1. Run services as dedicated users
2. Enable security hardening options
3. Configure resource limits
4. Use EnvironmentFile for secrets
5. Enable logging to journal
6. Set up log rotation
7. Configure monitoring

## Examples

See `examples/sample_deployment_outputs.py` for complete examples.

Generated samples are in `examples/rendered_configs/`:
- `docker-compose.yml`: Full Docker Compose configuration
- `kubernetes/`: Complete K8s manifests
- `systemd/`: systemd service files

## Future Enhancements

- [ ] Helm charts for Kubernetes
- [ ] Docker Swarm mode support
- [ ] Nomad job specifications
- [ ] AWS CloudFormation templates
- [ ] Terraform modules
- [ ] Ansible playbooks
- [ ] Network policies for Kubernetes
- [ ] Ingress configuration
- [ ] Certificate management
- [ ] Backup configurations

## Contributing

When adding new templates:

1. Create template in appropriate directory
2. Update `renderer.py` if needed
3. Add comprehensive tests
4. Update this README
5. Generate sample outputs
6. Update documentation

## License

MIT License - See project LICENSE file.
