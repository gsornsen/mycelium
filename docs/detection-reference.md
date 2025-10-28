# Service Detection API Reference

Complete API documentation for all service detection modules in the Mycelium onboarding system.

## Table of Contents

- [Overview](#overview)
- [Orchestrator Module](#orchestrator-module)
- [Docker Detection](#docker-detection)
- [Redis Detection](#redis-detection)
- [PostgreSQL Detection](#postgresql-detection)
- [Temporal Detection](#temporal-detection)
- [GPU Detection](#gpu-detection)
- [Data Models](#data-models)
- [Type Definitions](#type-definitions)

## Overview

The detection system provides a comprehensive API for discovering infrastructure services and hardware. All detection
functions are non-blocking, thread-safe, and include built-in error handling.

**Import paths:**

```python
from mycelium_onboarding.detection import (
    detect_all,
    detect_all_async,
    DetectionSummary,
    generate_detection_report,
    update_config_from_detection,
)

from mycelium_onboarding.detection.docker_detector import detect_docker
from mycelium_onboarding.detection.redis_detector import detect_redis, scan_common_redis_ports
from mycelium_onboarding.detection.postgres_detector import detect_postgres, scan_common_postgres_ports
from mycelium_onboarding.detection.temporal_detector import detect_temporal
from mycelium_onboarding.detection.gpu_detector import detect_gpus
```

## Orchestrator Module

The orchestrator coordinates all detection modules and provides high-level APIs.

### detect_all()

Run all detections synchronously using parallel execution.

**Signature:**

```python
def detect_all() -> DetectionSummary
```

**Returns:**

- `DetectionSummary`: Complete detection results for all services

**Performance:**

- Target: \<5 seconds
- Typical: 2-3 seconds
- All detections run in parallel using ThreadPoolExecutor

**Example:**

```python
from mycelium_onboarding.detection import detect_all

summary = detect_all()

if summary.has_docker:
    print(f"Docker {summary.docker.version} available")

if summary.has_redis:
    for redis in summary.redis:
        print(f"Redis instance on port {redis.port}")

print(f"Detection completed in {summary.detection_time:.2f}s")
```

**Error Handling:**

- Individual detector failures are caught and returned as unavailable
- Network timeouts are handled gracefully
- Returns complete summary even if some services fail

______________________________________________________________________

### detect_all_async()

Async version of detect_all() for use in async contexts.

**Signature:**

```python
async def detect_all_async() -> DetectionSummary
```

**Returns:**

- `DetectionSummary`: Complete detection results for all services

**Example:**

```python
import asyncio
from mycelium_onboarding.detection import detect_all_async

async def main():
    summary = await detect_all_async()
    print(f"Found {len(summary.redis)} Redis instances")

asyncio.run(main())
```

**Usage:**

- Preferred in async applications (FastAPI, aiohttp, etc.)
- Uses same parallel execution as synchronous version
- Can be awaited alongside other async operations

______________________________________________________________________

### generate_detection_report()

Generate formatted detection report in multiple formats.

**Signature:**

```python
def generate_detection_report(
    summary: DetectionSummary,
    format: str = "text"
) -> str
```

**Parameters:**

- `summary` (DetectionSummary): Detection results to format
- `format` (str): Output format - "text", "json", or "yaml"

**Returns:**

- `str`: Formatted report string

**Raises:**

- `ValueError`: If format is not supported

**Example:**

```python
from mycelium_onboarding.detection import detect_all, generate_detection_report

summary = detect_all()

# Human-readable text
text_report = generate_detection_report(summary, format="text")
print(text_report)

# Machine-readable JSON
json_report = generate_detection_report(summary, format="json")
import json
data = json.loads(json_report)

# YAML for config management
yaml_report = generate_detection_report(summary, format="yaml")
```

______________________________________________________________________

### update_config_from_detection()

Update MyceliumConfig based on detection results.

**Signature:**

```python
def update_config_from_detection(
    summary: DetectionSummary,
    base_config: MyceliumConfig | None = None
) -> MyceliumConfig
```

**Parameters:**

- `summary` (DetectionSummary): Detection results
- `base_config` (MyceliumConfig | None): Optional base config to update

**Returns:**

- `MyceliumConfig`: Updated configuration with detected values

**Logic:**

- Enables services that are detected and available
- Updates ports from first detected instance
- Preserves existing custom configuration values
- Re-enables all services with defaults if nothing detected

**Example:**

```python
from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

# Detect services
summary = detect_all()

# Load existing config
manager = ConfigManager()
existing_config = manager.load()

# Update config with detected values
updated_config = update_config_from_detection(summary, existing_config)

# Save updated config
manager.save(updated_config)
```

______________________________________________________________________

### DetectionSummary

Summary dataclass containing all detection results.

**Definition:**

```python
@dataclass
class DetectionSummary:
    docker: DockerDetectionResult
    redis: list[RedisDetectionResult]
    postgres: list[PostgresDetectionResult]
    temporal: TemporalDetectionResult
    gpu: GPUDetectionResult
    detection_time: float  # Total time in seconds
```

**Properties:**

```python
@property
def has_docker(self) -> bool:
    """Check if Docker is available."""
    return self.docker.available

@property
def has_redis(self) -> bool:
    """Check if at least one Redis instance is available."""
    return any(r.available for r in self.redis)

@property
def has_postgres(self) -> bool:
    """Check if at least one PostgreSQL instance is available."""
    return any(p.available for p in self.postgres)

@property
def has_temporal(self) -> bool:
    """Check if Temporal is available."""
    return self.temporal.available

@property
def has_gpu(self) -> bool:
    """Check if at least one GPU is available."""
    return self.gpu.available
```

**Example:**

```python
summary = detect_all()

# Check availability
if summary.has_docker:
    print(f"Docker version: {summary.docker.version}")

# Access multiple instances
if summary.has_redis:
    print(f"Found {len(summary.redis)} Redis instance(s)")
    for i, redis in enumerate(summary.redis, 1):
        print(f"  {i}. {redis.host}:{redis.port}")

# Check detection performance
if summary.detection_time > 5.0:
    print("Warning: Detection took longer than expected")
```

## Docker Detection

Detect Docker daemon availability and version.

### detect_docker()

**Signature:**

```python
def detect_docker() -> DockerDetectionResult
```

**Returns:**

- `DockerDetectionResult`: Docker detection result

**Detection Method:**

- Attempts to import and use docker Python SDK
- Checks Docker socket accessibility
- Retrieves version information
- Validates user permissions

**Example:**

```python
from mycelium_onboarding.detection.docker_detector import detect_docker

result = detect_docker()

if result.available:
    print(f"Docker {result.version} available at {result.socket_path}")
else:
    print(f"Docker unavailable: {result.error_message}")
```

______________________________________________________________________

### verify_docker_permissions()

**Signature:**

```python
def verify_docker_permissions() -> tuple[bool, str]
```

**Returns:**

- `tuple[bool, str]`: (success, message)

**Purpose:**

- Check if current user has Docker permissions
- Provide helpful error messages for permission issues

**Example:**

```python
from mycelium_onboarding.detection.docker_detector import verify_docker_permissions

has_perms, message = verify_docker_permissions()
if not has_perms:
    print(f"Permission issue: {message}")
    print("Try: sudo usermod -aG docker $USER")
```

______________________________________________________________________

### DockerDetectionResult

**Definition:**

```python
@dataclass
class DockerDetectionResult:
    available: bool
    version: str | None
    socket_path: str | None
    error_message: str | None
```

**Fields:**

- `available`: Whether Docker daemon is accessible
- `version`: Docker version string (e.g., "24.0.5")
- `socket_path`: Path to Docker socket (e.g., "/var/run/docker.sock")
- `error_message`: Error description if unavailable

## Redis Detection

Detect Redis instances on common ports.

### scan_common_redis_ports()

Scan common Redis ports for active instances.

**Signature:**

```python
def scan_common_redis_ports(
    host: str = "localhost",
    ports: list[int] | None = None,
    timeout: float = 1.0
) -> list[RedisDetectionResult]
```

**Parameters:**

- `host` (str): Host to scan (default: "localhost")
- `ports` (list\[int\] | None): Ports to scan (default: \[6379, 6380, 6381\])
- `timeout` (float): Connection timeout in seconds (default: 1.0)

**Returns:**

- `list[RedisDetectionResult]`: List of detected Redis instances

**Example:**

```python
from mycelium_onboarding.detection.redis_detector import scan_common_redis_ports

# Scan default ports
instances = scan_common_redis_ports()
for redis in instances:
    print(f"Redis {redis.version} on port {redis.port}")

# Scan custom ports
custom_instances = scan_common_redis_ports(
    host="localhost",
    ports=[6379, 6400, 6500],
    timeout=2.0
)
```

______________________________________________________________________

### detect_redis()

Detect single Redis instance on specific port.

**Signature:**

```python
def detect_redis(
    host: str = "localhost",
    port: int = 6379,
    timeout: float = 1.0
) -> RedisDetectionResult
```

**Parameters:**

- `host` (str): Redis host
- `port` (int): Redis port
- `timeout` (float): Connection timeout in seconds

**Returns:**

- `RedisDetectionResult`: Detection result for specified instance

**Example:**

```python
from mycelium_onboarding.detection.redis_detector import detect_redis

result = detect_redis(host="localhost", port=6379)
if result.available:
    if result.password_required:
        print("Redis requires authentication")
    else:
        print(f"Redis {result.version} accessible")
```

______________________________________________________________________

### RedisDetectionResult

**Definition:**

```python
@dataclass
class RedisDetectionResult:
    available: bool
    host: str
    port: int
    version: str | None
    password_required: bool
    error_message: str | None
```

**Fields:**

- `available`: Whether Redis instance is accessible
- `host`: Redis host address
- `port`: Redis port number
- `version`: Redis version (e.g., "7.2.3")
- `password_required`: Whether authentication is required
- `error_message`: Error description if unavailable

## PostgreSQL Detection

Detect PostgreSQL instances on common ports.

### scan_common_postgres_ports()

Scan common PostgreSQL ports for active instances.

**Signature:**

```python
def scan_common_postgres_ports(
    host: str = "localhost",
    ports: list[int] | None = None,
    timeout: float = 2.0
) -> list[PostgresDetectionResult]
```

**Parameters:**

- `host` (str): Host to scan (default: "localhost")
- `ports` (list\[int\] | None): Ports to scan (default: \[5432, 5433\])
- `timeout` (float): Connection timeout in seconds (default: 2.0)

**Returns:**

- `list[PostgresDetectionResult]`: List of detected PostgreSQL instances

**Example:**

```python
from mycelium_onboarding.detection.postgres_detector import scan_common_postgres_ports

instances = scan_common_postgres_ports()
for pg in instances:
    print(f"PostgreSQL {pg.version} on port {pg.port}")
    print(f"  Auth method: {pg.authentication_method}")
```

______________________________________________________________________

### detect_postgres()

Detect single PostgreSQL instance on specific port.

**Signature:**

```python
def detect_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 2.0
) -> PostgresDetectionResult
```

**Parameters:**

- `host` (str): PostgreSQL host
- `port` (int): PostgreSQL port
- `timeout` (float): Connection timeout in seconds

**Returns:**

- `PostgresDetectionResult`: Detection result for specified instance

**Example:**

```python
from mycelium_onboarding.detection.postgres_detector import detect_postgres

result = detect_postgres(host="localhost", port=5432)
if result.available:
    print(f"PostgreSQL {result.version}")
    print(f"Authentication: {result.authentication_method}")
```

______________________________________________________________________

### PostgresDetectionResult

**Definition:**

```python
@dataclass
class PostgresDetectionResult:
    available: bool
    host: str
    port: int
    version: str | None
    authentication_method: str | None
    error_message: str | None
```

**Fields:**

- `available`: Whether PostgreSQL instance is accessible
- `host`: PostgreSQL host address
- `port`: PostgreSQL port number
- `version`: PostgreSQL version (e.g., "15.4")
- `authentication_method`: Auth method ("trust", "md5", "scram-sha-256", etc.)
- `error_message`: Error description if unavailable

## Temporal Detection

Detect Temporal workflow server.

### detect_temporal()

**Signature:**

```python
def detect_temporal(
    host: str = "localhost",
    frontend_port: int = 7233,
    ui_port: int = 8233,
    timeout: float = 2.0
) -> TemporalDetectionResult
```

**Parameters:**

- `host` (str): Temporal host (default: "localhost")
- `frontend_port` (int): gRPC frontend port (default: 7233)
- `ui_port` (int): Web UI port (default: 8233)
- `timeout` (float): Connection timeout in seconds

**Returns:**

- `TemporalDetectionResult`: Temporal detection result

**Detection Method:**

- Checks gRPC health endpoint on frontend port
- Checks HTTP health endpoint on UI port
- Retrieves version information if available

**Example:**

```python
from mycelium_onboarding.detection.temporal_detector import detect_temporal

result = detect_temporal()

if result.available:
    print(f"Temporal {result.version} available")
    print(f"  Frontend: localhost:{result.frontend_port}")
    print(f"  UI: http://localhost:{result.ui_port}")
else:
    print(f"Temporal unavailable: {result.error_message}")
```

______________________________________________________________________

### TemporalDetectionResult

**Definition:**

```python
@dataclass
class TemporalDetectionResult:
    available: bool
    frontend_port: int
    ui_port: int
    version: str | None
    error_message: str | None
```

**Fields:**

- `available`: Whether Temporal server is accessible
- `frontend_port`: gRPC frontend port (typically 7233)
- `ui_port`: Web UI port (typically 8233)
- `version`: Temporal version (e.g., "1.22.3")
- `error_message`: Error description if unavailable

## GPU Detection

Detect GPU hardware and capabilities.

### detect_gpus()

Detect all available GPUs (NVIDIA, AMD, Intel).

**Signature:**

```python
def detect_gpus() -> GPUDetectionResult
```

**Returns:**

- `GPUDetectionResult`: GPU detection result with all devices

**Detection Method:**

- NVIDIA: Parses nvidia-smi XML output
- AMD: Parses rocm-smi output
- Intel: Parses sycl-ls output

**Example:**

```python
from mycelium_onboarding.detection.gpu_detector import detect_gpus

result = detect_gpus()

if result.available:
    print(f"Found {len(result.gpus)} GPU(s)")
    print(f"Total memory: {result.total_memory_mb} MB")

    for gpu in result.gpus:
        print(f"\n{gpu.vendor.value.upper()}: {gpu.model}")
        print(f"  Memory: {gpu.memory_mb} MB")
        print(f"  Driver: {gpu.driver_version}")

        if gpu.cuda_version:
            print(f"  CUDA: {gpu.cuda_version}")
        if gpu.rocm_version:
            print(f"  ROCm: {gpu.rocm_version}")
else:
    print(f"No GPUs detected: {result.error_message}")
```

______________________________________________________________________

### GPUDetectionResult

**Definition:**

```python
@dataclass
class GPUDetectionResult:
    available: bool
    gpus: list[GPU]
    total_memory_mb: int
    error_message: str | None
```

**Fields:**

- `available`: Whether any GPUs are detected
- `gpus`: List of detected GPU devices
- `total_memory_mb`: Sum of memory across all GPUs
- `error_message`: Error description if none detected

______________________________________________________________________

### GPU

**Definition:**

```python
@dataclass
class GPU:
    vendor: GPUVendor
    model: str
    memory_mb: int | None
    driver_version: str | None
    cuda_version: str | None
    rocm_version: str | None
    index: int
```

**Fields:**

- `vendor`: GPU vendor (GPUVendor.NVIDIA, GPUVendor.AMD, GPUVendor.INTEL)
- `model`: GPU model name
- `memory_mb`: GPU memory in megabytes
- `driver_version`: Driver version string
- `cuda_version`: CUDA version (NVIDIA only)
- `rocm_version`: ROCm version (AMD only)
- `index`: Device index number

______________________________________________________________________

### GPUVendor

**Definition:**

```python
class GPUVendor(str, Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"
```

**Values:**

- `NVIDIA`: NVIDIA GPUs (detected via nvidia-smi)
- `AMD`: AMD GPUs (detected via rocm-smi)
- `INTEL`: Intel GPUs (detected via sycl-ls)
- `UNKNOWN`: Unknown or unrecognized vendor

## Data Models

### Summary of All Detection Result Types

| Service    | Result Type               | Multiple Instances  | Version Info           |
| ---------- | ------------------------- | ------------------- | ---------------------- |
| Docker     | `DockerDetectionResult`   | No                  | Yes                    |
| Redis      | `RedisDetectionResult`    | Yes                 | Yes                    |
| PostgreSQL | `PostgresDetectionResult` | Yes                 | Yes                    |
| Temporal   | `TemporalDetectionResult` | No                  | Yes                    |
| GPU        | `GPUDetectionResult`      | Yes (multiple GPUs) | Yes (driver/CUDA/ROCm) |

### Common Patterns

**All detection results include:**

- `available: bool` - Service availability status
- `error_message: str | None` - Error description if unavailable

**Service results with network connection:**

- `host: str` - Service host address
- `port: int` - Service port number

**Results with version information:**

- `version: str | None` - Service version string

## Type Definitions

### Type Annotations

```python
from typing import Protocol

class Detector(Protocol):
    """Protocol for all detector functions."""

    def __call__(self) -> DetectionResult:
        """Run detection and return result."""
        ...

# Type aliases
DetectionResult = Union[
    DockerDetectionResult,
    RedisDetectionResult,
    PostgresDetectionResult,
    TemporalDetectionResult,
    GPUDetectionResult,
]

# Format types
OutputFormat = Literal["text", "json", "yaml"]
```

### Error Types

Detection functions do not raise exceptions for normal operation. All errors are captured in result objects:

```python
result = detect_docker()
if not result.available:
    # Handle unavailable service
    print(f"Error: {result.error_message}")
```

**Common error messages:**

- Docker: "Docker daemon not running", "Permission denied"
- Redis: "Connection refused", "Authentication required"
- PostgreSQL: "Connection refused", "Authentication failed"
- Temporal: "Connection refused", "Server not responding"
- GPU: "No GPU hardware detected", "Driver not installed"

## Usage Patterns

### Basic Detection

```python
from mycelium_onboarding.detection import detect_all

# Simple detection
summary = detect_all()
print(f"Services available: {summary.has_docker}, {summary.has_redis}")
```

### Async Detection

```python
import asyncio
from mycelium_onboarding.detection import detect_all_async

async def check_services():
    summary = await detect_all_async()
    return summary.has_docker and summary.has_redis

# In async context
result = await check_services()
```

### Config Integration

```python
from mycelium_onboarding.detection import detect_all, update_config_from_detection
from mycelium_onboarding.config.manager import ConfigManager

# Detect and update config
summary = detect_all()
config = update_config_from_detection(summary)

# Save config
manager = ConfigManager()
manager.save(config)
```

### Report Generation

```python
from mycelium_onboarding.detection import detect_all, generate_detection_report
import json

# Generate JSON report
summary = detect_all()
json_report = generate_detection_report(summary, format="json")
data = json.loads(json_report)

# Access specific values
docker_version = data["docker"]["version"]
redis_instances = len(data["redis"]["instances"])
```

## Performance Considerations

### Parallelization

All detections run in parallel using ThreadPoolExecutor:

- Maximum 5 concurrent detections
- Individual timeouts prevent hanging
- Total time typically 2-3 seconds

### Timeouts

Default timeouts for each service:

- Docker: Internal timeout (immediate)
- Redis: 1.0 second per port
- PostgreSQL: 2.0 seconds per port
- Temporal: 2.0 seconds
- GPU: 5.0 seconds (command execution)

### Caching

Detection results are not cached by default. For applications requiring frequent checks, implement caching:

```python
import time
from functools import lru_cache

@lru_cache(maxsize=1)
def cached_detect_all():
    return detect_all()

# Clear cache every 60 seconds
last_detection = time.time()
if time.time() - last_detection > 60:
    cached_detect_all.cache_clear()
    last_detection = time.time()
```

## See Also

- [Detection Guide](detection-guide.md) - User guide with examples
- [Integration Guide](detection-integration.md) - Integration patterns
- [Configuration Reference](configuration-reference.md) - Config system API
- [Architecture Overview](ARCHITECTURE_DIAGRAMS.md) - System architecture

______________________________________________________________________

For issues or contributions, visit: https://github.com/gsornsen/mycelium
