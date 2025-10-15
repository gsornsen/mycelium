# Deployment Generation Guide

Complete guide to generating and managing Mycelium deployments.

## Overview

The Mycelium deployment system generates production-ready configurations for multiple deployment methods:

- **Docker Compose** - Container orchestration for development and small-scale deployments
- **Kubernetes** - Cloud-native deployments with horizontal scalability
- **systemd** - Native Linux service management for traditional infrastructure

All deployment configurations are generated from your `mycelium.yaml` configuration file using Jinja2 templates, ensuring consistency and reproducibility across environments.

## Quick Start

### 1. Initialize Configuration

First, run the interactive wizard to create your configuration:

```bash
mycelium init
```

This will guide you through:
- Service detection
- Service selection and configuration
- Deployment method selection
- Advanced configuration options

### 2. Generate Deployment

Generate deployment files based on your configuration:

```bash
# Use deployment method from config
mycelium deploy generate

# Specify method explicitly
mycelium deploy generate --method kubernetes

# Custom output directory
mycelium deploy generate --output ./my-deployment

# Skip secrets generation
mycelium deploy generate --no-secrets
```

### 3. Start Services

Start the deployed services:

```bash
mycelium deploy start
```

### 4. Check Status

Monitor your services:

```bash
mycelium deploy status
```

## Deployment Methods

### Docker Compose

Docker Compose provides the simplest deployment method, ideal for development environments and single-host deployments.

#### Generated Files

- `docker-compose.yml` - Service definitions
- `.env` - Environment variables and credentials
- `README.md` - Usage instructions

#### Configuration Example

```yaml
project_name: my-project
deployment:
  method: docker-compose
  auto_start: true
  healthcheck_timeout: 60
services:
  redis:
    enabled: true
    port: 6379
    persistence: true
    max_memory: 256mb
  postgres:
    enabled: true
    port: 5432
    database: myapp
    max_connections: 100
```

#### Deployment Steps

1. **Review credentials** in `.env` file:
   ```bash
   cd ~/.local/share/mycelium/deployments/my-project
   vim .env
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```bash
   docker-compose ps
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Stop services**:
   ```bash
   docker-compose down
   ```

#### Service Configuration

**Redis Configuration:**
```yaml
services:
  redis:
    enabled: true
    port: 6379
    persistence: true      # Enable RDB snapshots
    max_memory: 256mb      # Memory limit
    version: "7-alpine"    # Optional specific version
```

**PostgreSQL Configuration:**
```yaml
services:
  postgres:
    enabled: true
    port: 5432
    database: myapp
    max_connections: 100
    version: "15-alpine"   # Optional specific version
```

**Temporal Configuration:**
```yaml
services:
  temporal:
    enabled: true
    ui_port: 8080
    frontend_port: 7233
    namespace: default
```

#### Volumes and Persistence

Docker Compose automatically creates named volumes for data persistence:

- `{project}-redis-data` - Redis RDB snapshots
- `{project}-postgres-data` - PostgreSQL data directory
- `{project}-temporal-data` - Temporal server data

To remove all data (destructive):
```bash
docker-compose down -v
```

#### Networking

All services are connected via a dedicated bridge network named `{project}-network`, allowing inter-service communication using service names as hostnames.

#### Common Issues

**Port conflicts:**
```bash
# Error: port is already allocated
# Solution: Change port in config and regenerate
```

**Permission errors:**
```bash
# Error: permission denied
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Container won't start:**
```bash
# Check logs for specific error
docker-compose logs redis
```

### Kubernetes

Kubernetes deployment provides production-grade orchestration with automatic scaling, self-healing, and rolling updates.

#### Generated Files

- `kubernetes/00-namespace.yaml` - Dedicated namespace
- `kubernetes/10-redis.yaml` - Redis Deployment and Service
- `kubernetes/20-postgres.yaml` - PostgreSQL StatefulSet and Service
- `kubernetes/30-temporal.yaml` - Temporal Deployment and Service
- `kubernetes/kustomization.yaml` - Kustomize configuration
- `kubernetes/README.md` - Usage instructions

#### Configuration Example

```yaml
project_name: my-k8s-app
deployment:
  method: kubernetes
  healthcheck_timeout: 120
services:
  redis:
    enabled: true
    port: 6379
  postgres:
    enabled: true
    port: 5432
    database: production_db
```

#### Deployment Steps

1. **Review manifests**:
   ```bash
   cd ~/.local/share/mycelium/deployments/my-k8s-app/kubernetes
   ```

2. **Apply using Kustomize** (recommended):
   ```bash
   kubectl apply -k .
   ```

   Or **apply manually**:
   ```bash
   kubectl apply -f 00-namespace.yaml
   kubectl apply -f 10-redis.yaml
   kubectl apply -f 20-postgres.yaml
   ```

3. **Wait for pods to be ready**:
   ```bash
   kubectl wait --for=condition=ready pod --all \
       -n my-k8s-app --timeout=300s
   ```

4. **Check deployment status**:
   ```bash
   kubectl get all -n my-k8s-app
   ```

5. **View pod logs**:
   ```bash
   kubectl logs -f deployment/redis -n my-k8s-app
   ```

#### Resource Management

Generated manifests include sensible resource requests and limits:

**Redis:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**PostgreSQL:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

Adjust these based on your workload and cluster capacity.

#### Storage

PostgreSQL uses PersistentVolumeClaims (PVC) for data persistence. Ensure your cluster has:

1. **StorageClass configured**:
   ```bash
   kubectl get storageclass
   ```

2. **Sufficient storage quota**:
   ```bash
   kubectl describe namespace my-k8s-app
   ```

#### Service Access

Services are exposed within the cluster by default:

**Internal access:**
```bash
# From another pod in the same namespace
redis://redis:6379
postgresql://postgres:5432/mydb
```

**External access via port-forward:**
```bash
kubectl port-forward svc/redis 6379:6379 -n my-k8s-app
kubectl port-forward svc/postgres 5432:5432 -n my-k8s-app
```

**External access via LoadBalancer** (edit service type):
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  type: LoadBalancer  # Change from ClusterIP
  ports:
    - port: 6379
```

#### Scaling

Scale deployments horizontally:

```bash
# Scale Redis
kubectl scale deployment redis --replicas=3 -n my-k8s-app

# Scale with autoscaling
kubectl autoscale deployment redis \
    --cpu-percent=70 --min=2 --max=10 -n my-k8s-app
```

#### Updates and Rollbacks

**Rolling update:**
```bash
kubectl set image deployment/redis \
    redis=redis:7.2-alpine -n my-k8s-app
```

**Rollback:**
```bash
kubectl rollout undo deployment/redis -n my-k8s-app
```

**Check rollout status:**
```bash
kubectl rollout status deployment/redis -n my-k8s-app
```

#### Cleanup

**Delete all resources:**
```bash
kubectl delete -k .
# Or
kubectl delete namespace my-k8s-app
```

#### Common Issues

**ImagePullBackOff:**
```bash
# Check image name and registry access
kubectl describe pod <pod-name> -n my-k8s-app
```

**Pending pods:**
```bash
# Check resource availability
kubectl describe pod <pod-name> -n my-k8s-app
# Look for "Insufficient cpu" or "Insufficient memory"
```

**PVC not binding:**
```bash
# Check storage class and PVC status
kubectl get pvc -n my-k8s-app
kubectl describe pvc <pvc-name> -n my-k8s-app
```

### systemd

systemd deployment provides native Linux service management, ideal for traditional infrastructure and edge deployments.

#### Generated Files

- `systemd/{project}-redis.service` - Redis service unit
- `systemd/{project}-postgres.service` - PostgreSQL service unit
- `systemd/{project}-temporal.service` - Temporal service unit
- `systemd/install.sh` - Installation script
- `systemd/README.md` - Usage instructions

#### Prerequisites

Ensure required services are installed on the host:

**For Redis:**
```bash
# Debian/Ubuntu
sudo apt-get install redis-server

# RHEL/CentOS
sudo yum install redis

# Arch
sudo pacman -S redis
```

**For PostgreSQL:**
```bash
# Debian/Ubuntu
sudo apt-get install postgresql

# RHEL/CentOS
sudo yum install postgresql-server

# Arch
sudo pacman -S postgresql
```

#### Installation

1. **Review service files**:
   ```bash
   cd ~/.local/share/mycelium/deployments/my-project/systemd
   cat my-project-redis.service
   ```

2. **Run installation script**:
   ```bash
   sudo ./install.sh
   ```

   This will:
   - Copy service files to `/etc/systemd/system/`
   - Reload systemd daemon
   - Display enable/start instructions

3. **Enable services** (start on boot):
   ```bash
   sudo systemctl enable my-project-redis
   sudo systemctl enable my-project-postgres
   ```

4. **Start services**:
   ```bash
   sudo systemctl start my-project-redis
   sudo systemctl start my-project-postgres
   ```

#### Service Management

**Check status:**
```bash
systemctl status my-project-redis
```

**View logs:**
```bash
journalctl -u my-project-redis -f
```

**Restart service:**
```bash
sudo systemctl restart my-project-redis
```

**Stop service:**
```bash
sudo systemctl stop my-project-redis
```

**Disable service:**
```bash
sudo systemctl disable my-project-redis
```

#### Configuration

Service configuration files are typically located at:
- Redis: `/etc/redis/redis.conf`
- PostgreSQL: `/etc/postgresql/*/main/postgresql.conf`

After modifying configuration:
```bash
sudo systemctl restart my-project-redis
```

#### Uninstallation

1. **Stop and disable services**:
   ```bash
   sudo systemctl stop my-project-*
   sudo systemctl disable my-project-*
   ```

2. **Remove service files**:
   ```bash
   sudo rm /etc/systemd/system/my-project-*.service
   sudo systemctl daemon-reload
   ```

3. **Clean up data** (optional):
   ```bash
   sudo rm -rf /var/lib/redis/my-project
   sudo rm -rf /var/lib/postgresql/my-project
   ```

#### Common Issues

**Service fails to start:**
```bash
# Check detailed logs
journalctl -u my-project-redis -n 50 --no-pager

# Check service status
systemctl status my-project-redis -l
```

**Permission denied:**
```bash
# Ensure service user has permissions
sudo chown -R redis:redis /var/lib/redis/my-project
```

**Port already in use:**
```bash
# Find process using port
sudo lsof -i :6379
# or
sudo ss -tulpn | grep 6379
```

## Secrets Management

Mycelium includes secure secrets management for deployment credentials.

### Generating Secrets

Secrets are automatically generated when you run:

```bash
mycelium deploy generate
```

To skip secrets generation:
```bash
mycelium deploy generate --no-secrets
```

### Viewing Secrets

View secrets status (passwords are masked):

```bash
mycelium deploy secrets
```

Output:
```
┏━━━━━━━━━━━━┳━━━━━━━━┓
┃ Service    ┃ Status ┃
┡━━━━━━━━━━━━╇━━━━━━━━┩
│ PostgreSQL │ ✓ Set  │
│ Redis      │ ✓ Set  │
└────────────┴────────┘
```

### Rotating Secrets

Rotate a specific secret:

```bash
mycelium deploy secrets postgres --rotate
mycelium deploy secrets redis --rotate
mycelium deploy secrets temporal --rotate
```

After rotation, regenerate deployment files to apply changes:
```bash
mycelium deploy generate
```

### Secret Storage

Secrets are stored securely at:
```
~/.local/state/mycelium/secrets/{project-name}.json
```

File permissions are automatically set to `0600` (owner read/write only).

### Security Best Practices

1. **Never commit secrets to version control**
   ```bash
   echo ".env" >> .gitignore
   echo "secrets/" >> .gitignore
   ```

2. **Rotate secrets regularly**
   ```bash
   # Quarterly rotation recommended
   mycelium deploy secrets postgres --rotate
   ```

3. **Use different secrets per environment**
   ```bash
   # Development
   mycelium deploy generate --output dev/

   # Production (rotate first)
   mycelium deploy secrets postgres --rotate
   mycelium deploy generate --output prod/
   ```

4. **Backup secrets securely**
   ```bash
   # Encrypt before storing
   tar -czf secrets.tar.gz ~/.local/state/mycelium/secrets/
   gpg -c secrets.tar.gz
   rm secrets.tar.gz
   ```

## Troubleshooting

### General Issues

**Configuration not found:**
```bash
Error: No configuration file found

# Solution: Run init wizard
mycelium init
```

**Invalid configuration:**
```bash
# Validate configuration
mycelium config validate

# Fix errors and regenerate
mycelium deploy generate
```

### Docker Compose Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Verify Docker is running
docker ps

# Check disk space
df -h
```

**Network issues:**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

### Kubernetes Issues

**Pods stuck in Pending:**
```bash
# Check events
kubectl describe pod <pod-name> -n <namespace>

# Check node resources
kubectl top nodes

# Check PVC binding
kubectl get pvc -n <namespace>
```

**Services not accessible:**
```bash
# Verify service endpoints
kubectl get endpoints -n <namespace>

# Check network policies
kubectl get networkpolicies -n <namespace>
```

### systemd Issues

**Service won't start:**
```bash
# Check syntax
systemd-analyze verify /etc/systemd/system/my-service.service

# Check dependencies
systemctl list-dependencies my-service

# Enable debug logging
journalctl -u my-service -o verbose
```

## FAQ

### General Questions

**Q: Can I use multiple deployment methods?**

A: Yes! Generate different deployment methods to the same project:
```bash
mycelium deploy generate --method docker-compose --output compose/
mycelium deploy generate --method kubernetes --output k8s/
mycelium deploy generate --method systemd --output systemd/
```

**Q: How do I update my deployment after config changes?**

A: Regenerate the deployment files:
```bash
mycelium config set services.redis.port 6380
mycelium deploy generate
```

**Q: Can I customize the generated files?**

A: Yes, but they'll be overwritten on regeneration. For permanent changes, modify your configuration or extend the templates.

### Docker Compose Questions

**Q: How do I expose services to the network?**

A: Services are exposed on localhost by default. To expose on all interfaces, modify the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "0.0.0.0:6379:6379"  # Expose on all interfaces
```

**Q: How do I use a specific Docker image version?**

A: Specify version in your configuration:
```yaml
services:
  redis:
    version: "7.2-alpine"
```

### Kubernetes Questions

**Q: How do I use my own container registry?**

A: Modify the image references in the generated manifests:
```yaml
spec:
  containers:
  - name: redis
    image: my-registry.com/redis:7-alpine
```

**Q: How do I add resource limits?**

A: Edit the Deployment manifests to add or modify resources:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### systemd Questions

**Q: Can I run services as a different user?**

A: Yes, edit the service file:
```ini
[Service]
User=myuser
Group=mygroup
```

**Q: How do I add environment variables?**

A: Add them to the service file:
```ini
[Service]
Environment="MY_VAR=value"
EnvironmentFile=/etc/myproject/env
```

## Next Steps

1. **Explore Advanced Configuration**: See [Deployment API Reference](deployment-reference.md)
2. **Integrate Programmatically**: See [Deployment Integration Guide](deployment-integration.md)
3. **Customize Templates**: See the templates directory in your installation
4. **Set up Monitoring**: Add observability to your deployments
5. **Automate Deployments**: Create CI/CD pipelines using the CLI

## Support

- **Documentation**: https://github.com/gsornsen/mycelium
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Community**: Join our community discussions

---

*Generated with Mycelium Onboarding System*
