# Temporal + PostgreSQL Deployment Guide

## Overview

This guide covers the deployment and validation of Temporal workflow orchestration with PostgreSQL persistence for the Mycelium Smart Onboarding system.

**Sprint**: Sprint 4 - Temporal Workflow Testing
**Phase**: Phase 2 - Temporal + PostgreSQL Deployment
**Status**: Production-Ready

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture](#architecture)
3. [Deployment Steps](#deployment-steps)
4. [Validation](#validation)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Health Checks](#health-checks)
8. [Common Issues](#common-issues)
9. [Performance Tuning](#performance-tuning)
10. [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Docker**: Docker 20.10+ and Docker Compose 1.29+
- **Ports**: 5432 (PostgreSQL), 7233 (Temporal gRPC), 8080 (Temporal UI)

### Software Dependencies

- Python 3.10 or higher
- UV package manager (`pip install uv`)
- asyncpg for PostgreSQL connectivity
- httpx for HTTP checks

### Network Requirements

- Internet access for Docker image pulls
- Open ports for inter-service communication
- No firewall blocking on required ports

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────┐
│          Temporal + PostgreSQL Stack            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐        ┌──────────────┐     │
│  │   Temporal   │◄──────►│  PostgreSQL  │     │
│  │   Server     │        │   Database   │     │
│  │   (1.22.0)   │        │   (15.3)     │     │
│  └──────────────┘        └──────────────┘     │
│         │                        │             │
│    Port 7233                Port 5432          │
│    (gRPC)                  (SQL)              │
│         │                                       │
│  ┌──────────────┐                             │
│  │  Temporal UI │                             │
│  │   (Web UI)   │                             │
│  └──────────────┘                             │
│         │                                       │
│    Port 8080                                   │
│    (HTTP)                                      │
└─────────────────────────────────────────────────┘
```

### Service Dependencies

1. **PostgreSQL**: Core persistence layer
   - Stores workflow state
   - Maintains execution history
   - Provides visibility database

2. **Temporal Server**: Workflow orchestration
   - Executes workflows
   - Manages task queues
   - Coordinates workers

3. **Temporal UI**: Monitoring and debugging
   - Workflow visualization
   - Execution history
   - Real-time monitoring

## Deployment Steps

### Step 1: Configuration

Create deployment configuration file:

```bash
# Create config file
cat > temporal-deployment-config.yaml <<EOF
version: "1.0"
project_name: temporal-deployment

deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 90

services:
  redis:
    enabled: false

  postgres:
    enabled: true
    version: "15.3"
    port: 5432
    database: temporal
    max_connections: 100
    custom_config:
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      max_wal_size: "1GB"

  temporal:
    enabled: true
    version: "1.22.0"
    ui_port: 8080
    frontend_port: 7233
    namespace: default
EOF

# Copy to config directory
mkdir -p ~/.config/mycelium
cp temporal-deployment-config.yaml ~/.config/mycelium/config.yaml
```

### Step 2: Validate Configuration

```bash
# Validate configuration syntax and compatibility
uv run mycelium config validate
```

Expected output:
```
✓ Configuration valid: /home/user/.config/mycelium/config.yaml
Configuration Summary:
  Project: temporal-deployment
  Schema Version: 1.0
  Deployment: docker-compose
  Enabled Services: postgres (port 5432), temporal (UI: 8080, gRPC: 7233)
```

### Step 3: Deploy Services

```bash
# Deploy with automatic approval
uv run mycelium deploy start --yes

# Or deploy interactively for review
uv run mycelium deploy start
```

Deployment will:
1. Detect existing services (reuse if available)
2. Validate PostgreSQL-Temporal compatibility
3. Generate deployment configurations
4. Start Docker containers
5. Initialize Temporal schema
6. Create default namespace

### Step 4: Verify Deployment

```bash
# Check container status
docker ps --filter "name=temporal"

# View deployment status
uv run mycelium deploy status
```

Expected containers:
- `{project}-postgres`: PostgreSQL 15.3 (healthy)
- `{project}-temporal`: Temporal 1.22.0 (healthy)

### Step 5: Run Validation

```bash
# Run comprehensive validation
python -c "
import asyncio
from mycelium_onboarding.deployment.validation import validate_deployment

async def main():
    report = await validate_deployment(
        postgres_host='localhost',
        postgres_port=5432,
        temporal_host='localhost',
        temporal_port=7233
    )
    print(report.format_summary())

asyncio.run(main())
"
```

## Validation

### Automated Validation

The deployment includes a comprehensive validation system:

```python
from mycelium_onboarding.deployment.validation import DeploymentValidator

validator = DeploymentValidator()
report = await validator.validate(
    postgres_host="localhost",
    postgres_port=5432,
    postgres_database="temporal",
    postgres_user="postgres",
    postgres_password="changeme",
    temporal_host="localhost",
    temporal_port=7233,
    temporal_ui_port=8080,
    temporal_namespace="default",
)

if report.is_healthy():
    print("✓ Deployment is healthy!")
else:
    print(report.format_summary())
```

### Validation Checks

The validator performs:

**PostgreSQL Checks:**
- Port connectivity (5432)
- Version detection
- Database connection
- Temporal schema validation
- Connection pool status

**Temporal Checks:**
- gRPC port connectivity (7233)
- Cluster health
- Namespace existence
- Frontend service availability

**Temporal UI Checks:**
- HTTP port connectivity (8080)
- Web endpoint response

**Integration Checks:**
- Temporal → PostgreSQL connectivity
- Namespace registration
- Data persistence

### Success Criteria

Deployment is successful when:
- ✅ PostgreSQL is healthy (all checks pass)
- ✅ Temporal server is healthy (cluster responding)
- ✅ Integration checks pass (services can communicate)
- ⚠️ UI may be degraded (optional component)

## Configuration

### PostgreSQL Configuration

Located in `.env` file:

```bash
# PostgreSQL credentials
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme  # CHANGE THIS!
POSTGRES_DB=temporal

# Connection string
POSTGRES_URL=postgresql://postgres:changeme@localhost:5432/temporal
```

### Temporal Configuration

Environment variables in docker-compose:

```yaml
environment:
  - DB=postgresql
  - DB_PORT=5432
  - POSTGRES_SEEDS=postgres
  - DEFAULT_NAMESPACE=default
  - TEMPORAL_CLI_ADDRESS=temporal:7233
```

### Dynamic Configuration

Temporal dynamic config (`config/dynamicconfig/development-sql.yaml`):

```yaml
# Workflow execution limits
limit.maxIDLength:
  - value: 255
    constraints: {}

# Worker limits
limit.maxActivityConcurrentExecutions:
  - value: 1000
    constraints: {}

# RPS limits
frontend.rps:
  - value: 2400
    constraints: {}
```

## Troubleshooting

### Common Deployment Issues

#### Issue: PostgreSQL Connection Refused

**Symptoms:**
```
Error: Cannot connect to PostgreSQL at localhost:5432
```

**Resolution:**
```bash
# Check PostgreSQL container
docker logs {project}-postgres

# Verify port mapping
docker ps | grep postgres

# Test connection manually
psql postgresql://postgres:changeme@localhost:5432/temporal -c "SELECT version();"
```

#### Issue: Temporal Fails to Start

**Symptoms:**
```
Container restarting continuously
Error: Unable to create dynamic config client
```

**Resolution:**
```bash
# Check Temporal logs
docker logs {project}-temporal --tail 100

# Verify PostgreSQL is healthy
docker exec {project}-postgres pg_isready

# Ensure dynamic config file exists
ls -la ~/.local/share/mycelium/deployments/{project}/config/dynamicconfig/

# Restart Temporal
docker restart {project}-temporal
```

#### Issue: Temporal UI Not Accessible

**Symptoms:**
```
Connection refused on port 8080
HTTP endpoint not responding
```

**Resolution:**
```bash
# Wait for full startup (UI takes 60-90 seconds)
sleep 60

# Check port binding
docker port {project}-temporal 8080

# Access UI directly
curl http://localhost:8080

# UI is optional - server functions without it
```

### Diagnostic Commands

```bash
# View all deployment logs
docker-compose -f ~/.local/share/mycelium/deployments/{project}/docker-compose.yml logs -f

# Check service health
docker ps --filter "name={project}"

# Inspect PostgreSQL
docker exec -it {project}-postgres psql -U postgres -d temporal -c "\dt"

# Test Temporal gRPC
docker exec -it {project}-temporal tctl cluster health
```

## Health Checks

### PostgreSQL Health

```bash
# Container health check
docker inspect {project}-postgres | jq '.[0].State.Health'

# Manual check
pg_isready -h localhost -p 5432 -U postgres
```

### Temporal Health

```bash
# Container health check
docker inspect {project}-temporal | jq '.[0].State.Health'

# Cluster health (from within container)
docker exec {project}-temporal tctl cluster health
```

### Continuous Monitoring

```python
# Health check script
from mycelium_onboarding.deployment.validation import validate_deployment

async def monitor_deployment():
    while True:
        report = await validate_deployment()
        if not report.can_proceed():
            # Alert on issues
            print(f"WARNING: {report.format_summary()}")
        await asyncio.sleep(60)  # Check every minute
```

## Common Issues

### Issue: Port Already in Use

**Error:**
```
Error: Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Solution:**
```bash
# Find conflicting service
lsof -i :5432

# Use alternate port in config
services:
  postgres:
    port: 5433  # Change to available port
```

### Issue: Insufficient Memory

**Error:**
```
OOMKilled
Container stopped due to memory limit
```

**Solution:**
```bash
# Increase Docker memory limit
# Or reduce PostgreSQL buffers in config
custom_config:
  shared_buffers: "128MB"  # Reduced from 256MB
  effective_cache_size: "512MB"  # Reduced from 1GB
```

### Issue: Schema Already Exists

**Error:**
```
Error: relation "namespaces" already exists
```

**Solution:**
```bash
# Expected - schema initialization is idempotent
# Temporal auto-setup skips existing schemas
# No action needed
```

## Performance Tuning

### PostgreSQL Optimization

For production workloads:

```yaml
custom_config:
  shared_buffers: "4GB"              # 25% of system RAM
  effective_cache_size: "12GB"       # 75% of system RAM
  maintenance_work_mem: "1GB"
  checkpoint_completion_target: "0.9"
  wal_buffers: "16MB"
  default_statistics_target: "100"
  random_page_cost: "1.1"
  effective_io_concurrency: "200"
  work_mem: "20MB"
  min_wal_size: "1GB"
  max_wal_size: "4GB"
  max_worker_processes: "8"
  max_parallel_workers_per_gather: "4"
  max_parallel_workers: "8"
  max_parallel_maintenance_workers: "4"
```

### Temporal Optimization

```yaml
environment:
  # Increase RPS limits
  - frontend.rps=10000

  # Worker concurrency
  - limit.maxActivityConcurrentExecutions=5000

  # Connection pooling
  - persistence.numHistoryShards=512
```

## Security Considerations

### Change Default Passwords

```bash
# Generate strong password
openssl rand -base64 32

# Update .env file
sed -i 's/POSTGRES_PASSWORD=changeme/POSTGRES_PASSWORD=<strong-password>/' \
  ~/.local/share/mycelium/deployments/{project}/.env
```

### Network Security

```yaml
# Bind only to localhost
services:
  postgres:
    ports:
      - "127.0.0.1:5432:5432"
  temporal:
    ports:
      - "127.0.0.1:7233:7233"
      - "127.0.0.1:8080:8080"
```

### Data Persistence

```bash
# Backup PostgreSQL data
docker exec {project}-postgres pg_dump -U postgres temporal > backup.sql

# Restore from backup
docker exec -i {project}-postgres psql -U postgres temporal < backup.sql
```

## Advanced Topics

### Custom Temporal Namespaces

```bash
# Create additional namespace
docker exec {project}-temporal tctl namespace register --namespace production

# List all namespaces
docker exec {project}-temporal tctl namespace list
```

### Scaling Considerations

For high-throughput deployments:

1. **Horizontal Scaling**: Run multiple Temporal workers
2. **PostgreSQL Replication**: Set up read replicas
3. **Load Balancing**: Use nginx/HAProxy for gRPC
4. **Resource Limits**: Set memory/CPU limits in docker-compose

### Integration with CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Deploy Temporal
  run: |
    uv run mycelium deploy start --yes
    uv run python tests/integration/deployment/test_deployment_validation.py
```

## References

- [Temporal Documentation](https://docs.temporal.io/)
- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [Sprint 3 - PostgreSQL Compatibility System](/home/gerald/git/mycelium/mycelium_onboarding/deployment/postgres/)
- [Deployment Validation API](/home/gerald/git/mycelium/mycelium_onboarding/deployment/validation/)

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Run validation: `uv run python test_deployment_validation.py`
- Review troubleshooting section above
- File issue with deployment report attached

---

**Last Updated**: 2025-11-09
**Version**: 1.0.0
**Maintainer**: DevOps Team
