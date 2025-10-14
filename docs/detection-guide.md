# Service Detection Guide

Complete guide to using Mycelium's automated service detection system for discovering and configuring infrastructure services.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Detect All Services](#detect-all-services)
- [Individual Service Detection](#individual-service-detection)
- [Output Formats](#output-formats)
- [Configuration Integration](#configuration-integration)
- [Understanding Detection Results](#understanding-detection-results)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

The Mycelium service detection system automatically discovers available infrastructure services on your system, including:

- **Docker**: Container runtime availability and version
- **Redis**: In-memory data store instances on common ports
- **PostgreSQL**: Relational database instances
- **Temporal**: Workflow orchestration server
- **GPU Hardware**: NVIDIA, AMD, and Intel GPU devices

Detection runs in parallel for optimal performance, completing all checks in under 5 seconds.

### Key Features

- Parallel execution for fast detection (<5s total)
- Multiple output formats (text, JSON, YAML)
- Automatic configuration file updates
- Multi-instance detection (Redis/PostgreSQL on different ports)
- Multi-vendor GPU support (NVIDIA, AMD, Intel)
- Graceful error handling for unavailable services
- Zero external dependencies for detection

## Quick Start

### Detect All Services

Run comprehensive detection of all available services:

```bash
mycelium detect services
```

Output example:
```
Service Detection Report
================================================================================
Detection completed in 2.34s

Docker:
  Status: Available
  Version: 24.0.5
  Socket: /var/run/docker.sock

Redis:
  Status: Available
  Instances: 1
    1. localhost:6379
       Version: 7.2.3

PostgreSQL:
  Status: Available
  Instances: 1
    1. localhost:5432
       Version: 15.4

Temporal:
  Status: Available
  Frontend Port: 7233
  UI Port: 8233
  Version: 1.22.3

GPU:
  Status: Available
  Total GPUs: 1
  Total Memory: 24576 MB
    1. NVIDIA: NVIDIA RTX 3090
       Memory: 24576 MB
       Driver: 535.104.05
       CUDA: 12.2

Summary:
  Total Services Available: 5/5
```

### Save Detected Configuration

Automatically update your configuration file with detected settings:

```bash
mycelium detect services --save-config
```

This will:
1. Run all service detections
2. Update `~/.config/mycelium/mycelium.yaml` with detected ports and versions
3. Enable services that are detected
4. Preserve your existing custom settings

### JSON Output for Automation

For programmatic use or CI/CD pipelines:

```bash
mycelium detect services --format json
```

Output example:
```json
{
  "detection_time": 2.34,
  "docker": {
    "available": true,
    "version": "24.0.5",
    "socket_path": "/var/run/docker.sock",
    "error_message": null
  },
  "redis": {
    "available": true,
    "instances": [
      {
        "host": "localhost",
        "port": 6379,
        "version": "7.2.3",
        "password_required": false
      }
    ]
  },
  "postgres": {
    "available": true,
    "instances": [
      {
        "host": "localhost",
        "port": 5432,
        "version": "15.4",
        "authentication_method": "trust"
      }
    ]
  },
  "temporal": {
    "available": true,
    "frontend_port": 7233,
    "ui_port": 8233,
    "version": "1.22.3",
    "error_message": null
  },
  "gpu": {
    "available": true,
    "total_memory_mb": 24576,
    "gpus": [
      {
        "vendor": "nvidia",
        "model": "NVIDIA RTX 3090",
        "memory_mb": 24576,
        "driver_version": "535.104.05",
        "cuda_version": "12.2",
        "rocm_version": null,
        "index": 0
      }
    ],
    "error_message": null
  }
}
```

## Detect All Services

The `detect services` command performs comprehensive detection of all infrastructure services.

### Usage

```bash
mycelium detect services [OPTIONS]
```

### Options

- `--format [text|json|yaml]`: Output format (default: text)
- `--save-config`: Save detected settings to configuration file

### Examples

**Basic detection with human-readable output:**
```bash
mycelium detect services
```

**Detection with config save:**
```bash
mycelium detect services --save-config
```

**Machine-readable JSON output:**
```bash
mycelium detect services --format json > detection-results.json
```

**YAML output for configuration management:**
```bash
mycelium detect services --format yaml
```

### What Gets Detected

1. **Docker Daemon**
   - Availability status
   - Version information
   - Socket path location
   - Permission checks

2. **Redis Instances**
   - Scans ports: 6379, 6380, 6381
   - Connection status
   - Version information
   - Authentication requirements

3. **PostgreSQL Instances**
   - Scans ports: 5432, 5433
   - Connection status
   - Version information
   - Authentication method

4. **Temporal Server**
   - Frontend port (gRPC): 7233
   - UI port (HTTP): 8233
   - Version information
   - Namespace availability

5. **GPU Hardware**
   - NVIDIA GPUs (via nvidia-smi)
   - AMD GPUs (via rocm-smi)
   - Intel GPUs (via sycl-ls)
   - Memory capacity
   - Driver versions
   - CUDA/ROCm versions

## Individual Service Detection

Detect specific services independently for targeted diagnostics.

### Detect Docker

```bash
mycelium detect docker
```

Output:
```
Detecting Docker...

✓ Docker Available
  Version: 24.0.5
  Socket: /var/run/docker.sock
```

### Detect Redis

```bash
mycelium detect redis
```

Output:
```
Detecting Redis instances...

✓ Found 2 Redis instance(s)

  Instance 1:
    Host: localhost
    Port: 6379
    Version: 7.2.3

  Instance 2:
    Host: localhost
    Port: 6380
    Version: 7.2.3
    Auth: Required
```

### Detect PostgreSQL

```bash
mycelium detect postgres
```

Output:
```
Detecting PostgreSQL instances...

✓ Found 1 PostgreSQL instance(s)

  Instance 1:
    Host: localhost
    Port: 5432
    Version: 15.4
    Auth Method: trust
```

### Detect Temporal

```bash
mycelium detect temporal
```

Output:
```
Detecting Temporal server...

✓ Temporal Available
  Frontend Port: 7233
  UI Port: 8233
  Version: 1.22.3
```

### Detect GPU

```bash
mycelium detect gpu
```

Output:
```
Detecting GPUs...

✓ Found 2 GPU(s)
  Total Memory: 49152 MB

  GPU 1:
    Vendor: NVIDIA
    Model: NVIDIA RTX 3090
    Memory: 24576 MB
    Driver: 535.104.05
    CUDA: 12.2

  GPU 2:
    Vendor: AMD
    Model: AMD Radeon RX 7900 XTX
    Memory: 24576 MB
    Driver: 23.20
    ROCm: 5.7.0
```

## Output Formats

### Text Format (Default)

Human-readable format with clear sections and status indicators.

Best for:
- Interactive terminal use
- Manual diagnostics
- Initial setup and exploration

Example:
```bash
mycelium detect services
```

### JSON Format

Structured JSON for programmatic consumption.

Best for:
- CI/CD pipelines
- Automation scripts
- Integration with monitoring systems
- Parsing with jq or similar tools

Example:
```bash
mycelium detect services --format json | jq '.docker.version'
```

### YAML Format

YAML output for configuration management tools.

Best for:
- Ansible playbooks
- Configuration management
- Documentation generation
- Human-readable structured data

Example:
```bash
mycelium detect services --format yaml
```

## Configuration Integration

### Automatic Configuration Updates

The `--save-config` flag automatically updates your Mycelium configuration with detected values:

```bash
mycelium detect services --save-config
```

**What happens:**

1. Runs full service detection
2. Loads existing configuration (or creates default)
3. Updates detected service settings:
   - Enables services that are available
   - Updates port numbers from detected instances
   - Updates version information
   - Preserves custom configuration values
4. Saves configuration to `~/.config/mycelium/mycelium.yaml`

**Example workflow:**

```bash
# Initial setup
mycelium config init

# Detect and configure services
mycelium detect services --save-config

# Verify configuration
mycelium config show
```

### Configuration Update Behavior

**Services Detected:**
- Service is enabled in config
- Port is set to first detected instance
- Version is updated if detected

**Services Not Detected:**
- Service is disabled in config
- Port number is preserved (for manual configuration)
- Version is preserved

**Custom Settings Preserved:**
- Project name
- Memory limits (Redis max_memory)
- Database names
- Connection pool sizes
- All other non-detected settings

### Manual Integration

You can also manually integrate detection results into your workflow:

```bash
# Save detection results
mycelium detect services --format json > detection.json

# Parse and use in your scripts
cat detection.json | jq '.redis.instances[0].port'
```

## Understanding Detection Results

### Status Indicators

- **Available**: Service is running and accessible
- **Not Available**: Service is not running or not accessible
- **Error**: Specific error message indicating why detection failed

### Docker Detection

**What's checked:**
- Docker daemon is running
- Docker socket is accessible
- User has permission to access Docker

**Common states:**
- Available + version: Docker is fully functional
- Not Available: Docker not installed or not running
- Permission Error: User needs to be added to docker group

### Redis Detection

**What's checked:**
- Redis server is listening on common ports (6379, 6380, 6381)
- Connection can be established
- INFO command responds (for version detection)

**Common states:**
- Available + version: Redis is fully functional
- Password Required: Redis requires authentication
- Not Available: No Redis instances found on scanned ports

### PostgreSQL Detection

**What's checked:**
- PostgreSQL server is listening on common ports (5432, 5433)
- Connection can be established
- Version information is accessible

**Common states:**
- Available + version: PostgreSQL is fully functional
- Authentication Required: Database requires credentials
- Not Available: No PostgreSQL instances found on scanned ports

### Temporal Detection

**What's checked:**
- Temporal frontend (gRPC) is accessible on port 7233
- Temporal UI is accessible on port 8233
- Version information from health endpoint

**Common states:**
- Available + version: Temporal is fully functional
- Connection Refused: Temporal server not running
- Not Available: Temporal not installed or not configured

### GPU Detection

**What's checked:**
- NVIDIA GPUs: nvidia-smi command available and responsive
- AMD GPUs: rocm-smi command available and responsive
- Intel GPUs: sycl-ls command available and responsive

**Information extracted:**
- GPU model and vendor
- Total memory capacity
- Driver version
- CUDA version (NVIDIA)
- ROCm version (AMD)

**Common states:**
- Available + devices: GPUs detected and accessible
- Not Available: No GPU hardware or drivers not installed
- Driver Error: GPU present but driver issues detected

## Performance

### Detection Time

The detection system is optimized for speed through parallel execution:

- **Target**: <5 seconds for all detections
- **Typical**: 2-3 seconds with all services available
- **Individual**: <1 second per service

### Performance Optimization

Detection uses concurrent execution via ThreadPoolExecutor:
- All 5 detectors run in parallel
- Individual timeouts prevent hanging
- Failed detections don't block others

### Benchmarking

Check detection performance on your system:

```bash
# Run multiple times and check timing
for i in {1..5}; do
  mycelium detect services --format json | jq '.detection_time'
done
```

## Troubleshooting

### No Services Detected

**Issue**: Detection shows no services available

**Solutions:**
1. Verify services are actually running:
   ```bash
   # Check Docker
   systemctl status docker  # or: docker ps

   # Check Redis
   redis-cli ping

   # Check PostgreSQL
   psql -c "SELECT version();"

   # Check Temporal
   tctl cluster health
   ```

2. Check firewall/network settings
3. Verify services are listening on expected ports:
   ```bash
   netstat -tlnp | grep -E '6379|5432|7233|8233'
   ```

### Permission Errors

**Issue**: "Permission denied" errors during detection

**Docker Permission Error:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker ps
```

**PostgreSQL Connection Error:**
```bash
# Update pg_hba.conf for trust authentication (development only)
# Or set proper credentials in your application
```

### Slow Detection

**Issue**: Detection takes longer than 5 seconds

**Diagnostics:**
```bash
# Check network latency
ping localhost

# Check service health
docker ps -a
redis-cli ping
psql -c "SELECT 1;"
```

**Solutions:**
1. Ensure services are local (remote services are slower)
2. Check for network issues or DNS resolution problems
3. Verify no firewall rules causing timeouts

### Incorrect Version Information

**Issue**: Version shows as "unknown" or incorrect

**Causes:**
- Service doesn't expose version via standard methods
- Insufficient permissions to query version
- Service is behind proxy/load balancer

**Solutions:**
1. Verify direct access to service
2. Check service logs for version information
3. Manually set version in configuration if needed

### GPU Not Detected

**Issue**: GPU hardware present but not detected

**Solutions:**

**NVIDIA:**
```bash
# Verify nvidia-smi works
nvidia-smi

# If not working, reinstall drivers
# Ubuntu/Debian:
sudo apt install nvidia-driver-535

# Verify CUDA
nvcc --version
```

**AMD:**
```bash
# Verify ROCm installation
rocm-smi

# If not working, install ROCm
# See: https://rocmdocs.amd.com/
```

**Intel:**
```bash
# Verify Intel GPU support
sycl-ls

# Install Intel oneAPI if needed
```

### Multiple Instances Not Detected

**Issue**: Only one Redis/PostgreSQL instance detected, but multiple are running

**Cause**: Services running on non-standard ports

**Solution:**
Detection scans these ports:
- Redis: 6379, 6380, 6381
- PostgreSQL: 5432, 5433

For other ports, manually configure in `mycelium.yaml`:

```yaml
services:
  redis:
    enabled: true
    port: 6400  # Your custom port

  postgres:
    enabled: true
    port: 5555  # Your custom port
```

## Advanced Usage

### Scripting and Automation

**Check if services are ready before deployment:**

```bash
#!/bin/bash
# wait-for-services.sh

echo "Waiting for required services..."

RESULT=$(mycelium detect services --format json)

DOCKER=$(echo $RESULT | jq -r '.docker.available')
REDIS=$(echo $RESULT | jq -r '.redis.available')
POSTGRES=$(echo $RESULT | jq -r '.postgres.available')

if [[ "$DOCKER" == "true" ]] && [[ "$REDIS" == "true" ]] && [[ "$POSTGRES" == "true" ]]; then
  echo "All services ready!"
  exit 0
else
  echo "Services not ready. Please start required services."
  exit 1
fi
```

**Extract specific values:**

```bash
# Get Redis port
REDIS_PORT=$(mycelium detect services --format json | jq -r '.redis.instances[0].port')

# Get PostgreSQL version
PG_VERSION=$(mycelium detect services --format json | jq -r '.postgres.instances[0].version')

# Get GPU memory
GPU_MEMORY=$(mycelium detect services --format json | jq -r '.gpu.total_memory_mb')
```

### CI/CD Integration

**GitHub Actions example:**

```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Detect Services
        run: |
          mycelium detect services --format json > detection.json
          cat detection.json

      - name: Validate Environment
        run: |
          DOCKER_AVAILABLE=$(jq -r '.docker.available' detection.json)
          if [[ "$DOCKER_AVAILABLE" != "true" ]]; then
            echo "Docker not available"
            exit 1
          fi

      - name: Deploy
        run: |
          # Your deployment steps
```

### Custom Detection Workflows

**Detect, configure, and start services:**

```bash
#!/bin/bash
# auto-setup.sh

# Detect services
echo "Detecting services..."
mycelium detect services --save-config

# Show configuration
echo "Current configuration:"
mycelium config show

# Start missing services (example)
if ! mycelium detect docker | grep -q "Available"; then
  echo "Starting Docker..."
  sudo systemctl start docker
fi

# Verify all services ready
mycelium detect services
```

### Integration with Monitoring

**Export detection results to monitoring system:**

```bash
# Export to Prometheus format
mycelium detect services --format json | jq -r '
  "mycelium_docker_available \(.docker.available | if . then 1 else 0 end)",
  "mycelium_redis_available \(.redis.available | if . then 1 else 0 end)",
  "mycelium_postgres_available \(.postgres.available | if . then 1 else 0 end)",
  "mycelium_temporal_available \(.temporal.available | if . then 1 else 0 end)",
  "mycelium_gpu_available \(.gpu.available | if . then 1 else 0 end)",
  "mycelium_gpu_count \(.gpu.gpus | length)",
  "mycelium_gpu_memory_mb \(.gpu.total_memory_mb)",
  "mycelium_detection_time_seconds \(.detection_time)"
'
```

## Related Documentation

- [Configuration Guide](configuration-guide.md) - Managing Mycelium configuration
- [API Reference](detection-reference.md) - Complete API documentation
- [Integration Guide](detection-integration.md) - Integrating detection into your application
- [Troubleshooting](troubleshooting-environment.md) - Environment troubleshooting

## See Also

- [M01 Environment Activation](environment-activation.md)
- [M02 Configuration System](configuration-guide.md)
- [Architecture Overview](ARCHITECTURE_DIAGRAMS.md)

---

For issues, questions, or contributions, visit: https://github.com/gsornsen/mycelium
