# Mycelium Deployment Guide

Production deployment, infrastructure monitoring, Docker/Kubernetes templates, and scalability guidelines for the
Mycelial network.

## Table of Contents

1. [Infrastructure Requirements](#infrastructure-requirements)
1. [Docker Deployment](#docker-deployment)
1. [Kubernetes Deployment](#kubernetes-deployment)
1. [Service Discovery](#service-discovery)
1. [Health Monitoring](#health-monitoring)
1. [Scalability Guidelines](#scalability-guidelines)
1. [Production Best Practices](#production-best-practices)
1. [Troubleshooting](#troubleshooting)

## Infrastructure Requirements

### Minimal (Markdown Mode)

**Resources**:

- RAM: 100MB
- CPU: 1 core
- Disk: 10MB
- Network: None required

**Use Cases**:

- Single-user development
- Offline workflows
- Git-tracked coordination

### Recommended (Redis Mode)

**Resources**:

- RAM: 500MB (Redis: 256MB, Agents: 256MB)
- CPU: 2 cores
- Disk: 50MB
- Network: Local or LAN

**Use Cases**:

- Multi-agent collaboration
- Real-time workflows
- Production deployments

### Production (Redis + Temporal)

**Resources**:

- RAM: 2GB (Redis: 512MB, Temporal: 1GB, Agents: 512MB)
- CPU: 4 cores
- Disk: 500MB (Temporal persistence)
- Network: Low-latency LAN or data center

**Use Cases**:

- Durable workflows
- Multi-machine coordination
- Enterprise deployments

## Docker Deployment

### Docker Compose (Recommended)

Complete stack with Redis, Temporal, and monitoring:

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"  # gRPC
      - "8233:8233"  # Web UI
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgres
    depends_on:
      - postgres

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
    volumes:
      - postgres-data:/var/lib/postgresql/data

  # Optional: Redis Commander (GUI)
  redis-commander:
    image: rediscommander/redis-commander:latest
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
    depends_on:
      - redis

volumes:
  redis-data:
  postgres-data:
```

**Start services**:

```bash
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f redis

# Health check
/infra-check

# Stop services
docker-compose down
```

### Individual Containers

**Redis only**:

```bash
docker run -d \
  --name mycelium-redis \
  -p 6379:6379 \
  -v mycelium-redis-data:/data \
  redis:latest \
  redis-server --appendonly yes

# Verify
docker exec mycelium-redis redis-cli ping
```

**Valkey (Redis fork)**:

```bash
docker run -d \
  --name mycelium-valkey \
  -p 6379:6379 \
  -v mycelium-valkey-data:/data \
  valkey/valkey:latest

# Verify
docker exec mycelium-valkey valkey-cli ping
```

## Kubernetes Deployment

### Redis Deployment

```yaml
# k8s/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mycelium-redis
  namespace: mycelium
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:latest
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: mycelium-redis
  namespace: mycelium
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: mycelium
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**Deploy**:

```bash
kubectl create namespace mycelium
kubectl apply -f k8s/redis-deployment.yaml

# Verify
kubectl get pods -n mycelium
kubectl logs -n mycelium -l app=redis

# Test connection
kubectl run -it --rm redis-test \
  --image=redis:latest \
  --restart=Never \
  --namespace=mycelium \
  -- redis-cli -h mycelium-redis ping
```

### Temporal Deployment

```yaml
# k8s/temporal-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mycelium-temporal
  namespace: mycelium
spec:
  replicas: 1
  selector:
    matchLabels:
      app: temporal
  template:
    metadata:
      labels:
        app: temporal
    spec:
      containers:
      - name: temporal
        image: temporalio/auto-setup:latest
        ports:
        - containerPort: 7233
          name: grpc
        - containerPort: 8233
          name: web
        env:
        - name: DB
          value: "postgresql"
        - name: POSTGRES_SEEDS
          value: "postgres"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PWD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password

---
apiVersion: v1
kind: Service
metadata:
  name: mycelium-temporal
  namespace: mycelium
spec:
  selector:
    app: temporal
  ports:
  - port: 7233
    targetPort: 7233
    name: grpc
  - port: 8233
    targetPort: 8233
    name: web
  type: ClusterIP
```

### ConfigMap for Agent Configuration

```yaml
# k8s/agent-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mycelium-config
  namespace: mycelium
data:
  config.json: |
    {
      "coordination": {
        "mode": "redis",
        "redis": {
          "url": "redis://mycelium-redis:6379",
          "db": 0,
          "connection_timeout_seconds": 5
        }
      },
      "temporal": {
        "enabled": true,
        "host": "mycelium-temporal:7233"
      }
    }
```

## Service Discovery

### DNS-Based Discovery (Kubernetes)

```javascript
// Auto-detect services in Kubernetes cluster
import { CoordinationClient } from 'mycelium/lib/coordination.js';

const client = new CoordinationClient({
  mode: 'redis',
  redis: {
    // Kubernetes DNS: <service-name>.<namespace>.svc.cluster.local
    url: process.env.REDIS_URL || 'redis://mycelium-redis.mycelium.svc.cluster.local:6379'
  }
});
await client.initialize();
```

### Environment-Based Discovery

```bash
# Set in deployment manifest or .env
export REDIS_URL="redis://mycelium-redis:6379"
export TEMPORAL_HOST="mycelium-temporal:7233"
export COORDINATION_MODE="redis"

# Or via Kubernetes secrets
kubectl create secret generic mycelium-env \
  --from-literal=REDIS_URL=redis://mycelium-redis:6379 \
  --namespace=mycelium
```

### Health Check Script

```bash
#!/bin/bash
# .infra-check.sh - Custom service discovery

discover_redis() {
    # Try common locations
    for host in \
        "mycelium-redis.mycelium.svc.cluster.local" \
        "mycelium-redis" \
        "redis" \
        "localhost"; do

        if redis-cli -h "$host" ping &>/dev/null; then
            echo "redis://$host:6379"
            return 0
        fi
    done
    return 1
}

discover_temporal() {
    for host in \
        "mycelium-temporal.mycelium.svc.cluster.local" \
        "mycelium-temporal" \
        "temporal" \
        "localhost"; do

        if tctl --address "$host:7233" cluster health &>/dev/null; then
            echo "$host:7233"
            return 0
        fi
    done
    return 1
}

REDIS_URL=$(discover_redis)
TEMPORAL_HOST=$(discover_temporal)

export REDIS_URL TEMPORAL_HOST
```

## Health Monitoring

### Infrastructure Health Check

Use the built-in `/infra-check` command:

```bash
# Quick check
/infra-check

# Detailed diagnostics
/infra-check --verbose

# Custom config
/infra-check --config .infra-check.json

# Output to file
/infra-check --output health-report.json
```

### Configuration

**`.infra-check.json`**:

```json
{
  "checks": {
    "redis": {
      "enabled": true,
      "url": "${REDIS_URL:-redis://localhost:6379}",
      "timeout_seconds": 5,
      "critical": true
    },
    "temporal": {
      "enabled": true,
      "host": "${TEMPORAL_HOST:-localhost:7233}",
      "timeout_seconds": 10,
      "critical": false
    },
    "taskqueue": {
      "enabled": false
    },
    "gpu": {
      "enabled": false
    },
    "postgresql": {
      "enabled": false,
      "connection_string": "${DATABASE_URL}"
    },
    "custom_services": [
      {
        "name": "model-server",
        "url": "http://localhost:8080/health",
        "timeout_seconds": 3,
        "critical": false
      }
    ]
  },
  "alerting": {
    "on_failure": "email",
    "email": "ops@example.com",
    "slack_webhook": "${SLACK_WEBHOOK_URL}"
  }
}
```

### Monitoring Endpoints

**Redis metrics**:

```bash
# Memory usage
redis-cli info memory

# Client connections
redis-cli info clients

# Operations per second
redis-cli info stats | grep instantaneous_ops_per_sec

# Key space
redis-cli dbsize
```

**Temporal metrics**:

```bash
# Cluster health
tctl cluster health

# Workflow status
tctl workflow list

# Worker status
tctl task-queue describe --task-queue mycelium-tasks
```

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'redis'
    static_configs:
      - targets: ['mycelium-redis:6379']
    metrics_path: '/metrics'

  - job_name: 'temporal'
    static_configs:
      - targets: ['mycelium-temporal:8080']
```

## Scalability Guidelines

### Performance Benchmarks

**Redis Mode**:

- **Agents**: Scales to 100+ concurrent agents
- **Throughput**: 234K messages/min
- **Latency**: 0.8ms avg
- **Overhead**: \<5%

**TaskQueue Mode**:

- **Agents**: Scales to 50+ concurrent agents
- **Throughput**: 3K tasks/min
- **Latency**: 100ms avg
- **Overhead**: ~10%

**Markdown Mode**:

- **Agents**: Scales to 20 concurrent agents
- **Throughput**: 6K operations/min
- **Latency**: 500ms avg
- **Overhead**: ~20%

### Horizontal Scaling

**Redis Cluster** (for >100 agents):

```bash
# Create Redis cluster with 3 masters + 3 replicas
docker-compose -f docker-compose-cluster.yml up -d

# Or Kubernetes StatefulSet
kubectl apply -f k8s/redis-cluster.yaml
```

**Multi-Region Deployment**:

```
Region 1 (us-east)              Region 2 (eu-west)
┌─────────────────┐             ┌─────────────────┐
│ Redis Master    │<──repl──────│ Redis Replica   │
│ Temporal        │             │ Temporal Worker │
│ Agents (50)     │             │ Agents (50)     │
└─────────────────┘             └─────────────────┘
```

### Vertical Scaling

**Resource allocation**:

```yaml
# k8s/redis-deployment.yaml (scaled up)
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Load Balancing

**Agent distribution**:

```javascript
// Distribute agents across Redis shards
const agents = ['ai-engineer', 'data-engineer', ...];

for (const agent of agents) {
  const shard = hash(agent) % NUM_SHARDS;
  const client = new CoordinationClient({
    redis: { url: `redis://shard-${shard}:6379` }
  });
  await client.storeAgentStatus(agent, status);
}
```

## Production Best Practices

### High Availability

**Redis Sentinel** (automatic failover):

```bash
docker run -d \
  --name redis-sentinel \
  -p 26379:26379 \
  redis:latest \
  redis-sentinel /etc/redis/sentinel.conf
```

**Configuration**:

```conf
# sentinel.conf
sentinel monitor mycelium-redis redis-master 6379 2
sentinel down-after-milliseconds mycelium-redis 5000
sentinel failover-timeout mycelium-redis 10000
```

### Data Persistence

**Redis AOF** (append-only file):

```bash
# Enable in redis.conf or command-line
redis-server --appendonly yes --appendfsync everysec

# Backup AOF file
cp /data/appendonly.aof /backup/appendonly-$(date +%Y%m%d).aof
```

**Temporal persistence**:

```yaml
# Use PostgreSQL for durable workflow state
environment:
  - DB=postgresql
  - POSTGRES_SEEDS=postgres.mycelium.svc.cluster.local
```

### Security

**Redis authentication**:

```bash
# Set password
redis-cli CONFIG SET requirepass "your-strong-password"

# Or in redis.conf
requirepass your-strong-password

# Connect with password
export REDIS_URL="redis://:your-strong-password@localhost:6379"
```

**TLS encryption**:

```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 \
  -keyout redis-key.pem \
  -out redis-cert.pem \
  -days 365 -nodes

# Enable TLS in redis.conf
tls-port 6380
tls-cert-file /tls/redis-cert.pem
tls-key-file /tls/redis-key.pem

# Connect with TLS
export REDIS_URL="rediss://localhost:6380"
```

**Network policies** (Kubernetes):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mycelium-network-policy
  namespace: mycelium
spec:
  podSelector:
    matchLabels:
      app: redis
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: mycelium
    ports:
    - protocol: TCP
      port: 6379
```

### Backup & Recovery

**Automated backups**:

```bash
#!/bin/bash
# backup-mycelium.sh

# Redis backup
redis-cli --rdb /backup/redis-$(date +%Y%m%d-%H%M%S).rdb

# Temporal backup (PostgreSQL)
pg_dump -U temporal temporal > /backup/temporal-$(date +%Y%m%d-%H%M%S).sql

# Rotate old backups (keep last 7 days)
find /backup -name "*.rdb" -mtime +7 -delete
find /backup -name "*.sql" -mtime +7 -delete
```

**Automated with cron**:

```cron
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-mycelium.sh
```

## Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
docker ps | grep redis

# Check logs
docker logs mycelium-redis

# Test connection
redis-cli ping

# Check network connectivity (Kubernetes)
kubectl run -it --rm debug \
  --image=redis:latest \
  --restart=Never \
  -- redis-cli -h mycelium-redis ping
```

### Temporal Connection Issues

```bash
# Check if Temporal is running
docker ps | grep temporal

# Check health
tctl cluster health

# View logs
docker logs mycelium-temporal

# Test from pod (Kubernetes)
kubectl run -it --rm tctl-debug \
  --image=temporalio/tctl:latest \
  --restart=Never \
  -- cluster health --address mycelium-temporal:7233
```

### Performance Issues

**Redis slow queries**:

```bash
# Enable slow log
redis-cli CONFIG SET slowlog-log-slower-than 10000  # 10ms

# View slow queries
redis-cli SLOWLOG GET 10
```

**Memory issues**:

```bash
# Check memory usage
redis-cli INFO memory

# Check max memory setting
redis-cli CONFIG GET maxmemory

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

**Network latency**:

```bash
# Measure Redis latency
redis-cli --latency

# Measure from specific location
redis-cli --latency -h mycelium-redis.mycelium.svc.cluster.local
```

### Scaling Issues

**Too many connections**:

```bash
# Check current connections
redis-cli INFO clients

# Increase max clients
redis-cli CONFIG SET maxclients 10000

# Use connection pooling in clients
```

**High CPU usage**:

```bash
# Check CPU usage
top -p $(pgrep redis-server)

# Identify expensive commands
redis-cli --bigkeys

# Consider sharding or clustering
```

## Next Steps

- **Read [onboarding.md](./onboarding.md)** - Complete installation guide
- **Read [coordination.md](./coordination.md)** - Coordination patterns and API
- **Read [agents.md](./agents.md)** - Agent development and management
- **See [examples/](../../docs/examples/)** - Production deployment examples

## Support

- **Documentation**: [.mycelium/modules/](./)
- **Issues**: https://github.com/gsornsen/mycelium/issues
- **Main README**: [README.md](../../README.md)
